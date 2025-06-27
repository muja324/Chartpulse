import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD
from ta.momentum import RSIIndicator
from fpdf import FPDF
from io import BytesIO
import datetime

# --- Page Config ---
st.set_page_config(page_title="ChartPulse AI", layout="wide")
st.title("📈 ChartPulse — AI Chart Analyzer")

# --- Tabs ---
tabs = st.tabs(["📊 AI Analysis", "🔁 Backtest Panel"])

# --- Data Fetch Function ---
def get_data(symbol, interval):
    ticker = yf.Ticker(symbol + ".BS")
    if interval == "1d":
        df = ticker.history(period="3mo", interval="1d")
    elif interval == "1wk":
        df = ticker.history(period="6mo", interval="1wk")
    else:
        df = ticker.history(period="1y", interval="1mo")
    return df.reset_index()

# --- AI Insight ---
def generate_ai_insight(df):
    try:
        if df.empty:
            return "No data available."
        df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
        macd = MACD(close=df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()

        latest = df.iloc[-1]
        insight = []

        if df["Close"].iloc[-1] > df["Close"].rolling(20).mean().iloc[-1]:
            insight.append("📈 The stock is currently in a **bullish trend**.")
        else:
            insight.append("📉 The stock is in a **bearish trend**.")

        rsi = latest["RSI"]
        if rsi > 70:
            insight.append(f"⚠️ RSI is {rsi:.1f} — Overbought condition.")
        elif rsi < 30:
            insight.append(f"📉 RSI is {rsi:.1f} — Oversold condition.")
        else:
            insight.append(f"🔍 RSI is {rsi:.1f} — Neutral zone.")

        if latest["MACD"] > latest["MACD_signal"]:
            insight.append("✅ MACD is above signal — bullish momentum.")
        else:
            insight.append("❌ MACD is below signal — bearish signal.")

        if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
            insight.append("📊 **AI Signal: BUY**")
        elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
            insight.append("📊 **AI Signal: SELL**")
        else:
            insight.append("📊 **AI Signal: NEUTRAL**")

        return "\n".join(insight)
    except Exception as e:
        return f"Error analyzing data: {e}"

# --- Pattern Detection ---
def detect_patterns(df):
    patterns = []
    try:
        lows = df["Low"].rolling(window=5).min()
        latest_lows = lows[-10:]
        if (latest_lows.iloc[-3] > latest_lows.iloc[-2] < latest_lows.iloc[-1]):
            patterns.append("📉 Possible **Double Bottom** detected — may signal reversal.")

        if (
            df["High"].iloc[-5] < df["High"].iloc[-4] > df["High"].iloc[-3] and
            df["High"].iloc[-2] < df["High"].iloc[-4]
        ):
            patterns.append("🧠 Possible **Head & Shoulders** pattern.")
    except Exception as e:
        patterns.append(f"❌ Error in pattern detection: {e}")
    return "\n".join(patterns) if patterns else "No clear chart patterns found."

# --- PDF Export ---
def export_to_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    buffer = BytesIO()
    pdf.output(buffer, 'F')
    buffer.seek(0)
    return buffer

# --- AI Ask Mock ---
def ai_ask_reply(query):
    if "trend" in query.lower():
        return "The trend is determined by moving averages and momentum indicators."
    return "AI analysis is limited to pattern and indicator signals."

# --- TradingView Embed ---
def tradingview_widget(symbol):
    symbol_code = symbol.upper() + ":NSE"
    html_code = f"""
    <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_xxx&symbol={symbol_code}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Etc/UTC&withdateranges=1&hideideas=1&studies_overrides={{}}" 
            width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
    """
    st.components.v1.html(html_code, height=500)

# --- Tab 1: AI Analysis ---
with tabs[0]:
    st.sidebar.header("⚙️ Settings")
    symbol = st.sidebar.text_input("Stock Symbol (NSE only)", "RELIANCE")
    interval = st.sidebar.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    try:
        df = get_data(symbol, interval)
        st.subheader(f"📊 AI-Based Chart Insight — {symbol.upper()} ({interval})")
        ai_result = generate_ai_insight(df)
        st.success(ai_result)

        pattern_result = detect_patterns(df)
        st.subheader("🔎 Detected Chart Patterns")
        st.warning(pattern_result)

        if st.button("📄 Export AI Insight as PDF"):
            pdf = export_to_pdf(ai_result + "\n\n" + pattern_result)
            st.download_button("⬇️ Download PDF", data=pdf, file_name="chart_insight.pdf")

        with st.expander("📈 Show Price Chart"):
            st.line_chart(df[["Close"]])

        st.subheader("📺 Live Chart — TradingView")
        tradingview_widget(symbol)

        st.subheader("💬 AI Ask Chart Assistant")
        query = st.text_input("Ask anything about this chart")
        if query:
            response = ai_ask_reply(query)
            st.info(response)

    except Exception as e:
        st.error(f"Failed to fetch/analyze: {e}")

# --- Tab 2: Backtest Panel ---
with tabs[1]:
    st.header("🔁 Backtesting Panel")
    bt_symbol = st.text_input("Symbol for Backtest (NSE only)", "RELIANCE")
    bt_strategy = st.selectbox("Strategy", ["RSI Strategy", "MACD Strategy", "Combined RSI + MACD"])

    try:
        df_bt = get_data(bt_symbol, "1d")
        df_bt.dropna(inplace=True)
        df_bt["RSI"] = RSIIndicator(close=df_bt["Close"], window=14).rsi()
        macd = MACD(close=df_bt["Close"])
        df_bt["MACD"] = macd.macd()
        df_bt["MACD_signal"] = macd.macd_signal()

        signals = []
        for i in range(1, len(df_bt)):
            if bt_strategy == "RSI Strategy":
                if df_bt["RSI"].iloc[i-1] < 30 and df_bt["RSI"].iloc[i] > 30:
                    signals.append((df_bt["Date"].iloc[i], "BUY", df_bt["Close"].iloc[i]))
                elif df_bt["RSI"].iloc[i-1] > 70 and df_bt["RSI"].iloc[i] < 70:
                    signals.append((df_bt["Date"].iloc[i], "SELL", df_bt["Close"].iloc[i]))
            elif bt_strategy == "MACD Strategy":
                if df_bt["MACD"].iloc[i-1] < df_bt["MACD_signal"].iloc[i-1] and df_bt["MACD"].iloc[i] > df_bt["MACD_signal"].iloc[i]:
                    signals.append((df_bt["Date"].iloc[i], "BUY", df_bt["Close"].iloc[i]))
                elif df_bt["MACD"].iloc[i-1] > df_bt["MACD_signal"].iloc[i-1] and df_bt["MACD"].iloc[i] < df_bt["MACD_signal"].iloc[i]:
                    signals.append((df_bt["Date"].iloc[i], "SELL", df_bt["Close"].iloc[i]))
            else:
                if df_bt["RSI"].iloc[i] < 30 and df_bt["MACD"].iloc[i] > df_bt["MACD_signal"].iloc[i]:
                    signals.append((df_bt["Date"].iloc[i], "BUY", df_bt["Close"].iloc[i]))
                elif df_bt["RSI"].iloc[i] > 70 and df_bt["MACD"].iloc[i] < df_bt["MACD_signal"].iloc[i]:
                    signals.append((df_bt["Date"].iloc[i], "SELL", df_bt["Close"].iloc[i]))

        st.subheader("📍 Backtest Results")
        if signals:
            signal_df = pd.DataFrame(signals, columns=["Date", "Signal", "Price"])
            st.dataframe(signal_df)
        else:
            st.info("No signals generated for selected strategy.")

    except Exception as e:
        st.error(f"Backtest failed: {e}")
