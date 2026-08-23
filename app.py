import streamlit as st
import streamlit.components.v1 as components
import requests
import google.generativeai as genai

st.set_page_config(
    page_title="Crypto AI Analyst - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

st.title("📈 Crypto Swing AI Analyst")
st.caption("by Rey472")

# Ambil semua data pair + nama asli + logo koin dari API Indodax
@st.cache_data(ttl=3600)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        
        pairs_dict = {}
        for item in res:
            ticker_id = item.get('ticker_id', '')
            if ticker_id.endswith('_idr'):
                symbol = ticker_id.replace('_idr', '').upper()
                desc = item.get('description', symbol)
                # Rapikan nama agar tidak dobel BTC/IDR (BTC/IDR)
                if desc.upper() == f"{symbol}/IDR" or desc.upper() == symbol:
                    clean_name = symbol
                else:
                    clean_name = f"{desc} ({symbol})"
                    
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
            "Bitcoin (BTC)": {
                'ticker_id': 'btc_idr', 'symbol': 'BTC', 
                'clean_name': 'Bitcoin (BTC)', 
                'logo_url': 'https://indodax.com/v2/logo/png/color/btc.png'
            }
        }

pairs_data = get_all_indodax_pairs()

# Sidebar
st.sidebar.header("⚙️ Pengaturan")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

selected_label = st.sidebar.selectbox(
    "🔍 Cari & Pilih Koin / Pair Indodax",
    options=list(pairs_data.keys()),
    index=0
)

selected_info = pairs_data[selected_label]
ticker_id = selected_info['ticker_id']
symbol = selected_info['symbol']

st.sidebar.markdown("---")
if selected_info['logo_url']:
    st.sidebar.image(selected_info['logo_url'], width=50)
st.sidebar.subheader(selected_info['clean_name'])
st.sidebar.write(f"**Pair Code:** `{ticker_id}`")

if api_key:
    genai.configure(api_key=api_key)

# Main Dashboard
st.markdown("---")

col_logo, col_title = st.columns([1, 6])
with col_logo:
    if selected_info['logo_url']:
        st.image(selected_info['logo_url'], width=64)
with col_title:
    st.subheader(f"{selected_info['clean_name']} / IDR")

# Embed Grafik TradingView Interaktif Realtime
st.markdown("#### 📊 Grafik Candlestick Market")

tradingview_html = f"""
<div class="tradingview-widget-container" style="height:500px;width:100%;">
  <div id="tradingview_chart" style="height:500px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "INDODAX:{symbol}IDR",
    "interval": "60",
    "timezone": "Asia/Jakarta",
    "theme": "dark",
    "style": "1",
    "locale": "id",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": false,
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tradingview_html, height=520)

# Tombol Analisis AI
if st.button("🔍 Mulaikan Analisis Market", use_container_width=True):
    try:
        url = f"https://indodax.com/api/ticker/{ticker_id}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()['ticker']
        harga = int(res['last'])
        high = int(res['high'])
        low = int(res['low'])

        c1, c2, c3 = st.columns(3)
        c1.metric(label="Harga Saat Ini", value=f"Rp {harga:,}")
        c2.metric(label="High 24j", value=f"Rp {high:,}")
        c3.metric(label="Low 24j", value=f"Rp {low:,}")

        if not api_key:
            st.warning("⚠️ Harap masukkan **Gemini API Key** di sidebar untuk menggunakan fitur analisis AI!")
        else:
            with st.spinner(f"AI sedang menganalisis pergerakan market {selected_info['clean_name']}..."):
                prompt = f"""
                Kamu adalah konsultan Swing Trading Crypto profesional.
                Lakukan analisis teknikal ringkas dan praktis untuk aset berikut:
                - Nama Koin: {selected_info['clean_name']}
                - Harga Saat Ini: Rp {harga:,}
                - Harga Tertinggi 24j: Rp {high:,}
                - Harga Terendah 24j: Rp {low:,}

                Berikan rekomendasi dalam format poin rapi:
                1. 🎯 Area Beli / Buy Entry (Range harga ideal)
                2. 📈 Target Profit / TP (TP1 & TP2)
                3. 🛑 Stop Loss / SL (Manajemen risiko)
                4. 💡 Ringkasan Analisis & Alasan Swing Trade
                """
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                
                st.markdown("### 🤖 Hasil Analisis AI Gemini")
                st.info(response.text)
                
    except Exception as e:
        st.error("Gagal mengambil data dari Indodax. Silakan coba beberapa saat lagi.")
