import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page configurations
st.set_page_config(page_title="Mega Auto Sector Scanner", layout="wide")

st.title("🚗 TechnoFunda Mega Auto Sector Scanner (100+ Stocks)")
st.write("Is engine me Auto, Auto Components, Electric Vehicles (EV) Infrastructure aur Ancillary segments ke small-caps se large-caps tak 100+ stocks mapped hain.")

# --- 1. Pure 100+ Auto Sector Universe ---
@st.cache_data(ttl=86400)
def load_auto_universe():
    tickers = [
        # --- LARGE CAPS (OEMs & Heavyweights) ---
        "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "EICHERMOT.NS", "TVSMOTOR.NS", "HEROMOTOCO.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS",
        
        # --- AUTO ANCILLARY & COMPONENTS (Mid to Small Caps) ---
        "BHARATFORG.NS", "SONACOMS.NS", "TIINDIA.NS", "BALKRISIND.NS", "BOSCHLTD.NS", "SUPRAJIT.NS", "ENDURANCE.NS", "UNOINDA.NS",
        "CIEINDIA.NS", "SANDHAR.NS", "MNDAcorp.NS", "GRAVITA.NS", "SUBROS.NS", "SHARDAMOTR.NS", "PRICOL.NS", "LUMAXIND.NS",
        "FIEMIND.NS", "RICOAUTO.NS", "JAYBARMARU.NS", "AUTOLIT.NS", "BANCOINDIA.NS", "TALBROSAUTO.NS", "GABRIEL.NS", "STEELCAS.NS",
        "SURAJEST.NS", "RKFORGE.NS", "MUNJALAU.NS", "ALIGNCON.NS", "ASAL.NS", "IFBIND.NS", "MENONBE.NS", "DENSO.NS",
        
        # --- TYRES & TUBES ---
        "MRF.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "CEATLTD.NS", "JKTYRE.NS", "GOODYEAR.NS", "TVSSRICHAK.NS", "MODITYRES.NS",
        
        # --- EV INFRASTRUCTURE, BATTERIES & ELECTRICALS ---
        "EXIDEIND.NS", "AMARAJABAT.NS", "EXICOM.NS", "HBLPOWER.NS", "SERVOTECH.NS", "SJS.NS", "KPITTECH.NS", "TATAPOWER.NS",
        
        # --- FORGINGS, CASTINGS & BEARINGS ---
        "TIMKEN.NS", "SKFINDIA.NS", "SCHAEFFLER.NS", "AIAENG.NS", "MENON.NS", "ROLEXRNG.NS", "KIMS.NS", "REPL.NS",
        "RAJRATAN.NS", "MMFORG.NS", "BALAMINES.NS", "RAMKRISHN.NS", "SIMMONDS.NS", "MAHINDCIE.NS", "PANCHMAHAL.NS",
        
        # --- SMALL CAP & MICRO CAP MOMENTUM AUTO STOCKS ---
        "PANACHE.NS", "AUTOIND.NS", "SALZERELEC.NS", "SAMKRG.NS", "OLECTRA.NS", "JBMAUTO.NS", "SMLISUZU.NS", "FORCEMOT.NS",
        "SINTERCOM.NS", "INNOVACAP.NS", "RACLGEAR.NS", "SHIVAMAUTO.NS", "GNA.NS", "NDRAUTO.NS", "PPAP.NS", "REPL.NS",
        "SMAL.NS", "CREATIVE.NS", "REVATHI.NS", "MOLDTEKPAC.NS", "OSWALAGRO.NS", "SARAUTO.NS", "SIMMONDS.NS", "DUNCANS.NS",
        "VIMAL.NS", "TAAL.NS", "ALICON.NS", "AEROFLEX.NS", "KIRLIND.NS", "GEOMETRIC.NS", "PRADEEP.NS", "HINDCOMP.NS"
    ]
    # Duplicates hata kar alphabetically sort karna
    return sorted(list(set(tickers)))

