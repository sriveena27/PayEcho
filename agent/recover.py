from __future__ import annotations

import json
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are PayEcho's AI Revenue Recovery Assistant. Your job is to generate personalized, high-conversion recovery recommendations for finance and collections employees.

You receive:
1. Customer Facts (company name, outstanding amount, invoice details, due date, days overdue, risk segment).
2. Current Interaction (latest message or notes from employee/customer).
3. Recalled Memory (customer-scoped memory retrieved from Hindsight, containing past promises, payment history, reasons for delay, and outcomes).
4. Employee Question (what the employee wants guidance on).

CRITICAL RULES FOR RECOMMENDATION & BEHAVIOR:

1. EMPTY MEMORY CASE:
If `recalled_memory` is empty (list is empty `[]`), you MUST NOT pretend to remember any previous customer interactions or history. State clearly in `reason` and `summary` that no historical memory was available. Base your recommendation purely on current customer facts and the latest interaction.

2. MISSED PROMISE CASE:
If `recalled_memory` or customer facts contain evidence that the customer previously promised payment by a specific date and that date HAS PASSED without payment:
- Explicitly flag the missed promise in `summary` and `reason`, mentioning the promised date.
- Set `action` to a direct follow-up on the unfulfilled commitment.
- Set `tone` to "firm but professional".
- In `message`, explicitly reference the previous commitment date and ask for immediate settlement or updated payment confirmation.
- Do NOT invent a missed promise if no date was missed.

3. SPECIFIC PAYMENT DATE STILL PENDING CASE:
If the customer requested or promised a specific future payment date and that date has NOT YET PASSED:
- Reference that upcoming payment date.
- Do NOT call it a missed promise.
- Set `tone` to "collaborative".
- In `message`, confirm the expected payment date politely and ask if everything remains on track.

4. POSITIVE HISTORY CASE:
If the customer has a history of on-time payments, kept promises, or positive responsiveness:
- Acknowledge their positive track record in `summary` and `reason`.
- Set `tone` to "warm and appreciative" or "collaborative".
- Keep the payment request clear without making it sound like an escalation.

5. EMPLOYEE QUESTION:
Ensure the recommendation directly answers the employee's question (`employee_question`).

