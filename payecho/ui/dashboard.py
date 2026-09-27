from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from agent.recover import recover
from database.services import (
    calculate_days_overdue,
    calculate_risk,
    get_customer,
    get_interactions,
    get_invoice_summary,
    get_promises,
    list_customers,
    recall_customer_memory,
    record_outcome,
)
from memory.hindsight_memory import hindsight_configured


def _risk_badge(risk: str) -> str:
    return {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(risk, "⚪")


def _customer_frame(customers: list[dict]) -> pd.DataFrame:
    rows = []
    for customer in customers:
        cid = customer["customer_id"]
        invoices = get_invoice_summary(cid)
        outstanding = sum(float(x["outstanding_amount"]) for x in invoices)
        risk = calculate_risk(cid)
        rows.append({**customer, "outstanding": outstanding, "risk": risk})
    return pd.DataFrame(rows)


def render_dashboard() -> None:
    st.title("💰 PayEcho")
    st.caption("AI Revenue Recovery with persistent customer memory")

    if not hindsight_configured():
        st.warning("Hindsight Cloud is not configured. Add HINDSIGHT_API_KEY to your local .env for live memory.")
    else:
        st.success("Hindsight Cloud memory is configured.")

    customers = _customer_frame(list_customers())
    if customers.empty:
        st.error("No customers found. Run `python database/setup_db.py` first.")
        return

    left, center, right = st.columns([1.15, 2.0, 1.45])

    with left:
        st.subheader("Customers")
        search = st.text_input("Search customer", placeholder="ABC Ltd")
        risk_filter = st.multiselect("Risk filter", ["High", "Medium", "Low"], default=[])
        filtered = customers.copy()
        if search:
            filtered = filtered[filtered["company_name"].str.contains(search, case=False, na=False)]
        if risk_filter:
            filtered = filtered[filtered["risk"].isin(risk_filter)]

        if filtered.empty:
            st.info("No customers found.")
            return

        options = filtered["customer_id"].tolist()
        selected_id = st.radio(
            "Select customer",
            options,
            format_func=lambda cid: (
                f"{_risk_badge(customers.loc[customers.customer_id == cid, 'risk'].iloc[0])} "
                f"{customers.loc[customers.customer_id == cid, 'company_name'].iloc[0]} — "
                f"₹{customers.loc[customers.customer_id == cid, 'outstanding'].iloc[0]:,.0f}"
            ),
            label_visibility="collapsed",
        )

    customer = get_customer(selected_id)
    invoices = get_invoice_summary(selected_id)
    interactions = get_interactions(selected_id)
    promises = get_promises(selected_id)
    risk = calculate_risk(selected_id)
    days_overdue = calculate_days_overdue(selected_id)
    outstanding = sum(float(x["outstanding_amount"]) for x in invoices)

    query = "payment history, reasons for delay, extensions, promises, missed promises, payment outcomes"
    recalled = recall_customer_memory(selected_id, query)

    with center:
        st.subheader(customer["company_name"])
        a, b, c, d = st.columns(4)
        a.metric("Outstanding", f"₹{outstanding:,.0f}")
        b.metric("Risk", f"{_risk_badge(risk)} {risk}")
        c.metric("Days overdue", days_overdue)
        d.metric("Segment", customer["segment"])

        st.markdown("### Invoice Information")
        if invoices:
            st.dataframe(pd.DataFrame(invoices), use_container_width=True, hide_index=True)

        st.markdown("### Interaction Timeline")
        for row in interactions:
            st.markdown(
                f"**{row['timestamp'][:10]} · {row['channel']}** — {row['summary']}  \n"
                f"*Outcome: {row['outcome'] or 'Not recorded'}*"
            )

        st.markdown("### Promises")
        if promises:
            st.dataframe(pd.DataFrame(promises), use_container_width=True, hide_index=True)
        else:
            st.caption("No recorded promises.")

        st.markdown("### 🧠 AI Customer Memory")
        if recalled:
            for item in recalled:
                st.info(f"{item.get('date', '')} · {item.get('type', 'memory')} — {item.get('summary', '')}")
        elif hindsight_configured():
            st.caption("No relevant Hindsight memories were recalled for this query yet.")
        else:
            st.caption("Live Hindsight memory is unavailable until HINDSIGHT_API_KEY is configured.")

    with right:
        st.subheader("🤖 AI Recovery Assistant")
        question = st.text_area(
            "Employee question",
            st.session_state.get("employee_question", "What should I do about this customer?"),
            height=100,
        )
        st.session_state["employee_question"] = question

        current = interactions[0] if interactions else {}
        customer_data = {
            **customer,
            "outstanding_amount": outstanding,
            "days_overdue": days_overdue,
            "risk": risk,
            "invoices": invoices,
            "promises": promises,
        }

        if st.button("Generate Recommendation", type="primary", use_container_width=True):
            st.session_state["recovery_result"] = recover(
                customer_data, current, recalled, question
            )

        result = st.session_state.get("recovery_result")
        if result:
            st.markdown("**Situation Summary**")
            st.write(result["summary"])
            st.markdown("**Recommended Action**")
            st.write(result["action"])
            st.markdown("**Why**")
            st.write(result["reason"])
            st.markdown(f"**Suggested Tone:** {result['tone']}")

            st.text_area("Edit before sending", result["message"], height=180, key="draft_message")
            st.markdown("**Memory Evidence**")
            if result["memory_evidence"]:
                for evidence in result["memory_evidence"]:
                    st.caption(str(evidence))
            else:
                st.caption("No recalled memory was used.")

        st.markdown("### Record Outcome")
        outcome = st.text_area(
            "What happened after the follow-up?",
            placeholder="Example: Customer confirmed payment will be made on 2026-10-02.",
            height=100,
        )
        if st.button("Save Outcome", use_container_width=True):
            if not outcome.strip():
                st.warning("Enter an outcome before saving.")
            else:
                try:
                    saved = record_outcome(
                        selected_id,
                        {"text": outcome, "channel": "simulated", "action_type": "follow_up_sent"},
                    )
                    st.success(
                        "Outcome saved to SQLite and sent to Hindsight. "
                        f"Memory status: {saved['memory'].get('status', 'unknown')}"
                    )
                    st.session_state.pop("recovery_result", None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save outcome: {exc}")

    st.divider()
    st.subheader("📊 Analytics")
    chart_df = customers[["company_name", "outstanding", "risk"]].copy()
    fig = px.bar(
        chart_df,
        x="company_name",
        y="outstanding",
        color="risk",
        title="Outstanding Amount by Customer",
        labels={"company_name": "Customer", "outstanding": "Outstanding (₹)"},
    )
    st.plotly_chart(fig, use_container_width=True)
