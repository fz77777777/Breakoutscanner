import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

# Page configurations
st.set_page_config(page_title="NSE Entire Market Scanner", layout="wide")

st.title("⚡ TechnoFunda LIVE Entire NSE Market Scanner")
st.write("Yeh engine LIVE NSE (2000+ Stocks) ki list nikal kar unpar Darvas Box aur Heavy Volume Breakout scan chalata hai.")

# --- 1. Dynamic Live NSE Universe Fetcher ---
@st.cache_data(ttl=86400) # Cache for 24 hours (Roz roz list download nahi karni padegi)
def fetch_entire_nse_universe():
    try:
        # Direct official/reliable source se NSE equity list uthana
        url = "https://raw.githubusercontent.com/anirban-m/nse-ticker-symbols/master/signals/symbols-active.txt"
        response = requests.get(url)
        if response.status_code == 200:
            symbols = response.text.splitlines()
            # Yahoo Finance format me badalna (e.g., RELIANCE -> RELIANCE.NS)
            nse_tickers = [f"{sym.strip()}.NS" for sym in symbols if sym.strip() and not sym.startswith('#')]
            return nse_tickers
    except Exception as e:
        st.error(f"NSE List fetch karne me dikkat aayi: {e}")
    
    # Fallback list agar internet issue ho
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "TATAMOTORS.NS", "SBIN.NS"]

# --- 2. Heavy-Duty Batch Processing Scanner ---
def scan_entire_market(ticker_list, vol_threshold=2.0, lookback_days=30, consolidation_window=7, max_box_width_pct=5.0):
    scanned_results = []
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    
    # Progress trackers
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 2000+ stocks ko 100-100 ke batches me todna taaki Yahoo Block na kare
    chunk_size = 100
    total_tickers = len(ticker_list)
    
    for i in range(0, total_tickers, chunk_size):
        batch = ticker_list[i:i + chunk_size]
        current_progress = min(1.0, i / total_tickers)
        progress_bar.progress(current_progress)
        status_text.text(f"Scanning Stocks {i} to {min(i + chunk_size, total_tickers)} of {total_tickers}...")
        
        try:
            # Batch Download
            data = yf.download(batch, start=start_date, progress=False, group_by='ticker')
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    # Single/Multi index handling safety
                    if ticker in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else [ticker]:
                        s_data = data[ticker].dropna() if isinstance(data.columns, pd.MultiIndex) else data.dropna()
                        
                        if len(s_data) < 40:
                            continue
                            
                        closes = s_data['Close'].values
                        vols = s_data['Volume'].values
                        highs = s_data['High'].values
                        lows = s_data['Low'].values
                        
                        # Last sessions data for Consolidation Box
                        c_closes = closes[-consolidation_window:]
                        c_highs = highs[-consolidation_window:]
                        c_lows = lows[-consolidation_window:]
                        
                        box_top = np.max(c_highs)
                        box_bottom = np.min(c_lows)
                        box_width_pct = ((box_top - box_bottom) / box_bottom) * 100
                        
                        # Filter 1: Box tightness check
                        if box_width_pct > max_box_width_pct:
                            continue
                            
                        # Filter 2: Lookback Window me Breakout dhoondna
                        breakout_found = False
                        search_end_idx = len(closes) - consolidation_window
                        search_start_idx = max(20, search_end_idx - lookback_days)
                        
                        for idx in range(search_start_idx, search_end_idx):
                            historical_avg_vol = np.mean(vols[idx-20:idx])
                            day_vol = vols[idx]
                            price_return = ((closes[idx] - closes[idx-1]) / closes[idx-1]) * 100
                            
                            if historical_avg_vol > 0 and day_vol > (historical_avg_vol * vol_threshold) and price_return >= 3.0:
                                if np.min(c_closes) >= closes[idx] * 0.95:
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
    status_text.text("Scan Completed Successfully! 🎉")
    return pd.DataFrame(scanned_results)

# --- 3. Sidebar Controls ---
st.sidebar.header("⚙️ Scanner Settings")
vol_mult = st.sidebar.slider("Minimum Breakout Volume Multiplier (x)", 1.5, 5.0, 2.5, 0.5)
box_tightness = st.sidebar.slider("Maximum Box Tightness/Width (%)", 2.0, 10.0, 5.0, 0.5)
consol_days = st.sidebar.number_input("Consolidation Days in Box", min_value=3, max_value=15, value=6)

# FIXED: Ab dono names bilkul match kar rahe hain
all_nse_tickers = fetch_entire_nse_universe()

st.sidebar.metric("Total Active NSE Symbols", len(all_nse_tickers))

if st.sidebar.button("Launch Full Market Scan 🚀", use_container_width=True):
    results_df = scan_entire_market(
        all_nse_tickers, 
        vol_threshold=vol_mult, 
        consolidation_window=consol_days, 
        max_box_width_pct=box_tightness
    )
    
    if not results_df.empty:
        st.subheader(f"🎯 Found {len(results_df)} Stocks blasting out on heavy volumes!")
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Pure NSE me filhal koi stock is strict box parameter me fit nahi baith raha hai. Sidebar se parameters thode loose karke check kariye.")
else:
    st.info("👈 Pure Indian Market (2000+ Stocks) ko scan karne ke liye sidebar me 'Launch Full Market Scan' dabao bhai!")
