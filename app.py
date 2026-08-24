import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from google import genai

st.set_page_config(
    page_title="Crypto AI Analyst Pro - Rey472", 
    page_icon="🪙", 
    layout="wide"
)

# 🔒 CSS Khusus: Hilangkan Menu Atas, Header, Toolbar, dan Logo Merah di HP & PC
hide_streamlit_style = """
            <style>
            #MainMenu {display: none !important;}
            header {display: none !important;}
            footer {display: none !important;}
            .stAppHeader {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="stDecoration"] {display: none !important;}
            [data-testid="stStatusWidget"] {display: none !important;}
            
            /* Sembunyikan Logo Merah / Streamlit Badge */
            div[class*="viewerBadge"] {display: none !important;}
            div[class*="stEmotioncache"] {background: transparent;}
            iframe[title="data-testid"] {display: none !important;}
            .viewerBadge_container__1A53K {display: none !important;}
            .viewerBadge_link__1S137 {display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize Session State
if 'journal' not in st.session_state:
    st.session_state.journal = []

# Fungsi Data Indodax
@st.cache_data(ttl=600)
def get_indodax_summary():
    try:
        url = "https://indodax.com/api/summaries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers).json()
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

# Header Utama
st.title("🚀 Crypto AI Trading Hub & Analyst Pro")
st.markdown("<h4 style='color: #4CAF50; margin-top: -15px;'>👨‍💻 Pencipta: <b>Rey472</b></h4>", unsafe_allow_html=True)
st.markdown("---")

# Menu Utama di Halaman Depan
st.markdown("### ⚙️ Pengaturan Koin & Strategi")
menu_col1, menu_col2 = st.columns(2)

with menu_col1:
    selected_label = st.selectbox(
        "🔍 Cari & Pilih Koin Utama:",
        options=list(pairs_data.keys()),
        index=0
    )

with menu_col2:
    trading_style = st.radio(
        "🎯 Pilih Mode Strategi AI:",
        ["Swing Trading (Santai / Menengah)", "Scalping (Cepat / Intraday)"],
        horizontal=True
    )

selected_info = pairs_data[selected_label]
ticker_id = selected_info['ticker_id']
symbol = selected_info['symbol']

st.markdown("---")

tab_main, tab_compare, tab_journal, tab_calc = st.tabs([
    "📈 Dashboard Utama & AI", 
    "🔀 Perbandingan Koin", 
    "📓 Jurnal Trading", 
    "🧮 Kalkulator & Converter"
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
        # Perbaikan Nama Judul (Tidak Double Lagi)
        st.subheader(f"{symbol} / IDR")

    # 🚀 GRAFIK TRADINGVIEW INSTAN (Bentuk Kotak di Web, Tanpa Loading Lama Muter-muter)
    st.markdown("#### 📊 Grafik Candlestick Market")
    
    # Menggunakan URL widget iframe resmi TradingView yang langsung dirender tanpa script berat
    tv_fast_url = f"https://s.tradingview.com/widgetembed/?symbol=BINANCE:{symbol}USDT&interval=60&hidesidetoolbar=0&hidetoptoolbar=0&symboledit=1&saveimage=1&toolbarbg=F1F3F6&studies=[]&theme=dark&style=1&timezone=Asia/Jakarta&withdateranges=1"
    
    components.iframe(tv_fast_url, height=500, scrolling=False)

    # Target Alert
    st.markdown("#### 🚨 Set Target Alert Harga Kamu")
    alert_target = st.number_input(f"Masukkan Harga Target Beli/Jual untuk {symbol} (Rp):", min_value=0, value=0, step=1000)

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

            if alert_target > 0:
                if harga <= alert_target:
                    st.balloons()
                    st.success(f"🎯 **ALERT DISENTUH!** Harga {symbol} saat ini (Rp {harga:,}) sudah mencapai target belimu (Rp {alert_target:,})!")
                else:
                    st.info(f"⏳ Harga saat ini masih di atas target alert (Selisih: Rp {harga - alert_target:,}).")

            st.markdown("#### ⚡ Sinyal Indikator Teknikal Ringkas")
            range_harga = high - low
            posisi_harga = ((harga - low) / range_harga) * 100 if range_harga > 0 else 50
            
            col_rsi, col_ma = st.columns(2)
            with col_rsi:
                if posisi_harga > 80:
                    st.warning(f"⚠️ **Momentum:** Overbought ({posisi_harga:.1f}%). Waspada koreksi!")
                elif posisi_harga < 20:
                    st.success(f"💡 **Momentum:** Oversold ({posisi_harga:.1f}%). Potensi akumulasi!")
                else:
                    st.info(f"⚖️ **Momentum:** Netral ({posisi_harga:.1f}%).")
                    
            with col_ma:
                avg_24h = (high + low) // 2
                if harga > avg_24h:
                    st.success(f"📈 **Tren Harian:** Bullish (di atas rata-rata Rp {avg_24h:,}).")
                else:
                    st.error(f"📉 **Tren Harian:** Bearish (di bawah rata-rata Rp {avg_24h:,}).")

            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
            else:
                with st.spinner(f"AI sedang menganalisis ({trading_style})..."):
                    client = genai.Client(api_key=api_key)
                    
                    prompt = f"""
                    Kamu adalah konsultan Trading Crypto profesional buatan Rey472.
                    Gaya Trading Pengguna: {trading_style}
                    
                    Lakukan analisis teknikal dan sentimen singkat untuk aset berikut:
                    - Nama Aset: {selected_info['clean_name']}
                    - Harga Saat Ini: Rp {harga:,}
                    - Harga Tertinggi 24j: Rp {high:,}
                    - Harga Terendah 24j: Rp {low:,}

                    Berikan rekomendasi spesifik sesuai gaya {trading_style} dalam format poin rapi:
                    1. 🌐 Sentimen Pasar AI Rey472 (Bullish / Neutral / Bearish)
                    2. 🟢 Rekomendasi Aksi: (BUY / WAIT / SELL)
                    3. 📥 Area Beli / Buy Entry (Range harga ideal dalam Rp)
                    4. 🎯 Target Profit / TP (TP1 & TP2 dalam Rp)
                    5. 🛑 Stop Loss / SL (Batas rugi dalam Rp)
                    6. 💡 Ringkasan Analisis & Alasan
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=prompt
                    )
                    
                    st.markdown("### 🤖 Hasil Analisis AI Rey472 & Sentimen Pasar")
                    st.info(response.text)
                    
        except Exception as e:
            st.error(f"Gagal memuat analisis: {e}")

