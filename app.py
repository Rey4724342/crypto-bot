import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
import time
import google.generativeai as genai

st.set_page_config(
    page_title="Crypto AI Trading Hub & Analyst Pro - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

# 🔒 CSS Khusus Mobile & Desktop
responsive_css = """
            <style>
            #MainMenu, header, footer, .stAppHeader, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], div[class*="viewerBadge"] {
                display: none !important;
            }
            @media screen and (max-width: 768px) {
                .stTabs [data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; flex-wrap: nowrap; }
                .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 8px 10px; }
                div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: 100% !important; min-width: 100% !important; }
            }
            </style>
            """
st.markdown(responsive_css, unsafe_allow_html=True)

# Session State Initialization
if 'journal' not in st.session_state:
    st.session_state.journal = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'academy_step' not in st.session_state:
    st.session_state.academy_step = 1

# ⚡ CACHING & API FUNCTIONS
@st.cache_data(ttl=60)
def get_indodax_summary():
    try:
        url = "https://indodax.com/api/summaries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers, timeout=3).json()
    except Exception:
        return {}

@st.cache_data(ttl=3600)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=4).json()
        
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

@st.cache_data(ttl=1800)
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/"
        res = requests.get(url, timeout=3).json()
        data = res['data'][0]
        return data['value'], data['value_classification']
    except Exception:
        return "50", "Neutral"

@st.cache_data(ttl=600)
def get_crypto_news_robust():
    try:
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=4)
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

@st.cache_data(ttl=10)
def get_indodax_depth(ticker_id):
    try:
        formatted_pair = ticker_id if ticker_id.endswith('_idr') else f"{ticker_id.lower()}_idr"
        url = f"https://indodax.com/api/depth/{formatted_pair}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        
        bids = res.get('buy', [])[:5]
        asks = res.get('sell', [])[:5]
        return bids, asks
    except Exception:
        return [], []

# 🤖 Helper Function Panggilan Gemini Aman & Stabil
def call_gemini_fast(api_key, prompt):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 200,
            }
        )
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception:
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception:
            pass
    return None

pairs_data = get_all_indodax_pairs()

