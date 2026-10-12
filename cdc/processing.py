"""Idempotent CDC materialization and factual monitoring into local SQLite."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def initialize(db):
    db.execute("CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY, customer_code TEXT NOT NULL, amount REAL NOT NULL, status TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS processed (topic TEXT NOT NULL, partition_no INTEGER NOT NULL, offset_no INTEGER NOT NULL, PRIMARY KEY(topic, partition_no, offset_no))")
    db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, at TEXT NOT NULL)")
    db.commit()


def apply_event(db: sqlite3.Connection, payload: dict, topic: str, partition: int, offset: int) -> bool:
    """Debezium envelope; transactional offset deduplication, no blind event replay."""
    op = payload.get("op")
    if op not in {"r", "c", "u", "d"}:
        raise ValueError("Unsupported CDC operation")
    row = payload.get("after") if op != "d" else payload.get("before")
    if not isinstance(row, dict) or not isinstance(row.get("order_id"), int):
        raise ValueError("Missing order_id")
    if op != "d":
        amount = float(row.get("amount", -1))
        if amount < 0 or not 0 <= amount <= 1_000_000:
            raise ValueError("Invalid amount")
        if row.get("status") not in {"created", "paid", "shipped", "cancelled"}:
            raise ValueError("Invalid status")
        customer = row.get("customer_code")
        if not isinstance(customer, str) or not customer:
            raise ValueError("Invalid customer")
    with db:
        if db.execute("SELECT 1 FROM processed WHERE topic=? AND partition_no=? AND offset_no=?", (topic, partition, offset)).fetchone():
            return False
        if op == "d":
            db.execute("DELETE FROM orders WHERE order_id=?", (row["order_id"],))
        else:
            db.execute("INSERT INTO orders VALUES (?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET customer_code=excluded.customer_code, amount=excluded.amount, status=excluded.status",
                       (row["order_id"], customer, amount, row["status"]))
        db.execute("INSERT INTO processed VALUES (?,?,?)", (topic, partition, offset))
        db.execute("INSERT INTO events(event_type,at) VALUES (?,?)", (op, datetime.now(timezone.utc).isoformat()))
    return True


def metrics(path="artifacts/cdc.db"):
    dbfile = Path(path)
    if not dbfile.is_file():
        return {"orders": 0, "events": 0, "recent_events": [], "configured": False}
    with sqlite3.connect(dbfile) as db:
        initialize(db)
        rows = db.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type").fetchall()
        return {"orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
                "events": db.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                "recent_events": [{"type": k, "count": n} for k, n in rows], "configured": True}
