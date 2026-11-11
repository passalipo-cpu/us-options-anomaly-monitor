# US Options Anomaly Monitor

Hourly options-chain anomaly monitor with Telegram alerts.

## MVP scope
- Python 3.11+
- Yahoo Finance adapter for a configurable ticker watchlist (unofficial, best-effort; not full-market coverage)
- Cboe adapter placeholder until an authorized feed/API is configured
- SQLite history
- Heuristic anomaly score (0-100): volume/OI, contract volume, premium turnover, IV movement, quote spread
- Telegram notifications
- GitHub Actions hourly scheduler

> **Coverage limitation:** This MVP does not scan every US-listed option. A genuine US-wide scan requires an authoritative full option symbol universe and appropriately licensed options data. Yahoo Finance/yfinance is not a guaranteed complete market feed. Cboe access may require commercial entitlement. Alerts are not investment advice or proof of opening flow.

## Setup
1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and enter Telegram credentials, or keep dry-run enabled.
4. Configure `WATCHLIST` or edit `config.yaml`.
5. Run: `python -m src.main`.

## GitHub Actions secrets
In **Settings → Secrets and variables → Actions → Repository secrets**, add `TELEGRAM_BOT_TOKEN` (the token issued by BotFather) and `TELEGRAM_CHAT_ID` (the destination chat ID). Use repository secrets, not Environment secrets, unless the workflow is explicitly assigned to that environment. If either secret is missing, the scanner will still run and write alert details to the Actions log, but it will not send Telegram messages. Enable Actions and run **Hourly Options Scan** manually. The schedule is hourly in a UTC window that covers the New York regular trading session across daylight-saving changes; exchange holidays and times outside 09:30-16:00 New York time are skipped.

## Environment
`WATCHLIST` (default SPY,QQQ,IWM,AAPL,MSFT,NVDA,TSLA), `MAX_EXPIRATIONS` (4), `MIN_VOLUME` (100), `ALERT_SCORE` (65), `DATABASE_PATH` (data/options.db), `DRY_RUN` (1).

## Interpretation and limitations
- Open interest normally updates daily, not hourly.
- Yahoo volume is generally cumulative within the trading session; comparisons are reset at the New York trading-day boundary.
- Volume/OI is a screening metric, not evidence that trades opened new positions.
- Sweep/aggressor detection requires trade-level prints and reliable bid/ask classification.
- GitHub runners are ephemeral. SQLite Actions cache is best-effort, not durable transactional storage. Use managed PostgreSQL or a persistent host for production history.

For research/education only. Validate data quality, entitlements, and licensing before production use.
