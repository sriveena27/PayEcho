from __future__ import annotations

import streamlit as st
from ui.customers import render_customers_view


def render_dashboard() -> None:
    """Dashboard view delegating to render_customers_view."""
    render_customers_view()

