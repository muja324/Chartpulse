
import streamlit as st
from streamlit.components.v1 import html

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker (TradingView)")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbol_input = st.sidebar.text_input("Enter TradingView Symbol (e.g., NSE:RELIANCE)", "NSE:RELIANCE")
width = st.sidebar.slider("Chart Width", 600, 1400, 1000)
height = st.sidebar.slider("Chart Height", 400, 1000, 600)

# --- TradingView Widget Embed ---
tradingview_widget = f"""
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": {width},
    "height": {height},
    "symbol": "{symbol_input}",
    "interval": "D",
    "timezone": "Asia/Kolkata",
    "theme": "light",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "hide_top_toolbar": false,
    "save_image": false,
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
<!-- TradingView Widget END -->
"""

html(tradingview_widget, height=height + 50)
