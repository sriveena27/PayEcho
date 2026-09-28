from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.mock_data import get_invoice_summary, get_promises, list_customers


def render_analytics() -> None:
    """Render the Analytics Dashboard with 3 Plotly charts."""
    st.title("📊 PayEcho Recovery Analytics")
    st.caption("Insights on account aging, recovery performance, and payment promises")

    customers = list_customers()
    if not customers:
        st.warning("No data available to generate analytics.")
        return

    # Section 1: Top Metrics Summary
    st.markdown("### 📈 Key Recovery Performance Metrics")
    total_overdue = 0.0
    total_promised = 0.0
    total_customers = len(customers)

    for c in customers:
        cid = c["customer_id"]
        invoices = get_invoice_summary(cid)
        promises = get_promises(cid)
        total_overdue += sum(float(inv.get("outstanding_amount", 0)) for inv in invoices)
        total_promised += sum(float(p.get("amount", 0)) for p in promises if str(p.get("status")).lower() in ["kept", "pending"])

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Outstanding Balance", f"₹{total_overdue:,.0f}")
    col_b.metric("Active Promised/Recovered", f"₹{total_promised:,.0f}")
    col_c.metric("Active Customer Accounts", total_customers)

    st.divider()

    # Section 2: Two Column Charts Layout
    col1, col2 = st.columns(2)

    # Chart 1: Recovery progress across customers/invoices
    with col1:
        st.subheader("1. Recovery Progress by Customer")
        progress_rows = []
        for c in customers:
            cid = c["customer_id"]
            invoices = get_invoice_summary(cid)
            promises = get_promises(cid)

            outstanding = sum(float(inv.get("outstanding_amount", 0)) for inv in invoices)
            promised_amt = sum(float(p.get("amount", 0)) for p in promises if str(p.get("status")).lower() in ["kept", "pending"])

            progress_rows.append({
                "Customer": c["company_name"],
                "Outstanding Balance": outstanding,
                "Promised / Recovered": promised_amt,
                "Segment": c.get("segment", "SMB"),
            })

        df_progress = pd.DataFrame(progress_rows)
        fig_progress = px.bar(
            df_progress,
            x="Customer",
            y=["Outstanding Balance", "Promised / Recovered"],
            title="Outstanding Balance vs Promised Amount",
            barmode="group",
            color_discrete_sequence=["#EF4444", "#10B981"],
            labels={"value": "Amount (₹)", "variable": "Account Status"},
        )
        fig_progress.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig_progress, use_container_width=True)

    # Chart 2: Aging of overdue invoices grouped by days overdue
    with col2:
        st.subheader("2. Overdue Invoice Aging Buckets")
        aging_buckets = {
            "0–15 Days": 0.0,
            "16–30 Days": 0.0,
            "31–45 Days": 0.0,
            "45+ Days": 0.0,
        }

        for c in customers:
            cid = c["customer_id"]
            invoices = get_invoice_summary(cid)
            days = c.get("days_overdue", 0)
            outstanding = sum(float(inv.get("outstanding_amount", 0)) for inv in invoices)

            if days <= 15:
                aging_buckets["0–15 Days"] += outstanding
            elif days <= 30:
                aging_buckets["16–30 Days"] += outstanding
            elif days <= 45:
                aging_buckets["31–45 Days"] += outstanding
            else:
                aging_buckets["45+ Days"] += outstanding

        df_aging = pd.DataFrame(list(aging_buckets.items()), columns=["Aging Bucket", "Outstanding Amount"])
        fig_aging = px.pie(
            df_aging,
            names="Aging Bucket",
            values="Outstanding Amount",
            title="Overdue Balance Distribution by Aging Category",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu,
        )
        fig_aging.update_traces(textinfo="percent+label")
        fig_aging.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_aging, use_container_width=True)

    st.divider()

    # Chart 3: Promises kept vs missed vs pending
    st.subheader("3. Payment Promises Track Record (Kept vs Missed vs Pending)")
    promise_data = []
    for c in customers:
        cid = c["customer_id"]
        promises = get_promises(cid)
        for p in promises:
            promise_data.append({
                "Customer": c["company_name"],
                "Status": p.get("status", "Pending"),
                "Amount": float(p.get("amount", 0)),
            })

    if not promise_data:
        promise_data = [
            {"Customer": "ABC Ltd", "Status": "Missed", "Amount": 80000.0},
            {"Customer": "XYZ Pvt Ltd", "Status": "Pending", "Amount": 35000.0},
            {"Customer": "PQR Solutions", "Status": "Kept", "Amount": 25000.0},
        ]

    df_promises = pd.DataFrame(promise_data)
    summary_df = df_promises.groupby("Status").agg(
        Count=("Amount", "count"),
        Total_Amount=("Amount", "sum"),
    ).reset_index()

    fig_promise = px.bar(
        summary_df,
        x="Status",
        y="Total_Amount",
        color="Status",
        text="Count",
        title="Promise Volume & Amount Breakdown",
        color_discrete_map={"Kept": "#10B981", "Pending": "#F59E0B", "Missed": "#EF4444"},
        labels={"Total_Amount": "Total Amount (₹)", "Count": "Number of Promises"},
    )
    fig_promise.update_traces(texttemplate="%{text} promise(s)", textposition="outside")
    fig_promise.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_promise, use_container_width=True)
