"""
PayEcho — AI Recovery Agent: Before/After Memory Demo

This is not just a technical test — it is the core PayEcho demonstration.
CASE 1 shows the AI reasoning with no remembered history.
CASE 2 shows the same type of situation PLUS remembered Hindsight history.
The difference in output must come from the LLM's own reasoning given the
recalled_memory input, not from anything hardcoded here.
"""

from agent.recover import recover

CUSTOMER_DATA = {
    "company_name": "ABC Ltd",
    "outstanding_amount": 80000,
    "invoice_id": "INV-1024",
    "due_date": "2026-09-20",
    "days_overdue": 10,
    "segment": "Enterprise",
}

CURRENT_INTERACTION = {
    "summary": "Employee is reviewing the account ahead of a follow-up call."
}

QUESTION = "What should I do about this customer?"

MEMORY_CASE_2 = [
    {
        "date": "2026-09-05",
        "summary": "Customer explained that a temporary cash-flow issue was delaying payment.",
        "type": "customer_explanation",
    },
    {
        "date": "2026-09-12",
        "summary": "Customer promised to pay the outstanding invoice by 2026-09-20.",
        "type": "payment_promise",
    },
    {
        "date": "2026-09-22",
        "summary": "The promised payment date passed and no payment was recorded.",
        "type": "missed_promise",
    },
]


def _print_result(result: dict) -> None:
    print(f"Summary:         {result['summary']}")
    print(f"Recommended Action: {result['action']}")
    print(f"Reason:          {result['reason']}")
    print(f"Suggested Tone:  {result['tone']}")
    print(f"Draft Message:   {result['message']}")
    print(f"Memory Evidence: {result['memory_evidence']}")


def run_demo() -> None:
    print("=" * 50)
    print("CASE 1: NO MEMORY")
    print("=" * 50)
    case_1 = recover(CUSTOMER_DATA, CURRENT_INTERACTION, [], QUESTION)
    _print_result(case_1)

    print("\n" + "=" * 50)
    print("CASE 2: WITH MEMORY")
    print("=" * 50)
    case_2 = recover(CUSTOMER_DATA, CURRENT_INTERACTION, MEMORY_CASE_2, QUESTION)
    _print_result(case_2)

    print("\n" + "=" * 50)
    print("COMPARISON CHECK")
    print("=" * 50)
    print(f"Case 1 memory_evidence is empty: {case_1['memory_evidence'] == []}")
    print(f"Case 2 memory_evidence is non-empty: {bool(case_2['memory_evidence'])}")
    print("If both checks above are True, the before/after demo is working correctly.")


# --- Automated assertions (kept for CI / quick sanity checks) ---
def test_recover_contract_without_memory(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = recover(CUSTOMER_DATA, CURRENT_INTERACTION, [], QUESTION)
    assert set(result) == {"summary", "action", "reason", "tone", "message", "memory_evidence"}
    assert result["memory_evidence"] == []


def test_recover_contract_with_memory(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = recover(CUSTOMER_DATA, CURRENT_INTERACTION, MEMORY_CASE_2, QUESTION)
    assert set(result) == {"summary", "action", "reason", "tone", "message", "memory_evidence"}
    assert result["memory_evidence"]


if __name__ == "__main__":
    run_demo()
