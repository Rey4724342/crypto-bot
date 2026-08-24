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

# 🔒 CSS Responsif Khusus Komputer & Android
responsive_css = """
            <style>
            #MainMenu {display: none !important;}
            header {display: none !important;}
            footer {display: none !important;}
            .stAppHeader {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="stDecoration"] {display: none !important;}
            [data-testid="stStatusWidget"] {display: none !important;}
            div[class*="viewerBadge"] {display: none !important;}

            @media only screen and (max-width: 768px) {
                .stTabs [data-baseweb="tab-list"] {
                    gap: 4px;
                    overflow-x: auto;
                    flex-wrap: nowrap;
                }
                .stTabs [data-baseweb="tab"] {
                    font-size: 12px;
                    padding: 8px 10px;
                }
                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }
            }
            </style>
            """
st.markdown(responsive_css, unsafe_allow_html=True)

if 'journal' not in st.session_state:
    st.session_state.journal = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data(ttl=300)
def get_indodax_summary():
    try:
        url = "https://indodax.com/api/summaries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers, timeout=5).json()
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def get_all_indodax_pairs():
    try:
        url = "https://indodax.com/api/pairs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        
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

tab_main, tab_compare, tab_journal, tab_calc, tab_chat = st.tabs([
    "📈 Dashboard Utama & AI", 
    "🔀 Perbandingan Koin", 
    "📓 Jurnal Trading", 
    "🧮 Kalkulator & Averaging",
    "💬 Asisten AI Chat"
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

    # ⚡ SOLUSI ANTI-LOADING ANDROID: Menggunakan TradingView Advanced Widget Container Script
    st.markdown("#### 📊 Grafik Candlestick Market (Real-Time)")
    
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:450px;width:100%">
      <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
        "autosize": true,
        "symbol": "BINANCE:{symbol}USDT",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "id",
        "allow_symbol_change": true,
        "calendar": false,
        "support_host": "https://www.tradingview.com"
      }}
      </script>
    </div>
    """
    components.html(tv_html, height=460)

    st.markdown("---")

    st.markdown(f"### 💼 Analisis Posisi Portofolio Saya ({symbol})")
    st.caption("💡 *Ketik angka polos tanpa titik/koma (misal: 1324307).*")

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
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5).json()['ticker']
            
            current_market_price = int(res['last'])
            high = int(res['high'])
            low = int(res['low'])

            if current_market_price <= low * 1.02:
                st.warning("⚠️ **Perhatian Risk**: Harga pasar saat ini berada sangat dekat dengan titik terendah (Low 24j). Pertimbangkan konfirmasi pantulan support.")
            elif current_market_price >= high * 0.98:
                st.warning("🔥 **Perhatian Area High**: Harga berada di dekat puncak 24j. Hati-hati terhadap aksi profit taking.")

            if my_buy_price > 0:
                pnl_rp = (current_market_price - my_buy_price) * my_amount_coin
                pnl_pct = ((current_market_price - my_buy_price) / my_buy_price) * 100
            else:
                pnl_rp = 0
                pnl_pct = 0

            c1, c2, c3 = st.columns(3)
            c1.metric(label="Harga Pasar Saat Ini", value=f"Rp {current_market_price:,}")
            c2.metric(label="Modal/Harga Beli Kamu", value=f"Rp {int(my_buy_price):,}")
            
            if my_buy_price > 0:
                if pnl_pct >= 0:
                    c3.metric(label="Status PnL (Keuntungan)", value=f"+Rp {int(pnl_rp):,}", delta=f"+{pnl_pct:.2f}%")
                else:
                    c3.metric(label="Status PnL (Kerugian)", value=f"-Rp {abs(int(pnl_rp)):,}", delta=f"{pnl_pct:.2f}%")
            else:
                c3.metric(label="Status PnL", value="Belum diisi (0)")

            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets!")
            else:
                with st.spinner(f"AI sedang merespon analisis cepat koin {symbol}..."):
                    client = genai.Client(api_key=api_key)
                    
                    prompt = f"""
                    Kamu adalah konsultan Trading Crypto profesional buatan Rey472.
                    Gaya Trading Pengguna: {trading_style}
                    
                    Data Posisi Pengguna:
                    - Nama Aset: {selected_info['clean_name']}
                    - Harga Beli Awal Pengguna: Rp {my_buy_price:,}
                    - Harga Pasar Saat Ini: Rp {current_market_price:,}
                    - Status Profit/Loss Sementara: {pnl_pct:.2f}% (Rp {int(pnl_rp):,})
                    - Harga Tertinggi 24j: Rp {high:,}
                    - Harga Terendah 24j: Rp {low:,}

                    Berikan analisis ringkas, padat, dan taktis dalam format poin rapi:
                    1. 🌐 Analisis Posisi Saat Ini
                    2. 🟢 Rekomendasi Aksi Utama: (HOLD / TAKE PROFIT / CUT LOSS / BUY ON DIP)
                    3. 🛑 Saran Harga Stop Loss (SL) yang aman.
                    4. 🎯 Target Jual / Take Profit (TP1 & TP2) dalam Rupiah.
                    5. 💡 Tips Manajemen Risiko singkat dari AI Rey472.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt
                    )
                    
                    st.markdown("### 🤖 Hasil Analisis Kilat AI Rey472")
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
            
            res1 = requests.get(f"https://indodax.com/api/ticker/{t1}", timeout=5).json()['ticker']
            res2 = requests.get(f"https://indodax.com/api/ticker/{t2}", timeout=5).json()['ticker']
            
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
        j_price = st.number_input("Harga Beli/Jual (Rp):", min_value=0.0, value=0.0, step=100.0)
        j_notes = st.text_area("Catatan Alasan Trade / Strategi:")
        
        submitted = st.form_submit_button("➕ Simpan ke Catatan")
        if submitted:
            st.session_state.journal.append({
                "Koin": j_coin,
                "Tipe": j_type,
                "Harga": f"Rp {j_price:,.0f}",
                "Catatan": j_notes
            })
            st.success("Catatan trading tersimpan!")

    if st.session_state.journal:
        st.markdown("#### 📜 Riwayat Catatan Kamu:")
        df_j = pd.DataFrame(st.session_state.journal)
        st.dataframe(df_j, use_container_width=True)
        if st.button("🗑️ Hapus Semua Catatan"):
            st.session_state.journal = []
            st.rerun()

