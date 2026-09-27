from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "payecho.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT,
    segment TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    outstanding_amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    channel TEXT NOT NULL,
    summary TEXT NOT NULL,
    outcome TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS promises (
    promise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS recovery_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    outcome TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);
"""

CUSTOMERS = [
    ("C01", "ABC Ltd", "Ravi Kumar", "ravi@abc.example", "Enterprise", "Active"),
    ("C02", "XYZ Pvt Ltd", "Priya Shah", "priya@xyz.example", "SMB", "Active"),
    ("C03", "PQR Solutions", "Arjun Rao", "arjun@pqr.example", "SMB", "Active"),
    ("C04", "Nova Systems", "Meera Das", "meera@nova.example", "Enterprise", "Active"),
    ("C05", "BrightWorks", "Kiran Patel", "kiran@bright.example", "SMB", "Active"),
]

INVOICES = [
    ("INV-1024", "C01", 100000.0, "2026-09-10", 80000.0, "Overdue"),
    ("INV-1025", "C02", 50000.0, "2026-09-15", 35000.0, "Overdue"),
    ("INV-1026", "C03", 12000.0, "2026-09-20", 12000.0, "Overdue"),
    ("INV-1027", "C04", 90000.0, "2026-09-25", 45000.0, "Partially Paid"),
    ("INV-1028", "C05", 18000.0, "2026-09-26", 18000.0, "Overdue"),
]

INTERACTIONS = [
    ("C01", "2026-09-10T10:00:00", "phone", "Customer explained a temporary cash-flow issue and requested additional time.", "extension requested"),
    ("C01", "2026-09-18T11:30:00", "email", "Customer promised to pay ₹80,000 by 2026-09-25.", "promise made"),
    ("C01", "2026-09-26T09:15:00", "phone", "Promised date passed and payment has not been received.", "no payment"),
    ("C02", "2026-09-16T14:00:00", "email", "Customer said their internal approval is pending.", "approval pending"),
    ("C02", "2026-09-24T15:00:00", "chat", "Customer requested a short extension and promised an update.", "follow-up promised"),
    ("C03", "2026-09-21T10:15:00", "email", "Customer did not respond to the first overdue notice.", "no response"),
    ("C04", "2026-09-25T13:20:00", "phone", "Customer made a partial payment and said the balance would follow.", "partial payment"),
    ("C05", "2026-09-27T09:00:00", "email", "First reminder sent; no response yet.", "no response"),
]

PROMISES = [
    ("C01", "2026-09-25", 80000.0, "Missed"),
    ("C02", "2026-09-29", 35000.0, "Pending"),
    ("C04", "2026-09-30", 45000.0, "Pending"),
]

def setup_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.executemany(
            """INSERT OR IGNORE INTO customers
            (customer_id, company_name, contact_name, email, segment, status)
            VALUES (?, ?, ?, ?, ?, ?)""",
            CUSTOMERS,
        )
        conn.executemany(
            """INSERT OR IGNORE INTO invoices
            (invoice_id, customer_id, amount, due_date, outstanding_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)""",
            INVOICES,
        )
        if conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0] == 0:
            conn.executemany(
                """INSERT INTO interactions
                (customer_id, timestamp, channel, summary, outcome)
                VALUES (?, ?, ?, ?, ?)""",
                INTERACTIONS,
            )
        if conn.execute("SELECT COUNT(*) FROM promises").fetchone()[0] == 0:
            conn.executemany(
                """INSERT INTO promises
                (customer_id, promised_date, amount, status)
                VALUES (?, ?, ?, ?)""",
                PROMISES,
            )
    print(f"Database ready: {DB_PATH}")

if __name__ == "__main__":
    setup_database()
