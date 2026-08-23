import streamlit as st
import requests
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime

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
        res = requests.get(url).json()
        
        pairs_dict = {}
        for item in res:
            ticker_id = item.get('ticker_id', '')
            if ticker_id.endswith('_idr'):
                description = item.get('description', ticker_id.replace('_idr', '').upper())
                symbol = ticker_id.replace('_idr', '').upper()
                logo_url = item.get('url_logo_png', '')
                
                display_label = f"{description} ({symbol})"
                pairs_dict[display_label] = {
                    'ticker_id': ticker_id,
                    'symbol': symbol,
                    'description': description,
                    'logo_url': logo_url
                }
        return dict(sorted(pairs_dict.items()))
    except Exception:
        return {
            "Bitcoin (BTC)": {
                'ticker_id': 'btc_idr', 'symbol': 'BTC', 
                'description': 'Bitcoin', 
                'logo_url': 'https://indodax.com/v2/logo/png/color/btc.png'
            }
        }

# Fungsi mengambil data riwayat Candle (Klines) Indodax
def get_klines_data(pair, tf="1h"):
    try:
        # API klines Indodax
        url = f"https://indodax.com/tradingview/history_v2?symbol={pair.upper()}&resolution=60&from={int(datetime.now().timestamp()) - 86400*7}&to={int(datetime.now().timestamp())}"
        res = requests.get(url).json()
        
        if res.get('s') == 'ok':
            times = [datetime.fromtimestamp(t) for t in res['t']]
            return {
                'time': times,
                'open': res['o'],
                'high': res['h'],
                'low': res['l'],
                'close': res['c'],
                'volume': res['v']
            }
    except Exception:
        return None
    return None

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

st.sidebar.markdown("---")
if selected_info['logo_url']:
    st.sidebar.image(selected_info['logo_url'], width=50)
st.sidebar.subheader(selected_info['description'])
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
    st.subheader(f"{selected_info['description']} ({selected_info['symbol']}/IDR)")

# Tampilkan Chart Candlestick
st.markdown("#### 📊 Grafik Candlestick Market")
chart_data = get_klines_data(ticker_id)

if chart_data:
    fig = go.Figure(data=[go.Candlestick(
        x=chart_data['time'],
        open=chart_data['open'],
        high=chart_data['high'],
        low=chart_data['low'],
        close=chart_data['close'],
        increasing_line_color='#00c076', # Warna hijau
        decreasing_line_color='#ff3b30'  # Warna merah
    )])
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Grafik candlestick sedang memuat atau tidak tersedia untuk pair ini.")

# Tombol Analisis AI
if st.button("🔍 Mulaikan Analisis Market", use_container_width=True):
    try:
        res = requests.get(f"https://indodax.com/api/ticker/{ticker_id}").json()['ticker']
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
            with st.spinner(f"AI sedang menganalisis pergerakan market {selected_info['description']}..."):
                prompt = f"""
                Kamu adalah konsultan Swing Trading Crypto profesional.
                Lakukan analisis teknikal ringkas dan praktis untuk aset berikut:
                - Nama Koin: {selected_info['description']} ({selected_info['symbol']})
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
                
    except Exception:
        st.error("Gagal mengambil data dari Indodax. Silakan coba beberapa saat lagi.")
