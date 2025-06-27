import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ChartPulse TV", layout="wide")
st.title("📈 ChartPulse — TradingView Chart")

st.sidebar.header("⚙️ Settings")
default_symbol = "BSE:RELIANCE"
symbol = st.sidebar.text_input("Enter TradingView Symbol (e.g., NSE:TCS, BSE:RELIANCE)", default_symbol)

tradingview_html = f"""
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="tradingview_{symbol.replace(':','_')}"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": 700,
    "symbol": "{symbol}",
    "interval": "D",
    "timezone": "Asia/Kolkata",
    "theme": "light",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "save_image": false,
    "container_id": "tradingview_{symbol.replace(':','_')}"
  }});
  </script>
</div>
<!-- TradingView Widget END -->
"""

components.html(tradingview_html, height=750)
