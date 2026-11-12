# US Options Anomaly Monitor

Hourly options-chain screening for U.S. equities and ETFs, with detailed Polish anomaly explanations, CSV/HTML/TXT reports, Gmail email summaries and optional Telegram notifications.

## Watchlist
- 107 underlyings: original 7 symbols plus 75 additional equities and 25 additional ETFs.
- Complete list: universe.csv; configuration: config.yaml.
- The configured list is a curated watchlist, not the complete U.S. options market. Yahoo Finance may not provide a chain for every symbol and does not guarantee complete, licensed real-time coverage.
- Yahoo adapter scans up to 4 nearest expiration dates per underlying. Cboe integration is currently a placeholder requiring an authorized feed; no Cboe website scraping is performed.

## Detailed anomaly explanations
Every alert explains the contract, CALL/PUT right, expiry, strike, underlying price (if available), ITM/ATM/OTM estimate, days to expiry, session volume, previous Open Interest, Volume/OI calculation, estimated premium turnover, volume increase since the previous same-session snapshot, Implied Volatility change, bid/ask spread, points assigned to each factor, data-quality issues, and a plain-language interpretation.

The anomaly score and data confidence are independent. For example, Volume/OI of 540x with OI=1 is mathematically correct but has low reliability because the denominator is tiny. The report highlights that case.

Current score is a heuristic threshold model, not a statistical deviation from a rolling 20/60-session baseline. CALL or PUT does not identify who initiated a trade. Volume/OI is not proof of opening positions. Open Interest is normally refreshed daily. Estimated premium is volume × last price × standard 100 multiplier, not verified notional value from each execution. Sweep/aggressor detection requires trade-level data and bid/ask classification.

## Output per in-session run
- Detailed explanations for the top 40 alerts in the Actions log.
- CSV with all alerts from that scan.
- HTML report with up to 30 expanded explanations.
- Plain-text summary with up to 30 explanations.
- GitHub Actions artifact named options-scan-reports-N, retained for 30 days.
- One Gmail summary email to email@gmail.com on every in-session scan, including zero-alert runs, if Gmail SMTP secrets are set. The email includes HTML content and CSV/HTML attachments.
- Optional Telegram notifications for up to 20 top contracts, if Telegram secrets are set.

## Gmail setup
In Settings → Secrets and variables → Actions → Repository secrets, add:
- EMAIL_USERNAME = email@gmail.com
- EMAIL_APP_PASSWORD = Google App Password generated for this Gmail account

Use a Google App Password, not the normal account password. Google App Passwords require 2-Step Verification and may be unavailable for some account configurations. Recipient is configured as email@gmail.com; SMTP uses smtp.gmail.com port 587 with STARTTLS.

Optional Telegram secrets:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

If email secrets are missing, the scan still runs and the reports are uploaded as a GitHub Actions artifact. If Telegram secrets are missing, Telegram messages are skipped.

## Run and inspect
1. Open the Actions tab.
2. Run Hourly Options Scan manually, or let the weekday schedule execute.
3. Open the scan job and inspect Run scanner for the human-readable explanations.
4. Download options-scan-reports-N from the run's Artifacts section for CSV/HTML/TXT.

The scanner checks actual New York regular-session hours and exchange holidays. The broad UTC cron window accounts for daylight-saving changes.

## Local setup
Python 3.11+; install requirements.txt, copy .env.example to .env, then run python -m src.main. Use DRY_RUN=1 for local testing.

## Storage and data limitations
SQLite is persisted using GitHub Actions cache, which is best-effort and not a durable transactional database. For production history, use managed PostgreSQL or a persistent host. Yahoo Finance/yfinance is unofficial, may be rate-limited or delayed, and does not constitute a complete U.S. options feed.

Research and education only. An alert is not investment advice or a proof of opening institutional flow.