REQUIRED OUTPUT FORMAT:
You MUST respond ONLY with a JSON object containing EXACTLY these six keys:
{
  "summary": "Concise overview of customer situation, outstanding amount, and memory status.",
  "action": "Recommended next action for the employee.",
  "reason": "Why this action is recommended, referencing evidence or facts.",
  "tone": "Suggested communication tone (e.g., firm but professional, collaborative, warm and appreciative).",
  "message": "Draft follow-up message editable by the employee.",
  "memory_evidence": [list of recalled memory items or snippets used as evidence]
}
""".strip()

REQUIRED_KEYS = {"summary", "action", "reason", "tone", "message", "memory_evidence"}


def _fallback(
    customer_data: dict[str, Any],
    current_interaction: dict[str, Any] | str | None,
    recalled_memory: list[dict],
    employee_question: str,
) -> dict[str, Any]:
    company = customer_data.get("company_name", "the customer")
    outstanding = float(customer_data.get("outstanding_amount", 0) or 0)
    days = int(customer_data.get("days_overdue", 0) or 0)
    invoices = customer_data.get("invoices", [])
    inv_id = invoices[0].get("invoice_id", "INV-1001") if (invoices and isinstance(invoices, list) and isinstance(invoices[0], dict)) else customer_data.get("invoice_id", "invoice")

    has_memory = bool(recalled_memory)

    is_missed = any(
        isinstance(m, dict) and (m.get("type") == "missed_promise" or "missed" in str(m.get("summary", "")).lower() or "passed" in str(m.get("summary", "")).lower())
        for m in recalled_memory
    )
    is_pending = (
        any(
            isinstance(m, dict) and (m.get("type") == "payment_date_pending" or "pending" in str(m.get("summary", "")).lower() or "extension" in str(m.get("summary", "")).lower())
            for m in recalled_memory
        )
        and not is_missed
    )

    is_positive = (
        any(
            isinstance(m, dict) and (m.get("type") == "kept_promise" or "kept" in str(m.get("summary", "")).lower() or "positive" in str(m.get("summary", "")).lower())
            for m in recalled_memory
        )
        and not is_missed
    )

    if not has_memory:
        return {
            "summary": f"{company} has an outstanding balance of ₹{outstanding:,.0f} ({days} days overdue). No historical memory is available for this customer.",
            "action": "Send a standard professional payment reminder requesting a confirmed payment date.",
            "reason": f"No historical customer memory was available in Hindsight. Recommendation is based solely on current account facts and overdue status. Question asked: '{employee_question}'",
            "tone": "Professional",
            "message": (
                f"Dear {company} team,\n\n"
                f"We are following up regarding outstanding invoice {inv_id} for ₹{outstanding:,.0f}, which is currently {days} days overdue.\n\n"
                f"Please let us know the current payment status and confirm when we can expect payment.\n\n"
                f"Thank you,\nFinance & Collections Team"
            ),
            "memory_evidence": [],
        }

    if is_missed:
        evidence = [m for m in recalled_memory if isinstance(m, dict) and ("miss" in str(m).lower() or m.get("type") == "missed_promise")] or recalled_memory[:2]
        return {
            "summary": f"{company} has an outstanding balance of ₹{outstanding:,.0f} ({days} days overdue) and previously missed a promised payment date.",
            "action": "Issue a firm follow-up referencing the unfulfilled payment commitment and request an immediate transfer.",
            "reason": f"Hindsight memory contains evidence of a missed payment promise. Direct follow-up is necessary to prevent further delay. Question addressed: '{employee_question}'",
            "tone": "Firm but professional",
            "message": (
                f"Dear {company} team,\n\n"
                f"We are following up on your previous payment commitment for invoice {inv_id} (₹{outstanding:,.0f}). The promised payment date has passed, but we have not yet received payment confirmation.\n\n"
                f"Please review this urgently and provide payment confirmation or transfer details today.\n\n"
                f"Best regards,\nAccounts Receivable Team"
            ),
            "memory_evidence": evidence,
        }

    if is_pending:
        evidence = [m for m in recalled_memory if isinstance(m, dict) and ("pending" in str(m).lower() or "extension" in str(m).lower() or m.get("type") == "payment_date_pending")] or recalled_memory[:2]
        return {
            "summary": f"{company} has an outstanding invoice of ₹{outstanding:,.0f} ({days} days overdue) with an agreed upcoming payment date pending.",
            "action": "Send a collaborative touchpoint to confirm that payment processing is on track for the scheduled date.",
            "reason": f"Customer has an active pending payment date request on file. A collaborative touchpoint ensures prompt processing without escalating. Question addressed: '{employee_question}'",
            "tone": "Collaborative",
            "message": (
                f"Dear {company} team,\n\n"
                f"We are checking in regarding invoice {inv_id} for ₹{outstanding:,.0f}. As discussed, we understand payment is scheduled for your upcoming committed date.\n\n"
                f"Please confirm if everything remains on track or if you require any additional invoice details from our side.\n\n"
                f"Thank you,\nFinance Team"
            ),
            "memory_evidence": evidence,
        }

    if is_positive:
        evidence = [m for m in recalled_memory if isinstance(m, dict) and ("kept" in str(m).lower() or "paid" in str(m).lower() or m.get("type") == "kept_promise")] or recalled_memory[:2]
        return {
            "summary": f"{company} has an open balance of ₹{outstanding:,.0f} ({days} days overdue) and a strong historical record of timely payments.",
            "action": "Send a warm, courteous reminder acknowledging their excellent payment history.",
            "reason": f"Hindsight memory shows a positive payment history. A polite reminder preserves goodwill while securing payment. Question addressed: '{employee_question}'",
            "tone": "Warm and appreciative",
            "message": (
                f"Dear {company} team,\n\n"
                f"Thank you for your continued partnership with us. We noticed invoice {inv_id} (₹{outstanding:,.0f}) is slightly past due. Given your excellent payment history, we wanted to bring this to your attention in case it slipped through.\n\n"
                f"Please let us know if you need any assistance or remittance details.\n\n"
                f"Warm regards,\nFinance Team"
            ),
            "memory_evidence": evidence,
        }

    return {
        "summary": f"{company} has an outstanding balance of ₹{outstanding:,.0f} ({days} days overdue). Recalled memory provides historical context.",
        "action": "Follow up with customer referencing prior communication and request a clear payment timeline.",
        "reason": f"Recommendation incorporates recalled customer memory snippets from Hindsight. Question addressed: '{employee_question}'",
        "tone": "Professional and empathetic",
        "message": (
            f"Dear {company} team,\n\n"
            f"We are following up regarding invoice {inv_id} for ₹{outstanding:,.0f}. "
            f"Please share an update on the payment schedule at your earliest convenience.\n\n"
            f"Thank you,\nFinance Team"
        ),
        "memory_evidence": recalled_memory[:2],
    }


def _validate(
    result: Any,
    customer_data: dict[str, Any],
    current_interaction: dict[str, Any] | str | None,
    recalled_memory: list[dict],
    employee_question: str,
) -> dict[str, Any]:
    if not isinstance(result, dict) or not REQUIRED_KEYS.issubset(result.keys()):
        return _fallback(customer_data, current_interaction, recalled_memory, employee_question)

    evidence = result.get("memory_evidence")
    if not isinstance(evidence, list):
        evidence = []

    return {
        "summary": str(result.get("summary", "")),
        "action": str(result.get("action", "")),
        "reason": str(result.get("reason", "")),
        "tone": str(result.get("tone", "")),
        "message": str(result.get("message", "")),
        "memory_evidence": evidence,
    }


def recover(
    customer_data: dict[str, Any],
    current_interaction: dict[str, Any] | str | None,
    recalled_memory: list[dict],
    employee_question: str,
) -> dict[str, Any]:
    """
    Recover function contract:
    Input:
      customer_data: dict
      current_interaction: string or dict
      recalled_memory: list of dicts
      employee_question: str
    Output:
      dict with exact keys: summary, action, reason, tone, message, memory_evidence
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback(customer_data, current_interaction, recalled_memory, employee_question)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        payload = {
            "customer_data": customer_data,
            "current_interaction": current_interaction or {},
            "recalled_memory": recalled_memory or [],
            "employee_question": employee_question or "What should I do about this customer?",
        }

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        return _validate(parsed, customer_data, current_interaction, recalled_memory, employee_question)
    except Exception:
        return _fallback(customer_data, current_interaction, recalled_memory, employee_question)