# ================= TAB 2: PERBANDINGAN KOIN =================
with tab_compare:
    st.markdown("### 🔀 Bandingkan 2 Koin Indodax")
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        coin1_label = st.selectbox("Pilih Koin Pertama:", options=list(pairs_data.keys()), index=0)
    with comp_col2:
        coin2_label = st.selectbox("Pilih Koin Kedua:", options=list(pairs_data.keys()), index=min(1, len(pairs_data)-1))
        
    if st.button("⚖️ Bandingkan Sekarang"):
        try:
            t1 = pairs_data[coin1_label]['ticker_id']
            t2 = pairs_data[coin2_label]['ticker_id']
            
            res1 = requests.get(f"https://indodax.com/api/ticker/{t1}").json()['ticker']
            res2 = requests.get(f"https://indodax.com/api/ticker/{t2}").json()['ticker']
            
            c1_col, c2_col = st.columns(2)
            with c1_col:
                st.subheader(coin1_label)
                st.metric("Harga Terakhir", f"Rp {int(res1['last']):,}")
                st.metric("High 24j", f"Rp {int(res1['high']):,}")
                st.metric("Low 24j", f"Rp {int(res1['low']):,}")
                st.metric("Volume 24j", f"{float(res1['vol_idr']):,.0f} IDR")
                
            with c2_col:
                st.subheader(coin2_label)
                st.metric("Harga Terakhir", f"Rp {int(res2['last']):,}")
                st.metric("High 24j", f"Rp {int(res2['high']):,}")
                st.metric("Low 24j", f"Rp {int(res2['low']):,}")
                st.metric("Volume 24j", f"{float(res2['vol_idr']):,.0f} IDR")
        except Exception as err:
            st.error(f"Gagal membandingkan koin: {err}")

