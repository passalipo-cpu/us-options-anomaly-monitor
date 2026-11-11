from datetime import datetime
from zoneinfo import ZoneInfo
import exchange_calendars as xcals

def is_us_regular_session(now_utc=None):
    now=(now_utc or datetime.now(ZoneInfo('UTC'))).astimezone(ZoneInfo('America/New_York'))
    cal=xcals.get_calendar('XNYS')
    try:
        session=cal.date_to_session(now.date(),direction='none')
        op=cal.session_open(session).to_pydatetime().astimezone(ZoneInfo('America/New_York'))
        cl=cal.session_close(session).to_pydatetime().astimezone(ZoneInfo('America/New_York'))
        return op <= now <= cl
    except Exception:
        return False
