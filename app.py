import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(
    page_title="Crypto AI Analyst - Rey472", 
    page_icon="🪙", 
    layout="centered"
)

st.title("📈 Crypto Swing AI Analyst")
st.caption("by Rey472")

# Ambil semua data pair + nama asli + logo koin dari API Indodax
@st.cache_data(ttl=3600)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        res = requests.get(url).json()
        
        pairs_dict = {}
        for item in res:
            ticker_id = item.get('ticker_id', '')
            # Filter hanya pair IDR
            if ticker_id.endswith('_idr'):
                # Nama asli (misal: "Bitcoin", "Ethereum")
                description = item.get('description', ticker_id.replace('_idr', '').upper())
                symbol = ticker_id.replace('_idr', '').upper()
                logo_url = item.get('url_logo_png', '')
                
                # Format label pencarian: "Bitcoin (BTC)"
                display_label = f"{description} ({symbol})"
                
                pairs_dict[display_label] = {
                    'ticker_id': ticker_id,
                    'symbol': symbol,
                    'description': description,
                    'logo_url': logo_url
                }
        return dict(sorted(pairs_dict.items()))
    except Exception as e:
        # Fallback jika API bermasalah
        return {
            "Bitcoin (BTC)": {
                'ticker_id': 'btc_idr', 'symbol': 'BTC', 
                'description': 'Bitcoin', 
                'logo_url': 'https://indodax.com/v2/logo/png/color/btc.png'
            }
        }

# Memuat data pair
pairs_data = get_all_indodax_pairs()

# Sidebar Input
st.sidebar.header("⚙️ Pengaturan")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# Fitur Pencarian & Dropdown dengan Nama Lengkap (Autocomplete)
selected_label = st.sidebar.selectbox(
    "🔍 Cari & Pilih Koin / Pair Indodax",
    options=list(pairs_data.keys()),
    index=0,
    help="Ketik nama koin (misal: Bitcoin, Solana, Shiba Inu) untuk mencari dengan cepat"
)

selected_info = pairs_data[selected_label]
ticker_id = selected_info['ticker_id']

# Tampilkan Informasi Koin Terpilih di Sidebar
st.sidebar.markdown("---")
if selected_info['logo_url']:
    st.sidebar.image(selected_info['logo_url'], width=50)
st.sidebar.subheader(selected_info['description'])
st.sidebar.write(f"**Pair Code:** `{ticker_id}`")

if api_key:
    genai.configure(api_key=api_key)

# Main Dashboard
st.markdown("---")

# Header Koin
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if selected_info['logo_url']:
        st.image(selected_info['logo_url'], width=64)
with col_title:
    st.subheader(f"{selected_info['description']} ({selected_info['symbol']}/IDR)")

if st.button("🔍 Mulaikan Analisis Market", use_container_width=True):
    try:
        res = requests.get(f"https://indodax.com/api/ticker/{ticker_id}").json()['ticker']
        harga = int(res['last'])
        high = int(res['high'])
        low = int(res['low'])

        # Menampilkan indikator harga dasar
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
                
    except Exception as e:
        st.error("Gagal mengambil data dari Indodax. Silakan coba beberapa saat lagi.")
