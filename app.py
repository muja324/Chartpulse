import os
import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD, ADXIndicator, Supertrend
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
from fpdf import FPDF
from io import BytesIO

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse AI", layout="wide")
st.title("📈 ChartPulse — AI Chart Analyzer")

# --- Tabs ---
tabs = st.tabs([
    "📊 AI Analysis",
    "📉 TradingView Chart",
    "🔁 Backtest Panel",
    "🔔 Alerts"
])

# --- Utility: Fetch historical data ---
def get_data(symbol: str, interval: str) -> pd.DataFrame:
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
        st.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# --- AI Insight Generator ---
def generate_ai_insight(df: pd.DataFrame) -> str:
    if df.empty:
        return "No data available."
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    macd_obj = MACD(df["Close"])
    df["MACD"] = macd_obj.macd()
    df["MACD_signal"] = macd_obj.macd_signal()

    latest = df.iloc[-1]
    trend = "bullish" if latest["Close"] > df["Close"].rolling(20).mean().iloc[-1] else "bearish"
    rsi = latest["RSI"]
    rsi_state = ("Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
    macd_state = ("above signal" if latest["MACD"] > latest["MACD_signal"] else "below signal")

    if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
        ai_sig = "BUY"
    elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
        ai_sig = "SELL"
    else:
        ai_sig = "NEUTRAL"

    return "\n".join([
        f"📈 Trend: **{trend.upper()}**",
        f"🔍 RSI: {rsi:.1f} — {rsi_state}",
        f"📊 MACD is {macd_state}",
        f"📡 AI Signal: **{ai_sig}**"
    ])

# --- Pattern Detection ---
def detect_patterns(df: pd.DataFrame) -> str:
    patterns = []
    try:
        lows = df["Low"].rolling(5).min()
        if lows.iloc[-3] > lows.iloc[-2] < lows.iloc[-1]:
            patterns.append("Double Bottom")
        highs = df["High"]
        if highs.iloc[-5] < highs.iloc[-4] > highs.iloc[-3] and highs.iloc[-2] < highs.iloc[-4]:
            patterns.append("Head & Shoulders")
    except:
        pass
    return "No clear patterns found." if not patterns else ", ".join(patterns)

# --- PDF Export (Unicode‐safe) ---
def export_to_pdf(content: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    # register DejaVu Sans for full Unicode
    font_path = (
        "./DejaVuSans.ttf"
        if os.path.exists("./DejaVuSans.ttf")
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)
    for line in content.splitlines():
        pdf.multi_cell(0, 8, line)
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    return buf

# --- TAB 0: AI Analysis ---
with tabs[0]:
    st.sidebar.header("⚙️ Settings")
    symbol = st.sidebar.text_input("Stock Symbol (NSE only)", "RELIANCE").upper()
    interval = st.sidebar.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    df = get_data(symbol, interval)
    if df.empty:
        st.error("Failed to load data.")
    else:
        st.subheader(f"📊 AI-Based Chart Insight — {symbol} ({interval})")
        ai_text = generate_ai_insight(df)
        st.success(ai_text)

        st.subheader("🔎 Detected Chart Patterns")
        patterns = detect_patterns(df)
        st.warning(patterns)

        if st.button("📄 Export Insight as PDF"):
            pdf_buf = export_to_pdf(ai_text + "\n\n" + patterns)
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_buf,
                file_name=f"{symbol}_analysis.pdf",
                mime="application/pdf"
            )

        with st.expander("📈 Show Price Chart"):
            st.line_chart(df[["Close"]])

# --- TAB 1: TradingView Chart ---
with tabs[1]:
    st.subheader("📉 Live TradingView Chart")
    tv_symbol = st.text_input("TradingView Symbol", "NSE:RELIANCE")
    interval_tv = st.selectbox("Interval", ["D", "W", "M"], index=0)

    # add multiple built-in indicators
    studies = ["MA%4020", "BB%4020", "RSI%4014"]
    studies_q = "&".join(f"studies[]={s}" for s in studies)
    iframe = f'''
    <iframe
      src="https://s.tradingview.com/widgetembed/?symbol={tv_symbol}
        &interval={interval_tv}
        &hidesidetoolbar=1
        &toolbarbg=f1f3f6
        &saveimage=1
        &theme=light
        &style=1
        &timezone=Asia/Kolkata
        &{studies_q}"
      width="100%" height="500"
      frameborder="0"
      allowtransparency="true"
      scrolling="no">
    </iframe>
    '''
    st.components.v1.html(iframe, height=500)

# --- TAB 2: Backtest Panel ---
with tabs[2]:
    st.header("🔁 Backtesting Panel")
    bt_symbol = st.text_input("Symbol for Backtest (NSE only)", "RELIANCE")
    strategy = st.selectbox("Strategy", ["RSI Strategy", "MACD Strategy", "Combined RSI + MACD"])

    df_bt = get_data(bt_symbol, "1d")
    if df_bt.empty:
        st.error("Failed to fetch backtest data.")
    else:
        df_bt.dropna(inplace=True)
        df_bt["RSI"] = RSIIndicator(df_bt["Close"], window=14).rsi()
        macd_o = MACD(df_bt["Close"])
        df_bt["MACD"] = macd_o.macd()
        df_bt["MACD_signal"] = macd_o.macd_signal()

        trades = []
        for i in range(1, len(df_bt)):
            prev, curr = df_bt.iloc[i - 1], df_bt.iloc[i]
            if strategy == "RSI Strategy":
                if prev["RSI"] < 30 <= curr["RSI"]:
                    trades.append((curr["Date"], "BUY", curr["Close"]))
                if prev["RSI"] > 70 >= curr["RSI"]:
                    trades.append((curr["Date"], "SELL", curr["Close"]))
            elif strategy == "MACD Strategy":
                if prev["MACD"] < prev["MACD_signal"] <= curr["MACD"]:
                    trades.append((curr["Date"], "BUY", curr["Close"]))
                if prev["MACD"] > prev["MACD_signal"] >= curr["MACD"]:
                    trades.append((curr["Date"], "SELL", curr["Close"]))
            else:
                if curr["RSI"] < 30 and curr["MACD"] > curr["MACD_signal"]:
                    trades.append((curr["Date"], "BUY", curr["Close"]))
                if curr["RSI"] > 70 and curr["MACD"] < curr["MACD_signal"]:
                    trades.append((curr["Date"], "SELL", curr["Close"]))

        if trades:
            df_trades = pd.DataFrame(trades, columns=["Date", "Signal", "Price"])
            st.dataframe(df_trades)
        else:
            st.info("No signals for this strategy.")

# --- TAB 3: Alerts ---
with tabs[3]:
    st.header("🔔 Watchlist Alerts")
    watch_raw = st.text_input("Enter NSE tickers (comma-separated)", "RELIANCE, TCS, INFY")
    watchlist = [t.strip().upper() for t in watch_raw.split(",") if t.strip()]

    if not watchlist:
        st.info("Add some tickers to your watchlist above.")
    else:
        buy_alerts, sell_alerts = [], []
        for tk in watchlist:
            df_w = get_data(tk, "1d")
            if df_w.empty or len(df_w) < 20:
                continue
            latest = df_w.iloc[-1]

            # Calculate indicators
            rsi = RSIIndicator(df_w["Close"], window=14).rsi().iloc[-1]
            macd_o = MACD(df_w["Close"])
            macd, sig = macd_o.macd().iloc[-1], macd_o.macd_signal().iloc[-1]
            bb = BollingerBands(df_w["Close"], window=20, window_dev=2)
            bb_low, bb_high = bb.bollinger_lband().iloc[-1], bb.bollinger_hband().iloc[-1]
            adx = ADXIndicator(df_w["High"], df_w["Low"], df_w["Close"], window=14).adx().iloc[-1]
            vwap = VolumeWeightedAveragePrice(
                df_w["High"], df_w["Low"], df_w["Close"], df_w["Volume"], window=14
            ).volume_weighted_average_price().iloc[-1]
            st_obj = Supertrend(df_w["High"], df_w["Low"], df_w["Close"], window=7, multiplier=3)
            supertrend = st_obj.supertrend().iloc[-1]

            # Define Buy/Sell
            cond_buy = (
                rsi < 30 and
                macd > sig and
                latest["Close"] < bb_low and
                latest["Close"] > vwap and
                latest["Close"] > supertrend and
                adx > 25
            )
            cond_sell = (
                rsi > 70 and
                macd < sig and
                latest["Close"] > bb_high and
                latest["Close"] < vwap and
                latest["Close"] < supertrend and
                adx > 25
            )

            if cond_buy:
                buy_alerts.append(
                    f"✅ {tk} BUY | RSI={rsi:.1f}, MACD diff={macd-sig:.2f}, "
                    f"BB_low={bb_low:.2f}, VWAP={vwap:.2f}, ST={supertrend:.2f}, ADX={adx:.1f}"
                )
            if cond_sell:
                sell_alerts.append(
                    f"⛔ {tk} SELL | RSI={rsi:.1f}, MACD diff={macd-sig:.2f}, "
                    f"BB_high={bb_high:.2f}, VWAP={vwap:.2f}, ST={supertrend:.2f}, ADX={adx:.1f}"
                )

        if buy_alerts:
            st.subheader("Buy Alerts")
            for msg in buy_alerts:
                st.success(msg)
        else:
            st.info("No BUY alerts at the moment.")

        if sell_alerts:
            st.subheader("Sell Alerts")
            for msg in sell_alerts:
                st.error(msg)
        else:
            st.info("No SELL alerts at the moment.")
