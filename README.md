# 🚴 Strava Training Kilometers Analytics (TUI & Flashy HTML Export)

A modern, responsive Terminal User Interface (TUI) application for Linux designed to analyze Strava training activities, calculate combined kilometers for specific workout name phrases over a given year, present rich text analytics in your terminal, and export interactive, flashy HTML/JavaScript dashboard reports.

---

## ✨ Features

- **Flexible Strava Authentication**:
  - **Official Strava API (OAuth 2.0)**: Automatic local callback receiver (`http://localhost:8000/callback`) and 1-click browser authorization. Includes automatic token refresh.
  - **Direct Access Token**: Paste your personal access token or refresh token directly.
  - **Web Session Login**: Sign in with Strava email/username and password.
  - **Demo / Sample Mode**: Realistic full-year dataset (cycling, running, swimming, workouts) for offline testing and immediate evaluation.
- **Phrase Filtering & Distance Summation**:
  - Filter training sessions containing specific phrases in their title (e.g. `Interval`, `Commute`, `Long Run`, `Tempo`, `Race`).
  - Compute total combined kilometers for any selected year (e.g. 2026, 2025, 2024).
  - Filter by sport type (`All`, `Run`, `Ride`, `VirtualRide`, `Swim`, `Hike`, `Workout`).
- **Comprehensive Textual Analytics**:
  - **Hero Metric**: Large Combined Distance display in bold Strava orange (`#FC4C02`).
  - **KPI Cards**: Matching activities count, total moving time, elevation gain, average speed/pace.
  - **Terminal Bar Chart**: Monthly kilometers progression rendered with Unicode bar blocks directly in the terminal.
  - **Sport Breakdown Table**: Distance and elevation distribution across disciplines.
  - **Interactive DataTable**: Browse, scroll, and select activities to open the telemetry modal with a button to view directly on Strava.
- **Flashy HTML & JavaScript Report Export**:
  - Standalone, dark-themed responsive dashboard.
  - **Animated KPI Counters**: Dynamic count-up animation upon page load.
  - **Celebration Confetti**: Festive fireworks animation (`canvas-confetti`).
  - **Interactive Charts (Chart.js)**: Monthly kilometers bar chart, cumulative milestone growth curve, and sport breakdown doughnut chart.
  - **Live Search & Filter Table**: Filter activities on-the-fly, sort by any column, and filter by sport pills.
  - **Browser Actions**: "Download as CSV", "Print / Save as PDF", and clickable Strava links.

---

## 🚀 Quick Start

### 1. Launch the Application

On any new Linux machine, simply clone the repo and run:

```bash
# Using the launcher script (automatically creates .venv and installs dependencies on first run):
./run.sh

# Or directly with python3 (also auto-bootstraps environment if needed):
python3 main.py
```

### 2. Immediate Demo Mode (No Strava Account Needed)

To explore all features right away with realistic sample data:

```bash
./run.sh --demo
```

### 3. Non-Interactive CLI Mode (Headless Report)

Generate a text summary and a flashy HTML report directly from the command line:

```bash
./run.sh --demo --year 2025 --phrase "Interval" --export my_report.html
```

---

## 🔑 Authentication Guide

When launching the TUI, if no active credentials exist, the **Authentication Modal** will appear:

### Option 1: Official Strava API (Recommended)
1. Visit [strava.com/settings/api](https://www.strava.com/settings/api) (free for all Strava accounts).
2. Create an API application:
   - **Application Name**: My Training Analytics
   - **Website**: `http://localhost`
   - **Authorization Callback Domain**: `localhost`
3. Enter your **Client ID** and **Client Secret** into the app.
4. Click **"Connect with Strava"**:
   - The app spins up a local background HTTP server and opens your browser.
   - Click "Authorize" on Strava.
   - The token is captured automatically and saved locally (`~/.config/strava_tui/credentials.json`) with `0600` permissions.

### Option 2: Direct Token
Paste your existing Strava `access_token` into the input field and click **"Connect with Token"**.

### Option 3: Username & Password
Enter your Strava email and password. The app will submit a session login to Strava and store the authenticated session cookies.

### Option 4: Demo Mode
Click **"Launch in Demo Mode"** to load realistic sample activities for offline exploration.

---

## ⌨️ Hotkeys & Navigation

| Key | Action |
|:---:|:---|
| <kbd>q</kbd> | Quit application |
| <kbd>e</kbd> | Export flashy HTML dashboard |
| <kbd>o</kbd> | Open exported HTML report in default browser |
| <kbd>r</kbd> | Re-fetch / refresh data from Strava |
| <kbd>a</kbd> | Switch account or re-authenticate |
| <kbd>t</kbd> | Toggle light / dark theme |
| <kbd>Enter</kbd> | View details of selected activity in the table |

---

## 🧪 Running Automated Tests

All tests are implemented using `pytest` and `pytest-asyncio`:

```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

---

## 📁 Project Structure

```
├── strava_tui/
│   ├── auth/
│   │   ├── api_oauth.py       # OAuth2 callback receiver and token refresher
│   │   ├── credentials.py     # Secure credentials storage (~/.config/strava_tui/)
│   │   └── web_session.py     # Username/password session authentication
│   ├── client/
│   │   ├── base.py            # Abstract BaseStravaClient
│   │   ├── api_client.py      # Official Strava v3 REST API client with caching
│   │   ├── web_client.py      # Session-based activity client
│   │   └── mock_client.py     # Realistic mock data generator for demo/offline
│   ├── data/
│   │   ├── models.py          # Activity, AthleteProfile, AggregatedStats models
│   │   └── analyzer.py        # Phrase filter, year filter, kilometer summation
│   ├── export/
│   │   └── html_exporter.py   # Flashy HTML dashboard generator with JS charts & confetti
│   ├── ui/
│   │   ├── screens/
│   │   │   ├── auth_screen.py # Interactive authentication modal screen
│   │   │   ├── main_screen.py # Main dashboard screen (filters, KPIs, charts, table)
│   │   │   └── activity_modal.py # Activity telemetry inspection dialog
│   │   └── widgets/
│   │       ├── ascii_chart.py # Monthly Unicode bar chart and sport table
│   │       └── stat_card.py   # Metric cards widget
│   └── app.py                 # Main Textual App class
├── tests/                     # Comprehensive unit & integration tests
├── main.py                    # Application entry point CLI
├── run.sh                     # Bash launcher
└── requirements.txt           # Project dependencies
```
