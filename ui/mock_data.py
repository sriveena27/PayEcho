from __future__ import annotations

from datetime import datetime
from typing import Any
from agent.recover import recover as agent_recover

# Fictional / Synthetic Customer Database for Mock Frontend Development
MOCK_CUSTOMERS = [
    {
        "customer_id": "C01",
        "company_name": "ABC Ltd",
        "contact_name": "Rahul Sharma",
        "email": "rahul@abcltd.com",
        "segment": "Enterprise",
        "status": "Active",
        "outstanding_amount": 80000.0,
        "days_overdue": 43,
        "risk": "High",
    },
    {
        "customer_id": "C02",
        "company_name": "XYZ Pvt Ltd",
        "contact_name": "Anita Desai",
        "email": "anita@xyzpvtltd.com",
        "segment": "SMB",
        "status": "Active",
        "outstanding_amount": 35000.0,
        "days_overdue": 12,
        "risk": "Medium",
    },
    {
        "customer_id": "C03",
        "company_name": "PQR Solutions",
        "contact_name": "Suresh Gupta",
        "email": "suresh@pqrsolutions.com",
        "segment": "SMB",
        "status": "Active",
        "outstanding_amount": 12000.0,
        "days_overdue": 7,
        "risk": "Low",
    },
    {
        "customer_id": "C04",
        "company_name": "Acme Corp",
        "contact_name": "David Miller",
        "email": "david@acmecorp.com",
        "segment": "Enterprise",
        "status": "Active",
        "outstanding_amount": 50000.0,
        "days_overdue": 17,
        "risk": "Medium",
    },
]

MOCK_INVOICES = {
    "C01": [
        {
            "invoice_id": "INV-1001",
            "customer_id": "C01",
            "amount": 80000.0,
            "due_date": "2026-08-15",
            "outstanding_amount": 80000.0,
            "status": "Overdue",
        }
    ],
    "C02": [
        {
            "invoice_id": "INV-1002",
            "customer_id": "C02",
            "amount": 35000.0,
            "due_date": "2026-09-15",
            "outstanding_amount": 35000.0,
            "status": "Overdue",
        }
    ],
    "C03": [
        {
            "invoice_id": "INV-1003",
            "customer_id": "C03",
            "amount": 12000.0,
            "due_date": "2026-09-20",
            "outstanding_amount": 12000.0,
            "status": "Overdue",
        }
    ],
    "C04": [
        {
            "invoice_id": "INV-1004",
            "customer_id": "C04",
            "amount": 50000.0,
            "due_date": "2026-09-10",
            "outstanding_amount": 50000.0,
            "status": "Overdue",
        }
    ],
}

MOCK_INTERACTIONS = {
    "C01": [
        {
            "interaction_id": 1,
            "customer_id": "C01",
            "timestamp": "2026-09-20 10:00:00",
            "channel": "phone",
            "summary": "Customer promised full payment of ₹80,000 by 2026-09-22 following bank clearance.",
            "outcome": "Promise Made",
        },
        {
            "interaction_id": 2,
            "customer_id": "C01",
            "timestamp": "2026-09-10 14:30:00",
            "channel": "email",
            "summary": "Initial overdue notice sent for invoice INV-1001.",
            "outcome": "No Response",
        },
    ],
    "C02": [
        {
            "interaction_id": 3,
            "customer_id": "C02",
            "timestamp": "2026-09-25 11:15:00",
            "channel": "email",
            "summary": "Customer requested an extension to pay on 2026-10-05 after client clearance.",
            "outcome": "Promise Made",
        }
    ],
    "C03": [
        {
            "interaction_id": 4,
            "customer_id": "C03",
            "timestamp": "2026-09-21 09:30:00",
            "channel": "phone",
            "summary": "Friendly payment reminder call completed.",
            "outcome": "In Review",
        }
    ],
    "C04": [
        {
            "interaction_id": 5,
            "customer_id": "C04",
            "timestamp": "2026-09-26 16:00:00",
            "channel": "email",
            "summary": "Automated billing statement generated and emailed.",
            "outcome": "No Response",
        }
    ],
}

MOCK_PROMISES = {
    "C01": [
        {
            "promise_id": 1,
            "customer_id": "C01",
            "promised_date": "2026-09-22",
            "amount": 80000.0,
            "status": "Missed",
        }
    ],
    "C02": [
        {
            "promise_id": 2,
            "customer_id": "C02",
            "promised_date": "2026-10-05",
            "amount": 35000.0,
            "status": "Pending",
        }
    ],
    "C03": [
        {
            "promise_id": 3,
            "customer_id": "C03",
            "promised_date": "2026-08-10",
            "amount": 25000.0,
            "status": "Kept",
        }
    ],
    "C04": [],
}

