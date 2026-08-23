import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(page_title="Crypto AI Analyst", layout="centered")
st.title("📈 Crypto Swing AI Analyst")
st.caption("by Rey472")

# Sidebar Input
api_key = st.sidebar.text_input("Gemini API Key", type="password")
pair = st.sidebar.selectbox("Pilih Pair Indodax", ["btc_idr", "eth_idr", "sol_idr"])

if api_key:
    genai.configure(api_key=api_key)

# Ambil data dari Indodax
if st.button("🔍 Analisis Market"):
    res = requests.get(f"https://indodax.com/api/ticker/{pair}").json()['ticker']
    harga = int(res['last'])
    high = int(res['high'])
    low = int(res['low'])

    st.metric(label=f"Harga {pair.upper()}", value=f"Rp {harga:,}")

    if not api_key:
        st.warning("Masukkan Gemini API Key di sidebar!")
    else:
        with st.spinner("AI sedang menganalisis..."):
            prompt = f"""
            Analisis pair {pair} untuk Swing Trading:
            - Harga Saat Ini: Rp {harga}
            - Tertinggi 24j: Rp {high}
            - Terendah 24j: Rp {low}

            Berikan saran ringkas:
            1. Area Beli (Entry)
            2. Target Profit (TP)
            3. Stop Loss (SL)
            4. Ringkasan Alasan Analisis
            """
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            st.write(response.text)
