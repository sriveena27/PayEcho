# PayEcho Architecture

PayEcho follows the finalized project specification.

## Module 1 — Frontend / Streamlit UI

Reads:
- `get_customer(customer_id)`
- `get_invoice_summary(customer_id)`
- `get_interactions(customer_id)`
- `recover(...)`

Writes:
- `record_outcome(customer_id, outcome)`

## Module 2 — Backend + Database + Hindsight

Owns:
- SQLite schema
- Synthetic seed data
- Hindsight Retain
- Hindsight Recall
- Outcome recording

## Module 3 — AI Agent + LLM

Contract:

```python
recover(customer_data, current_interaction, recalled_memory, employee_question)
```

Returns:

```python
{
    "summary": str,
    "action": str,
    "reason": str,
    "tone": str,
    "message": str,
    "memory_evidence": list
}
```
