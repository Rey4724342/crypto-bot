import streamlit as st
import requests
import pandas as pd
from google import genai
from google.genai import types

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Crypto Bot AI",
    page_icon="🪙",
    layout="wide"
)

# 2. Fungsi Ambil Data Indodax
@st.cache_data(ttl=10)
def get_crypto_data():
    try:
        url = "https://indodax.com/api/summaries"
        res = requests.get(url, timeout=10)
        return res.json().get("tickers", {})
    except Exception as e:
        st.error(f"Gagal mengambil data Indodax: {e}")
        return {}

# 3. Fungsi Pemanggilan AI dengan SDK Resmi Baru (google-genai)
def get_ai_analysis(prompt):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY belum diisi di Streamlit Secrets."

    try:
        # Inisialisasi client SDK baru
        client = genai.Client(api_key=api_key)
        
        # Menggunakan model terbaru yang stabil
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        if response and response.text:
            return response.text
    except Exception as e:
        # Jika model utama sibuk, fallback ke gemini-2.0-flash
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            if response and response.text:
                return response.text
        except Exception as inner_e:
            return None

    return None

# --- UI Utama ---
st.title("🪙 Crypto Market & AI Analyzer")

tickers = get_crypto_data()

if tickers:
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

    # Tampilan Metric
    col1, col2, col3 = st.columns(3)
    col1.metric("Harga Saat Ini", f"Rp {last_price:,}")
    col2.metric("Harga Tertinggi (24j)", f"Rp {high_price:,}")
    col3.metric("Harga Terendah (24j)", f"Rp {low_price:,}")

    if high_price > 0 and last_price >= (high_price * 0.98):
        st.warning("🔥 **Perhatian Area High**: Harga berada di dekat puncak 24j. Hati-hati terhadap aksi profit taking.")

    buy_price = st.number_input("Modal / Harga Beli Kamu (Rp):", min_value=0, value=0, step=100)

    if st.button("🤖 Dapatkan Analisis AI"):
        with st.spinner("Sedang menganalisis pasar..."):
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
                st.error("⚠️ Kuota API Gemini kamu sedang limit / habis. Tunggu 1 menit lalu coba lagi, atau cek API Key kamu di Google AI Studio.")
else:
    st.info("Memuat data pasar...")
