import os
import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD
from ta.momentum import RSIIndicator
from fpdf import FPDF
from io import BytesIO

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse AI", layout="wide")
st.title("📈 ChartPulse — AI Chart Analyzer")

# --- Tabs ---
tabs = st.tabs(["📊 AI Analysis", "📉 TradingView Chart", "🔁 Backtest Panel"])

# --- Function to Get Data ---
def get_data(symbol, interval):
    try:
        ticker = yf.Ticker(symbol + ".NS")
        if interval == "1d":
            df = ticker.history(period="3mo", interval="1d")
        elif interval == "1wk":
            df = ticker.history(period="6mo", interval="1wk")
        else:
            df = ticker.history(period="1y", interval="1mo")
        return df.reset_index()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- AI Insight Generator ---
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

        # Trend
        if latest["Close"] > df["Close"].rolling(20).mean().iloc[-1]:
            insight.append("📈 The stock is currently in a **bullish trend**.")
        else:
            insight.append("📉 The stock is in a **bearish trend**.")

        # RSI
        rsi = latest["RSI"]
        if rsi > 70:
            insight.append(f"⚠️ RSI is {rsi:.1f} — Overbought condition.")
        elif rsi < 30:
            insight.append(f"📉 RSI is {rsi:.1f} — Oversold condition.")
        else:
            insight.append(f"🔍 RSI is {rsi:.1f} — Neutral zone.")

        # MACD
        if latest["MACD"] > latest["MACD_signal"]:
            insight.append("✅ MACD is above signal — bullish momentum.")
        else:
            insight.append("❌ MACD is below signal — bearish signal.")

        # Combined AI Signal
        if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
            insight.append("📊 **AI Signal: BUY**")
        elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
            insight.append("📊 **AI Signal: SELL**")
        else:
            insight.append("📊 **AI Signal: NEUTRAL**")

        return "\n".join(insight)
    except Exception as e:
        return f"Error analyzing data: {e}"

# --- Chart Pattern Detection ---
def detect_patterns(df):
    patterns = []
    try:
        lows = df["Low"].rolling(window=5).min()
        latest_lows = lows[-10:]
        # Double bottom?
        if (latest_lows.iloc[-3] > latest_lows.iloc[-2] < latest_lows.iloc[-1]):
            patterns.append("📉 Possible **Double Bottom** detected — may signal reversal.")
        # Head & Shoulders?
        if (
            df["High"].iloc[-5] < df["High"].iloc[-4] > df["High"].iloc[-3]
            and df["High"].iloc[-2] < df["High"].iloc[-4]
        ):
            patterns.append("🧠 Possible **Head & Shoulders** pattern.")
    except Exception as e:
        patterns.append(f"❌ Error in pattern detection: {e}")
    return "\n".join(patterns) if patterns else "No clear chart patterns found."

# --- PDF Export (Unicode-safe) ---
def export_to_pdf(content: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()

    # Register a Unicode TTF font (DejaVu Sans)
    # Ensure you have DejaVuSans.ttf in your project or system fonts
    font_path = (
        "./DejaVuSans.ttf"
        if os.path.exists("./DejaVuSans.ttf")
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    # Add each line
    for line in content.splitlines():
        pdf.multi_cell(0, 8, line)

    # Output to bytes and wrap in BytesIO
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

# --- Tab 1: AI Analysis ---
with tabs[0]:
    st.sidebar.header("⚙️ Settings")
    symbol = st.sidebar.text_input("Stock Symbol (NSE only)", "RELIANCE").upper()
    interval = st.sidebar.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    df = get_data(symbol, interval)
    if not df.empty:
        st.subheader(f"📊 AI-Based Chart Insight — {symbol} ({interval})")
        ai_result = generate_ai_insight(df)
        st.success(ai_result)

        st.subheader("🔎 Detected Chart Patterns")
        pattern_result = detect_patterns(df)
        st.warning(pattern_result)

        if st.button("📄 Export AI Insight as PDF"):
            pdf_buffer = export_to_pdf(ai_result + "\n\n" + pattern_result)
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_buffer,
                file_name=f"{symbol}_analysis.pdf",
                mime="application/pdf"
            )

        with st.expander("📈 Show Price Chart"):
            st.line_chart(df[["Close"]])
    else:
        st.error("Failed to load data.")

# --- Tab 2: TradingView Chart ---
with tabs[1]:
    st.subheader("📺 Live TradingView Chart")
    trading_symbol = st.text_input(
        "Enter TradingView Symbol (e.g., `NSE:RELIANCE`)",
        "NSE:RELIANCE"
    )
    html = f"""
    <iframe
      src="https://s.tradingview.com/widgetembed/?frameElementId=tv_{trading_symbol.replace(':','')}"
      &symbol={trading_symbol}&interval=D&hidesidetoolbar=1
      &symboledit=1&saveimage=1&toolbarbg=f1f3f6
      &studies=[]&theme=light&style=1&timezone=Asia/Kolkata
      &withdateranges=1&hideideas=1&locale=en"
      width="100%" height="500" frameborder="0"
      allowtransparency="true" scrolling="no">
    </iframe>
    """
    st.components.v1.html(html, height=500)

# --- Tab 3: Backtest Panel ---
with tabs[2]:
    st.header("🔁 Backtesting Panel")
    bt_symbol = st.text_input("Symbol for Backtest (NSE only)", "RELIANCE")
    bt_strategy = st.selectbox(
        "Strategy",
        ["RSI Strategy", "MACD Strategy", "Combined RSI + MACD"]
    )

    df_bt = get_data(bt_symbol, "1d")
    if not df_bt.empty:
        df_bt.dropna(inplace=True)
        df_bt["RSI"] = RSIIndicator(close=df_bt["Close"], window=14).rsi()
        macd = MACD(close=df_bt["Close"])
        df_bt["MACD"] = macd.macd()
        df_bt["MACD_signal"] = macd.macd_signal()

        signals = []
        for i in range(1, len(df_bt)):
            prev = df_bt.iloc[i - 1]
            curr = df_bt.iloc[i]

            if bt_strategy == "RSI Strategy":
                if prev["RSI"] < 30 and curr["RSI"] > 30:
                    signals.append((curr["Date"], "BUY", curr["Close"]))
                elif prev["RSI"] > 70 and curr["RSI"] < 70:
                    signals.append((curr["Date"], "SELL", curr["Close"]))

            elif bt_strategy == "MACD Strategy":
                if prev["MACD"] < prev["MACD_signal"] and curr["MACD"] > curr["MACD_signal"]:
                    signals.append((curr["Date"], "BUY", curr["Close"]))
                elif prev["MACD"] > prev["MACD_signal"] and curr["MACD"] < curr["MACD_signal"]:
                    signals.append((curr["Date"], "SELL", curr["Close"]))

            else:  # Combined RSI + MACD
                if curr["RSI"] < 30 and curr["MACD"] > curr["MACD_signal"]:
                    signals.append((curr["Date"], "BUY", curr["Close"]))
                elif curr["RSI"] > 70 and curr["MACD"] < curr["MACD_signal"]:
                    signals.append((curr["Date"], "SELL", curr["Close"]))

        st.subheader("📍 Backtest Results")
        if signals:
            signal_df = pd.DataFrame(signals, columns=["Date", "Signal", "Price"])
            st.dataframe(signal_df)
        else:
            st.info("No signals generated for selected strategy.")
    else:
        st.error("Failed to load backtest data.")