# Header Utama
st.title("🚀 Crypto AI Trading Hub & Analyst Pro")
st.markdown("<h4 style='color: #4CAF50; margin-top: -15px;'>👨‍💻 Pencipta: <b>Rey472</b></h4>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("### ⚙️ Pengaturan Koin & Strategi")
menu_col1, menu_col2 = st.columns(2)

with menu_col1:
    selected_label = st.selectbox("🔍 Cari & Pilih Koin Utama:", options=list(pairs_data.keys()), index=0)

with menu_col2:
    trading_style = st.radio("🎯 Pilih Mode Strategi AI:", ["Swing Trading (Santai / Menengah)", "Scalping (Cepat / Intraday)"], horizontal=True)

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

    # GRAFIK TRADINGVIEW
    st.markdown("#### 📊 Grafik Candlestick Market (Real-Time)")
    
    tv_fast_widget = f"""
    <div id="tv_chart_container" style="height:450px;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "width": "100%",
      "height": 450,
      "symbol": "BINANCE:{symbol}USDT",
      "interval": "D",
      "timezone": "Asia/Jakarta",
      "theme": "dark",
      "style": "1",
      "locale": "id",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_container"
    }});
    </script>
    """
    components.html(tv_fast_widget, height=460)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.link_button(f"🔗 Buka Chart {symbol} (Tab Baru)", f"https://id.tradingview.com/chart/?symbol=BINANCE:{symbol}USDT", use_container_width=True)
    with col_btn2:
        st.link_button(f"🌐 Buka Market {symbol} (Indodax)", f"https://indodax.com/market/{symbol}IDR", use_container_width=True)

    st.markdown("---")

    # SINYAL INDIKATOR OTOMATIS
    st.markdown("### 📊 Sinyal Indikator Otomatis (RSI & MA)")
    
    try:
        ticker_res = requests.get(f"https://indodax.com/api/ticker/{ticker_id}", timeout=3).json()['ticker']
        curr_p = float(ticker_res['last'])
        hi_p = float(ticker_res['high'])
        lo_p = float(ticker_res['low'])
        
        pos_range = (curr_p - lo_p) / (hi_p - lo_p) if (hi_p - lo_p) > 0 else 0.5
        rsi_est = int(pos_range * 100)
        
        ind_col1, ind_col2, ind_col3 = st.columns(3)
        
        with ind_col1:
            st.metric("Estimasi RSI (14)", f"{rsi_est}")
            if rsi_est >= 70:
                st.error("⚠️ **Overbought**: Harga sudah tinggi.")
            elif rsi_est <= 30:
                st.success("🟢 **Oversold**: Harga tergolong diskon.")
            else:
                st.info("⚖️ **Netral**: Pergerakan stabil.")

        with ind_col2:
            ma20_est = (hi_p + lo_p) / 2
            st.metric("Moving Average (MA20)", f"Rp {int(ma20_est):,}")
            if curr_p > ma20_est:
                st.success("🟢 **Diatas MA20**: Tren Uptrend.")
            else:
                st.error("🔴 **Dibawah MA20**: Tren Downtrend.")

        with ind_col3:
            vol_idr = float(ticker_res.get('vol_idr', 0))
            st.metric("Volume 24 Jam", f"Rp {int(vol_idr):,}")
            if vol_idr > 10_000_000_000:
                st.success("🔥 **Likuiditas Tinggi**")
            else:
                st.warning("💧 **Likuiditas Sedang/Rendah**")

    except Exception:
        st.caption("Gagal memuat sinyal indikator otomatis.")

    st.markdown("---")

    # LIVE ORDERBOOK RINGKAS
    st.markdown("### 📑 Live Orderbook Ringkas (Top 5 Bid & Ask Indodax)")
    bids, asks = get_indodax_depth(ticker_id)
    
    ob_col1, ob_col2 = st.columns(2)
    
    with ob_col1:
        st.success("🟢 **Order Beli (Bids)**")
        if bids:
            df_bids = pd.DataFrame(bids, columns=["Harga (Rp)", "Jumlah Koin"])
            df_bids["Harga (Rp)"] = df_bids["Harga (Rp)"].apply(lambda x: f"Rp {int(float(x)):,}")
            st.table(df_bids)
        else:
            st.caption("Data Bids tidak tersedia.")

    with ob_col2:
        st.error("🔴 **Order Jual (Asks)**")
        if asks:
            df_asks = pd.DataFrame(asks, columns=["Harga (Rp)", "Jumlah Koin"])
            df_asks["Harga (Rp)"] = df_asks["Harga (Rp)"].apply(lambda x: f"Rp {int(float(x)):,}")
            st.table(df_asks)
        else:
            st.caption("Data Asks tidak tersedia.")

    st.markdown("---")

    st.markdown(f"### 💼 Analisis Posisi Portofolio Saya ({symbol})")

    with st.form("portfolio_form"):
        my_buy_price = st.number_input(f"Harga Beli Kamu (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        btn_submit = st.form_submit_button("🤖 Mulaikan Analisis AI Posisi & Sinyal Market", use_container_width=True)

    if btn_submit:
        try:
            url = f"https://indodax.com/api/ticker/{ticker_id}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=3).json()['ticker']
            
            current_market_price = int(res['last'])
            high = int(res['high'])
            low = int(res['low'])

            if my_buy_price > 0:
                pnl_pct = ((current_market_price - my_buy_price) / my_buy_price) * 100
            else:
                pnl_pct = 0

            c1, c2, c3 = st.columns(3)
            c1.metric(label="Harga Pasar Saat Ini", value=f"Rp {current_market_price:,}")
            c2.metric(label="Harga Beli Kamu", value=f"Rp {int(my_buy_price):,}")
            
            if my_buy_price > 0:
                c3.metric(label="Status PnL (%)", value=f"{pnl_pct:.2f}%", delta=f"{pnl_pct:.2f}%")
            else:
                c3.metric(label="Status PnL", value="Belum diisi")

            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
            else:
                with st.spinner("AI sedang menganalisis cepat..."):
                    prompt = f"""
                    Anda adalah pakar analisis trading crypto.
                    Koin: {selected_info['clean_name']}
                    Strategi: {trading_style}
                    Harga Beli User: Rp {my_buy_price:,}
                    Harga Pasar: Rp {current_market_price:,}
                    PnL: {pnl_pct:.2f}%
                    High 24h: Rp {high:,} | Low 24h: Rp {low:,}

                    Berikan respon singkat maks 3 baris:
                    1. Rekomendasi Aksi (HOLD/TP/SL/BUY)
                    2. Rencana TP & SL Singkat
                    """
                    
                    reply_text = call_gemini_fast(api_key, prompt)
                    st.markdown("### 🤖 Hasil Analisis Kilat AI Rey472")
                    
                    if reply_text:
                        st.info(reply_text)
                    else:
                        st.warning("⚠️ Server AI Google sedang mengalami trafik tinggi. Berpindah ke analisis sinyal indikator lokal:")
                        if my_buy_price > 0:
                            if pnl_pct >= 5:
                                st.success("🟢 **Rekomendasi:** TAKE PROFIT / AMBIL UNTUNG (Posisi profit > 5%).")
                            elif pnl_pct <= -5:
                                st.error("🔴 **Rekomendasi:** STOP LOSS / PERTIMBANGKAN CUT LOSS (Posisi minus > 5%).")
                            else:
                                st.info("⚖️ **Rekomendasi:** HOLD (Pergerakan harga masih dalam rentang wajar).")
                        else:
                            if current_market_price <= low * 1.02:
                                st.success("🟢 **Rekomendasi:** POTENSI BUY (Harga dekat titik terendah 24 jam).")
                            else:
                                st.info("⚖️ **Rekomendasi:** WAIT & SEE (Pantau pergerakan harga terlebih dahulu).")
                    
        except Exception as e:
            st.error(f"Gagal memuat analisis: {e}")

# ================= TAB 2: AKADEMI =================
with tab_edu:
    st.markdown("### 🎓 Akademi & Ujian Simulasi Kasus Nyata")
    st.caption("Selesaikan misi untuk melatih mental & skill trading!")

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
        st.write("**Materi Singkat:** Uang dingin wajib digunakan dalam trading!")
        
        st.markdown("#### 📝 Uji Pemahaman Kasus Nyata Misi 1:")
        st.warning("⚠️ **Studi Kasus:** Kamu memiliki uang tabungan darurat Rp 2.000.000 untuk bayar kontrakan bulan depan. Seorang teman mengajakmu membeli koin yang diklaim akan naik 500% dalam seminggu. Apa tindakan yang benar?")
        
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
                st.success("🎉 **BENAR SEKALI!** Uang kebutuhan jangka pendek/darurat tidak boleh dipakai trading.")
                if st.button("➡️ Lanjut ke Misi 2"):
                    st.session_state.academy_step = 2
                    st.rerun()
            else:
                st.error("❌ **SALAH!** Keputusan ini sangat berbahaya.")

    elif st.session_state.academy_step == 2:
        st.markdown("### 🕯️ Misi 2: Membaca Psikologi Candlestick")
        st.info("🎯 **Target Misi:** Menafsirkan arah pergerakan harga.")
        
        st.markdown("#### 📝 Uji Pemahaman Kasus Nyata Misi 2:")
        st.warning("⚠️ **Studi Kasus:** Grafik koin membentuk 3 candle merah besar berturut-turut dengan volume meningkat. Apa arti kondisi ini?")
        
        ans_m2 = st.radio(
            "Pilih analisis yang paling logis:",
            [
                "A. Tekanan jual (seller) sedang sangat kuat, pasar sedang bearish/turun.",
                "B. Sebentar lagi harga pasti naik drastis, jadi harus langsung all-in.",
                "C. Market sedang tidak aktif."
            ],
            index=None,
            key="quiz_m2"
        )

        if ans_m2:
            if ans_m2.startswith("A"):
                st.success("🎉 **TEPAT SEKALI!** Tiga candle merah panjang menandakan dominasi seller.")
                if st.button("➡️ Lanjut ke Misi 3"):
                    st.session_state.academy_step = 3
                    st.rerun()
            else:
                st.error("❌ **Kurang tepat.** Jangan melawan arus tren turun.")

    elif st.session_state.academy_step == 3:
        st.markdown("### 🧱 Misi 3: Menentukan Area Support & Resistance")
        st.info("🎯 **Target Misi:** Menempatkan titik eksekusi beli dan jual.")

        st.markdown("#### 📝 Uji Pemahaman Kasus Nyata Misi 3:")
        st.warning("⚠️ **Studi Kasus:** Harga koin sedang mendekati garis Resistance kuat dan laju kenaikan harga mulai melambat. Apa tindakan terbaik?")
        
        ans_m3 = st.radio(
            "Pilih strategi yang tepat:",
            [
                "A. Memborong lebih banyak koin di dekat resistance.",
                "B. Bersiap merealisasikan keuntungan (Take Profit) sebagian atau seluruhnya.",
                "C. Membiarkan saja tanpa rencana."
            ],
            index=None,
            key="quiz_m3"
        )

        if ans_m3:
            if ans_m3.startswith("B"):
                st.success("🎉 **HEBAT!** Taking profit di area resistance adalah langkah yang disiplin.")
                if st.button("➡️ Lanjut ke Misi 4"):
                    st.session_state.academy_step = 4
                    st.rerun()
            else:
                st.error("❌ **Kurang tepat.** Membeli di area resistance berisiko terkena pembalikan arah.")

    elif st.session_state.academy_step == 4:
        st.markdown("### 📊 Misi 4: Lab Praktik Langsung di TradingView")
        practice_chart_code = """
        <iframe 
            src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:BTCUSDT&interval=D&hidesidetoolbar=1&theme=dark&style=1&timezone=Asia%2FJakarta&locale=id"
            style="width: 100%; height: 480px; border: none; border-radius: 8px;"
            loading="lazy">
        </iframe>
        """
        components.html(practice_chart_code, height=490)
        st.success("🏆 **Selamat!** Kamu telah menyelesaikan modul pembelajaran Akademi Rey472!")

# ================= TAB 3: SENTIMEN & BERITA =================
with tab_sentimen:
    st.markdown("### 🧠 Sentimen Pasar Crypto Global & Berita Real-Time")
    
    col_fg, col_news = st.columns([1, 2])
    
    with col_fg:
        st.markdown("#### 😱 Crypto Fear & Greed Index")
        fng_val, fng_class = get_fear_and_greed()
        
        try:
            val_num = int(fng_val)
        except ValueError:
            val_num = 50
            
        color_code = "#FF4D4D" if val_num <= 25 else "#FFA500" if val_num <= 45 else "#FFD700" if val_num <= 55 else "#00E676"

        st.markdown(
            f"""
            <div style="border: 2px solid {color_code}; border-radius: 12px; padding: 20px; text-align: center; background-color: #1a1c23;">
                <h1 style="color: {color_code}; font-size: 64px; margin: 0;">{fng_val}</h1>
                <h3 style="color: #FFFFFF; margin: 10px 0 0 0;">{fng_class.upper()}</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📌 Panduan Aksi Trading Berdasarkan Indikator:")
        
        if val_num >= 75:
            st.error("🔥 **EXTREME GREED (Sangat Rakus):** Pasar mengalami euforia & FOMO tinggi. **Saran:** Waktu yang tepat untuk Take Profit (Jual secara bertahap). Hindari beli baru di pucuk!")
        elif val_num >= 55:
            st.warning("🤑 **GREED (Rakus):** Optimisme pasar meningkat pesat. **Saran:** Amankan sebagian keuntungan dan pasang Stop Loss yang ketat.")
        elif val_num <= 25:
            st.success("💎 **EXTREME FEAR (Sangat Takut):** Pasar ketakutan berlebihan & harga diskon besar. **Saran:** Peluang emas untuk mencari koin bagus (Buy the Dip).")
        elif val_num <= 45:
            st.info("😰 **FEAR (Takut):** Pasar ragu-ragu dan cenderung turun. **Saran:** Pantau koin potensial dan masuk bertahap.")
        else:
            st.info("⚖️ **NEUTRAL (Netral):** Pergerakan pasar seimbang. **Saran:** Ikuti tren teknikal teknis (Support/Resistance).")

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
                    if news['desc']:
                        st.write(news['desc'])
                    st.caption(f"🗓️ {news['date']} | 🌐 CoinDesk")
                st.markdown("---")
        else:
            st.info("Sedang memuat berita pasar...")

# ================= TAB 4: PERBANDINGAN KOIN =================
with tab_compare:
    st.markdown("### 🔀 Bandingkan 2 Koin Indodax")
    
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        coin1_label = st.selectbox("Pilih Koin Pertama:", options=list(pairs_data.keys()), index=0)
    with comp_col2:
        coin2_label = st.selectbox("Pilih Koin Kedua:", options=list(pairs_data.keys()), index=min(1, len(pairs_data)-1))
        
    if st.button("⚖️ Bandingkan Sekarang", use_container_width=True):
        try:
            t1 = pairs_data[coin1_label]['ticker_id']
            t2 = pairs_data[coin2_label]['ticker_id']
            
            res1 = requests.get(f"https://indodax.com/api/ticker/{t1}", timeout=5).json()['ticker']
            res2 = requests.get(f"https://indodax.com/api/ticker/{t2}", timeout=5).json()['ticker']
            
            c1_col, c2_col = st.columns(2)
            with c1_col:
                st.subheader(coin1_label)
                st.metric("Harga Terakhir", f"Rp {int(res1['last']):,}")
                st.metric("Harga Tertinggi (24j)", f"Rp {int(res1['high']):,}")
                st.metric("Harga Terendah (24j)", f"Rp {int(res1['low']):,}")
                st.metric("Volume IDR", f"Rp {int(float(res1.get('vol_idr', 0))):,}")
            with c2_col:
                st.subheader(coin2_label)
                st.metric("Harga Terakhir", f"Rp {int(res2['last']):,}")
                st.metric("Harga Tertinggi (24j)", f"Rp {int(res2['high']):,}")
                st.metric("Harga Terendah (24j)", f"Rp {int(res2['low']):,}")
                st.metric("Volume IDR", f"Rp {int(float(res2.get('vol_idr', 0))):,}")
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
        
        submitted = st.form_submit_button("➕ Simpan ke Catatan", use_container_width=True)
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
            
            st.success(f"🎯 **Harga Rata-Rata Baru**: Rp {avg_final_price:,.2f}")
            st.info(f"💰 Total Modal: **Rp {total_modal:,.0f}** | Total Aset: **{total_koin:.4f} {symbol}**")

# ================= TAB 7: ASISTEN AI CHAT =================
with tab_chat:
    st.markdown("### 💬 Asisten Trading AI Rey472")

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
                    chat_prompt = f"Koin terpilih: {symbol}.\nPertanyaan: {user_query}"
                    reply = call_gemini_fast(api_key, chat_prompt)
                    if reply:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    else:
                        fallback_msg = "Maaf, server AI sedang padat. Silakan ulangi pertanyaanmu dalam beberapa detik."
                        st.warning(fallback_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})
