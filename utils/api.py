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

def extract_player_tables(summary: dict):
    """
    Build per-team player stat tables from an ESPN boxscore summary.

    Returns:
        dict: {team_abbrev: [ {Player, MIN, PTS, REB, AST}, ... ], ...}
    """
    result = {}
    box = summary.get("boxscore", {})
    players_groups = box.get("players", [])

    for team_group in players_groups:
        team_info = team_group.get("team", {})
        abbrev = team_info.get("abbreviation")
        if not abbrev:
            continue

        statistics = team_group.get("statistics", [])
        if not statistics:
            continue

        # Use the first stat schema (usually the main one)
        stat_meta = statistics[0]
        labels = stat_meta.get("labels") or []
        label_index = {label: idx for idx, label in enumerate(labels)}

        def pick_stat(row_stats, label_candidates):
            for lab in label_candidates:
                idx = label_index.get(lab)
                if idx is not None and idx < len(row_stats):
                    return row_stats[idx]
            return ""

        rows = []
        for athlete_entry in team_group.get("athletes", []):
            athlete = athlete_entry.get("athlete", {})
            stat_sets = athlete_entry.get("stats", [])
            if not stat_sets:
                continue

            # Assume first stat set matches labels
            row_stats = stat_sets[0]

            row = {
                "Player": athlete.get("displayName", "Unknown"),
                "MIN": pick_stat(row_stats, ["MIN", "Minutes"]),
                "PTS": pick_stat(row_stats, ["PTS", "Points"]),
                "REB": pick_stat(row_stats, ["REB", "Rebounds"]),
                "AST": pick_stat(row_stats, ["AST", "Assists"]),
            }
            rows.append(row)

        result[abbrev] = rows

    return result
