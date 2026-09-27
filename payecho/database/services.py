from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from database.setup_db import DB_PATH
from memory.hindsight_memory import recall_customer_memory, retain_interaction


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_customer(customer_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    return dict(row) if row else None


def get_invoice_summary(customer_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM invoices WHERE customer_id = ? ORDER BY due_date",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_interactions(customer_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM interactions WHERE customer_id = ? ORDER BY timestamp DESC",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_promises(customer_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM promises WHERE customer_id = ? ORDER BY promised_date DESC",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recovery_actions(customer_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM recovery_actions WHERE customer_id = ? ORDER BY timestamp DESC",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_customers() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY company_name").fetchall()
    return [dict(row) for row in rows]


def calculate_days_overdue(customer_id: str, today: date | None = None) -> int:
    today = today or date.today()
    invoices = get_invoice_summary(customer_id)
    overdue_days = []
    for invoice in invoices:
        if float(invoice["outstanding_amount"]) > 0 and invoice["due_date"]:
            due = date.fromisoformat(invoice["due_date"])
            overdue_days.append(max((today - due).days, 0))
    return max(overdue_days, default=0)


def calculate_risk(customer_id: str) -> str:
    outstanding = sum(float(x["outstanding_amount"]) for x in get_invoice_summary(customer_id))
    missed_promises = sum(1 for x in get_promises(customer_id) if x["status"].lower() == "missed")
    days_overdue = calculate_days_overdue(customer_id)
    if missed_promises or outstanding >= 75000 or days_overdue >= 30:
        return "High"
    if outstanding >= 25000 or days_overdue >= 15:
        return "Medium"
    return "Low"


def record_outcome(customer_id: str, outcome: dict[str, Any] | str) -> dict[str, Any]:
    """Write an employee outcome to SQLite and retain it in Hindsight."""
    if isinstance(outcome, str):
        outcome = {"text": outcome}

    text = str(outcome.get("text", "")).strip()
    if not text:
        raise ValueError("Outcome text cannot be empty")

    action_type = str(outcome.get("action_type", "follow_up_sent"))
    timestamp = str(outcome.get("timestamp", datetime.now().isoformat(timespec="seconds")))

    with _connect() as conn:
        conn.execute(
            """INSERT INTO recovery_actions
            (customer_id, action_type, timestamp, outcome)
            VALUES (?, ?, ?, ?)""",
            (customer_id, action_type, timestamp, text),
        )
        conn.execute(
            """INSERT INTO interactions
            (customer_id, timestamp, channel, summary, outcome)
            VALUES (?, ?, ?, ?, ?)""",
            (
                customer_id,
                timestamp,
                str(outcome.get("channel", "simulated")),
                text,
                str(outcome.get("interaction_outcome", "outcome recorded")),
            ),
        )
        conn.commit()

    memory_result = retain_interaction(
        customer_id,
        text,
        {
            "type": "recovery_outcome",
            "source": "payecho",
            "channel": outcome.get("channel", "simulated"),
            "timestamp": timestamp,
        },
    )
    return {"sqlite": True, "memory": memory_result}


# Re-export the two memory functions at the service boundary expected by the spec.
__all__ = [
    "get_customer",
    "get_invoice_summary",
    "get_interactions",
    "retain_interaction",
    "recall_customer_memory",
    "record_outcome",
    "get_promises",
    "get_recovery_actions",
    "list_customers",
    "calculate_days_overdue",
    "calculate_risk",
]
