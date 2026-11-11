import logging
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from .config import WATCHLIST,MAX_EXPIRATIONS,MIN_VOLUME,ALERT_SCORE,DATABASE_PATH,DRY_RUN,TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID
from .providers.yahoo import fetch_chain
from .storage import connect,previous_snapshot,save_snapshot,alert_already_sent,record_alert_sent
from .scoring import score_contract
from .telegram import send_message
from .market_hours import is_us_regular_session

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger(__name__)
NY=ZoneInfo("America/New_York")

def safe_number(value, default=0.0):
    try:
        result=float(value)
        return result if math.isfinite(result) else default
    except (TypeError,ValueError):
        return default

def safe_int(value):
    return int(safe_number(value,0.0))

def run():
    if not is_us_regular_session():
        log.info("Outside US regular session; skipping scan.")
        return
    session_day=datetime.now(NY).date().isoformat()
    db=connect(DATABASE_PATH)
    try:
        for ticker in WATCHLIST:
            log.info("Fetching %s",ticker)
            frame=fetch_chain(ticker,MAX_EXPIRATIONS)
            if frame.empty:
                log.warning("No options data for %s",ticker)
                continue
            alerts=[]
            for _,row in frame.iterrows():
                volume=safe_int(row.get("volume"))
                if volume<MIN_VOLUME:
                    continue
                symbol=str(row.get("contractSymbol") or "")
                previous=previous_snapshot(db,symbol,session_day) if symbol and symbol!="nan" else None
                result=score_contract(row,previous)
                if result["score"]>=ALERT_SCORE and symbol and not alert_already_sent(db,symbol,session_day):
                    alerts.append((row,result))
            # Persist after scoring: comparisons use the preceding snapshot from this session only.
            save_snapshot(db,frame)
            for row,result in sorted(alerts,key=lambda x:x[1]["score"],reverse=True)[:10]:
                msg=(f"OPTIONS ANOMALY | {row.get('ticker')} {row.get('option_type')}\n"
                     f"Contract: {row.get('contractSymbol')}\nExpiry: {row.get('expiry')} | Strike: {row.get('strike')}\n"
                     f"Score: {result['score']}/100\nVolume: {safe_int(row.get('volume')):,} | "
                     f"OI: {safe_int(row.get('openInterest')):,} | Vol/OI: {result['volume_oi']}x\n"
                     f"Last: ${safe_number(row.get('lastPrice')):.2f} | Est. premium: ${result['premium']:,.0f}\n"
                     f"Reasons: {', '.join(result['reasons'])}\n"
                     "Screening signal only; not proof of opening flow.")
                if DRY_RUN:
                    log.info("DRY RUN ALERT\n%s",msg)
                else:
                    send_message(TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID,msg)
                    record_alert_sent(db,str(row.get("contractSymbol")),session_day,result["score"])
    finally:
        db.close()

if __name__=="__main__":
    run()
