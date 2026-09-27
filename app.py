import streamlit as st
from ui.dashboard import render_dashboard

st.set_page_config(
    page_title="PayEcho — AI Revenue Recovery",
    page_icon="💰",
    layout="wide",
)

render_dashboard()
