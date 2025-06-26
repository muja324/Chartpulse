# chartpulse/app.py — Using Alpha Vantage instead of yfinance

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from alpha_vantage.timeseries import TimeSeries
import ta  # Technical Analysis indicators

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker (Alpha Vantage)")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Stock Symbols (comma-separated)", "RELIANCE.BSE, TCS.BSE").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Chart", True)

# --- Interval Selector ---
interval = st.selectbox("🕒 Select Interval", ["1d"], index=0)

# --- Auto Refresh ---
REFRESH_INTERVAL = 1  # in minutes
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="refresh")

# --- Helper Functions ---
def fetch_data(symbol):
    try:
        api_key = st.secrets["alpha_vantage"]["XLXA2BC7S1DP5413"]
        ts = TimeSeries(key=api_key, output_format='pandas')
        data, meta = ts.get_daily(symbol=symbol, outputsize='compact')

        df = data.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume"
        })
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        # Add technical indicators
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()

        return df

    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} — Daily Chart", height=400)
    st.plotly_chart(fig, use_container_width=True)

def safe_fmt(val, digits=2):
    try:
        return f"{val:.{digits}f}"
    except:
        return "N/A"

# --- Main Loop ---
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last Updated: `{now}`")

for symbol in symbols:
    st.markdown(f"---\n### 🔍 {symbol}")
    df = fetch_data(symbol)

    if df.empty:
        st.error(f"⚠️ No data for {symbol}")
        continue

    try:
        latest = float(df["Close"].iloc[-1])
        breakout = float(df["High"].tail(20).max())
        breakdown = float(df["Low"].tail(20).min())

        rsi = float(df["RSI"].dropna().iloc[-1]) if not df["RSI"].dropna().empty else None
        macd = float(df["MACD"].dropna().iloc[-1]) if not df["MACD"].dropna().empty else None

        st.markdown(
            f"**Price:** ₹{safe_fmt(latest)} | "
            f"📈 BO: ₹{safe_fmt(breakout)} | "
            f"📉 BD: ₹{safe_fmt(breakdown)} | "
            f"RSI: {safe_fmt(rsi, 1)} | "
            f"MACD: {safe_fmt(macd)}"
        )

        if show_chart:
            plot_chart(df, symbol)

    except Exception as e:
        st.error(f"⚠️ Processing error for {symbol}")
        st.exception(e)