# --- 2. Structural Scanning Engine ---
def scan_auto_sector(ticker_list, vol_threshold=2.0, lookback_days=30, consolidation_window=6, max_box_width_pct=6.0):
    scanned_results = []
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # API failure aur blockage se bachne ke liye safe batch chunks
    chunk_size = 20
    total_tickers = len(ticker_list)
    
    for i in range(0, total_tickers, chunk_size):
        batch = ticker_list[i:i + chunk_size]
        current_progress = min(1.0, i / total_tickers)
        progress_bar.progress(current_progress)
        status_text.text(f"Scanning Auto Segment Stocks {i} to {min(i + chunk_size, total_tickers)} of {total_tickers}...")
        
        try:
            data = yf.download(batch, start=start_date, progress=False)
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    # Multi-index slicing safety framework
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data.columns.levels[1]:
                            s_data = data.xs(ticker, axis=1, level=1).dropna()
                        elif ticker in data.columns.levels[0]:
                            s_data = data[ticker].dropna()
                        else:
                            continue
                    else:
                        s_data = data.dropna()
                        
                    if len(s_data) < 40:
                        continue
                        
                    closes = s_data['Close'].values
                    vols = s_data['Volume'].values
                    highs = s_data['High'].values
                    lows = s_data['Low'].values
                    
                    # Darvas Box Window Setup
                    c_closes = closes[-consolidation_window:]
                    c_highs = highs[-consolidation_window:]
                    c_lows = lows[-consolidation_window:]
                    
                    box_top = np.max(c_highs)
                    box_bottom = np.min(c_lows)
                    box_width_pct = ((box_top - box_bottom) / box_bottom) * 100
                    
                    # Filter 1: Box Width Range Constraints
                    if box_width_pct > max_box_width_pct:
                        continue
                        
                    # Filter 2: Scanning history for institutional breakout
                    breakout_found = False
                    search_end_idx = len(closes) - consolidation_window
                    search_start_idx = max(20, search_end_idx - lookback_days)
                    
                    for idx in range(search_start_idx, search_end_idx):
                        historical_avg_vol = np.mean(vols[idx-20:idx])
                        day_vol = vols[idx]
                        price_return = ((closes[idx] - closes[idx-1]) / closes[idx-1]) * 100
                        
                        # Institutional entry confirmation: 2x+ volume spurt with structural price jump
                        if historical_avg_vol > 0 and day_vol > (historical_avg_vol * vol_threshold) and price_return >= 3.0:
                            if np.min(c_closes) >= closes[idx] * 0.93:
                                breakout_found = True
                                scanned_results.append({
                                    "Ticker": ticker.replace(".NS", ""),
                                    "Current Price (₹)": round(closes[-1], 2),
                                    "Box Top (₹)": round(box_top, 2),
                                    "Box Bottom (₹)": round(box_bottom, 2),
                                    "Box Tightness (%)": f"{box_width_pct:.2f}%",
                                    "Breakout Date": s_data.index[idx].strftime('%d %b %Y'),
                                    "Breakout Return (%)": f"+{price_return:.2f}%",
                                    "Volume Multiplier": f"{day_vol / historical_avg_vol:.1f}x"
                                })
                                break
                except Exception:
                    continue
        except Exception:
            continue
            
    progress_bar.progress(1.0)
    status_text.text("Auto Sector Scan Completed Successfully! 🎉")
    return pd.DataFrame(scanned_results)

# --- 3. Sidebar Controls Layout ---
st.sidebar.header("⚙️ Strategy Adjustments")
vol_mult = st.sidebar.slider("Minimum Breakout Volume Multiplier (x)", 1.5, 5.0, 2.0, 0.5)
box_tightness = st.sidebar.slider("Maximum Box Tightness/Width (%)", 2.0, 15.0, 6.0, 0.5)
consol_days = st.sidebar.number_input("Consolidation Days in Box", min_value=3, max_value=15, value=5)

auto_universe = load_auto_universe()
st.sidebar.metric("Total Auto Stocks Loaded", len(auto_universe))

# --- 4. Execution Dashboard ---
if st.sidebar.button("Scan Entire Auto Sector 🚀", use_container_width=True):
    results_df = scan_auto_sector(
        auto_universe, 
        vol_threshold=vol_mult, 
        consolidation_window=consol_days, 
        max_box_width_pct=box_tightness
    )
    
    if not results_df.empty:
        st.subheader(f"🎯 Found {len(results_df)} Auto Setup Matches inside Consolidation Zones")
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Filhal is tight filter me koi auto stock fit nahi baith raha hai. Range thodi wide (e.g. Tightness 8% या 10%) karke dubara check karein.")
else:
    st.info("👈 Auto sector ke pure 100+ stocks ka X-ray nikalne ke liye side wale button ko dabaayein.")
