import sqlite3

from src.storage import alert_already_sent, connect, record_alert_sent

def test_alert_is_deduplicated_only_within_same_session():
    db = connect(":memory:")
    symbol = "SPY261120C00600000"
    assert not alert_already_sent(db, symbol, "2026-11-11")
    record_alert_sent(db, symbol, "2026-11-11", 82.5)
    assert alert_already_sent(db, symbol, "2026-11-11")
    assert not alert_already_sent(db, symbol, "2026-11-12")
    db.close()
