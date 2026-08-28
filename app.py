import streamlit as st
import requests
import pandas as pd
import time
import google.generativeai as genai

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Crypto Bot AI",
    page_icon="🪙",
    layout="wide"
)

# 2. Fungsi Pemanggilan API Indodax
@st.cache_data(ttl=10)
def get_crypto_data():
    try:
        url = "https://indodax.com/api/summaries"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get("tickers", {})
    except Exception as e:
        st.error(f"Gagal mengambil data Indodax: {e}")
        return {}

# 3. Fungsi Pemanggilan AI dengan Auto-Retry Tangguh
def get_ai_analysis(prompt):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY belum diisi di Secrets Streamlit Cloud."

    genai.configure(api_key=api_key)
    
    # Urutan model yang dicoba jika server sibuk/limit
    models_to_try = [
        'gemini-1.5-flash', 
        'gemini-2.0-flash', 
        'gemini-1.5-flash-8b', 
        'gemini-1.5-pro'
    ]

    # Percobaan hingga 3 kali jika server 503
    for attempt in range(3):
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception:
                time.sleep(1)  # Jeda sebentar sebelum coba lagi
                continue

    return None

# --- UI Utama ---
st.title("🪙 Crypto Market & AI Analyzer")

tickers = get_crypto_data()

if tickers:
    # Filter pasangan koin berbasis IDR
    pair_list = sorted([k for k in tickers.keys() if k.endswith("_idr")])
    
    selected_pair = st.selectbox(
        "Pilih Pasangan Koin (IDR):", 
        pair_list, 
        index=pair_list.index("btc_idr") if "btc_idr" in pair_list else 0
    )

    coin_info = tickers[selected_pair]
    last_price = int(coin_info.get("last", 0))
    high_price = int(coin_info.get("high", 0))
    low_price = int(coin_info.get("low", 0))
    vol_idr = float(coin_info.get("vol_idr", 0))

    # Tampilan Informasi Harga
    col1, col2, col3 = st.columns(3)
    col1.metric("Harga Saat Ini", f"Rp {last_price:,}")
    col2.metric("Harga Tertinggi (24j)", f"Rp {high_price:,}")
    col3.metric("Harga Terendah (24j)", f"Rp {low_price:,}")

    # Indikator Area Tertinggi
    if high_price > 0 and last_price >= (high_price * 0.98):
        st.warning("🔥 **Perhatian Area High**: Harga berada di dekat puncak 24j. Hati-hati terhadap aksi profit taking.")

    # Input Modal Pengguna
    buy_price = st.number_input("Modal / Harga Beli Kamu (Rp):", min_value=0, value=0, step=100)

    # Tombol Analisis AI
    if st.button("🤖 Dapatkan Analisis AI"):
        with st.spinner("Sedang menghubungi AI Gemini..."):
            prompt = f"""
            Kamu adalah analis pasar kripto profesional. Analisis data koin berikut dari Indodax:
            - Pasangan: {selected_pair.upper()}
            - Harga Saat Ini: Rp {last_price:,}
            - Harga Tertinggi 24j: Rp {high_price:,}
            - Harga Terendah 24j: Rp {low_price:,}
            - Volume 24j (IDR): Rp {vol_idr:,.0f}
            - Harga Modal Pengguna: Rp {buy_price:,}

            Berikan kesimpulan ringkas:
            1. Kondisi tren harga saat ini.
            2. Potensi risiko (Take Profit/Stop Loss).
            3. Saran aksi cepat untuk pengguna berdasarkan modalnya.
            """
            
            ai_result = get_ai_analysis(prompt)
            
            if ai_result:
                st.success("### Analisis AI:")
                st.markdown(ai_result)
            else:
                st.error("⚠️ Server AI Google sedang sibuk (503). Silakan klik tombol sekali lagi dalam beberapa detik.")
else:
    st.info("Memuat data pasar...")
