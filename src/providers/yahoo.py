"""Best-effort Yahoo Finance adapter; unofficial and incomplete by design."""
from datetime import datetime, timezone
import logging
import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

def fetch_chain(ticker: str, max_expirations: int = 4) -> pd.DataFrame:
    instrument = yf.Ticker(ticker)
    frames = []
    for expiry in instrument.options[:max_expirations]:
        try:
            chain = instrument.option_chain(expiry)
            for side, frame in (('CALL', chain.calls), ('PUT', chain.puts)):
                if frame is None or frame.empty:
                    continue
                part = frame.copy()
                part['ticker'] = ticker
                part['expiry'] = expiry
                part['option_type'] = side
                part['snapshot_utc'] = datetime.now(timezone.utc).isoformat()
                frames.append(part)
        except Exception as exc:
            log.warning('%s %s: %s', ticker, expiry, exc)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
