import streamlit as st
import time

def show_loader(msg="Loading..."):
    with st.spinner(msg):
        time.sleep(1)
