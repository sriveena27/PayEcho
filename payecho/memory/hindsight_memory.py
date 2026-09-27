from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://api.hindsight.vectorize.io"
DEFAULT_BANK_PREFIX = "payecho"


def _client():
    api_key = os.getenv("HINDSIGHT_API_KEY")
    if not api_key:
        return None
    try:
        from hindsight_client import Hindsight
    except ImportError as exc:
        raise RuntimeError("Install hindsight-client before using Hindsight Cloud.") from exc

    return Hindsight(
        base_url=os.getenv("HINDSIGHT_BASE_URL", DEFAULT_BASE_URL),
        api_key=api_key,
        timeout=float(os.getenv("HINDSIGHT_TIMEOUT", "30")),
    )


def _bank_id(customer_id: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in customer_id)
    return f"{os.getenv('HINDSIGHT_BANK_PREFIX', DEFAULT_BANK_PREFIX)}_{safe}"


def hindsight_configured() -> bool:
    return bool(os.getenv("HINDSIGHT_API_KEY"))


def ensure_customer_bank(customer_id: str) -> str:
    """Create the customer-scoped Hindsight bank if it does not already exist."""
    client = _client()
    if client is None:
        raise RuntimeError("HINDSIGHT_API_KEY is not configured.")

    bank_id = _bank_id(customer_id)
    try:
        client.create_bank(
            bank_id=bank_id,
            name=f"PayEcho — {customer_id}",
            mission="Remember only the payment relationship and recovery history for this PayEcho customer.",
            disposition={"skepticism": 3, "literalism": 4, "empathy": 4},
        )
    except Exception as exc:
        # Bank creation is idempotent from the application's perspective.
        # A conflict/already-exists response should not stop the workflow.
        message = str(exc).lower()
        if not any(token in message for token in ("already", "exist", "409", "conflict")):
            raise
    finally:
        try:
            client.close()
        except Exception:
            pass
    return bank_id


def retain_interaction(
    customer_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retain a customer-scoped interaction in Hindsight Cloud."""
    if not text or not text.strip():
        raise ValueError("Memory text cannot be empty")

    client = _client()
    if client is None:
        return {
            "status": "local_only",
            "reason": "HINDSIGHT_API_KEY is not configured",
            "customer_id": customer_id,
            "text": text,
        }

    bank_id = _bank_id(customer_id)
    ensure_customer_bank(customer_id)
    metadata = metadata or {}
    timestamp = metadata.get("timestamp") or datetime.now().isoformat(timespec="seconds")

    try:
        result = client.retain(
            bank_id=bank_id,
            content=text,
            context=f"PayEcho customer recovery history for customer_id={customer_id}",
            timestamp=datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")),
            metadata={"customer_id": customer_id, **metadata},
            retain_async=False,
        )
        return {
            "status": "retained",
            "customer_id": customer_id,
            "bank_id": bank_id,
            "result": repr(result),
        }
    finally:
        try:
            client.close()
        except Exception:
            pass


def recall_customer_memory(customer_id: str, query: str) -> list[dict[str, Any]]:
    """Recall only memories from the selected customer's Hindsight bank."""
    client = _client()
    if client is None:
        return []

    bank_id = _bank_id(customer_id)
    ensure_customer_bank(customer_id)
    try:
        response = client.recall(
            bank_id=bank_id,
            query=query,
            types=["experience", "observation", "world"],
            budget=os.getenv("HINDSIGHT_RECALL_BUDGET", "mid"),
            max_tokens=int(os.getenv("HINDSIGHT_MAX_TOKENS", "4096")),
        )
        memories: list[dict[str, Any]] = []
        for item in getattr(response, "results", []) or []:
            memories.append(
                {
                    "date": getattr(item, "timestamp", None) or getattr(item, "date", ""),
                    "summary": getattr(item, "text", str(item)),
                    "type": getattr(item, "type", "experience"),
                    "customer_id": customer_id,
                }
            )
        return memories
    finally:
        try:
            client.close()
        except Exception:
            pass
