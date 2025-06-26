import streamlit as st

def apply_ui(df):
    st.subheader("📉 Data Preview")
    st.dataframe(df.tail(5))
