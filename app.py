import os
import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
from fpdf import FPDF
from io import BytesIO

# ——————————————————————————————————————————————————————————————
# 1) Custom Supertrend implementation (replaces ta.trend.Supertrend)
def calc_supertrend(df: pd.DataFrame, period: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
    hl2 = (df["High"] + df["Low"]) / 2
    # True Range
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift(1)).abs()
    tr3 = (df["Low"]  - df["Close"].shift(1)).abs()
    df["TR"]  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(period, min_periods=1).mean()

    # Basic bands
    upper_band = hl2 + multiplier * df["ATR"]
    lower_band = hl2 - multiplier * df["ATR"]

    # Supertrend logic
    supertrend = [None] * len(df)
    supertrend[period - 1] = upper_band.iloc[period - 1]

    for i in range(period, len(df)):
        prev_st   = supertrend[i - 1]
        curr_close = df["Close"].iloc[i]
        curr_upper = upper_band.iloc[i]
        curr_lower = lower_band.iloc[i]
        if curr_close > prev_st:
            supertrend[i] = curr_lower
        else:
            supertrend[i] = curr_upper

    df["Supertrend"] = supertrend
    # clean up
    df.drop(["TR", "ATR"], axis=1, inplace=True)
    return df

# ——————————————————————————————————————————————————————————————
# Utility: fetch price history
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
        st.error(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()

# ——————————————————————————————————————————————————————————————
# AI Insight generator
def generate_ai_insight(df: pd.DataFrame) -> str:
    if df.empty:
        return "No data available."
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    macd_o     = MACD(df["Close"])
    df["MACD"] = macd_o.macd()
    df["MACD_signal"] = macd_o.macd_signal()

    latest  = df.iloc[-1]
    trend   = "BULLISH" if latest["Close"] > df["Close"].rolling(20).mean().iloc[-1] else "BEARISH"
    rsi     = latest["RSI"]
    rsi_st  = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    macd_st = "above signal" if latest["MACD"] > latest["MACD_signal"] else "below signal"

    if rsi < 30 and latest["MACD"] > latest["MACD_signal"]:
        signal = "BUY"
    elif rsi > 70 and latest["MACD"] < latest["MACD_signal"]:
        signal = "SELL"
    else:
        signal = "NEUTRAL"

    return "\n".join([
        f"📈 Trend: **{trend}**",
        f"🔍 RSI: {rsi:.1f} — {rsi_st}",
        f"📊 MACD is {macd_st}",
        f"📡 AI Signal: **{signal}**"
    ])

# ——————————————————————————————————————————————————————————————
# Pattern detection (double bottom & head&shoulders)
def detect_patterns(df: pd.DataFrame) -> str:
    patterns = []
    try:
        lows  = df["Low"].rolling(5).min()
        if lows.iloc[-3] > lows.iloc[-2] < lows.iloc[-1]:
            patterns.append("Double Bottom")
        highs = df["High"]
        if highs.iloc[-5] < highs.iloc[-4] > highs.iloc[-3] and highs.iloc[-2] < highs.iloc[-4]:
            patterns.append("Head & Shoulders")
    except:
        pass
    return "No clear patterns found." if not patterns else ", ".join(patterns)

# ——————————————————————————————————————————————————————————————
# PDF export with Unicode font
def export_to_pdf(content: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
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

# ——————————————————————————————————————————————————————————————
# Streamlit UI
st.set_page_config(page_title="ChartPulse AI", layout="wide")
st.title("📈 ChartPulse — AI Chart Analyzer")
tabs = st.tabs(["📊 AI Analysis", "📉 TradingView", "🔁 Backtest", "🔔 Alerts"])

# --- Tab 0: AI Analysis ---
with tabs[0]:
    st.sidebar.header("⚙️ Settings")
    symbol   = st.sidebar.text_input("Stock Symbol (NSE)", "RELIANCE").upper()
    interval = st.sidebar.selectbox("Interval", ["1d","1wk","1mo"], index=0)

    df = get_data(symbol, interval)
    if df.empty:
        st.error("Failed to load data.")
    else:
        st.subheader(f"AI Insight — {symbol} ({interval})")
        ai_txt = generate_ai_insight(df)
        st.success(ai_txt)

        st.subheader("Detected Patterns")
        st.warning(detect_patterns(df))

        if st.button("📄 Export as PDF"):
            pdf_buf = export_to_pdf(ai_txt + "\n\n" + detect_patterns(df))
            st.download_button("⬇️ Download PDF",
                               pdf_buf,
                               file_name=f"{symbol}_analysis.pdf",
                               mime="application/pdf")

        with st.expander("Price Chart"):
            st.line_chart(df[["Close"]])

# --- Tab 1: TradingView ---
with tabs[1]:
    st.subheader("Live TradingView Chart")
    tv_sym    = st.text_input("TV Symbol", "NSE:RELIANCE")
    tv_int    = st.selectbox("Interval", ["D","W","M"], index=0)
    studies   = ["MA%4020","BB%4020","RSI%4014"]
    studies_q = "&".join(f"studies[]={s}" for s in studies)
    iframe = f"""
      <iframe src="https://s.tradingview.com/widgetembed/
        ?symbol={tv_sym}&interval={tv_int}
        &hidesidetoolbar=1&saveimage=1
        &theme=light&style=1&timezone=Asia/Kolkata
        &{studies_q}"
        width="100%" height="500" frameborder="0"
        allowtransparency="true" scrolling="no"></iframe>
    """
    st.components.v1.html(iframe, height=500)

# --- Tab 2: Backtest ---
with tabs[2]:
    st.header("Backtesting Panel")
    bt_sym    = st.text_input("Backtest Symbol", "RELIANCE")
    strategy  = st.selectbox("Strategy", ["RSI","MACD","Combined"])
    df_bt = get_data(bt_sym, "1d")
    if df_bt.empty:
        st.error("No backtest data.")
    else:
        df_bt.dropna(inplace=True)
        df_bt["RSI"] = RSIIndicator(df_bt["Close"], window=14).rsi()
        macd_obj     = MACD(df_bt["Close"])
        df_bt["MACD"]        = macd_obj.macd()
        df_bt["MACD_signal"] = macd_obj.macd_signal()
        trades = []
        for i in range(1, len(df_bt)):
            prev, curr = df_bt.iloc[i-1], df_bt.iloc[i]
            if strategy=="RSI" and prev["RSI"]<30<=curr["RSI"]:
                trades.append((curr["Date"],"BUY",curr["Close"]))
            if strategy=="RSI" and prev["RSI"]>70>=curr["RSI"]:
                trades.append((curr["Date"],"SELL",curr["Close"]))
            if strategy=="MACD" and prev["MACD"]<prev["MACD_signal"]<=curr["MACD"]:
                trades.append((curr["Date"],"BUY",curr["Close"]))
            if strategy=="MACD" and prev["MACD"]>prev["MACD_signal"]>=curr["MACD"]:
                trades.append((curr["Date"],"SELL",curr["Close"]))
            if strategy=="Combined":
                if curr["RSI"]<30 and curr["MACD"]>curr["MACD_signal"]:
                    trades.append((curr["Date"],"BUY",curr["Close"]))
                if curr["RSI"]>70 and curr["MACD"]<curr["MACD_signal"]:
                    trades.append((curr["Date"],"SELL",curr["Close"]))
        if trades:
            st.dataframe(pd.DataFrame(trades, columns=["Date","Signal","Price"]))
        else:
            st.info("No signals generated.")

# --- Tab 3: Alerts ---
with tabs[3]:
    st.header("🛎️ Watchlist Alerts")
    raw = st.text_input("Tickers (comma-sep)", "RELIANCE, TCS, INFY")
    watch = [t.strip().upper() for t in raw.split(",") if t.strip()]
    if not watch:
        st.info("Add tickers above.")
    else:
        buy_list, sell_list = [], []
        for tk in watch:
            df_w = get_data(tk, "1d")
            if df_w.empty or len(df_w)<20:
                continue
            # compute all indicators
            df_w = calc_supertrend(df_w, period=7, multiplier=3)
            rsi    = RSIIndicator(df_w["Close"], window=14).rsi().iloc[-1]
            macd_o = MACD(df_w["Close"])
            macd   = macd_o.macd().iloc[-1]
            sig    = macd_o.macd_signal().iloc[-1]
            bb     = BollingerBands(df_w["Close"], window=20, window_dev=2)
            bb_low = bb.bollinger_lband().iloc[-1]
            bb_hi  = bb.bollinger_hband().iloc[-1]
            adx    = ADXIndicator(df_w["High"], df_w["Low"], df_w["Close"], window=14).adx().iloc[-1]
            vwap   = VolumeWeightedAveragePrice(
                        df_w["High"], df_w["Low"],
                        df_w["Close"], df_w["Volume"], window=14
                     ).volume_weighted_average_price().iloc[-1]
            st_line = df_w["Supertrend"].iloc[-1]
            close   = df_w["Close"].iloc[-1]

            # Buy/Sell logic
            buy_cond  = rsi<30 and macd>sig and close<bb_low and close>vwap and close>st_line and adx>25
            sell_cond = rsi>70 and macd<sig and close>bb_hi and close<vwap and close<st_line and adx>25

            if buy_cond:
                buy_list.append(f"✅ {tk} BUY | RSI={rsi:.1f}, MACDdiff={macd-sig:.2f}, "
                                f"BB_low={bb_low:.2f}, VWAP={vwap:.2f}, ST={st_line:.2f}, ADX={adx:.1f}")
            if sell_cond:
                sell_list.append(f"⛔ {tk} SELL | RSI={rsi:.1f}, MACDdiff={macd-sig:.2f}, "
                                 f"BB_high={bb_hi:.2f}, VWAP={vwap:.2f}, ST={st_line:.2f}, ADX={adx:.1f}")

        if buy_list:
            st.subheader("Buy Alerts")
            for msg in buy_list:
                st.success(msg)
        else:
            st.info("No BUY alerts.")

        if sell_list:
            st.subheader("Sell Alerts")
            for msg in sell_list:
                st.error(msg)
        else:
            st.info("No SELL alerts.")
