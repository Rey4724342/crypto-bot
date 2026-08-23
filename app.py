import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from google import genai

st.set_page_config(
    page_title="Crypto AI Analyst - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

st.title("📈 Crypto AI Analyst & Trading Hub")
st.caption("by Rey472")

# 1. Fungsi Ambil Data Pasangan Indodax
@st.cache_data(ttl=600)
def get_indodax_summary():
    try:
        url = "https://indodax.com/api/summaries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers).json()
        return res
    except Exception:
        return {}

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

# Sidebar Pengaturan
st.sidebar.header("⚙️ Navigasi & Pengaturan")

selected_label = st.sidebar.selectbox(
    "🔍 Cari & Pilih Koin / Pair Indodax",
    options=list(pairs_data.keys()),
    index=0
)

selected_info = pairs_data[selected_label]
ticker_id = selected_info['ticker_id']
symbol = selected_info['symbol']

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Mode Gaya Trading AI")
trading_style = st.sidebar.radio(
    "Pilih Strategi:",
    ["Swing Trading (Santai / Menengah)", "Scalping (Cepat / Intraday)"]
)

st.sidebar.markdown("---")
if selected_info['logo_url']:
    st.sidebar.image(selected_info['logo_url'], width=50)
st.sidebar.subheader(selected_info['clean_name'])
st.sidebar.write(f"**Pair Code:** `{ticker_id}`")

# 2. FITUR 1: Top Gainers & Losers (Di Atas Dashboard)
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
                # Estimasi sederhana perubahan % 24j berdasarkan high/low
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

# Main Header
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if selected_info['logo_url']:
        st.image(selected_info['logo_url'], width=64)
with col_title:
    st.subheader(f"{selected_info['clean_name']} / IDR")

# Embed Grafik TradingView
st.markdown("#### 📊 Grafik Candlestick Market")
tv_symbol = f"BINANCE:{symbol}USDT" if symbol != "BTC" else "BINANCE:BTCUSDT"

tradingview_html = f"""
<div class="tradingview-widget-container" style="height:480px;width:100%;">
  <div id="tradingview_chart" style="height:480px;width:100%;"></div>
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
components.html(tradingview_html, height=500)

# Tombol Analisis AI & Ambil Ticker
if st.button("🔍 Mulaikan Analisis Market (AI & Sinyal)", use_container_width=True):
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

        # 3. FITUR 2: Indikator Sinyal Teknikal (RSI Estimasi & Position)
        st.markdown("#### ⚡ Sinyal Indikator Teknikal Ringkas")
        range_harga = high - low
        posisi_harga = ((harga - low) / range_harga) * 100 if range_harga > 0 else 50
        
        col_rsi, col_ma = st.columns(2)
        with col_rsi:
            if posisi_harga > 80:
                st.warning(f"⚠️ **Kondisi Momentum:** mendekati Overbought ({posisi_harga:.1f}% dari range harian). Waspada koreksi!")
            elif posisi_harga < 20:
                st.success(f"💡 **Kondisi Momentum:** mendekati Oversold ({posisi_harga:.1f}% dari range harian). Potensi akumulasi!")
            else:
                st.info(f"⚖️ **Kondisi Momentum:** Netral ({posisi_harga:.1f}% dari range harian).")
                
        with col_ma:
            avg_24h = (high + low) // 2
            if harga > avg_24h:
                st.success(f"📈 **Tren Harian:** Di atas rata-rata 24j (Rp {avg_24h:,}). Sinyal Bulish pendek.")
            else:
                st.error(f"📉 **Tren Harian:** Di bawah rata-rata 24j (Rp {avg_24h:,}). Sinyal Bearish pendek.")

        # Eksekusi AI Gemini
        api_key = st.secrets.get("GEMINI_API_KEY")

        if not api_key:
            st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
        else:
            with st.spinner(f"AI sedang menganalisis ({trading_style})..."):
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                Kamu adalah konsultan Trading Crypto profesional.
                Gaya Trading Pengguna: {trading_style}
                
                Lakukan analisis teknikal dan berikan arahan untuk aset berikut:
                - Nama Aset: {selected_info['clean_name']}
                - Harga Saat Ini: Rp {harga:,}
                - Harga Tertinggi 24j: Rp {high:,}
                - Harga Terendah 24j: Rp {low:,}

                Berikan rekomendasi spesifik sesuai gaya {trading_style} dalam format poin rapi:
                1. 🟢 Rekomendasi Aksi: (BUY / WAIT / SELL)
                2. 📥 Area Beli / Buy Entry (Range harga ideal dalam Rp)
                3. 🎯 Target Profit / TP (TP1 & TP2 dalam Rp)
                4. 🛑 Stop Loss / SL (Batas rugi dalam Rp)
                5. 💡 Ringkasan Analisis & Alasan
                """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt
                )
                
                st.markdown("### 🤖 Hasil Analisis AI Gemini")
                st.info(response.text)
                
    except Exception as e:
        st.error(f"Gagal memuat analisis: {e}")

# 4. FITUR 3: Kalkulator Risk / Reward & Money Management
st.markdown("---")
st.markdown("### 🧮 Kalkulator Management Risiko & Posisi Beli")

calc_col1, calc_col2 = st.columns(2)

with calc_col1:
    modal_rp = st.number_input("Modal Trading Kamu (Rp):", min_value=10000, value=1000000, step=50000)
    risk_pct = st.slider("Batas Toleransi Rugi per Trade (% Modal):", min_value=1.0, max_value=10.0, value=2.0, step=0.5)

with calc_col2:
    entry_price = st.number_input("Rencana Harga Beli (Entry Rp):", min_value=1, value=100000)
    sl_price = st.number_input("Rencana Stop Loss (SL Rp):", min_value=1, value=95000)

if entry_price > sl_price:
    potensi_rugi_per_koin = entry_price - sl_price
    persen_rugi_koin = (potensi_rugi_per_koin / entry_price) * 100
    maks_resiko_rp = modal_rp * (risk_pct / 100)
    rekomendasi_posisi_rp = (maks_resiko_rp / persen_rugi_koin) * 100 if persen_rugi_koin > 0 else 0
    
    st.markdown("#### 📌 Hasil Perhitungan Risiko:")
    res_c1, res_c2 = st.columns(2)
    res_c1.metric("Maksimal Kerugian Aman", f"Rp {int(maks_resiko_rp):,}")
    res_c2.metric("Rekomendasi Posisi Beli (Alokasi Modal)", f"Rp {int(min(rekomendasi_posisi_rp, modal_rp)):,}")
    
    st.caption(f"💡 *Jika hitungan Stop Loss tersentuh (-{persen_rugi_koin:.2f}%), kamu hanya akan rugi Rp {int(maks_resiko_rp):,} sesuai batas risiko {risk_pct}% kamu.*")
else:
    st.warning("⚠️ Harga Stop Loss harus lebih rendah dari harga Entry Beli!")
