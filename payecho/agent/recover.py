from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are PayEcho's AI Revenue Recovery Assistant.

Use ONLY the supplied customer facts and recalled customer-scoped memories.
Do not invent payment history, promises, amounts, dates, outcomes, or customer preferences.
If a fact is missing, say that it is unknown.

Return valid JSON with exactly these keys:
summary, action, reason, tone, message, memory_evidence

memory_evidence must be a list containing only recalled memory items that materially support the recommendation.
The message must be professional, concise, personalized, and editable by a finance employee.
PayEcho does not send messages automatically.
""".strip()

REQUIRED_KEYS = {"summary", "action", "reason", "tone", "message", "memory_evidence"}


def _fallback(customer_data: dict[str, Any], recalled_memory: list[dict], question: str) -> dict[str, Any]:
    overdue = float(customer_data.get("outstanding_amount", 0) or 0)
    days = int(customer_data.get("days_overdue", 0) or 0)
    missed = any("miss" in str(m.get("summary", "")).lower() for m in recalled_memory)

    if missed:
        action = "Follow up on the missed commitment and request a firm, specific payment date."
        tone = "firm but empathetic"
    elif recalled_memory:
        action = "Follow up using the customer's previous reason for delay and request a clear payment update."
        tone = "professional and empathetic"
    else:
        action = "Send a professional overdue-payment follow-up and request a confirmed payment date."
        tone = "professional"

    evidence = recalled_memory[:3]
    return {
        "summary": (
            f"Outstanding amount: ₹{overdue:,.0f}; days overdue: {days}. "
            f"Employee question: {question}"
        ),
        "action": action,
        "reason": (
            "The recommendation uses recalled customer history."
            if evidence else
            "No prior customer memory was available, so the recommendation uses current account facts."
        ),
        "tone": tone,
        "message": (
            "Hello, we are following up regarding the outstanding invoice. "
            "Please share the current payment status and confirm the specific payment date. "
            "If there is an issue affecting payment, please let us know so we can review the next step."
        ),
        "memory_evidence": evidence,
    }


def _validate(result: Any, customer_data: dict[str, Any], memory: list[dict], question: str) -> dict[str, Any]:
    if not isinstance(result, dict) or not REQUIRED_KEYS.issubset(result):
        return _fallback(customer_data, memory, question)
    result["memory_evidence"] = result.get("memory_evidence") if isinstance(result.get("memory_evidence"), list) else []
    return {key: result[key] for key in REQUIRED_KEYS}


def recover(
    customer_data: dict[str, Any],
    current_interaction: dict[str, Any] | None,
    recalled_memory: list[dict],
    employee_question: str,
) -> dict[str, Any]:
    """Module 3 contract: facts + memory + employee question -> structured recovery result."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback(customer_data, recalled_memory, employee_question)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        payload = {
            "customer_data": customer_data,
            "current_interaction": current_interaction or {},
            "recalled_memory": recalled_memory,
            "employee_question": employee_question,
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
        return _validate(json.loads(raw), customer_data, recalled_memory, employee_question)
    except Exception:
        return _fallback(customer_data, recalled_memory, employee_question)
