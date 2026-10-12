import sqlite3
from fastapi.testclient import TestClient
from backend.main import app
from cdc.processing import apply_event, initialize, metrics
from cdc.ai import explain


def test_snapshot_upsert_delete_and_dedup(tmp_path):
    path = tmp_path / "state.db"
    with sqlite3.connect(path) as db:
        initialize(db)
        event = {"op": "r", "after": {"order_id": 7, "customer_code": "X", "amount": 50, "status": "created"}}
        assert apply_event(db, event, "orders", 0, 1)
        assert not apply_event(db, event, "orders", 0, 1)
        event["op"], event["after"]["status"] = "u", "paid"
        assert apply_event(db, event, "orders", 0, 2)
        assert db.execute("SELECT status FROM orders WHERE order_id=7").fetchone()[0] == "paid"
        assert apply_event(db, {"op": "d", "before": {"order_id": 7}}, "orders", 0, 3)
    result = metrics(path)
    assert result["orders"] == 0
    assert result["events"] == 3


def test_api_and_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("CDC_STORE", str(tmp_path / "missing.db"))
    monkeypatch.setenv("LLM_MODE", "mock")
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/api/metrics").json()["configured"] is False
    assert client.post("/api/ai/investigate").json()["mode"] == "mock"


def test_invalid_event():
    with sqlite3.connect(":memory:") as db:
        initialize(db)
        try:
            apply_event(db, {"op": "c", "after": {"order_id": 1, "amount": -1}}, "orders", 0, 1)
        except ValueError:
            pass
        else:
            raise AssertionError("negative amount must be rejected")
