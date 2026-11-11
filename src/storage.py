import os
import sqlite3
from datetime import datetime, timezone

def connect(path: str):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('''CREATE TABLE IF NOT EXISTS snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT, captured_at TEXT NOT NULL, ticker TEXT NOT NULL,
      contract_symbol TEXT NOT NULL, option_type TEXT, expiry TEXT, strike REAL, volume INTEGER,
      open_interest INTEGER, last_price REAL, bid REAL, ask REAL, implied_volatility REAL)''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_contract_time ON snapshots(contract_symbol,captured_at)')
    db.commit()
    return db

def previous_snapshot(db, symbol: str):
    r = db.execute('SELECT captured_at,volume,implied_volatility FROM snapshots WHERE contract_symbol=? ORDER BY id DESC LIMIT 1',(symbol,)).fetchone()
    return {'captured_at':r[0],'volume':r[1],'iv':r[2]} if r else None

def save_snapshot(db, frame):
    captured = datetime.now(timezone.utc).isoformat()
    rows = []
    for _, r in frame.iterrows():
        def n(key):
            v = r.get(key)
            return None if v is None else (v.item() if hasattr(v,'item') else v)
        rows.append((captured,str(n('ticker') or ''),str(n('contractSymbol') or ''),str(n('option_type') or ''),str(n('expiry') or ''),n('strike'),n('volume'),n('openInterest'),n('lastPrice'),n('bid'),n('ask'),n('impliedVolatility')))
    db.executemany('INSERT INTO snapshots(captured_at,ticker,contract_symbol,option_type,expiry,strike,volume,open_interest,last_price,bid,ask,implied_volatility) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',rows)
    db.commit()
