import sqlite3

from src.storage import previous_snapshot

def test_previous_snapshot_is_only_returned_for_same_new_york_session():
    db = sqlite3.connect(":memory:")
    db.execute("""CREATE TABLE snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        captured_at TEXT NOT NULL,
        contract_symbol TEXT NOT NULL,
        volume INTEGER,
        implied_volatility REAL
    )""")
    # 15:00 UTC is 10:00 in New York on this November date.
    db.execute(
        "INSERT INTO snapshots(captured_at, contract_symbol, volume, implied_volatility) VALUES (?, ?, ?, ?)",
        ("2026-11-11T15:00:00+00:00", "SPY261120C00600000", 1200, 0.42),
    )
    assert previous_snapshot(db, "SPY261120C00600000", "2026-11-11")["volume"] == 1200
    assert previous_snapshot(db, "SPY261120C00600000", "2026-11-12") is None
    db.close()
