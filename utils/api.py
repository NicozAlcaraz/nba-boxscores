from datetime import date
import requests
import streamlit as st


ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_SUMMARY_URL = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary"

# API utils

@st.cache_data(ttl=15, show_spinner=False)
def fetch_scoreboard(selected_date: date):
    """Fetch ESPN scoreboard json for a given date."""
    params = {"dates": selected_date.strftime("%Y%m%d")}
    resp = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=15, show_spinner=False)
def fetch_boxscore(event_id: str):
    """Fetch ESPN summary/box score json for a given event id."""
    params = {
        "event": event_id,
        "region": "us",
        "lang": "en",
        "contentorigin": "espn",
    }
    resp = requests.get(ESPN_SUMMARY_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def extract_team_line(team_entry: dict) -> dict:
    """
    From boxscore['teams'][i] entry, grab team info and some key stats.
    """
    team_info = team_entry.get("team", {})
    stats = {s.get("label", s.get("name", "")): s.get("displayValue", "")
             for s in team_entry.get("statistics", [])}

    return {
        "name": team_info.get("shortDisplayName") or team_info.get("displayName"),
        "abbrev": team_info.get("abbreviation"),
        "logo": team_info.get("logo"),
        "color": f"#{team_info.get('color')}" if team_info.get("color") else None,
        "FG": stats.get("FG", ""),
        "3PT": stats.get("3PT", ""),
        "FT": stats.get("FT", ""),
        "REB": stats.get("Rebounds", ""),
        "AST": stats.get("Assists", ""),
        "STL": stats.get("Steals", ""),
        "BLK": stats.get("Blocks", ""),
        "TO": stats.get("Turnovers", ""),
        "PIP": stats.get("Points in Paint", ""),
        "FBPs": stats.get("Fast Break Points", ""),
    }


def classify_status(event: dict):
    """
    Map ESPN event status -> (pill_class, short_text, detail_text).
    """
    status = event.get("status", {})
    s_type = status.get("type", {})
    state = s_type.get("state", "").lower()  # pre / in / post
    detail = s_type.get("shortDetail") or s_type.get("detail") or s_type.get("description") or ""

    if state == "in":
        pill_class = "live"
        short = "LIVE"
    elif state == "post":
        pill_class = "final"
        short = "Final"
    else:
        pill_class = "upcoming"
        short = "Upcoming"

    return pill_class, short, detail


def get_competitors(event: dict):
    """Return (away, home) competitor objects from an event."""
    comp = (event.get("competitions") or [{}])[0]
    competitors = comp.get("competitors") or []

    home = None
    away = None
    for c in competitors:
        if c.get("homeAway") == "home":
            home = c
        else:
            away = c
    return away, home
