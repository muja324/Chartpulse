import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker (TradingView Edition)")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Stock Symbols (comma-separated)", "RELIANCE, TCS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
interval = st.sidebar.selectbox("🕒 Interval", ["1", "5", "15", "30", "60", "D", "W", "M"], index=4)
st.sidebar.markdown("💡 Use `RELIANCE`, `TCS`, `INFY`, etc. for NSE stocks.")

# --- Auto Refresh ---
REFRESH_INTERVAL_MIN = 1
st_autorefresh(interval=REFRESH_INTERVAL_MIN * 60 * 1000, key="refresh")

# --- Telegram Function ---
def send_telegram_message(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            st.warning("⚠️ Telegram message failed.")
    except Exception as e:
        st.warning(f"❌ Telegram error: {e}")

# --- Main UI ---
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last Updated: `{now}`")

for symbol in symbols:
    st.markdown(f"---\n### 📊 {symbol}")
    
    tv_symbol = f"NSE:{symbol.upper()}"  # TradingView uses 'NSE:RELIANCE' format
    
    # Embed TradingView Chart
    st.components.v1.html(f"""
        <div class="tradingview-widget-container" style="margin-top: 20px;">
          <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_{symbol.lower()}&symbol={tv_symbol}&interval={interval}&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Asia/Kolkata&withdateranges=1&hidevolume=0&allow_symbol_change=1&hideideas=1"
            style="width:100%; height:550px;" frameborder="0" allowtransparency="true" scrolling="no">
          </iframe>
        </div>
    """, height=570)
