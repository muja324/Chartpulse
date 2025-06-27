import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import ta  # Technical Analysis indicators
import requests  # For Telegram alerts
from twelvedata import TDClient

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker (Twelve Data)")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Stock Symbols (comma-separated)", "RELIANCE.BSE, TCS.BSE").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Chart", True)

# --- Interval Selector ---
interval = st.selectbox("🕒 Select Interval", ["1day"], index=0)

# --- Auto Refresh ---
REFRESH_INTERVAL = 1  # in minutes
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="refresh")

# --- Telegram Function ---
def send_telegram_message(message):
    bot_token = "7934586337:AAGTBfUruRDbB1M4HKlBsf1C3FdZpdgJJIE"
    chat_id = "689374593"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            st.warning("⚠️ Telegram message failed.")
    except Exception as e:
        st.warning(f"❌ Telegram error: {e}")

# --- Helper Functions ---
def fetch_data(symbol):
    try:
        td = TDClient(apikey="8f62b13726f540a49e533f42cc6118e9")
        ts = td.time_series(symbol=symbol, interval=interval, outputsize=100)
        data = ts.as_pandas()

        data = data.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        })

        df = data.sort_index()
        df.index = pd.to_datetime(df.index)

        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()

        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def plot_chart(df, symbol):
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=[0.4, 0.15, 0.2, 0.25],
        subplot_titles=(f"{symbol} — Candlestick", "Volume", "RSI (14)", "MACD")
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        name="Price"
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", marker_color="#90caf9"
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        name="RSI", line=dict(color="#2962FF", width=2)
    ), row=3, col=1)

    fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD"],
        name="MACD", line=dict(color="blue", width=2)
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD_signal"],
        name="Signal", line=dict(color="orange", width=2)
    ), row=4, col=1)

    fig.update_layout(
        height=1000, showlegend=False, template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40), xaxis4_rangeslider_visible=False
    )

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

        if latest > breakout:
            alert_msg = f"🚀 {symbol} breakout alert!\nPrice: ₹{safe_fmt(latest)} > ₹{safe_fmt(breakout)}"
            send_telegram_message(alert_msg)

        elif latest < breakdown:
            alert_msg = f"⚠️ {symbol} breakdown alert!\nPrice: ₹{safe_fmt(latest)} < ₹{safe_fmt(breakdown)}"
            send_telegram_message(alert_msg)

        if show_chart:
            plot_chart(df, symbol)

    except Exception as e:
        st.error(f"⚠️ Processing error for {symbol}")
        st.exception(e)
