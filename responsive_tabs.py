import streamlit as st

def show_navigation():
    return st.radio("🔍 View", ["📈 Live Feed", "📊 Summary", "📄 Logs"], horizontal=True)
