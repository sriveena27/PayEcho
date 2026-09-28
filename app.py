import streamlit as st
from ui.analytics import render_analytics
from ui.customers import render_customers_view

st.set_page_config(
    page_title="PayEcho — AI Revenue Recovery",
    page_icon="💰",
    layout="wide",
)

st.sidebar.title("💰 PayEcho")
st.sidebar.caption("AI Revenue Recovery Platform")

nav_page = st.sidebar.radio(
    "Navigation",
    ["Customer Accounts", "Analytics"],
    index=0 if st.session_state.get("nav_page", "Customer Accounts") == "Customer Accounts" else 1,
    key="nav_radio",
)

st.session_state["nav_page"] = nav_page

if nav_page == "Customer Accounts":
    render_customers_view()
elif nav_page == "Analytics":
    render_analytics()

