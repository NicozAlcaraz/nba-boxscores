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


def _player_table_from_competitor(comp: dict):
    """
    Build a simple player 'leaders' table for a single team competitor
    from the scoreboard JSON.

    Returns: list of rows like
    { "Player": ..., "Pos": ..., "Jersey": ..., "PTS": ..., "REB": ..., "AST": ..., "Line": ... }
    """
    if not comp:
        return []

    leaders = comp.get("leaders", []) or []
    players = {}  # athlete_id -> row dict

    def ensure_row(athlete: dict):
        aid = athlete.get("id")
        if not aid:
            return None
        if aid not in players:
            players[aid] = {
                "Player": athlete.get("displayName") or athlete.get("fullName") or "Unknown",
                "Pos": (athlete.get("position") or {}).get("abbreviation", ""),
                "Jersey": athlete.get("jersey", ""),
                "PTS": "",
                "REB": "",
                "AST": "",
                "Line": "",
            }
        return players[aid]

    for cat in leaders:
        cat_name = (cat.get("name") or "").lower()  # "points", "rebounds", "assists", "rating", etc.
        for entry in cat.get("leaders", []) or []:
            athlete = entry.get("athlete") or {}
            row = ensure_row(athlete)
            if row is None:
                continue

            value = entry.get("displayValue", "")
            if cat_name == "points":
                row["PTS"] = value
            elif cat_name == "rebounds":
                row["REB"] = value
            elif cat_name == "assists":
                row["AST"] = value
            elif cat_name == "rating":
                # e.g. "46 PTS, 8 AST"
                row["Line"] = value

    # Return rows as a list (you can sort by points if you want)
    return list(players.values())


def extract_player_tables(summary: dict):
    """
    Build per-team player stat tables from an ESPN boxscore summary.

    Returns:
        dict: {team_abbrev: [ {Player, MIN, PTS, REB, AST}, ... ], ...}
    """
    result = {}
    box = summary.get("boxscore", {})
    players_groups = box.get("players", []) or []

    for team_group in players_groups:
        team_info = team_group.get("team", {}) or {}
        abbrev = team_info.get("abbreviation")
        if not abbrev:
            continue

        statistics = team_group.get("statistics") or []
        if not statistics:
            continue

        # Use the first statistics block as the base line (usually the main box)
        base_stats = statistics[0]
        labels = base_stats.get("labels") or []
        label_index = {label: idx for idx, label in enumerate(labels)}

        def pick_stat(row_stats, label_candidates):
            for lab in label_candidates:
                idx = label_index.get(lab)
                if idx is not None and idx < len(row_stats):
                    return row_stats[idx]
            return ""

        rows = []
        # NOTE: athletes are nested under base_stats, not directly under team_group
        for athlete_entry in base_stats.get("athletes", []) or []:
            athlete = athlete_entry.get("athlete", {}) or {}
            row_stats = athlete_entry.get("stats", []) or []

            row = {
                "Player": (
                    athlete.get("displayName")
                    or athlete.get("fullName")
                    or "Unknown"
                ),
                "MIN": pick_stat(row_stats, ["MIN", "Minutes"]),
                "PTS": pick_stat(row_stats, ["PTS", "Points"]),
                "REB": pick_stat(row_stats, ["REB", "Rebounds"]),
                "AST": pick_stat(row_stats, ["AST", "Assists"]),
            }
            rows.append(row)

        result[abbrev] = rows

    return result