# ================= TAB 4: KALKULATOR & AVERAGING =================
with tab_calc:
    st.markdown("### 🧮 Kalkulator Trading & Averaging Down")
    
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        st.markdown("#### 1. Risk / Reward Calculator")
        modal_rp = st.number_input("Modal Trading Kamu (Rp):", min_value=0.0, value=0.0, step=50000.0)
        risk_pct = st.slider("Batas Toleransi Rugi per Trade (% Modal):", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
        entry_price = st.number_input("Rencana Harga Beli (Entry Rp):", min_value=0.0, value=0.0)
        sl_price = st.number_input("Rencana Stop Loss (SL Rp):", min_value=0.0, value=0.0)

        if entry_price > 0 and sl_price > 0 and entry_price > sl_price:
            potensi_rugi_per_koin = entry_price - sl_price
            persen_rugi_koin = (potensi_rugi_per_koin / entry_price) * 100
            maks_resiko_rp = modal_rp * (risk_pct / 100)
            rekomendasi_posisi_rp = (maks_resiko_rp / persen_rugi_koin) * 100 if persen_rugi_koin > 0 else 0
            
            st.info(f"💡 Maksimal Rugi Aman: **Rp {int(maks_resiko_rp):,}**")
            st.success(f"💡 Alokasi Beli Ideal: **Rp {int(min(rekomendasi_posisi_rp, modal_rp)):,}**")
        else:
            st.warning("⚠️ Masukkan harga entry dan stop loss yang valid.")

    with calc_col2:
        st.markdown("#### 2. Kalkulator Averaging Down")
        avg_price1 = st.number_input("Harga Beli Pertama (Rp):", min_value=0.0, value=0.0, key="avg_p1")
        avg_qty1 = st.number_input(f"Jumlah Koin {symbol} Beli Pertama:", min_value=0.0, value=0.0, key="avg_q1")
        
        avg_price2 = st.number_input("Harga Beli Kedua / Serok (Rp):", min_value=0.0, value=0.0, key="avg_p2")
        avg_qty2 = st.number_input(f"Jumlah Koin {symbol} Beli Kedua:", min_value=0.0, value=0.0, key="avg_q2")

        if (avg_qty1 + avg_qty2) > 0:
            total_modal = (avg_price1 * avg_qty1) + (avg_price2 * avg_qty2)
            total_koin = avg_qty1 + avg_qty2
            avg_final_price = total_modal / total_koin
            
            st.success(f"🎯 **Harga Rata-Rata Baru (Average Price)**: Rp {avg_final_price:,.2f}")
            st.info(f"💰 Total Modal Dikeluarkan: **Rp {total_modal:,.0f}** | Total Aset: **{total_koin:.4f} {symbol}**")

# ================= TAB 5: ASISTEN AI CHAT =================
with tab_chat:
    st.markdown("### 💬 Asisten Trading AI Rey472")
    st.caption("Tanyakan apa saja seputar strategi crypto, cara membaca grafik, manajemen emosi, atau tips trading secara interaktif.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("Tanyakan sesuatu ke AI Rey472...")

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ API Key belum terkonfigurasi di Streamlit Secrets.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("AI sedang berpikir..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        chat_prompt = f"""
                        Kamu adalah Asisten Trading Crypto AI buatan Rey472 yang ramah, taktis, dan cerdas.
                        Koin yang sedang diamati pengguna saat ini: {symbol}.
                        Pertanyaan pengguna: {user_query}

                        Jawab secara jelas, praktis, dan langsung ke inti pembahasan.
                        """
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=chat_prompt
                        )
                        reply = response.text
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as err:
                        st.error(f"Gagal memproses pesan: {err}")
