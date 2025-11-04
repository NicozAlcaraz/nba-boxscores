import requests
from datetime import date, datetime
import streamlit as st
from streamlit_autorefresh import st_autorefresh

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_SUMMARY_URL = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary"


# Styling

st.set_page_config(
    page_title="NBA Box Scores (ESPN)",
    page_icon="🏀",
    layout="wide",
)

CUSTOM_CSS = """
<style>
/* Global dark-ish theme */
body, .stApp {
    background: radial-gradient(circle at top, #111827 0, #020617 55%, #000000 100%);
    color: #e5e7eb;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Remove default Streamlit header/footer */
header[data-testid="stHeader"] {
    background: transparent;
}
footer {visibility: hidden;}

/* Card look for each game */
.game-card {
    background: linear-gradient(135deg, rgba(31,41,55,0.95), rgba(15,23,42,0.98));
    border-radius: 18px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
    border: 1px solid rgba(148,163,184,0.25);
    box-shadow: 0 20px 30px rgba(0,0,0,0.45);
}

/* Title chips */
.game-meta {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
}

/* Team block */
.team-name {
    font-weight: 600;
    font-size: 1.1rem;
}
.team-score {
    font-weight: 700;
    font-size: 1.4rem;
}

/* Tag for game status */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(55,65,81,0.7);
    color: #f9fafb;
    margin-left: 0.4rem;
}

/* Live pulse */
.status-pill.live::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #ef4444;
    margin-right: 0.4rem;
    box-shadow: 0 0 0 4px rgba(239,68,68,0.35);
}

/* Finished pill */
.status-pill.final {
    background: rgba(34,197,94,0.18);
    color: #bbf7d0;
    border: 1px solid rgba(34,197,94,0.5);
}

/* Upcoming pill */
.status-pill.upcoming {
    background: rgba(59,130,246,0.16);
    color: #bfdbfe;
    border: 1px solid rgba(59,130,246,0.5);
}

/* Stat tables */
table {
    width: 100%;
    border-collapse: collapse;
}
thead tr th {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
    padding-bottom: 0.35rem;
}
tbody tr td {
    font-size: 0.86rem;
    padding: 0.2rem 0;
    border-bottom: 1px solid rgba(31,41,55,0.8);
}

/* Tiny divider */
.hr-soft {
    border: none;
    border-top: 1px solid rgba(148,163,184,0.25);
    margin: 0.7rem 0 0.5rem 0;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


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


# Sidebar

st.markdown(
    "<h1 style='margin-bottom:0.2rem;'>🏀 NBA Box Scores (ESPN)</h1>"
    "<p style='color:#9ca3af;font-size:0.85rem;margin-top:0;'>Live & historical box scores from ESPN’s public endpoints.</p>",
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### Filters")

    today = date.today()
    mode = st.radio("Mode", ["Today (live)", "Pick a date"])

    if mode == "Today (live)":
        selected_date = today
    else:
        selected_date = st.date_input("Game date", value=today)

    show_team_stats = st.checkbox("Show team stat breakdown", value=True)

    refresh_seconds = None
    if mode == "Today (live)":
        refresh_seconds = st.slider(
            "Auto-refresh (sec)",
            min_value=5,
            max_value=120,
            value=20,
            step=5,
        )

        #  Actually enable auto-refresh when on today's slate
        st_autorefresh(
            interval=refresh_seconds * 1000,  # milliseconds
            key="live_refresh",
        )


# Main content

with st.spinner("Pulling games from ESPN…"):
    try:
        scoreboard = fetch_scoreboard(selected_date)
        events = scoreboard.get("events", [])
    except Exception as e:
        st.error(f"Failed to load scoreboard: {e}")
        st.stop()

if not events:
    st.markdown(
        f"<p style='margin-top:1rem;color:#9ca3af;'>No NBA games found for "
        f"<strong>{selected_date.strftime('%B %d, %Y')}</strong>.</p>",
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown(
    f"<div style='margin-top:0.6rem;margin-bottom:0.6rem;'>Showing "
    f"<strong>{len(events)}</strong> game"
    f"{'' if len(events) == 1 else 's'} for "
    f"<strong>{selected_date.strftime('%B %d, %Y')}</strong>.</div>",
    unsafe_allow_html=True,
)

for event in events:
    event_id = event.get("id")
    name = event.get("name", "")
    away, home = get_competitors(event)
    pill_class, pill_short, pill_detail = classify_status(event)

    away_team = (away or {}).get("team", {})
    home_team = (home or {}).get("team", {})

    away_score = (away or {}).get("score")
    home_score = (home or {}).get("score")

    away_abbrev = away_team.get("abbreviation", "")
    home_abbrev = home_team.get("abbreviation", "")

    # Card wrapper
    st.markdown('<div class="game-card">', unsafe_allow_html=True)

    # Top row: game meta + status + scoreline
    col_meta, col_score = st.columns([2, 1])

    with col_meta:
        st.markdown(
            f'<div class="game-meta">{name}</div>'
            f'<div style="margin-top:0.2rem;font-size:0.8rem;color:#9ca3af;">'
            f'{pill_detail}'
            f'<span class="status-pill {pill_class}">{pill_short}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_score:
        # Away vs Home line
        st.markdown(
            "<div style='text-align:right;'>"
            f"<div class='team-name'>{away_abbrev or 'Away'} "
            f"<span class='team-score'>{away_score or '-'}</span></div>"
            f"<div class='team-name'>{home_abbrev or 'Home'} "
            f"<span class='team-score'>{home_score or '-'}</span></div>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Divider
    st.markdown('<hr class="hr-soft" />', unsafe_allow_html=True)

    # Box score / team stats
    if show_team_stats and event_id:
        try:
            summary = fetch_boxscore(event_id)
            box = summary.get("boxscore", {})
            team_entries = box.get("teams", [])

            if len(team_entries) == 2:
                away_box = extract_team_line(team_entries[0])
                home_box = extract_team_line(team_entries[1])

                c1, c2 = st.columns(2)

                def render_team_block(team_data, align_right=False):
                    align = "right" if align_right else "left"
                    st.markdown(
                        f"<div style='text-align:{align};margin-bottom:0.3rem;'>"
                        f"<span style='font-size:0.9rem;color:#9ca3af;'>"
                        f"{team_data['abbrev']}</span><br/>"
                        f"<span style='font-size:1.05rem;font-weight:600;'>{team_data['name']}</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

                    # Simple 2-column stat table
                    rows = [
                        ("FG", team_data["FG"]),
                        ("3PT", team_data["3PT"]),
                        ("FT", team_data["FT"]),
                        ("REB", team_data["REB"]),
                        ("AST", team_data["AST"]),
                        ("STL", team_data["STL"]),
                        ("BLK", team_data["BLK"]),
                        ("TO", team_data["TO"]),
                        ("PIP", team_data["PIP"]),
                        ("FBPs", team_data["FBPs"]),
                    ]
                    html_rows = "".join(
                        f"<tr><td>{label}</td><td style='text-align:right;'>{val}</td></tr>"
                        for label, val in rows if val != ""
                    )
                    table_html = (
                        "<table>"
                        "<thead><tr><th>Stat</th><th style='text-align:right;'>Value</th></tr></thead>"
                        f"<tbody>{html_rows}</tbody>"
                        "</table>"
                    )
                    st.markdown(table_html, unsafe_allow_html=True)

                with c1:
                    render_team_block(away_box, align_right=False)
                with c2:
                    render_team_block(home_box, align_right=True)

            else:
                st.caption("Team box-score data not available for this game (structure was unexpected).")

        except Exception as e:
            st.caption(f"Could not load box score for event {event_id}: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
