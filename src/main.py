import logging
from .config import WATCHLIST,MAX_EXPIRATIONS,MIN_VOLUME,ALERT_SCORE,DATABASE_PATH,DRY_RUN,TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID
from .providers.yahoo import fetch_chain
from .storage import connect,previous_snapshot,save_snapshot
from .scoring import score_contract
from .telegram import send_message
from .market_hours import is_us_regular_session

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger(__name__)

def run():
    if not is_us_regular_session():
        log.info('Outside US regular session; skipping scan.'); return
    db=connect(DATABASE_PATH)
    try:
        for ticker in WATCHLIST:
            log.info('Fetching %s',ticker)
            frame=fetch_chain(ticker,MAX_EXPIRATIONS)
            if frame.empty:
                log.warning('No options data for %s',ticker); continue
            alerts=[]
            for _,row in frame.iterrows():
                try: volume=int(row.get('volume') or 0)
                except (TypeError,ValueError): volume=0
                if volume<MIN_VOLUME: continue
                symbol=str(row.get('contractSymbol') or '')
                result=score_contract(row,previous_snapshot(db,symbol) if symbol else None)
                if result['score']>=ALERT_SCORE: alerts.append((row,result))
            save_snapshot(db,frame)
            for row,result in sorted(alerts,key=lambda x:x[1]['score'],reverse=True)[:10]:
                msg=(f"OPTIONS ANOMALY | {row.get('ticker')} {row.get('option_type')}\n"
                     f"Contract: {row.get('contractSymbol')}\nExpiry: {row.get('expiry')} | Strike: {row.get('strike')}\n"
                     f"Score: {result['score']}/100\nVolume: {int(row.get('volume') or 0):,} | OI: {int(row.get('openInterest') or 0):,} | Vol/OI: {result['volume_oi']}x\n"
                     f"Last: ${float(row.get('lastPrice') or 0):.2f} | Est. premium: ${result['premium']:,.0f}\n"
                     f"Reasons: {', '.join(result['reasons'])}\nScreening signal only; not proof of opening flow.")
                if DRY_RUN: log.info('DRY RUN ALERT\n%s',msg)
                else: send_message(TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID,msg)
    finally: db.close()

if __name__=='__main__': run()
