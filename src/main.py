import logging
import math
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import (
    WATCHLIST, MAX_EXPIRATIONS, MIN_VOLUME, ALERT_SCORE, DATABASE_PATH,
    REPORT_DIR, DRY_RUN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    EMAIL_USERNAME, EMAIL_APP_PASSWORD, EMAIL_TO, EMAIL_HOST, EMAIL_PORT,
    REQUEST_DELAY_SECONDS, MAX_DETAILED_LOG_ALERTS, MAX_EMAIL_ALERTS,
    MAX_TELEGRAM_ALERTS
)
from .providers.yahoo import fetch_chain
from .storage import connect, previous_snapshot, save_snapshot, alert_already_sent, record_alert_sent
from .scoring import score_contract, explain_contract
from .telegram import send_message
from .emailer import send_report as send_email_report
from .reporting import write_reports
from .market_hours import is_us_regular_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)
NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

def safe_number(value, default=None):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default

def safe_int(value, default=0):
    number = safe_number(value, None)
    return default if number is None else int(number)

def scalar(value):
    if value is None:
        return None
    try:
        value = value.item() if hasattr(value, "item") else value
    except Exception:
        pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        if value != value:
            return None
    except Exception:
        pass
    return value

def run():
    if not is_us_regular_session():
        log.info("Outside US regular session; skipping scan and report.")
        return

    started = datetime.now(UTC)
    session_day = datetime.now(NY).date().isoformat()
    now_label = started.strftime("%Y-%m-%d %H:%M:%S UTC")
    telegram_configured = bool(TELEGRAM_BOT_TOKEN.strip() and TELEGRAM_CHAT_ID.strip())
    email_configured = bool(EMAIL_USERNAME.strip() and EMAIL_APP_PASSWORD.strip())

    log.info("=== US OPTIONS MONITOR START ===")
    log.info("Watchlist: %s tickers | expirations per ticker: %s | alert threshold: %s/100",
             len(WATCHLIST), MAX_EXPIRATIONS, ALERT_SCORE)
    if not telegram_configured:
        log.warning("Telegram is not configured; alert summaries will not be sent to Telegram.")
    if not email_configured:
        log.warning("Email is not configured; reports will be saved as Actions artifacts only.")

    db = connect(DATABASE_PATH)
    alerts = []
    scanned_tickers = []
    no_data_tickers = []
    failed_tickers = []
    contracts_received = 0
    contracts_above_min_volume = 0
    ticker_alert_counts = {}

    try:
        for index, ticker in enumerate(WATCHLIST, start=1):
            log.info("[%s/%s] Fetching option chain: %s", index, len(WATCHLIST), ticker)
            try:
                frame = fetch_chain(ticker, MAX_EXPIRATIONS)
                if frame.empty:
                    no_data_tickers.append(ticker)
                    log.warning("%s: Yahoo Finance returned no option chain.", ticker)
                    continue

                scanned_tickers.append(ticker)
                contracts_received += len(frame)
                ticker_alerts = 0
                for _, row in frame.iterrows():
                    volume = safe_int(row.get("volume"))
                    if volume < MIN_VOLUME:
                        continue
                    contracts_above_min_volume += 1
                    contract_symbol = str(row.get("contractSymbol") or "")
                    previous = previous_snapshot(db, contract_symbol, session_day) if contract_symbol and contract_symbol != "nan" else None
                    result = score_contract(row, previous)
                    if result["score"] < ALERT_SCORE or not contract_symbol:
                        continue

                    timestamp = datetime.now(UTC).isoformat()
                    explanation = explain_contract(row, previous, result, timestamp)
                    data = {
                        "ticker": ticker,
                        "contract_symbol": contract_symbol,
                        "option_type": str(row.get("option_type") or ""),
                        "expiry": str(row.get("expiry") or ""),
                        "strike": scalar(row.get("strike")),
                        "underlying_price": scalar(row.get("underlying_price")),
                        "volume": volume,
                        "open_interest": safe_int(row.get("openInterest")),
                        "last_price": safe_number(row.get("lastPrice")),
                        "bid": safe_number(row.get("bid")),
                        "ask": safe_number(row.get("ask")),
                        "iv_pct": (safe_number(row.get("impliedVolatility"), 0) or 0) * 100
                    }
                    alerts.append({
                        "timestamp_utc": timestamp,
                        "data": data,
                        "score_data": result,
                        "explanation": explanation
                    })
                    ticker_alerts += 1

                ticker_alert_counts[ticker] = ticker_alerts
                # Preserve the current snapshot only after comparisons against the previous one.
                save_snapshot(db, frame)
                log.info("%s: %s contracts received; %s passed minimum volume; %s alerts.",
                         ticker, len(frame), sum(1 for _, r in frame.iterrows() if safe_int(r.get("volume")) >= MIN_VOLUME),
                         ticker_alerts)
            except Exception as exc:
                failed_tickers.append(ticker)
                log.exception("%s: fetch/processing failed: %s", ticker, exc)
            finally:
                if index < len(WATCHLIST) and REQUEST_DELAY_SECONDS > 0:
                    time.sleep(REQUEST_DELAY_SECONDS)
    finally:
        db.close()

    alerts.sort(key=lambda item: item["score_data"]["score"], reverse=True)
    log.info("=== DETAILED ANOMALY EXPLANATIONS: TOP %s OF %s ===",
             min(MAX_DETAILED_LOG_ALERTS, len(alerts)), len(alerts))
    for item in alerts[:MAX_DETAILED_LOG_ALERTS]:
        log.info("\n%s\n%s", item["explanation"], "-" * 100)

    finished = datetime.now(UTC)
    summary = {
        "session_day": session_day,
        "started_at": now_label,
        "finished_at": finished.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "requested_tickers": len(WATCHLIST),
        "scanned_tickers": len(scanned_tickers),
        "no_data_count": len(no_data_tickers),
        "failed_count": len(failed_tickers),
        "no_data_tickers": no_data_tickers,
        "failed_tickers": failed_tickers,
        "contracts_received": contracts_received,
        "contracts_above_min_volume": contracts_above_min_volume,
        "alerts_found": len(alerts),
        "alert_threshold": ALERT_SCORE,
        "ticker_alert_counts": ticker_alert_counts
    }

    reports = write_reports(summary, alerts, REPORT_DIR, MAX_EMAIL_ALERTS)
    log.info("=== SCAN SUMMARY ===")
    log.info("Watchlist requested: %s | scanned: %s | no data: %s | failed: %s",
             summary["requested_tickers"], summary["scanned_tickers"], summary["no_data_count"], summary["failed_count"])
    log.info("Option contracts received: %s | above volume threshold: %s | alerts >= %.0f: %s",
             contracts_received, contracts_above_min_volume, ALERT_SCORE, len(alerts))
    log.info("CSV report: %s", reports["csv"])
    log.info("HTML report: %s", reports["html"])
    log.info("Text report: %s", reports["text"])

    # One Telegram message per high-scoring contract, limited to avoid flooding the chat.
    if DRY_RUN:
        log.info("DRY_RUN=1: Telegram sending disabled.")
    elif not telegram_configured:
        log.warning("Telegram secrets missing: add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
    else:
        sent = 0
        for item in alerts[:MAX_TELEGRAM_ALERTS]:
            d = item["data"]
            s = item["score_data"]
            msg = (
                f"OPTIONS ANOMALY | {d['ticker']} {d['option_type']}\n"
                f"Contract: {d['contract_symbol']} | Expiry: {d['expiry']} | Strike: {d['strike']}\n"
                f"Score: {s['score']:.0f}/100 – {s['band']}\n"
                f"Data confidence: {s['confidence']} | Volume/OI: {s['volume_oi']}x\n"
                f"Volume: {d['volume']:,} | OI: {d['open_interest']:,}\n"
                f"Indicative premium: USD {s['premium']:,.0f}\n"
                f"Main factors: {', '.join(s['reasons'][:4])}\n"
                "Full explanation and CSV are in the emailed/Actions report. Not proof of opening flow."
            )
            try:
                send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                record_alert_sent(db=connect(DATABASE_PATH), symbol=d["contract_symbol"],
                                  session_day=session_day, score=s["score"])
                sent += 1
            except Exception:
                log.exception("Telegram send failed for %s", d["contract_symbol"])
        log.info("Telegram alerts sent: %s (limit %s).", sent, MAX_TELEGRAM_ALERTS)

    if email_configured:
        subject = f"[US Options Monitor] {len(alerts)} alerts | {session_day} | {finished.strftime('%H:%M UTC')}"
        try:
            sent = send_email_report(
                EMAIL_USERNAME, EMAIL_APP_PASSWORD, EMAIL_TO, subject,
                reports["email_text"], reports["email_html"],
                [reports["csv"], reports["html"]], EMAIL_HOST, EMAIL_PORT
            )
            log.info("Email report sent to %s: %s", EMAIL_TO, sent)
        except Exception as exc:
            log.exception("Email report could not be sent: %s", exc)
    else:
        log.warning("EMAIL_USERNAME and/or EMAIL_APP_PASSWORD missing. Report remains available as Actions artifact.")
    log.info("=== US OPTIONS MONITOR FINISHED ===")

if __name__ == "__main__":
    run()
