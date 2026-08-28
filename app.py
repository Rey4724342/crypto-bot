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

if 'journal' not in st.session_state:
    st.session_state.journal = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'academy_step' not in st.session_state:
    st.session_state.academy_step = 1

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
                symbol = ticker_id.replace('_idr', '').upper()
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

@st.cache_data(ttl=10)
def get_indodax_depth(pair_id):
    try:
        url = f"https://indodax.com/api/depth/{pair_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers, timeout=3).json()
    except Exception:
        return {'buy': [], 'sell': []}

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

def calculate_auto_indicators(last, high, low, buy_volume, sell_volume):
    signals = []
    price_range = high - low if high > low else 1
    pos_pct = ((last - low) / price_range) * 100
    
    if pos_pct > 80:
        signals.append(("⚠️ Overbought (Jenuh Beli)", "Harga mendekati High 24j. Potensi koreksi/profit taking.", "red"))
    elif pos_pct < 20:
        signals.append(("🟢 Oversold (Jenuh Jual)", "Harga mendekati Low 24j. Potensi pantulan Support.", "green"))
    else:
        signals.append(("🔵 Konsolidasi Neutral", "Harga berada di rentang tengah pergerakan harian.", "blue"))

    total_vol = buy_volume + sell_volume
    if total_vol > 0:
        buy_ratio = (buy_volume / total_vol) * 100
        if buy_ratio > 60:
            signals.append(("🔥 Strong Buying Pressure", f"Dominasi Bids sebesar {buy_ratio:.1f}%. Tekanan naik tinggi.", "green"))
        elif buy_ratio < 40:
            signals.append(("🔻 Strong Selling Pressure", f"Dominasi Asks sebesar {100-buy_ratio:.1f}%. Tekanan turun tinggi.", "red"))
        else:
            signals.append(("⚖️ Balanced Market", "Volume Bids dan Asks relatif seimbang.", "gray"))

    return signals

def call_gemini_with_fallback(client, prompt):
    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash']
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and hasattr(response, 'text') and response.text:
                    return response.text
            except Exception:
                time.sleep(1)
    return None

pairs_data = get_all_indodax_pairs()

