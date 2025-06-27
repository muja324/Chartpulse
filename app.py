import streamlit as st import requests import pandas as pd from datetime import datetime from ta.trend import MACD from ta.momentum import RSIIndicator from fpdf import FPDF from io import BytesIO import yfinance as yf

--- Page Config ---

st.set_page_config(page_title="ChartPulse AI", layout="wide") st.title("📈 ChartPulse — AI Chart Analyzer")

--- Sidebar Settings ---

st.sidebar.header("⚙️ Settings") default_symbol = "RELIANCE" symbol = st.sidebar.text_input("Stock Symbol (NSE only)", default_symbol) interval = st.sidebar.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

--- Fetch from Yahoo Finance ---

def fetch_yahoo_data(symbol, interval): ticker = yf.Ticker(symbol + ".NS") if interval == "1d": df = ticker.history(period="3mo", interval="1d") elif interval == "1wk": df = ticker.history(period="6mo", interval="1wk") else: df = ticker.history(period="1y", interval="1mo") return df.reset_index()

--- AI Insight Generator ---

def generate_ai_insight(df): try: if df.empty: return "No data available."

df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
    macd = MACD(close=df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()

    latest = df.iloc[-1]

    insight = []

    # Trend
    if df["Close"].iloc[-1] > df["Close"].rolling(20).mean().iloc[-1]:
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

    # Summary Signal
    if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
        insight.append("📊 **AI Signal: BUY**")
    elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
        insight.append("📊 **AI Signal: SELL**")
    else:
        insight.append("📊 **AI Signal: NEUTRAL**")

    return "\n".join(insight)

except Exception as e:
    return f"Error analyzing data: {e}"

--- Pattern Detection ---

def detect_patterns(df): patterns = [] try: lows = df["Low"].rolling(window=5).min() latest_lows = lows[-10:] if (latest_lows.iloc[-3] > latest_lows.iloc[-2] < latest_lows.iloc[-1]): patterns.append("📉 Possible Double Bottom detected — may signal reversal.")

if (
        df["High"].iloc[-5] < df["High"].iloc[-4] > df["High"].iloc[-3] and
        df["High"].iloc[-2] < df["High"].iloc[-4]
    ):
        patterns.append("🧠 Possible **Head & Shoulders** pattern.")
except Exception as e:
    patterns.append(f"❌ Error in pattern detection: {e}")
return "\n".join(patterns) if patterns else "No clear chart patterns found."

def explain_pattern(pattern_text): if "Double Bottom" in pattern_text: return "💬 This pattern often indicates a bullish reversal. Price forms two low points at a similar level." elif "Head & Shoulders" in pattern_text: return "💬 This is usually a bearish reversal signal. Look for a peak between two smaller peaks." return ""

--- PDF Export ---

def export_to_pdf(content): pdf = FPDF() pdf.add_page() pdf.set_font("Arial", size=12) for line in content.split('\n'): pdf.multi_cell(0, 10, line) buffer = BytesIO() pdf.output(buffer, 'F') buffer.seek(0) return buffer

--- Main ---

try: df = fetch_yahoo_data(symbol, interval)

st.subheader(f"📊 AI-Based Chart Insight — {symbol.upper()} ({interval})")
analysis = generate_ai_insight(df)
st.success(analysis)

pattern_insight = detect_patterns(df)
st.subheader("🔎 Detected Chart Patterns")
st.warning(pattern_insight)
st.markdown(explain_pattern(pattern_insight))

if st.button("📄 Export AI Insight as PDF"):
    pdf_data = export_to_pdf(analysis + "\n\n" + pattern_insight)
    st.download_button("⬇️ Download PDF", data=pdf_data, file_name="chart_insight.pdf")

except Exception as e: st.error(f"Failed to fetch/analyze: {e}")

--- Optional: Show Chart ---

with st.expander("🔍 Show Chart"): st.line_chart(df[["Close"]])

