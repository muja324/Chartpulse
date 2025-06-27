import streamlit as st
import yfinance as yf
from ta.trend import MACD
from ta.momentum import RSIIndicator
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="ChartPulse AI Pro", layout="wide")
st.title("📈 ChartPulse — AI + TradingView")

# --- Sidebar ---
st.sidebar.header("⚙️ Settings")
symbol = st.sidebar.text_input("Enter Symbol (e.g. NSE:RELIANCE, NASDAQ:AAPL)", "NSE:RELIANCE")
interval = st.sidebar.selectbox("Chart Interval", ["1", "5", "15", "30", "60", "D", "W", "M"], index=6)
theme = st.sidebar.selectbox("Theme", ["light", "dark"], index=1)

# --- Fetch NSE data using yfinance for AI analysis ---
def fetch_data(symbol):
    if ":" in symbol:
        code = symbol.split(":")[1]
    else:
        code = symbol
    ticker = yf.Ticker(code + ".NS")
    df = ticker.history(period="6mo", interval="1d")
    return df

# --- AI Chart Insight ---
def generate_ai_insight(df):
    try:
        df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
        macd = MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()

        latest = df.iloc[-1]
        insight = []

        # Trend
        if latest["Close"] > df["Close"].rolling(20).mean().iloc[-1]:
            insight.append("📈 The stock is in a **bullish trend**.")
        else:
            insight.append("📉 The stock is in a **bearish trend**.")

        # RSI
        rsi = latest["RSI"]
        if rsi > 70:
            insight.append(f"⚠️ RSI is {rsi:.1f} — Overbought.")
        elif rsi < 30:
            insight.append(f"📉 RSI is {rsi:.1f} — Oversold.")
        else:
            insight.append(f"🔍 RSI is {rsi:.1f} — Neutral.")

        # MACD
        if latest["MACD"] > latest["MACD_signal"]:
            insight.append("✅ MACD > Signal — bullish.")
        else:
            insight.append("❌ MACD < Signal — bearish.")

        # Final Signal
        if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
            insight.append("📊 **AI Signal: BUY**")
        elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
            insight.append("📊 **AI Signal: SELL**")
        else:
            insight.append("📊 **AI Signal: NEUTRAL**")

        return "\n".join(insight)
    except Exception as e:
        return f"AI Error: {e}"

# --- Display TradingView Chart ---
st.subheader(f"📊 Chart — {symbol}")
tradingview_html = f"""
<div class="tradingview-widget-container">
  <div id="tradingview_{symbol.replace(':', '')}"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": "650",
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Asia/Kolkata",
    "theme": "{theme}",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "details": true,
    "studies": ["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
    "container_id": "tradingview_{symbol.replace(':', '')}"
  }});
  </script>
</div>
"""
st.components.v1.html(tradingview_html, height=700)

# --- AI Insight ---
st.markdown("## 🤖 AI Insight")
try:
    df = fetch_data(symbol)
    ai_result = generate_ai_insight(df)
    st.success(ai_result)
except Exception as e:
    st.error(f"Error fetching data: {e}")

# --- Tips ---
with st.expander("🧠 Tips"):
    st.markdown("""
    - Use `NSE:RELIANCE`, `NASDAQ:GOOG`, or `CRYPTO:BTCUSD`
    - Chart supports drawing tools, studies, zoom, etc.
    - AI insights are based on RSI + MACD + trend logic.
    - Switch theme from the sidebar.
    """)
