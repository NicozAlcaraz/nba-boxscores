# NBA Boxscores (Streamlit App)

This project is a lightweight **Streamlit web app** that displays **live and historical NBA box scores** using **ESPN’s public API endpoints**.  
It features a modern dark UI with responsive game cards, auto-refresh for live games, and detailed team stats such as FG%, 3PT%, rebounds, assists, and more.

---

## Features

- **Live box scores** — see real-time updates for ongoing NBA games  
- **Historical results** — view past games by selecting a date  
- **Team stats breakdown** — toggle to view key team performance metrics  
- **Sleek design** — custom CSS with gradient backgrounds and soft shadows  
- **Auto-refresh** — configurable timer for live updates (today’s games only)

---

## Tech Stack

- **Python 3.12+**
- **[Streamlit](https://streamlit.io/)**
- **Requests (for ESPN API calls)**  
- Optional: **streamlit-autorefresh** for timed refresh behavior

---

## Installation

Clone the repository:

```bash
git clone https://github.com/nicozalcaraz/nba-boxscores.git
cd nba-boxscores


## Create environment
python -m venv .venv
source .venv/bin/activate   # on macOS/Linux
# or
.venv\Scripts\activate      # on Windows

## Install dependencies
pip install -r requirements.txt
```

Once running, open the link in your browser:

Local: http://localhost:8501 (or whatever the commandline tells you)

Network: your LAN address (useful for mobile viewing)

---

## Usage
In the sidebar, choose:
- Mode: “Today (live)” for real-time scores, or “Pick a date” for past games
- Optional: toggle Show team stat breakdown
- Adjust Auto-refresh (sec) if in live mode
- The app will fetch and display all games for the selected date.
- For live games, the page refreshes automatically to keep data updated.

---

## ESPN Endpoints Used
Scoreboard:
- https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard

Boxscore / Summary:
- https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary

These public JSON endpoints are parsed to display live and historical stats.
