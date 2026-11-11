import os
from dotenv import load_dotenv

load_dotenv()

def csv_list(name: str, default: str) -> list[str]:
    return [x.strip().upper() for x in os.getenv(name, default).split(',') if x.strip()]

WATCHLIST = csv_list('WATCHLIST', 'SPY,QQQ,IWM,AAPL,MSFT,NVDA,TSLA')
MAX_EXPIRATIONS = int(os.getenv('MAX_EXPIRATIONS', '4'))
MIN_VOLUME = int(os.getenv('MIN_VOLUME', '100'))
ALERT_SCORE = float(os.getenv('ALERT_SCORE', '65'))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/options.db')
DRY_RUN = os.getenv('DRY_RUN', '1').lower() in {'1','true','yes'}
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
