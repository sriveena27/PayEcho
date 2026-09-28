from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.mock_data import (
    calculate_days_overdue,
    calculate_risk,
    get_customer,
    get_interactions,
    get_invoice_summary,
    get_promises,
    list_customers,
    recall_customer_memory,
    record_outcome,
    recover,
)


def _risk_badge(risk: str) -> str:
    """Return risk indicator badge."""
    return {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}.get(risk, "⚪ Low")


def render_customers_view() -> None:
    """Render Customer Accounts list and 3-column Customer Detail screen."""
    st.title("💰 PayEcho Revenue Recovery")
    st.caption("AI Revenue Recovery Platform with Hindsight Persistent Customer Memory")

    # Fetch customer dataset from mock_data layer
    all_customers = list_customers()
    if not all_customers:
        st.error("No customers available.")
        return

    # Process customer dataframe
    cust_list = []
    for c in all_customers:
        cid = c["customer_id"]
        invoices = get_invoice_summary(cid)
        outstanding = sum(float(inv.get("outstanding_amount", 0)) for inv in invoices)
        risk = calculate_risk(cid)
        cust_list.append({
            **c,
            "outstanding": outstanding,
            "risk": risk,
        })
    df_customers = pd.DataFrame(cust_list)

    # Maintain selected customer in session state
    if "selected_customer_id" not in st.session_state or st.session_state["selected_customer_id"] not in df_customers["customer_id"].values:
        st.session_state["selected_customer_id"] = df_customers["customer_id"].iloc[0]

    # --- THREE COLUMN LAYOUT ---
    left_col, center_col, right_col = st.columns([1.1, 2.0, 1.4])

    # ==========================================
    # LEFT COLUMN: Customer Navigation & Filters
    # ==========================================
    with left_col:
        st.subheader("📋 Customer Accounts")
        search_query = st.text_input("Search customer", placeholder="e.g. ABC Ltd", key="cust_search_input")
        risk_filter = st.multiselect(
            "Risk Filter",
            options=["High", "Medium", "Low"],
            default=[],
            key="cust_risk_filter",
        )

        filtered_df = df_customers.copy()
        if search_query.strip():
            filtered_df = filtered_df[
                filtered_df["company_name"].str.contains(search_query, case=False, na=False)
            ]
        if risk_filter:
            filtered_df = filtered_df[filtered_df["risk"].isin(risk_filter)]

        if filtered_df.empty:
            st.warning("No matching customers found.")
        else:
            options = filtered_df["customer_id"].tolist()
            
            # Find current index
            curr_id = st.session_state["selected_customer_id"]
            index_val = options.index(curr_id) if curr_id in options else 0

            selected_id = st.radio(
                "Select Customer",
                options=options,
                index=index_val,
                format_func=lambda cid: (
                    f"{_risk_badge(df_customers.loc[df_customers.customer_id == cid, 'risk'].iloc[0])}\n"
                    f"**{df_customers.loc[df_customers.customer_id == cid, 'company_name'].iloc[0]}** — "
                    f"₹{df_customers.loc[df_customers.customer_id == cid, 'outstanding'].iloc[0]:,.0f}"
                ),
                key="customer_radio_selector",
                label_visibility="collapsed",
            )
            if selected_id != st.session_state["selected_customer_id"]:
                st.session_state["selected_customer_id"] = selected_id
                st.session_state.pop("recovery_result", None)
                st.rerun()

    # Load data for selected customer
    active_cid = st.session_state["selected_customer_id"]
    customer = get_customer(active_cid)
    invoices = get_invoice_summary(active_cid)
    interactions = get_interactions(active_cid)
    promises = get_promises(active_cid)
    risk_level = calculate_risk(active_cid)
    days_overdue = calculate_days_overdue(active_cid)
    total_outstanding = sum(float(inv.get("outstanding_amount", 0)) for inv in invoices)

    query_term = "payment history, promises, missed commitments, reasons for delay"
    recalled_memories = recall_customer_memory(active_cid, query_term)

    # ==========================================
    # CENTER COLUMN: Account Summary, Timeline, AI Memory
    # ==========================================
    with center_col:
        st.subheader(f"🏢 {customer['company_name']}")
        st.caption(f"Contact: {customer.get('contact_name', 'N/A')} ({customer.get('email', 'N/A')})")

        # 1. Account Summary
        st.markdown("### 💳 Account Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Outstanding", f"₹{total_outstanding:,.0f}")
        m2.metric("Risk Level", _risk_badge(risk_level))
        m3.metric("Days Overdue", f"{days_overdue} days")
        m4.metric("Segment", customer.get("segment", "SMB"))

        if invoices:
            st.markdown("**Active Overdue Invoices**")
            df_inv = pd.DataFrame(invoices)[["invoice_id", "amount", "due_date", "outstanding_amount", "status"]]
            st.dataframe(df_inv, use_container_width=True, hide_index=True)

        st.divider()

        # 2. Interaction Timeline
        st.markdown("### 📜 Interaction Timeline")
        st.caption("Chronological log of past communications and outcomes")
        if interactions:
            for item in interactions:
                ts = str(item.get("timestamp", ""))[:16]
                ch = str(item.get("channel", "email")).upper()
                summary = item.get("summary", "")
                outcome = item.get("outcome", "Not recorded")
                
                with st.container(border=True):
                    st.markdown(f"**📅 {ts}** · `CHANNEL: {ch}`")
                    st.write(summary)
                    st.caption(f"**Outcome:** `{outcome}`")
        else:
            st.info("No recorded interactions yet.")

        st.divider()

        # 3. AI Customer Memory (VISUALLY DISTINCT!)
        st.markdown("### 🧠 AI Customer Memory")
        st.caption("⚡ *Retrieved via Hindsight Persistent Memory Engine — Customer-Scoped*")
        
        # Visual callout box highlighting distinction between Customer History and AI Customer Memory
        st.markdown(
            """
            <div style="background-color: #1E293B; border-left: 4px solid #6366F1; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">
                <span style="color: #A5B4FC; font-weight: bold; font-size: 13px;">💡 PayEcho Memory Insight:</span>
                <span style="color: #CBD5E1; font-size: 12px;"> Customer History is raw interaction logs. AI Customer Memory represents Hindsight's semantic memory recall used directly by the AI Recovery Agent.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            if recalled_memories:
                for idx, mem in enumerate(recalled_memories):
                    m_date = mem.get("date", "Previous")
                    m_type = str(mem.get("type", "memory")).replace("_", " ").title()
                    m_summary = mem.get("summary", "")

                    # Color badge according to memory type
                    badge_color = "#3B82F6"  # Blue default
                    if "missed" in m_type.lower():
                        badge_color = "#EF4444"  # Red for missed promise
                    elif "pending" in m_type.lower():
                        badge_color = "#F59E0B"  # Yellow for pending date
                    elif "kept" in m_type.lower():
                        badge_color = "#10B981"  # Green for kept promise

                    st.markdown(
                        f"""
                        <div style="background-color: #0F172A; padding: 12px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #334155;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="background-color: {badge_color}; color: #FFFFFF; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                    🧠 {m_type}
                                </span>
                                <span style="color: #94A3B8; font-size: 12px;">{m_date}</span>
                            </div>
                            <div style="color: #F8FAFC; font-size: 13px; margin-top: 6px;">
                                {m_summary}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    """
                    <div style="background-color: #0F172A; padding: 14px; border-radius: 6px; border: 1px dashed #475569; text-align: center;">
                        <span style="color: #94A3B8; font-size: 13px;">🔍 <strong>Empty Memory State:</strong> No historical memory was recalled for this customer.</span><br/>
                        <small style="color: #64748B;">The AI Recovery Agent will rely solely on current facts without inventing history.</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================
    # RIGHT COLUMN: AI Recovery Assistant & Record Outcome
    # ==========================================
    with right_col:
        st.subheader("🤖 AI Recovery Assistant")

        emp_question = st.text_area(
            "Ask the AI Recovery Agent:",
            value=st.session_state.get("employee_question", "What should I do about this customer?"),
            height=85,
            key="employee_question_input",
        )
        st.session_state["employee_question"] = emp_question

        current_int = interactions[0] if interactions else {}
        customer_payload = {
            **customer,
            "outstanding_amount": total_outstanding,
            "days_overdue": days_overdue,
            "risk": risk_level,
            "invoices": invoices,
            "promises": promises,
        }

        if st.button("🚀 Generate AI Recommendation", type="primary", use_container_width=True):
            with st.spinner("Analyzing customer facts and Hindsight memory..."):
                rec_result = recover(
                    customer_payload,
                    current_int,
                    recalled_memories,
                    emp_question,
                )
                st.session_state["recovery_result"] = rec_result

        rec = st.session_state.get("recovery_result")
        if rec:
            st.markdown("#### 1. Situation Summary")
            st.info(rec.get("summary", ""))

            st.markdown("#### 2. Recommended Action")
            st.success(rec.get("action", ""))

            st.markdown("#### 3. Reason")
            st.write(rec.get("reason", ""))

            st.markdown("#### 4. Suggested Tone")
            st.markdown(f"🏷️ **{rec.get('tone', 'Professional')}**")

            st.markdown("#### 5. Draft Follow-up Message")
            st.caption("Editable message ready for sending via email, WhatsApp, or phone:")
            edited_msg = st.text_area(
                "Draft Message",
                value=rec.get("message", ""),
                height=160,
                key=f"draft_msg_area_{active_cid}",
                label_visibility="collapsed",
            )

            st.markdown("#### 🔍 Memory Evidence Used")
            mem_ev = rec.get("memory_evidence", [])
            if mem_ev:
                for ev in mem_ev:
                    if isinstance(ev, dict):
                        st.caption(f"• **{ev.get('date', 'Memory')}:** {ev.get('summary', str(ev))}")
                    else:
                        st.caption(f"• {str(ev)}")
            else:
                st.caption("No historical memory evidence was used (Empty Memory case).")

        st.divider()

        # Record Outcome Form
        st.markdown("### 📝 Record Recovery Outcome")
        with st.form(key=f"record_outcome_form_{active_cid}"):
            outcome_category = st.selectbox(
                "Outcome Status:",
                options=[
                    "Paid",
                    "Promise Made",
                    "Partial Payment",
                    "No Response",
                    "Dispute",
                    "Other",
                ],
            )
            outcome_notes = st.text_area(
                "Optional Details / Notes:",
                placeholder="e.g. Customer promised full transfer on 2026-10-10.",
                height=80,
            )
            submit_outcome = st.form_submit_button("Submit Outcome", use_container_width=True)

            if submit_outcome:
                outcome_text = f"Status: {outcome_category}. {outcome_notes.strip()}".strip()
                outcome_dict = {
                    "text": outcome_text,
                    "channel": "simulated",
                    "action_type": "follow_up_sent",
                    "outcome": outcome_category,
                }
                res = record_outcome(active_cid, outcome_dict)
                st.success(f"Outcome recorded successfully for {customer['company_name']}!")
                st.session_state.pop("recovery_result", None)
                st.rerun()
