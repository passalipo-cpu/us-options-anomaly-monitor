import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"

def _read_config():
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError:
        return {}

_FILE_CONFIG = _read_config()

def csv_list(name: str, default_items) -> list[str]:
    default = ",".join(default_items) if not isinstance(default_items, str) else default_items
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        raw = default
    return list(dict.fromkeys(item.strip().upper() for item in raw.split(",") if item.strip()))

WATCHLIST = csv_list("WATCHLIST", _FILE_CONFIG.get("watchlist", ["SPY","QQQ","IWM","AAPL","MSFT","NVDA","TSLA"]))
MAX_EXPIRATIONS = int(os.getenv("MAX_EXPIRATIONS", _FILE_CONFIG.get("max_expirations", 4)))
MIN_VOLUME = int(os.getenv("MIN_VOLUME", _FILE_CONFIG.get("min_volume", 100)))
ALERT_SCORE = float(os.getenv("ALERT_SCORE", _FILE_CONFIG.get("alert_score", 65)))
REQUEST_DELAY_SECONDS = float(os.getenv("REQUEST_DELAY_SECONDS", _FILE_CONFIG.get("request_delay_seconds", 0.35)))
MAX_DETAILED_LOG_ALERTS = int(os.getenv("MAX_DETAILED_LOG_ALERTS", _FILE_CONFIG.get("max_detailed_log_alerts", 40)))
MAX_EMAIL_ALERTS = int(os.getenv("MAX_EMAIL_ALERTS", _FILE_CONFIG.get("max_email_alerts", 30)))
MAX_TELEGRAM_ALERTS = int(os.getenv("MAX_TELEGRAM_ALERTS", _FILE_CONFIG.get("max_telegram_alerts", 20)))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/options.db")
REPORT_DIR = os.getenv("REPORT_DIR", "reports")
DRY_RUN = os.getenv("DRY_RUN", "1").lower() in {"1","true","yes"}
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "passalipo@gmail.com")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