st.title("🚀 Crypto AI Trading Hub & Analyst Pro")
st.markdown("<h4 style='color: #4CAF50; margin-top: -15px;'>👨‍💻 Pencipta: <b>Rey472</b></h4>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("### ⚙️ Pengaturan Koin & Strategi")
menu_col1, menu_col2 = st.columns(2)

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

st.markdown("---")

tab_main, tab_edu, tab_sentimen, tab_compare, tab_journal, tab_calc, tab_chat = st.tabs([
    "📈 Dashboard Utama & AI",
    "🎓 Akademi & Ujian Kasus",
    "📰 Sentimen & Berita Market",
    "🔀 Perbandingan Koin", 
    "📓 Jurnal Trading", 
    "🧮 Kalkulator & Averaging",
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
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "save_image": false,
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

    col_sig, col_ob = st.columns([1, 1])

    depth_data = get_indodax_depth(ticker_id)
    bids = depth_data.get('buy', [])[:5]
    asks = depth_data.get('sell', [])[:5]

    total_bid_vol = sum([float(b[1]) for b in bids]) if bids else 0
    total_ask_vol = sum([float(a[1]) for a in asks]) if asks else 0

    with col_sig:
        st.markdown("#### 📡 Sinyal Indikator Otomatis")
        try:
            ticker_res = requests.get(f"https://indodax.com/api/ticker/{ticker_id}", timeout=3).json()['ticker']
            l_price = float(ticker_res.get('last', 0))
            h_price = float(ticker_res.get('high', 0))
            lw_price = float(ticker_res.get('low', 0))

            auto_signals = calculate_auto_indicators(l_price, h_price, lw_price, total_bid_vol, total_ask_vol)
            for title, desc, col in auto_signals:
                if col == "green":
                    st.success(f"**{title}**\n\n{desc}")
                elif col == "red":
                    st.error(f"**{title}**\n\n{desc}")
                else:
                    st.info(f"**{title}**\n\n{desc}")
        except Exception:
            st.warning("Gagal mengalkulasi sinyal indikator otomatis.")

    with col_ob:
        st.markdown("#### 📖 Live Orderbook Ringkas")
        col_bids, col_asks = st.columns(2)

        with col_bids:
            st.caption("🟢 **Bids (Antrean Beli)**")
            if bids:
                df_bids = pd.DataFrame(bids, columns=["Harga (IDR)", "Jumlah"]).head(5)
                df_bids["Harga (IDR)"] = df_bids["Harga (IDR)"].apply(lambda x: f"Rp {int(float(x)):,}")
                st.dataframe(df_bids, use_container_width=True, hide_index=True)
            else:
                st.write("Tidak ada data Bids.")

        with col_asks:
            st.caption("🔴 **Asks (Antrean Jual)**")
            if asks:
                df_asks = pd.DataFrame(asks, columns=["Harga (IDR)", "Jumlah"]).head(5)
                df_asks["Harga (IDR)"] = df_asks["Harga (IDR)"].apply(lambda x: f"Rp {int(float(x)):,}")
                st.dataframe(df_asks, use_container_width=True, hide_index=True)
            else:
                st.write("Tidak ada data Asks.")

    st.markdown("---")

    st.markdown(f"### 💼 Analisis Posisi Portofolio Saya ({symbol})")
    st.caption("💡 *Ketik angka polos tanpa titik/koma (misal: 1324307).*")

    with st.form("portfolio_form"):
        my_buy_price = st.number_input(f"Harga Beli Awal Kamu (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        btn_submit = st.form_submit_button("🤖 Mulaikan Analisis AI Posisi & Sinyal Market", use_container_width=True)

    if btn_submit:
        try:
            url = f"https://indodax.com/api/ticker/{ticker_id}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5).json()['ticker']
            
            current_market_price = int(res['last'])
            high = int(res['high'])
            low = int(res['low'])

            if current_market_price <= low * 1.02:
                st.warning("⚠️ **Perhatian Risk**: Harga pasar saat ini berada sangat dekat dengan titik terendah (Low 24j). Pertimbangkan konfirmasi pantulan support.")
            elif current_market_price >= high * 0.98:
                st.warning("🔥 **Perhatian Area High**: Harga berada di dekat puncak 24j. Hati-hati terhadap aksi profit taking.")

            pnl_pct = ((current_market_price - my_buy_price) / my_buy_price) * 100 if my_buy_price > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric(label="Harga Pasar Saat Ini", value=f"Rp {current_market_price:,}")
            c2.metric(label="Modal/Harga Beli Kamu", value=f"Rp {int(my_buy_price):,}")
            
            if my_buy_price > 0:
                if pnl_pct >= 0:
                    c3.metric(label="Status PnL (Keuntungan)", value=f"+{pnl_pct:.2f}%", delta=f"+{pnl_pct:.2f}%")
                else:
                    c3.metric(label="Status PnL (Kerugian)", value=f"{pnl_pct:.2f}%", delta=f"{pnl_pct:.2f}%")
            else:
                c3.metric(label="Status PnL", value="Belum diisi (0)")

            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
            else:
                with st.spinner(f"AI sedang merespon analisis cepat koin {symbol}..."):
                    client = genai.Client(api_key=api_key)
                    
                    prompt = f"""
                    Kamu adalah konsultan Trading Crypto profesional buatan Rey472.
                    Gaya Trading Pengguna: {trading_style}
                    
                    Data Posisi Pengguna:
                    - Nama Aset: {selected_info['clean_name']}
                    - Harga Beli Awal Pengguna: Rp {my_buy_price:,}
                    - Harga Pasar Saat Ini: Rp {current_market_price:,}
                    - Status Profit/Loss Sementara: {pnl_pct:.2f}%
                    - Harga Tertinggi 24j: Rp {high:,}
                    - Harga Terendah 24j: Rp {low:,}

                    Berikan analisis ringkas, padat, dan taktis dalam format poin rapi:
                    1. 🌐 Analisis Posisi Saat Ini
                    2. 🟢 Rekomendasi Aksi Utama: (HOLD / TAKE PROFIT / CUT LOSS / BUY ON DIP)
                    3. 🛑 Saran Harga Stop Loss (SL) yang aman.
                    4. 🎯 Target Jual / Take Profit (TP1 & TP2) dalam Rupiah.
                    5. 💡 Tips Manajemen Risiko singkat dari AI Rey472.
                    """
                    
                    ai_result = call_gemini_with_fallback(client, prompt)
                    
                    if ai_result:
                        st.markdown("### 🤖 Hasil Analisis Kilat AI Rey472")
                        st.info(ai_result)
                    else:
                        st.error("⚠️ Server AI Google sedang sangat sibuk (503). Silakan klik tombol sekali lagi dalam beberapa detik.")
                    
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
        st.write("**Materi Singkat:** Jangan pernah memasukkan uang pinjaman atau uang SPP/belanja dapur ke market crypto karena pasar bisa naik-turun sewaktu-waktu.")
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
        st.write("Gunakan chart di bawah ini untuk menguji kemampuanmu memasang garis bantu secara mandiri:")

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
            "save_image": false,
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
            
        color_code = "#FF4D4D" if val_num <= 25 else "#FFA500" if val_num <= 45 else "#FFD700" if val_num <= 55 else "#90EE90" if val_num <= 75 else "#00E676"

        st.markdown(
            f"""
            <div style="border: 2px solid {color_code}; border-radius: 12px; padding: 20px; text-align: center; background-color: #1a1c23; margin-bottom: 15px;">
                <h1 style="color: {color_code}; font-size: 64px; margin: 0;">{fng_val}</h1>
                <h3 style="color: #FFFFFF; margin: 10px 0 0 0;">{fng_class.upper()}</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.caption("💡 **Cara Membaca Index:**")
        st.write("• **0-45 (Fear)**: Pasar sedang takut. Sering dianggap area peluang beli (*Buy the Dip*).")
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

# ================= TAB 5: JURNAL TRADING =================
with tab_journal:
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
        if st.button("🗑️ Hapus Semua Catatan"):
            st.session_state.journal = []
            st.rerun()

# ================= TAB 6: KALKULATOR & AVERAGING =================
with tab_calc:
    st.markdown("### 🧮 Kalkulator Trading & Averaging Down")
    
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
        else:
            st.warning("⚠️ Masukkan harga entry dan stop loss yang valid.")

    with calc_col2:
        st.markdown("#### 2. Kalkulator Averaging Down")
        avg_price1 = st.number_input("Harga Beli Pertama (Rp):", min_value=0.0, value=0.0, key="avg_p1")
        avg_qty1 = st.number_input(f"Jumlah Koin {symbol} Beli Pertama:", min_value=0.0, value=0.0, key="avg_q1")
        
        avg_price2 = st.number_input("Harga Beli Kedua / Serok (Rp):", min_value=0.0, value=0.0, key="avg_p2")
        avg_qty2 = st.number_input(f"Jumlah Koin {symbol} Beli Kedua:", min_value=0.0, value=0.0, key="avg_q2")

        if (avg_qty1 + avg_qty2) > 0:
            total_modal = (avg_price1 * avg_qty1) + (avg_price2 * avg_qty2)
            total_koin = avg_qty1 + avg_qty2
            avg_final_price = total_modal / total_koin
            
            st.success(f"🎯 **Harga Rata-Rata Baru (Average Price)**: Rp {avg_final_price:,.2f}")
            st.info(f"💰 Total Modal Dikeluarkan: **Rp {total_modal:,.0f}** | Total Aset: **{total_koin:.4f} {symbol}**")

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
                        client = genai.Client(api_key=api_key)
                        chat_prompt = f"""
                        Kamu adalah Asisten Trading Crypto AI buatan Rey472 yang ramah, taktis, dan cerdas.
                        Koin yang sedang diamati pengguna saat ini: {symbol}.
                        Pertanyaan pengguna: {user_query}

                        Jawab secara jelas, praktis, dan langsung ke inti pembahasan.
                        """
                        
                        ai_chat_result = call_gemini_with_fallback(client, chat_prompt)
                        if ai_chat_result:
                            st.markdown(ai_chat_result)
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_chat_result})
                        else:
                            st.error("⚠️ Server sedang sibuk. Silakan coba tanyakan kembali.")
                    except Exception as err:
                        st.error(f"Gagal memproses pesan: {err}")
