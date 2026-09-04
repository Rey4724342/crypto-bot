import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
import time
from google import genai

st.set_page_config(
    page_title="Crypto AI Trading Hub & Analyst Pro - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

# 🔒 CSS Khusus Mobile & Desktop
responsive_css = """
            <style>
            #MainMenu {display: none !important;}
            header {display: none !important;}
            footer {display: none !important;}
            .stAppHeader {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="stDecoration"] {display: none !important;}
            [data-testid="stStatusWidget"] {display: none !important;}
            div[class*="viewerBadge"] {display: none !important;}

            @media screen and (max-width: 768px) {
                .stTabs [data-baseweb="tab-list"] {
                    gap: 4px;
                    overflow-x: auto;
                    flex-wrap: nowrap;
                }
                .stTabs [data-baseweb="tab"] {
                    font-size: 12px;
                    padding: 8px 10px;
                }
                div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                    width: 100% !important;
                    min-width: 100% !important;
                }
            }
            </style>
            """
st.markdown(responsive_css, unsafe_allow_html=True)

# Inisialisasi Session States
if 'journal' not in st.session_state:
    st.session_state.journal = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'academy_step' not in st.session_state:
    st.session_state.academy_step = 1
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# 🚀 FUNGSI HELPER PEMANGGILAN AI GEMINI
def call_gemini_ai(prompt, api_key):
    client = genai.Client(api_key=api_key)
    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                error_str = str(e)
                if '503' in error_str or 'UNAVAILABLE' in error_str:
                    time.sleep(2)
                    continue
                else:
                    break
                    
    return "⚠️ Server Google AI sedang sangat sibuk (overload). Silakan coba kirim pertanyaan sekali lagi."

@st.cache_data(ttl=300)
def get_indodax_summary():
    try:
        url = "https://indodax.com/api/summaries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers, timeout=5).json()
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        
        pairs_dict = {}
        for item in res:
            ticker_id = item.get('ticker_id', '')
            if ticker_id.endswith('_idr'):
                symbol = item.get('symbol', ticker_id.replace('_idr', '').upper()).upper()
                desc = item.get('description', symbol)
                clean_name = f"{symbol} - {desc}" if desc.upper() != symbol else symbol
                logo_url = item.get('url_logo_png', '')
                
                pairs_dict[clean_name] = {
                    'ticker_id': ticker_id,
                    'symbol': symbol,
                    'clean_name': clean_name,
                    'logo_url': logo_url
                }
        return dict(sorted(pairs_dict.items()))
    except Exception:
        return {
            "BTC - Bitcoin": {
                'ticker_id': 'btc_idr', 
                'symbol': 'BTC', 
                'clean_name': 'BTC - Bitcoin', 
                'logo_url': 'https://indodax.com/v2/logo/png/color/btc.png'
            }
        }

@st.cache_data(ttl=1800)
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/"
        res = requests.get(url, timeout=5).json()
        data = res['data'][0]
        return data['value'], data['value_classification']
    except Exception:
        return "50", "Neutral"

@st.cache_data(ttl=900)
def get_crypto_news_robust():
    try:
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(res.content)
        
        news_items = []
        namespaces = {
            'media': 'http://search.yahoo.com/mrss/',
            'content': 'http://purl.org/rss/1.0/modules/content/'
        }

        for item in root.findall('./channel/item')[:6]:
            title = item.find('title').text if item.find('title') is not None else 'Berita Crypto'
            link = item.find('link').text if item.find('link') is not None else '#'
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            image_url = ""
            media_content = item.find('media:content', namespaces)
            if media_content is not None and 'url' in media_content.attrib:
                image_url = media_content.attrib['url']
            else:
                media_thumbnail = item.find('media:thumbnail', namespaces)
                if media_thumbnail is not None and 'url' in media_thumbnail.attrib:
                    image_url = media_thumbnail.attrib['url']
                else:
                    enclosure = item.find('enclosure')
                    if enclosure is not None and 'url' in enclosure.attrib:
                        image_url = enclosure.attrib['url']

            if not image_url:
                image_url = "https://images.cointelegraph.com/images/1200_aHR0cHM6Ly9zMy5jb2ludGVsZWdyYXBoLmNvbS91cGxvYWRzLzIwMjEtMDMvYTM1ZDgyMGUtZGVhMS00OWViLThkYTAtOGE4OGFiZmM0ODNmLmpwZw==.jpg"

            description = ""
            desc_node = item.find('description')
            if desc_node is not None and desc_node.text:
                clean_desc = re.sub('<[^<]+?>', '', desc_node.text)
                description = clean_desc[:130] + "..." if len(clean_desc) > 130 else clean_desc

            news_items.append({
                'title': title,
                'link': link,
                'image': image_url,
                'date': pub_date[:16] if pub_date else "Terbaru",
                'desc': description
            })
            
        return news_items
    except Exception:
        return []

# 📈 FUNGSI PEMPROSES KANDEL & RSI SEDERHANA
@st.cache_data(ttl=300)
def get_technical_indicators(pair_symbol):
    try:
        url = f"https://indodax.com/tradingview/history?symbol={pair_symbol}IDR&resolution=D&from={int(time.time())-30*86400}&to={int(time.time())}"
        res = requests.get(url, timeout=5).json()
        if res.get('s') == 'ok':
            closes = pd.Series(res['c'])
            ma20 = closes.rolling(20).mean().iloc[-1]
            
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi14 = 100 - (100 / (1 + rs)).iloc[-1]
            return round(rsi14, 2), round(ma20, 2)
    except Exception:
        pass
    return None, None

pairs_data = get_all_indodax_pairs()

# Header Utama
st.title("🚀 Crypto AI Trading Hub & Analyst Pro")
st.markdown("<h4 style='color: #4CAF50; margin-top: -15px;'>👨‍💻 Pencipta: <b>Rey472</b></h4>", unsafe_allow_html=True)

# 🎨 EFEK ANIMASI MENU DENGAN TOMBOL MEMBAL
animation_menu_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
  body { background-color: transparent; color: #f8fafc; padding: 5px; }
  .card-container { background-color: #1e293b; border-radius: 16px; padding: 15px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
  .menu-group { display: flex; gap: 8px; margin-bottom: 15px; }
  .btn-menu { flex: 1; padding: 10px 12px; border: none; border-radius: 10px; background-color: #334155; color: #94a3b8; font-weight: 600; font-size: 14px; cursor: pointer; transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), background-color 0.2s ease, color 0.2s ease; }
  .btn-menu:active { transform: translateY(2px) scale(0.94); }
  .btn-menu.active { background-color: #10b981; color: #0f172a; }
  .fitur-wrapper { min-height: 70px; }
  .fitur-box { display: none; opacity: 0; transform: translateY(12px); transition: opacity 0.3s ease-out, transform 0.3s ease-out; }
  .fitur-box.show { display: block; opacity: 1; transform: translateY(0); }
  .fitur-box h3 { color: #10b981; margin-bottom: 4px; font-size: 16px; }
  .fitur-box p { color: #cbd5e1; font-size: 13px; line-height: 1.4; }
</style>
</head>
<body>
  <div class="card-container">
    <div class="menu-group">
      <button class="btn-menu active" onclick="gantiFitur(event, 'fitur1')">Fitur 1</button>
      <button class="btn-menu" onclick="gantiFitur(event, 'fitur2')">Fitur 2</button>
      <button class="btn-menu" onclick="gantiFitur(event, 'fitur3')">Fitur 3</button>
    </div>
    <div class="fitur-wrapper">
      <div id="fitur1" class="fitur-box show">
        <h3>🚀 Fitur Utama</h3>
        <p>Gunakan dashboard interaktif untuk memantau pergerakan harga pasar real-time.</p>
      </div>
      <div id="fitur2" class="fitur-box">
        <h3>📊 Analisis Data</h3>
        <p>Analisis tren pasar Indodax dan indikator teknikal dengan cepat.</p>
      </div>
      <div id="fitur3" class="fitur-box">
        <h3>⚙️ Pengaturan Strategi</h3>
        <p>Atur strategi Swing atau Scalping sesuai dengan gaya trading kamu.</p>
      </div>
    </div>
  </div>
  <script>
    function gantiFitur(evt, fiturId) {
      document.querySelectorAll('.btn-menu').forEach(btn => btn.classList.remove('active'));
      evt.currentTarget.classList.add('active');
      document.querySelectorAll('.fitur-box').forEach(box => {
        box.classList.remove('show');
        box.style.display = 'none';
      });
      const targetBox = document.getElementById(fiturId);
      targetBox.style.display = 'block';
      setTimeout(() => { targetBox.classList.add('show'); }, 20);
    }
  </script>
</body>
</html>
"""
components.html(animation_menu_html, height=185)

st.markdown("---")

st.markdown("### ⚙️ Pengaturan Koin & Strategi")
menu_col1, menu_col2, menu_col3 = st.columns([2, 2, 1])

with menu_col1:
    selected_label = st.selectbox(
        "🔍 Cari & Pilih Koin Utama:",
        options=list(pairs_data.keys()),
        index=0
    )

with menu_col2:
    trading_style = st.radio(
        "🎯 Pilih Mode Strategi AI:",
        ["Swing Trading (Santai / Menengah)", "Scalping (Cepat / Intraday)"],
        horizontal=True
    )

selected_info = pairs_data[selected_label]
ticker_id = selected_info['ticker_id']
symbol = selected_info['symbol']

# ⭐ FITUR WATCHLIST / KOIN FAVORIT
with menu_col3:
    st.write("")
    st.write("")
    if symbol not in st.session_state.watchlist:
        if st.button("⭐ Tambah Watchlist", use_container_width=True):
            st.session_state.watchlist.append(symbol)
            st.success(f"{symbol} masuk favorit!")
    else:
        if st.button("❌ Hapus Watchlist", use_container_width=True):
            st.session_state.watchlist.remove(symbol)
            st.rerun()

if st.session_state.watchlist:
    st.caption(f"⭐ **Watchlist Kamu:** {', '.join(st.session_state.watchlist)}")

st.markdown("---")

tab_main, tab_edu, tab_sentimen, tab_compare, tab_journal, tab_calc, tab_chat = st.tabs([
    "📈 Dashboard Utama & AI",
    "🎓 Akademi & Ujian Kasus",
    "📰 Sentimen & Berita Market",
    "🔀 Perbandingan Koin", 
    "📓 Jurnal Trading & Checklist", 
    "🧮 Kalkulator, Averaging & DCA",
    "💬 Asisten AI Chat"
])

# ================= TAB 1: DASHBOARD UTAMA =================
with tab_main:
    st.markdown("### 🔥 Top Market Movers (24 Jam)")
    summary_data = get_indodax_summary()

    if summary_data and 'tickers' in summary_data:
        tickers = summary_data['tickers']
        mover_list = []
        
        for k, v in tickers.items():
            if k.endswith('_idr'):
                sym = k.replace('_idr', '').upper()
                try:
                    last_price = float(v.get('last', 0))
                    high_price = float(v.get('high', 0))
                    low_price = float(v.get('low', 0))
                    avg_price = (high_price + low_price) / 2 if (high_price + low_price) > 0 else last_price
                    change_pct = ((last_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0.0
                    mover_list.append({'Symbol': sym, 'Harga': last_price, 'Perubahan (%)': change_pct})
                except ValueError:
                    continue

        if mover_list:
            df_movers = pd.DataFrame(mover_list)
            top_gainers = df_movers.sort_values(by='Perubahan (%)', ascending=False).head(3)
            top_losers = df_movers.sort_values(by='Perubahan (%)', ascending=True).head(3)

            g_col, l_col = st.columns(2)
            with g_col:
                st.success("🟢 **Top Gainers**")
                for _, r in top_gainers.iterrows():
                    st.write(f"**{r['Symbol']}**: Rp {int(r['Harga']):,} (`+{r['Perubahan (%)']:.2f}%`)")
            with l_col:
                st.error("🔴 **Top Losers**")
                for _, r in top_losers.iterrows():
                    st.write(f"**{r['Symbol']}**: Rp {int(r['Harga']):,} (`{r['Perubahan (%)']:.2f}%`)")

    st.markdown("---")

    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if selected_info['logo_url']:
            st.image(selected_info['logo_url'], width=64)
    with col_title:
        st.subheader(f"{symbol} / IDR")

    # 📊 INDIKATOR TEKNIKAL OTOMATIS (RSI & MA)
    rsi_val, ma20_val = get_technical_indicators(symbol)
    if rsi_val and ma20_val:
        rsi_status = "🟢 Oversold (Potensi Beli)" if rsi_val <= 30 else ("🔴 Overbought (Rawan Jual)" if rsi_val >= 70 else "🟡 Netral")
        st.info(f"📊 **Sinyal Indikator Otomatis**: RSI (14) = **{rsi_val}** [{rsi_status}] | MA (20) = **Rp {int(ma20_val):,}**")

    # 📊 GRAFIK TRADINGVIEW
    st.markdown("#### 📊 Grafik Candlestick Market (Real-Time)")
    
    tv_widget_code = f"""
    <div class="tradingview-widget-container" style="height:480px;width:100%">
      <div id="tradingview_chart" style="height:480px;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "BINANCE:{symbol}USDT",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "id",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_widget_code, height=490)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.link_button(f"🔗 Buka Chart {symbol} (Tab Baru)", f"https://id.tradingview.com/chart/?symbol=BINANCE:{symbol}USDT", use_container_width=True)
    with col_btn2:
        st.link_button(f"🌐 Buka Market {symbol} (Indodax)", f"https://indodax.com/market/{symbol}IDR", use_container_width=True)

    st.markdown("---")

    st.markdown(f"### 💼 Analisis Posisi Portofolio Saya ({symbol})")
    st.caption("💡 *Ketik angka polos tanpa titik/koma (misal: 1324307).*")

    with st.form("portfolio_form"):
        col_input1, col_input2, col_input3, col_input4 = st.columns(4)
        with col_input1:
            my_buy_price = st.number_input(f"Harga Beli Awal Kamu (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        with col_input2:
            my_amount_coin = st.number_input(f"Jumlah Koin {symbol}:", min_value=0.0, value=0.0, step=0.1, format="%.4f")
        with col_input3:
            target_tp = st.number_input(f"Target Take Profit (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        with col_input4:
            stop_loss_input = st.number_input(f"Rencana Stop Loss (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        
        btn_submit = st.form_submit_button("🤖 Mulaikan Analisis AI Posisi Saya", use_container_width=True)

    if btn_submit or (my_buy_price > 0):
        try:
            url = f"https://indodax.com/api/ticker/{ticker_id}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5).json()['ticker']
            
            current_market_price = int(res['last'])
            high = int(res['high'])
            low = int(res['low'])

            if my_buy_price > 0:
                pnl_rp = (current_market_price - my_buy_price) * my_amount_coin
                pnl_pct = ((current_market_price - my_buy_price) / my_buy_price) * 100
            else:
                pnl_rp = 0
                pnl_pct = 0

            c1, c2, c3 = st.columns(3)
            c1.metric(label="Harga Pasar Saat Ini", value=f"Rp {current_market_price:,}")
            c2.metric(label="Modal/Harga Beli Kamu", value=f"Rp {int(my_buy_price):,}")
            
            if my_buy_price > 0:
                if pnl_pct >= 0:
                    c3.metric(label="Status PnL (Keuntungan)", value=f"+Rp {int(pnl_rp):,}", delta=f"+{pnl_pct:.2f}%")
                else:
                    c3.metric(label="Status PnL (Kerugian)", value=f"-Rp {abs(int(pnl_rp)):,}", delta=f"{pnl_pct:.2f}%")

                # 📊 FITUR 3: INDIKATOR MANAJEMEN RISIKO (RISK-TO-REWARD RATIO)
                if target_tp > my_buy_price and stop_loss_input > 0 and stop_loss_input < my_buy_price:
                    potential_reward = target_tp - my_buy_price
                    potential_risk = my_buy_price - stop_loss_input
                    rr_ratio = potential_reward / potential_risk if potential_risk > 0 else 0
                    
                    st.markdown("---")
                    if rr_ratio >= 2.0:
                        st.success(f"⚖️ **Rasio Risk-to-Reward:** 1 : {rr_ratio:.2f} *(Kategori: Sangat Baik / Ideal)*")
                    elif rr_ratio >= 1.0:
                        st.warning(f"⚖️ **Rasio Risk-to-Reward:** 1 : {rr_ratio:.2f} *(Kategori: Cukup / Moderat)*")
                    else:
                        st.error(f"⚖️ **Rasio Risk-to-Reward:** 1 : {rr_ratio:.2f} *(Kategori: Berisiko Tinggi / Potensi Potong Rugi Lebih Besar dari Untung)*")

                # 📊 TARGET PROFIT PROGRESS BAR
                if target_tp > my_buy_price:
                    progress_pct = min(max((current_market_price - my_buy_price) / (target_tp - my_buy_price), 0.0), 1.0)
                    st.write(f"🎯 **Kemajuan Menuju Target Profit (Rp {int(target_tp):,}):**")
                    st.progress(progress_pct)

            if btn_submit:
                api_key = st.secrets.get("GEMINI_API_KEY")

                if not api_key:
                    st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
                else:
                    with st.spinner(f"AI sedang merespon analisis cepat koin {symbol}..."):
                        # FITUR 4: PROMPT AI DIOPTIMALKAN UNTUK EVALUASI RISIKO & SL
                        prompt = f"""
                        Kamu adalah konsultan Trading Crypto profesional buatan Rey472.
                        Gaya Trading Pengguna: {trading_style}
                        
                        Data Posisi Pengguna:
                        - Nama Aset: {selected_info['clean_name']}
                        - Harga Beli Awal Pengguna: Rp {my_buy_price:,}
                        - Harga Pasar Saat Ini: Rp {current_market_price:,}
                        - Status Profit/Loss Sementara: {pnl_pct:.2f}% (Rp {int(pnl_rp):,})
                        - Target TP Pengguna: Rp {target_tp:,}
                        - Rencana Stop Loss (SL) Pengguna: Rp {stop_loss_input:,}
                        - Harga Tertinggi 24j: Rp {high:,}
                        - Harga Terendah 24j: Rp {low:,}

                        Berikan analisis ringkas, padat, dan taktis dalam format poin rapi:
                        1. 🌐 Analisis Posisi Saat Ini
                        2. 🟢 Rekomendasi Aksi Utama: (HOLD / TAKE PROFIT / CUT LOSS / BUY ON DIP)
                        3. 🛑 Evaluasi Rencana Stop Loss (SL) Pengguna (Apakah SL Rp {stop_loss_input:,} sudah aman dari Stop Loss Hunting/Swing Rendah?).
                        4. 🎯 Target Jual / Take Profit (TP1 & TP2) Rekomendasi AI dalam Rupiah.
                        5. 💡 Catatan Khusus AI Rey472 Mengenai Manajemen Risiko Posisi Ini.
                        """
                        
                        ai_reply = call_gemini_ai(prompt, api_key)
                        st.markdown("### 🤖 Hasil Penjelasan & Rekomendasi AI Rey472")
                        st.info(ai_reply)
                    
        except Exception as e:
            st.error(f"Gagal memuat analisis: {e}")

# ================= TAB 2: AKADEMI & UJIAN KASUS =================
with tab_edu:
    st.markdown("### 🎓 Akademi & Ujian Simulasi Kasus Nyata")
    st.caption("Belajar teori saja tidak cukup! Uji pemahamanmu lewat studi kasus nyata agar tidak bingung saat terjun langsung.")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        if st.button("🚀 Misi 1: Dasar & Psikologi", use_container_width=True):
            st.session_state.academy_step = 1
    with col_m2:
        if st.button("🕯️ Misi 2: Candlestick", use_container_width=True):
            st.session_state.academy_step = 2
    with col_m3:
        if st.button("🧱 Misi 3: Support/Resist", use_container_width=True):
            st.session_state.academy_step = 3
    with col_m4:
        if st.button("📊 Misi 4: Lab Charting", use_container_width=True):
            st.session_state.academy_step = 4

    st.markdown("---")

    if st.session_state.academy_step == 1:
        st.markdown("### 🚀 Misi 1: Pengelolaan Modal & Mental Trader")
        st.info("🎯 **Target Misi:** Menguji kedisiplinan mengelola risiko modal.")
        
        st.write("""
        **Materi Singkat:** Jangan pernah memasukkan uang pinjaman atau uang SPP/belanja dapur ke market crypto karena pasar bisa naik-turun sewaktu-waktu.
        """)
        
        st.markdown("#### 📝 Ujian Kasus Nyata Misi 1:")
        st.warning("⚠️ **Studi Kasus:** Kamu memiliki uang tabungan darurat sebesar Rp 2.000.000 yang akan dipakai minggu depan untuk bayar kontrakan. Tiba-tiba temanmu mengajak beli koin baru yang sedang viral. Apa tindakan yang benar?")
        
        ans_m1 = st.radio(
            "Pilih keputusan terbaikmu:",
            [
                "A. Masukkan setengah uang kontrakan ke koin tersebut biar cepat untung.",
                "B. Tolak ajakan tersebut karena itu bukan 'uang dingin' (melanggar manajemen risiko).",
                "C. Pinjam uang online dulu buat modal trading."
            ],
            index=None,
            key="quiz_m1"
        )
        
        if ans_m1:
            if ans_m1.startswith("B"):
                st.success("🎉 **BENAR SEKALI!** Uang kebutuhan jangka pendek tidak boleh dipakai trading. Kamu lulus ujian mental Misi 1!")
                if st.button("➡️ Lanjut ke Misi 2"):
                    st.session_state.academy_step = 2
                    st.rerun()
            else:
                st.error("❌ **SALAH/KELIRU!** Keputusan ini sangat berbahaya dalam dunia crypto dan bisa berujung stres finansial. Coba pilih opsi yang aman!")

    elif st.session_state.academy_step == 2:
        st.markdown("### 🕯️ Misi 2: Membaca Psikologi Candlestick")
        st.info("🎯 **Target Misi:** Menafsirkan arah tren lewat bentuk candle.")

        st.write("Perhatikan animasi pergerakan candle di bawah ini:")

        candlestick_anim = """
        <div style="display: flex; justify-content: space-around; background-color: #11141c; padding: 20px; border-radius: 12px; font-family: sans-serif; color: white;">
            <div style="text-align: center; width: 45%;">
                <h4 style="color: #00E676; margin-bottom: 5px;">🟢 Hijau (Bullish)</h4>
                <p style="font-size: 12px; color: #aaa;">Harga NAIK (Buyer Dominan)</p>
                <svg width="100" height="150">
                    <line x1="50" y1="10" x2="50" y2="140" stroke="#00E676" stroke-width="3" />
                    <rect x="30" y="30" width="40" height="80" fill="#00E676" rx="4">
                        <animate attributeName="height" values="20;80;20" dur="3s" repeatCount="indefinite" />
                    </rect>
                </svg>
            </div>
            <div style="text-align: center; width: 45%;">
                <h4 style="color: #FF5252; margin-bottom: 5px;">🔴 Merah (Bearish)</h4>
                <p style="font-size: 12px; color: #aaa;">Harga TURUN (Seller Dominan)</p>
                <svg width="100" height="150">
                    <line x1="50" y1="10" x2="50" y2="140" stroke="#FF5252" stroke-width="3" />
                    <rect x="30" y="30" width="40" height="80" fill="#FF5252" rx="4">
                        <animate attributeName="height" values="20;80;20" dur="3s" repeatCount="indefinite" />
                    </rect>
                </svg>
            </div>
        </div>
        """
        components.html(candlestick_anim, height=270)

        st.markdown("#### 📝 Ujian Kasus Nyata Misi 2:")
        st.warning("⚠️ **Studi Kasus:** Kamu melihat grafik harga sebuah koin membentuk 3 candle merah besar berturut-turut turun menembus batas bawah. Apa arti kondisi pasar ini?")
        
        ans_m2 = st.radio(
            "Pilih analisis yang paling logis:",
            [
                "A. Tekanan jual (seller) sedang sangat kuat, pasar sedang bearish/turun.",
                "B. Sebentar lagi harga pasti naik drastis, jadi harus langsung all-in.",
                "C. Market sedang libur."
            ],
            index=None,
            key="quiz_m2"
        )

        if ans_m2:
            if ans_m2.startswith("A"):
                st.success("🎉 **TEPAT SEKALI!** Tiga candle merah panjang menandakan dominasi seller yang kuat. Kamu paham cara membaca momentum!")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("⬅️ Kembali ke Misi 1"):
                        st.session_state.academy_step = 1
                        st.rerun()
                with col_b2:
                    if st.button("➡️ Lanjut ke Misi 3"):
                        st.session_state.academy_step = 3
                        st.rerun()
            else:
                st.error("❌ **Kurang tepat.** Jangan melawan arus tren turun yang kuat tanpa konfirmasi sinyal pantulan.")

    elif st.session_state.academy_step == 3:
        st.markdown("### 🧱 Misi 3: Menentukan Area Support & Resistance")
        st.info("🎯 **Target Misi:** Menempatkan titik eksekusi beli dan jual yang rasional.")

        col_sup, col_res = st.columns(2)
        with col_sup:
            st.success("🧱 **Support (Lantai Bawah)**")
            st.write("Tempat berkumpulnya pembeli (Buyer). Cocok untuk pasang posisi **Buy**.")
        with col_res:
            st.error("🧱 **Resistance (Atap Atas)**")
            st.write("Tempat berkumpulnya penjual (Seller). Cocok untuk pasang posisi **Take Profit**.")

        st.markdown("---")
        st.markdown("#### 📝 Ujian Kasus Nyata Misi 3:")
        st.warning("⚠️ **Studi Kasus:** Harga koin A sedang mendekati garis 'Atap' (Resistance) kuat dan mulai melambat kenaikannya. Tindakan apa yang paling bijak dilakukan trader?")
        
        ans_m3 = st.radio(
            "Pilih strategi yang tepat:",
            [
                "A. Memborong lebih banyak koin di harga pucuk resistance.",
                "B. Bersiap merealisasikan keuntungan (Take Profit) sebagian atau seluruhnya.",
                "C. Mematikan aplikasi dan tidur."
            ],
            index=None,
            key="quiz_m3"
        )

        if ans_m3:
            if ans_m3.startswith("B"):
                st.success("🎉 **HEBAT!** Area resistance adalah area rawan koreksi, sehingga mengambil profit di sana adalah keputusan profesional.")
                if st.button("➡️ Lanjut ke Misi 4: Lab Praktik Charting"):
                    st.session_state.academy_step = 4
                    st.rerun()
            else:
                st.error("❌ **Kurang tepat.** Membeli di area resistance memiliki risiko tinggi terkena penolakan harga (rejection).")

    elif st.session_state.academy_step == 4:
        st.markdown("### 📊 Misi 4: Lab Praktik Langsung di TradingView")
        st.info("🎯 **Target Misi:** Mempraktikkan analisis mandiri di chart profesional.")

        st.write("""
        Gunakan chart di bawah ini untuk menguji kemampuanmu memasang garis bantu (garis horizontal support/resistance) secara mandiri:
        """)

        practice_chart_code = """
        <div class="tradingview-widget-container" style="height:480px;width:100%">
          <div id="tradingview_practice" style="height:480px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({
            "autosize": true,
            "symbol": "BINANCE:BTCUSDT",
            "interval": "D",
            "timezone": "Asia/Jakarta",
            "theme": "dark",
            "style": "1",
            "locale": "id",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_practice"
          });
          </script>
        </div>
        """
        components.html(practice_chart_code, height=490)

        st.success("🏆 **Selamat!** Kamu telah menyelesaikan seluruh rangkaian materi & ujian studi kasus interaktif di Akademi Rey472!")

# ================= TAB 3: SENTIMEN & BERITA MARKET =================
with tab_sentimen:
    st.markdown("### 🧠 Sentimen Pasar Crypto Global & Berita Real-Time")
    
    col_fg, col_news = st.columns([1, 2])
    
    with col_fg:
        st.markdown("#### 😱 Fear & Greed Index")
        fng_val, fng_class = get_fear_and_greed()
        
        try:
            val_num = int(fng_val)
        except ValueError:
            val_num = 50
            
        if val_num <= 25:
            color_code = "#FF4D4D"
        elif val_num <= 45:
            color_code = "#FFA500"
        elif val_num <= 55:
            color_code = "#FFD700"
        elif val_num <= 75:
            color_code = "#90EE90"
        else:
            color_code = "#00E676"

        st.markdown(
            f"""
            <div style="
                border: 2px solid {color_code}; 
                border-radius: 12px; 
                padding: 20px; 
                text-align: center; 
                background-color: #1a1c23;
                margin-bottom: 15px;">
                <h1 style="color: {color_code}; font-size: 64px; margin: 0;">{fng_val}</h1>
                <h3 style="color: #FFFFFF; margin: 10px 0 0 0;">{fng_class.upper()}</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.caption("💡 **Cara Membaca Index:**")
        st.write("• **0-45 (Fear)**: Pasar sedang takut/diskonto. Sering dianggap area peluang beli (*Buy the Dip*).")
        st.write("• **55-100 (Greed)**: Pasar sedang sangat optimis/FOMO. Hati-hati potensi koreksi mendadak.")

    with col_news:
        st.markdown("#### 📰 Berita Crypto Terkini Real-Time")
        news_list = get_crypto_news_robust()
        
        if news_list:
            for news in news_list:
                img_col, text_col = st.columns([1, 3])
                with img_col:
                    st.image(news['image'], use_container_width=True)
                with text_col:
                    st.markdown(f"**[{news['title']}]({news['link']})**")
                    st.caption(f"🗓️ {news['date']} | 🌐 CoinDesk")
                    if news['desc']:
                        st.write(news['desc'])
                st.markdown("---")
        else:
            st.info("Gagal mengambil berita. Silakan muat ulang halaman.")

# ================= TAB 4: PERBANDINGAN KOIN =================
with tab_compare:
    st.markdown("### 🔀 Bandingkan 2 Koin Indodax")
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        coin1_label = st.selectbox("Pilih Koin Pertama:", options=list(pairs_data.keys()), index=0)
    with comp_col2:
        coin2_label = st.selectbox("Pilih Koin Kedua:", options=list(pairs_data.keys()), index=min(1, len(pairs_data)-1))
        
    if st.button("⚖️ Bandingkan Sekarang"):
        try:
            t1 = pairs_data[coin1_label]['ticker_id']
            t2 = pairs_data[coin2_label]['ticker_id']
            
            res1 = requests.get(f"https://indodax.com/api/ticker/{t1}", timeout=5).json()['ticker']
            res2 = requests.get(f"https://indodax.com/api/ticker/{t2}", timeout=5).json()['ticker']
            
            c1_col, c2_col = st.columns(2)
            with c1_col:
                st.subheader(coin1_label)
                st.metric("Harga Terakhir", f"Rp {int(res1['last']):,}")
                st.metric("High 24j", f"Rp {int(res1['high']):,}")
                st.metric("Low 24j", f"Rp {int(res1['low']):,}")
                st.metric("Volume 24j", f"{float(res1['vol_idr']):,.0f} IDR")
                
            with c2_col:
                st.subheader(coin2_label)
                st.metric("Harga Terakhir", f"Rp {int(res2['last']):,}")
                st.metric("High 24j", f"Rp {int(res2['high']):,}")
                st.metric("Low 24j", f"Rp {int(res2['low']):,}")
                st.metric("Volume 24j", f"{float(res2['vol_idr']):,.0f} IDR")
        except Exception as err:
            st.error(f"Gagal membandingkan koin: {err}")

# ================= TAB 5: JURNAL & CHECKLIST TRADING =================
with tab_journal:
    col_j1, col_j2 = st.columns([2, 1])
    
    with col_j1:
        st.markdown("### 📓 Jurnal Catatan Trading")
        
        with st.form("journal_form"):
            j_coin = st.text_input("Nama Koin / Ticker:", value=symbol)
            j_type = st.selectbox("Tipe Transaksi:", ["BUY / BELI", "SELL / JUAL"])
            j_price = st.number_input("Harga Beli/Jual (Rp):", min_value=0.0, value=0.0, step=100.0)
            j_notes = st.text_area("Catatan Alasan Trade / Strategi:")
            
            submitted = st.form_submit_button("➕ Simpan ke Catatan")
            if submitted:
                st.session_state.journal.append({
                    "Koin": j_coin,
                    "Tipe": j_type,
                    "Harga": f"Rp {j_price:,.0f}",
                    "Catatan": j_notes
                })
                st.success("Catatan trading tersimpan!")

        if st.session_state.journal:
            st.markdown("#### 📜 Riwayat Catatan Kamu:")
            df_j = pd.DataFrame(st.session_state.journal)
            st.dataframe(df_j, use_container_width=True)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                # 📥 DOWNLOAD JURNAL TO CSV
                csv_data = df_j.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Unduh Jurnal (File CSV)",
                    data=csv_data,
                    file_name="jurnal_trading_rey472.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_d2:
                if st.button("🗑️ Hapus Semua Catatan", use_container_width=True):
                    st.session_state.journal = []
                    st.rerun()

    # 📝 TRADE PLANNER CHECKLIST (ANTI FOMO)
    with col_j2:
        st.markdown("### ✅ Trade Planner Checklist")
        st.caption("Pastikan centang semua sebelum menekan tombol beli!")
        c_fomo1 = st.checkbox("Gunakan Uang Dingin (Bukan SPP/Utang)")
        c_fomo2 = st.checkbox("Sudah Menentukan Stop Loss (SL)")
        c_fomo3 = st.checkbox("Risk to Reward Minimal 1:2")
        c_fomo4 = st.checkbox("Tidak Terpancing Emosi FOMO / Viral")
        
        if c_fomo1 and c_fomo2 and c_fomo3 and c_fomo4:
            st.success("🔥 **SIAP ENTRY!** Kedisiplinanmu sudah 100% terjaga.")
        else:
            st.warning("⚠️ Selesaikan semua checklist disiplin di atas.")

# ================= TAB 6: KALKULATOR & DCA =================
with tab_calc:
    st.markdown("### 🧮 Kalkulator Trading, Averaging & Simulasi DCA")
    
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        st.markdown("#### 1. Risk / Reward Calculator")
        modal_rp = st.number_input("Modal Trading Kamu (Rp):", min_value=0.0, value=0.0, step=50000.0)
        risk_pct = st.slider("Batas Toleransi Rugi per Trade (% Modal):", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
        entry_price = st.number_input("Rencana Harga Beli (Entry Rp):", min_value=0.0, value=0.0)
        sl_price = st.number_input("Rencana Stop Loss (SL Rp):", min_value=0.0, value=0.0)

        if entry_price > 0 and sl_price > 0 and entry_price > sl_price:
            potensi_rugi_per_koin = entry_price - sl_price
            persen_rugi_koin = (potensi_rugi_per_koin / entry_price) * 100
            maks_resiko_rp = modal_rp * (risk_pct / 100)
            rekomendasi_posisi_rp = (maks_resiko_rp / persen_rugi_koin) * 100 if persen_rugi_koin > 0 else 0
            
            st.info(f"💡 Maksimal Rugi Aman: **Rp {int(maks_resiko_rp):,}**")
            st.success(f"💡 Alokasi Beli Ideal: **Rp {int(min(rekomendasi_posisi_rp, modal_rp)):,}**")

        st.markdown("---")
        st.markdown("#### 2. Kalkulator Averaging Down")
        avg_price1 = st.number_input("Harga Beli Pertama (Rp):", min_value=0.0, value=0.0, key="avg_p1")
        avg_qty1 = st.number_input(f"Jumlah Koin {symbol} Beli Pertama:", min_value=0.0, value=0.0, key="avg_q1")
        
        avg_price2 = st.number_input("Harga Beli Kedua / Serok (Rp):", min_value=0.0, value=0.0, key="avg_p2")
        avg_qty2 = st.number_input(f"Jumlah Koin {symbol} Beli Kedua:", min_value=0.0, value=0.0, key="avg_q2")

        if (avg_qty1 + avg_qty2) > 0:
            total_modal = (avg_price1 * avg_qty1) + (avg_price2 * avg_qty2)
            total_koin = avg_qty1 + avg_qty2
            avg_final_price = total_modal / total_koin
            
            st.success(f"🎯 **Harga Rata-Rata Baru**: Rp {avg_final_price:,.2f}")

    # 💰 SIMULASI INVESTASI RUTIN (DCA)
    with calc_col2:
        st.markdown("#### 3. Kalkulator Simulasi DCA (Dollar Cost Averaging)")
        st.caption("Hitung estimasi menabung crypto secara konsisten.")
        
        dca_amount = st.number_input("Alokasi Tabungan Rutin (Rp):", min_value=10000.0, value=100000.0, step=50000.0)
        dca_freq = st.selectbox("Frekuensi Menabung:", ["Mingguan (4x / Bulan)", "Bulanan (1x / Bulan)"])
        dca_duration = st.slider("Durasi Menabung (Bulan):", min_value=1, max_value=36, value=12)
        dca_est_return = st.slider("Estimasi Kenaikan Koin pertahun (%):", min_value=-50, max_value=200, value=25)

        total_months = dca_duration
        frequency_count = (total_months * 4) if "Mingguan" in dca_freq else total_months
        total_dca_modal = dca_amount * frequency_count
        
        growth_factor = 1 + (dca_est_return / 100)
        total_est_val = total_dca_modal * growth_factor
        est_profit = total_est_val - total_dca_modal

        st.info(f"💰 Total Modal Terkumpul: **Rp {int(total_dca_modal):,}**")
        st.success(f"🚀 Estimasi Nilai Akhir Portofolio: **Rp {int(total_est_val):,}** (+Rp {int(est_profit):,})")

# ================= TAB 7: ASISTEN AI CHAT =================
with tab_chat:
    st.markdown("### 💬 Asisten Trading AI Rey472")
    st.caption("Tanyakan apa saja seputar strategi crypto, cara membaca grafik, manajemen emosi, atau tips trading secara interaktif.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("Tanyakan sesuatu ke AI Rey472...")

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ API Key belum terkonfigurasi di Streamlit Secrets.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("AI sedang berpikir..."):
                    try:
                        chat_prompt = f"""
                        Kamu adalah Asisten Trading Crypto AI buatan Rey472 yang ramah, taktis, dan cerdas.
                        Koin yang sedang diamati pengguna saat ini: {symbol}.
                        Pertanyaan pengguna: {user_query}

                        Jawab secara jelas, praktis, dan langsung ke inti pembahasan.
                        """
                        reply = call_gemini_ai(chat_prompt, api_key)
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as err:
                        st.error(f"Gagal memproses pesan: {err}")
