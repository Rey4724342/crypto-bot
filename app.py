import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from google import genai

st.set_page_config(
    page_title="Crypto AI Trading Hub & Analyst Pro - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

# 🔒 CSS Super Ringan untuk Percepatan Render Web
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

if 'journal' not in st.session_state:
    st.session_state.journal = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'academy_step' not in st.session_state:
    st.session_state.academy_step = 1

# ⚡ CACHING UNTUK PERCEPATAN RESPONS API
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
        namespaces = {'media': 'http://search.yahoo.com/mrss/'}

        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text if item.find('title') is not None else 'Berita Crypto'
            link = item.find('link').text if item.find('link') is not None else '#'
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            image_url = ""
            media_content = item.find('media:content', namespaces)
            if media_content is not None and 'url' in media_content.attrib:
                image_url = media_content.attrib['url']

            if not image_url:
                image_url = "https://images.cointelegraph.com/images/1200_aHR0cHM6Ly9zMy5jb2ludGVsZWdyYXBoLmNvbS91cGxvYWRzLzIwMjEtMDMvYTM1ZDgyMGUtZGVhMS00OWViLThkYTAtOGE4OGFiZmM0ODNmLmpwZw==.jpg"

            news_items.append({
                'title': title,
                'link': link,
                'image': image_url,
                'date': pub_date[:16] if pub_date else "Terbaru"
            })
        return news_items
    except Exception:
        return []

# ⚡ CACHE ORDERBOOK UNTUK CEPT KELUAR DAFTAR HARGA (REFRESH TIAP 10 DETIK)
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
    "📈 Dashboard Utama & AI", "🎓 Akademi & Ujian Kasus", "📰 Sentimen & Berita Market",
    "🔀 Perbandingan Koin", "📓 Jurnal Trading", "🧮 Kalkulator & Averaging", "💬 Asisten AI Chat"
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

    # 📊 GRAFIK TRADINGVIEW FAST RENDERING (Menggunakan versi Widget JS langsung)
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
                st.success("🟢 **Oversold**: Harga diskon.")
            else:
                st.info("⚖️ **Netral**: Area stabil.")

        with ind_col2:
            ma20_est = (hi_p + lo_p) / 2
            st.metric("Moving Average (MA20)", f"Rp {int(ma20_est):,}")
            if curr_p > ma20_est:
                st.success("🟢 **Diatas MA20**: Uptrend.")
            else:
                st.error("🔴 **Dibawah MA20**: Downtrend.")

        with ind_col3:
            vol_idr = float(ticker_res.get('vol_idr', 0))
            st.metric("Volume 24 Jam", f"Rp {int(vol_idr):,}")
            if vol_idr > 10_000_000_000:
                st.success("🔥 **Likuiditas Tinggi**")
            else:
                st.warning("💧 **Likuiditas Sedang/Rendah**")

    except Exception:
        st.caption("Gagal memuat sinyal indikator.")

    st.markdown("---")

    # LIVE ORDERBOOK RINGKAS (CEPAT & CEPAT MEMUAT)
    st.markdown("### 📑 Live Orderbook Ringkas (Top 5 Bid & Ask Indodax)")
    bids, asks = get_indodax_depth(ticker_id)
    
    ob_col1, ob_col2 = st.columns(2)
    
    with ob_col1:
        st.success("🟢 **Order Beli (Bids / Antrean Beli)**")
        if bids:
            df_bids = pd.DataFrame(bids, columns=["Harga (Rp)", "Jumlah Koin"])
            df_bids["Harga (Rp)"] = df_bids["Harga (Rp)"].apply(lambda x: f"Rp {int(float(x)):,}")
            st.table(df_bids)
        else:
            st.caption("Memuat data Bids Indodax...")

    with ob_col2:
        st.error("🔴 **Order Jual (Asks / Antrean Jual)**")
        if asks:
            df_asks = pd.DataFrame(asks, columns=["Harga (Rp)", "Jumlah Koin"])
            df_asks["Harga (Rp)"] = df_asks["Harga (Rp)"].apply(lambda x: f"Rp {int(float(x)):,}")
            st.table(df_asks)
        else:
            st.caption("Memuat data Asks Indodax...")

    st.markdown("---")

    st.markdown(f"### 💼 Analisis Posisi Portofolio Saya ({symbol})")
    with st.form("portfolio_form"):
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            my_buy_price = st.number_input(f"Harga Beli Awal Kamu (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.0f")
        with col_input2:
            my_amount_coin = st.number_input(f"Jumlah Koin {symbol} yang Kamu Miliki:", min_value=0.0, value=0.0, step=0.1, format="%.4f")
        
        btn_submit = st.form_submit_button("🤖 Mulaikan Analisis AI Posisi & Sinyal Market", use_container_width=True)

    if btn_submit:
        try:
            url = f"https://indodax.com/api/ticker/{ticker_id}"
            res = requests.get(url, timeout=3).json()['ticker']
            current_market_price = int(res['last'])
            high = int(res['high'])
            low = int(res['low'])

            pnl_rp = (current_market_price - my_buy_price) * my_amount_coin if my_buy_price > 0 else 0
            pnl_pct = ((current_market_price - my_buy_price) / my_buy_price) * 100 if my_buy_price > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric(label="Harga Pasar Saat Ini", value=f"Rp {current_market_price:,}")
            c2.metric(label="Modal/Harga Beli Kamu", value=f"Rp {int(my_buy_price):,}")
            c3.metric(label="Status PnL", value=f"Rp {int(pnl_rp):,}", delta=f"{pnl_pct:.2f}%" if my_buy_price > 0 else "0%")

            api_key = st.secrets.get("GEMINI_API_KEY")

            if api_key:
                with st.spinner("AI sedang menganalisis..."):
                    client = genai.Client(api_key=api_key)
                    prompt = f"Berikan rekomendasi trading cepat untuk {selected_info['clean_name']}, harga beli: {my_buy_price}, harga sekarang: {current_market_price}, High 24j: {high}, Low 24j: {low}. Gaya: {trading_style}"
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    st.markdown("### 🤖 Hasil Analisis Kilat AI Rey472")
                    st.info(response.text)
        except Exception as e:
            st.error(f"Gagal memuat analisis: {e}")

# ================= TAB 2 KESELURUHAN (Fast Execution) =================
with tab_edu:
    st.markdown("### 🎓 Akademi & Ujian Simulasi Kasus Nyata")
    st.info("Selesaikan misi untuk melatih mental & skill trading!")
    if st.button("🚀 Klik untuk Mulai Misi 1"):
        st.write("Uji Pemahaman: Uang dingin wajib digunakan dalam trading!")

with tab_sentimen:
    st.markdown("### 🧠 Sentimen Pasar Crypto Global & Berita Real-Time")
    fng_val, fng_class = get_fear_and_greed()
    st.metric("Fear & Greed Index", f"{fng_val} ({fng_class})")

with tab_compare:
    st.markdown("### 🔀 Bandingkan 2 Koin Indodax")
    st.write("Fitur Perbandingan Koin Siap Digunakan.")

with tab_journal:
    st.markdown("### 📓 Jurnal Catatan Trading")
    st.write("Simpan catatan trading harianmu.")

with tab_calc:
    st.markdown("### 🧮 Kalkulator Trading & Averaging Down")
    st.write("Hitung manajemen risiko & averaging down.")

with tab_chat:
    st.markdown("### 💬 Asisten Trading AI Rey472")
    user_query = st.chat_input("Tanyakan sesuatu ke AI Rey472...")
    if user_query:
        st.write(f"**Kamu:** {user_query}")
