from database.setup_db import setup_database
from database.services import (
    calculate_days_overdue,
    calculate_risk,
    get_customer,
    get_interactions,
    get_invoice_summary,
)


def test_seeded_service_functions(tmp_path, monkeypatch):
    import database.setup_db as setup
    import database.services as services

    db_path = tmp_path / "payecho.db"
    monkeypatch.setattr(setup, "DB_PATH", db_path)
    monkeypatch.setattr(services, "DB_PATH", db_path)
    setup.setup_database()

    assert get_customer("C01")["company_name"] == "ABC Ltd"
    assert len(get_invoice_summary("C01")) == 1
    assert len(get_interactions("C01")) == 3
    assert calculate_risk("C01") == "High"
    assert calculate_days_overdue("C01") >= 0
