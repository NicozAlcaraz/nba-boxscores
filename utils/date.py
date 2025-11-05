from datetime import date, datetime
from zoneinfo import ZoneInfo

def get_nba_today() -> date:
    """Return 'today' in NBA/US Eastern time."""
    eastern_now = datetime.now(ZoneInfo("America/Los_Angeles"))
    return eastern_now.date()