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

# Ambil daftar koin dari Indodax
@st.cache_data(ttl=3600)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers).json()
        
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

pairs_data = get_all_indodax_pairs()

# Sidebar
st.sidebar.header("⚙️ Pengaturan")

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

# Main Dashboard
st.markdown("---")

col_logo, col_title = st.columns([1, 6])
with col_logo:
    if selected_info['logo_url']:
        st.image(selected_info['logo_url'], width=64)
with col_title:
    st.subheader(f"{selected_info['clean_name']} / IDR")

# Embed Grafik TradingView Universal
st.markdown("#### 📊 Grafik Candlestick Market")

tv_symbol = f"BINANCE:{symbol}USDT" if symbol != "BTC" else "BINANCE:BTCUSDT"

tradingview_html = f"""
<div class="tradingview-widget-container" style="height:500px;width:100%;">
  <div id="tradingview_chart" style="height:500px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "60",
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
components.html(tradingview_html, height=520)

# Tombol Analisis AI Sinyal Jual/Beli
if st.button("🔍 Mulaikan Analisis Market", use_container_width=True):
    try:
        url = f"https://indodax.com/api/ticker/{ticker_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers).json()['ticker']
        
        harga = int(res['last'])
        high = int(res['high'])
        low = int(res['low'])

        c1, c2, c3 = st.columns(3)
        c1.metric(label="Harga Saat Ini (Indodax)", value=f"Rp {harga:,}")
        c2.metric(label="High 24j", value=f"Rp {high:,}")
        c3.metric(label="Low 24j", value=f"Rp {low:,}")

        api_key = st.secrets.get("GEMINI_API_KEY")

        if not api_key:
            st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
        else:
            with st.spinner(f"AI sedang menghitung sinyal Beli & Jual untuk {selected_info['clean_name']}..."):
                genai.configure(api_key=api_key)
                
                # Prompt diperbarui agar AI memberikan angka harga beli dan jual yang pasti
                prompt = f"""
                Kamu adalah seorang Trader Senior dan Analis Crypto profesional.
                Berdasarkan data harga koin {selected_info['clean_name']} saat ini:
                - Harga Realtime: Rp {harga:,}
                - Harga Tertinggi 24j: Rp {high:,}
                - Harga Terendah 24j: Rp {low:,}

                Berikan rekomendasi trading jangka pendek / swing trade yang SANGAT JELAS dan DETAIL berupa angka harga spesifik dalam Rupiah (Rp):
                1. 🟢 **Rekomendasi Aksi**: (Pilih salah satu: *BUY / WAIT / SELL*)
                2. 📥 **Harga Beli (Buy Entry)**: Tentukan kisaran harga pastinya (Rp ...) untuk mulai membeli.
                3. 🎯 **Harga Jual / Target Profit (TP)**: Tentukan target harga jual pastinya untuk ambil untung (TP1 & TP2 dalam Rp ...).
                4. 🛑 **Batas Rugi / Stop Loss (SL)**: Tentukan batas pengamanan harga (dalam Rp ...) jika market berbalik turun.
                5. 💡 **Alasan / Analisis Singkat**: Berikan alasan logis mengapa harus beli/jual di kisaran harga tersebut.
                """
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                st.markdown("### 🤖 Sinyal Trading AI Gemini")
                st.info(response.text)
                
    except Exception as e:
        st.error(f"Gagal memuat analisis: {e}")
