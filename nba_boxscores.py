from datetime import date, datetime
from utils.css import CUSTOM_CSS
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.api import fetch_scoreboard, fetch_boxscore, extract_team_line, classify_status, get_competitors, extract_player_tables
from utils.date import get_nba_today
from zoneinfo import ZoneInfo

# Styling

st.set_page_config(
    page_title="NBA Box Scores (ESPN)",
    page_icon="🏀",
    layout="wide",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Sidebar

st.markdown(
    "<h1 style='margin-bottom:0.2rem;'>🏀 NBA Box Scores (ESPN)</h1>"
    "<p style='color:#9ca3af;font-size:0.85rem;margin-top:0;'>Live & historical box scores of NBA.</p>",
    unsafe_allow_html=True,
)

# Current US Eastern time banner
eastern_time = datetime.now(ZoneInfo("America/New_York"))
st.markdown(
    f"""
    <div class="est-banner">
        <div class="est-label">Current NBA Time · US Eastern</div>
        <div class="est-time">{eastern_time.strftime('%I:%M %p')}</div>
        <div class="est-date">{eastern_time.strftime('%A · %B %d, %Y')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### Filters")

    # Use whatever logic you have for 'today' (local or US Eastern)
    today = get_nba_today()
    mode = st.radio("Mode", ["Today (live)", "Pick a date"])

    if mode == "Today (live)":
        selected_date = today
    else:
        selected_date = st.date_input("Game date", value=today)

    show_team_stats = st.checkbox("Show team stat breakdown", value=True)

    # ---- Team filter (focus on specific teams) ----
    team_options = []
    try:
        # Use cached scoreboard to build list of teams for this date
        sb_preview = fetch_scoreboard(selected_date)
        preview_events = sb_preview.get("events", [])
        team_abbrevs = set()

        for ev in preview_events:
            away, home = get_competitors(ev)
            for comp in (away, home):
                team = (comp or {}).get("team", {})
                abbr = team.get("abbreviation")
                if abbr:
                    team_abbrevs.add(abbr)

        team_options = sorted(team_abbrevs)
    except Exception:
        team_options = []

    focus_teams = st.multiselect(
        "Focus on team(s)",
        options=team_options,
        help="Only show games where at least one selected team is playing.",
    )

    # ---- Auto-refresh for live mode ----
    refresh_seconds = None
    if mode == "Today (live)":
        refresh_seconds = st.slider(
            "Auto-refresh (sec)",
            min_value=5,
            max_value=120,
            value=20,
            step=5,
        )

        # Actually enable auto-refresh when on today's slate
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

    if focus_teams:
        if away_abbrev not in focus_teams and home_abbrev not in focus_teams:
            continue


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
    if event_id:
        try:
            summary = fetch_boxscore(event_id)
            box = summary.get("boxscore", {})
            team_entries = box.get("teams", [])

            # ── Team stats (your existing behavior, guarded by show_team_stats) ──
            if show_team_stats:
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

            # ── Player stats (new) ──
            player_tables = extract_player_tables(summary)

            with st.expander("Show player stats"):
                cpa, cph = st.columns(2)

                with cpa:
                    st.markdown(f"**{away_abbrev} Players**")
                    away_players = player_tables.get(away_abbrev, [])
                    if away_players:
                        st.table(away_players)
                    else:
                        st.caption("No player stats available.")

                with cph:
                    st.markdown(f"**{home_abbrev} Players**")
                    home_players = player_tables.get(home_abbrev, [])
                    if home_players:
                        st.table(home_players)
                    else:
                        st.caption("No player stats available.")

        except Exception as e:
            st.caption(f"Could not load box score for event {event_id}: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