# ================= TAB 3: JURNAL TRADING =================
with tab_journal:
    st.markdown("### 📓 Jurnal Catatan Trading")
    
    with st.form("journal_form"):
        j_coin = st.text_input("Nama Koin / Ticker:", value=symbol)
        j_type = st.selectbox("Tipe Transaksi:", ["BUY / BELI", "SELL / JUAL"])
        j_price = st.number_input("Harga Beli/Jual (Rp):", min_value=1, value=100000)
        j_notes = st.text_area("Catatan Alasan Trade / Strategi:")
        
        submitted = st.form_submit_button("➕ Simpan ke Catatan")
        if submitted:
            st.session_state.journal.append({
                "Koin": j_coin,
                "Tipe": j_type,
                "Harga": f"Rp {j_price:,}",
                "Catatan": j_notes
            })
            st.success("Catatan trading tersimpan!")

    if st.session_state.journal:
        st.markdown("#### 📜 Riwayat Catatan Kamu:")
        df_j = pd.DataFrame(st.session_state.journal)
        st.dataframe(df_j, use_container_width=True)
        if st.button("🗑️ Hapus Semua Catatan"):
            st.session_state.journal = []
            st.experimental_rerun()

# ================= TAB 4: KALKULATOR & CONVERTER =================
with tab_calc:
    st.markdown("### 🧮 Kalkulator Management Risiko & Converter Instant")
    
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        st.markdown("#### 1. Risk / Reward Calculator")
        modal_rp = st.number_input("Modal Trading Kamu (Rp):", min_value=10000, value=1000000, step=50000)
        risk_pct = st.slider("Batas Toleransi Rugi per Trade (% Modal):", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
        entry_price = st.number_input("Rencana Harga Beli (Entry Rp):", min_value=1, value=100000)
        sl_price = st.number_input("Rencana Stop Loss (SL Rp):", min_value=1, value=95000)

        if entry_price > sl_price:
            potensi_rugi_per_koin = entry_price - sl_price
            persen_rugi_koin = (potensi_rugi_per_koin / entry_price) * 100
            maks_resiko_rp = modal_rp * (risk_pct / 100)
            rekomendasi_posisi_rp = (maks_resiko_rp / persen_rugi_koin) * 100 if persen_rugi_koin > 0 else 0
            
            st.info(f"💡 Maksimal Rugi Aman: **Rp {int(maks_resiko_rp):,}**")
            st.success(f"💡 Alokasi Beli Ideal: **Rp {int(min(rekomendasi_posisi_rp, modal_rp)):,}**")
        else:
            st.warning("⚠️ Harga Stop Loss harus lebih rendah dari harga Entry Beli!")

    with calc_col2:
        st.markdown("#### 2. Instant Converter Rupiah ➡️ Koin")
        conv_rupiah = st.number_input("Jumlah Rupiah Beli:", min_value=10000, value=500000, step=50000)
        conv_price = st.number_input(f"Harga Koin {symbol} (Rp):", min_value=1, value=100000)
        fee_pct = 0.5
        
        nett_rp = conv_rupiah * (1 - (fee_pct/100))
        estimasi_koin = nett_rp / conv_price if conv_price > 0 else 0
        
        st.metric(f"Estimasi Koin {symbol} Diperoleh:", f"{estimasi_koin:.6f} {symbol}")
        st.caption(f"*Sudah termasuk potongan estimasi fee ~{fee_pct}% Indodax.")
