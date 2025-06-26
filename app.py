# chartpulse/app.py — Using Twelve Data API

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import ta  # Technical Analysis indicators
import telegram

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker (Twelve Data)")

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

# --- Telegram Alert Setup (optional) ---
use_telegram = st.sidebar.checkbox("📲 Enable Telegram Alerts")
telegram_bot_token = st.secrets.get("telegram", {}).get("bot_token", "")
telegram_chat_id = st.secrets.get("telegram", {}).get("chat_id", "")

def send_telegram(message):
    if use_telegram and telegram_bot_token and telegram_chat_id:
        try:
            bot = telegram.Bot(token=telegram_bot_token)
            bot.send_message(chat_id=telegram_chat_id, text=message)
        except Exception as e:
            st.warning(f"Telegram Error: {e}")

# --- Helper Function to Fetch Data ---
def fetch_data(symbol):
    try:
        api_key = st.secrets["twelvedata"]["api_key"]
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=30&apikey={api_key}"
        response = requests.get(url).json()

        if "values" not in response:
            raise ValueError(response.get("message", "Unknown error"))

        data = pd.DataFrame(response["values"])
        data.rename(columns={
            "datetime": "Date", "open": "Open", "high": "High",
            "low": "Low", "close": "Close", "volume": "Volume"
        }, inplace=True)

        data["Date"] = pd.to_datetime(data["Date"])
        data.set_index("Date", inplace=True)
        data = data.astype(float)
        data.sort_index(inplace=True)

        # Add indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        macd = ta.trend.MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()

        return data

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

        # --- Signal Alerts via Telegram ---
        if use_telegram:
            if latest > breakout:
                send_telegram(f"🚨 {symbol} BREAKOUT! Current Price: ₹{safe_fmt(latest)} > ₹{safe_fmt(breakout)}")
            elif latest < breakdown:
                send_telegram(f"⚠️ {symbol} BREAKDOWN! Current Price: ₹{safe_fmt(latest)} < ₹{safe_fmt(breakdown)}")

    except Exception as e:
        st.error(f"⚠️ Processing error for {symbol}")
        st.exception(e)
