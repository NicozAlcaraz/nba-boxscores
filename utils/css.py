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