
import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime
import io
from fpdf import FPDF

st.set_page_config(page_title="ChartPulse Pro", layout="wide")
st.title("📈 ChartPulse Pro — AI Trading Dashboard")

# Sidebar
st.sidebar.header("⚙️ Settings")
symbol = st.sidebar.text_input("Stock Symbol (e.g. RELIANCE)", "RELIANCE")
interval = st.sidebar.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
theme = st.sidebar.selectbox("Theme", ["light", "dark"], index=0)
fullscreen = st.sidebar.checkbox("Fullscreen Chart", True)
strategy_choice = st.sidebar.selectbox("Backtest Strategy", ["EMA Crossover", "RSI + MACD"], index=0)
show_analysis = st.sidebar.checkbox("Show AI Insight", True)

# Fetch Data
@st.cache_data
def fetch_data(symbol, interval):
    ticker = yf.Ticker(symbol + ".NS")
    if interval == "1d":
        return ticker.history(period="3mo", interval="1d")
    elif interval == "1wk":
        return ticker.history(period="6mo", interval="1wk")
    else:
        return ticker.history(period="1y", interval="1mo")

df = fetch_data(symbol, interval)
if df.empty:
    st.error("No data found.")
    st.stop()

# Indicators
df["EMA_20"] = EMAIndicator(close=df["Close"], window=20).ema_indicator()
df["EMA_50"] = EMAIndicator(close=df["Close"], window=50).ema_indicator()
df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
macd = MACD(close=df["Close"])
df["MACD"] = macd.macd()
df["MACD_signal"] = macd.macd_signal()

# AI Insight Generator
def generate_ai_insight(df):
    latest = df.iloc[-1]
    rsi = latest["RSI"]
    insight = []
    if latest["Close"] > df["EMA_20"].iloc[-1]:
        insight.append("📈 Stock is in a bullish trend.")
    else:
        insight.append("📉 Stock is in a bearish trend.")
    if rsi > 70:
        insight.append(f"⚠️ RSI is {rsi:.1f} (Overbought).")
    elif rsi < 30:
        insight.append(f"📉 RSI is {rsi:.1f} (Oversold).")
    else:
        insight.append(f"🔍 RSI is {rsi:.1f} (Neutral).")
    if latest["MACD"] > latest["MACD_signal"]:
        insight.append("✅ MACD shows bullish momentum.")
    else:
        insight.append("❌ MACD indicates bearish signal.")
    if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
        insight.append("📊 AI Signal: BUY")
    elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
        insight.append("📊 AI Signal: SELL")
    else:
        insight.append("📊 AI Signal: NEUTRAL")
    return "\n".join(insight)

# Backtesting strategies
def backtest(df, strategy):
    signals = []
    position = None
    for i in range(1, len(df)):
        if strategy == "EMA Crossover":
            if df["EMA_20"].iloc[i] > df["EMA_50"].iloc[i] and df["EMA_20"].iloc[i-1] <= df["EMA_50"].iloc[i-1]:
                signals.append(("BUY", df.index[i], df["Close"].iloc[i]))
            elif df["EMA_20"].iloc[i] < df["EMA_50"].iloc[i] and df["EMA_20"].iloc[i-1] >= df["EMA_50"].iloc[i-1]:
                signals.append(("SELL", df.index[i], df["Close"].iloc[i]))
        elif strategy == "RSI + MACD":
            if df["RSI"].iloc[i] < 30 and df["MACD"].iloc[i] > df["MACD_signal"].iloc[i]:
                signals.append(("BUY", df.index[i], df["Close"].iloc[i]))
            elif df["RSI"].iloc[i] > 70 and df["MACD"].iloc[i] < df["MACD_signal"].iloc[i]:
                signals.append(("SELL", df.index[i], df["Close"].iloc[i]))
    return signals

signals = backtest(df, strategy_choice)

# TradingView Chart Embed
tradingview_html = f"""
<div class="tradingview-widget-container">
  <div id="tradingview_{symbol}"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": {"800" if fullscreen else "600"},
    "symbol": "NSE:{symbol.upper()}",
    "interval": "{interval.replace('1d','D').replace('1wk','W').replace('1mo','M')}",
    "timezone": "Asia/Kolkata",
    "theme": "{theme}",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "withdateranges": true,
    "allow_symbol_change": true,
    "details": true,
    "studies": ["MACD@tv-basicstudies","RSI@tv-basicstudies"],
    "container_id": "tradingview_{symbol}"
  }});
  </script>
</div>
"""
st.components.v1.html(tradingview_html, height=850 if fullscreen else 650)

# Insights
if show_analysis:
    st.subheader("🧠 AI Insight")
    st.success(generate_ai_insight(df))

# Signal List
if signals:
    st.subheader("📍 Entry/Exit Points")
    for s in signals[-5:]:
        st.write(f"**{s[0]}** at ₹{s[2]:.2f} on {s[1].strftime('%Y-%m-%d')}")

# PDF Export
def export_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=1, align="L")
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

if st.button("📤 Export AI Insight as PDF"):
    pdf_data = export_to_pdf(generate_ai_insight(df))
    st.download_button("📥 Download PDF", data=pdf_data, file_name="chart_insight.pdf")

# Chat Assistant Panel (dummy interface)
with st.expander("💬 Ask ChartGPT"):
    query = st.text_input("Ask about the chart (e.g., 'Is it a good time to buy?')")
    if query:
        st.info("🤖 GPT: Based on the latest RSI and MACD, momentum is aligning with trend structure. Await confirmation or reversal near key support levels.")

