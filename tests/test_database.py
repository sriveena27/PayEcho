import sqlite3
from database.setup_db import SCHEMA

def test_schema_creates_all_tables(tmp_path):
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert {"customers", "invoices", "interactions", "promises", "recovery_actions"} <= tables