# Hindsight Recalled Memory (Customer-Scoped)
MOCK_RECALLED_MEMORIES = {
    "C01": [
        {
            "date": "2026-09-20",
            "summary": "Customer promised full payment of ₹80,000 by 2026-09-22 due to temporary bank delay.",
            "type": "promise_made",
        },
        {
            "date": "2026-09-23",
            "summary": "Promised payment date 2026-09-22 passed with ₹0 received. Commitment marked missed.",
            "type": "missed_promise",
        },
    ],
    "C02": [
        {
            "date": "2026-09-25",
            "summary": "Customer committed to pay ₹35,000 on 2026-10-05 once quarterly receivables clear.",
            "type": "payment_date_pending",
        }
    ],
    "C03": [
        {
            "date": "2026-08-10",
            "summary": "Customer paid previous invoice INV-0980 (₹25,000) on time immediately following reminder.",
            "type": "kept_promise",
        }
    ],
    "C04": [],  # EMPTY MEMORY CASE!
}

RECORDED_OUTCOMES_LOG = []


def list_customers() -> list[dict[str, Any]]:
    """Return all synthetic customer accounts."""
    return [c.copy() for c in MOCK_CUSTOMERS]


def get_customer(customer_id: str) -> dict[str, Any] | None:
    """Return single customer dictionary by ID."""
    for customer in MOCK_CUSTOMERS:
        if customer["customer_id"] == customer_id:
            return customer.copy()
    return None


def get_invoice_summary(customer_id: str) -> list[dict[str, Any]]:
    """Return invoices list for given customer_id."""
    return [inv.copy() for inv in MOCK_INVOICES.get(customer_id, [])]


def get_interactions(customer_id: str) -> list[dict[str, Any]]:
    """Return interactions list for given customer_id."""
    return [inter.copy() for inter in MOCK_INTERACTIONS.get(customer_id, [])]


def get_promises(customer_id: str) -> list[dict[str, Any]]:
    """Return promises list for given customer_id."""
    return [prom.copy() for prom in MOCK_PROMISES.get(customer_id, [])]


def calculate_days_overdue(customer_id: str) -> int:
    """Return days overdue for customer."""
    cust = get_customer(customer_id)
    return cust.get("days_overdue", 0) if cust else 0


def calculate_risk(customer_id: str) -> str:
    """Return risk rating for customer ("High", "Medium", "Low")."""
    cust = get_customer(customer_id)
    return cust.get("risk", "Low") if cust else "Low"


def recall_customer_memory(customer_id: str, query: str = "") -> list[dict[str, Any]]:
    """Return customer-scoped Hindsight recalled memory items."""
    return [m.copy() for m in MOCK_RECALLED_MEMORIES.get(customer_id, [])]


def recover(
    customer_data: dict[str, Any],
    current_interaction: dict[str, Any] | str | None,
    recalled_memory: list[dict],
    employee_question: str,
) -> dict[str, Any]:
    """Frontend-development placeholder routing directly to agent.recover."""
    return agent_recover(customer_data, current_interaction, recalled_memory, employee_question)


def record_outcome(customer_id: str, outcome: dict[str, Any] | str) -> dict[str, Any]:
    """Placeholder function to record outcome during frontend dummy execution."""
    if isinstance(outcome, str):
        outcome = {"text": outcome, "channel": "simulated", "action_type": "follow_up_sent"}

    text = str(outcome.get("text", "")).strip() or "Outcome recorded"
    channel = str(outcome.get("channel", "simulated"))
    outcome_label = str(outcome.get("outcome", outcome.get("action_type", "Recorded")))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "customer_id": customer_id,
        "timestamp": timestamp,
        "channel": channel,
        "summary": text,
        "outcome": outcome_label,
    }
    RECORDED_OUTCOMES_LOG.append(entry)

    if customer_id in MOCK_INTERACTIONS:
        MOCK_INTERACTIONS[customer_id].insert(0, {
            "interaction_id": len(MOCK_INTERACTIONS[customer_id]) + 10,
            "customer_id": customer_id,
            "timestamp": timestamp,
            "channel": channel,
            "summary": text,
            "outcome": outcome_label,
        })

    return {
        "status": "success",
        "mock": True,
        "message": f"Recorded outcome for customer {customer_id}",
        "record": entry,
    }
