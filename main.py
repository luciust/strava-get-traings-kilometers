#!/usr/bin/env python3
"""
Strava Training Kilometers Analytics TUI
Interactive Terminal UI to calculate combined kilometers of trainings matching a specific phrase in a year,
with flashy HTML & JavaScript report generation.
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def ensure_dependencies():
    """Verify that dependencies are met; auto-bootstrap .venv if running with clean python3."""
    try:
        import textual
        import rich
        import requests
        import aiohttp
        import jinja2
        return
    except ImportError:
        pass

    script_dir = Path(__file__).parent.resolve()
    venv_dir = script_dir / ".venv"
    venv_python = venv_dir / "bin" / "python3"
    req_file = script_dir / "requirements.txt"

    # Check if we are already inside an active venv but missing packages
    is_in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if is_in_venv:
        print("📦 Installing required dependencies into current environment...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        return

    # Check if .venv already exists
    if venv_python.exists():
        try:
            subprocess.check_call(
                [str(venv_python), "-c", "import textual, rich, requests, aiohttp, jinja2"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            print("📦 Installing required dependencies into .venv...")
            subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", str(req_file)])
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

    # .venv does not exist: create it and install requirements
    print("📦 First run detected: Setting up virtual environment (.venv) and installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", str(req_file)])
        print("✅ Environment ready. Launching application...\n")
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except Exception as e:
        print(f"⚠️  Could not auto-create virtual environment: {e}", file=sys.stderr)
        print("Try running via launcher: ./run.sh", file=sys.stderr)
        print("Or install manually: pip3 install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


# Ensure all required packages are present before importing application modules
ensure_dependencies()

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from strava_tui.app import StravaTuiApp
from strava_tui.auth.credentials import CredentialsManager
from strava_tui.client.api_client import StravaApiClient
from strava_tui.client.mock_client import MockStravaClient
from strava_tui.client.web_client import StravaWebClient
from strava_tui.data.analyzer import ActivityAnalyzer
from strava_tui.export.html_exporter import HtmlExporter


def main():
    parser = argparse.ArgumentParser(
        description="Strava Training Kilometers Analytics TUI & HTML Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive TUI:
  python3 main.py

  # Launch interactive TUI in Demo Mode (sample data):
  python3 main.py --demo

  # Non-interactive CLI report & export:
  python3 main.py --year 2025 --phrase "Interval" --export report.html --demo
        """,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with realistic sample activities",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year to filter activities (e.g. 2025)",
    )
    parser.add_argument(
        "--phrase",
        type=str,
        default="",
        help="Phrase in training name to search and sum kilometers for",
    )
    parser.add_argument(
        "--sport",
        type=str,
        default=None,
        help="Filter by sport type (e.g. Run, Ride, Swim)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        metavar="FILE",
        help="Export flashy HTML report to FILE and output text summary without launching TUI",
    )

    args = parser.parse_args()

    # If --export is specified, run in headless CLI mode
    if args.export:
        run_headless(args)
        return

    # Interactive TUI mode
    default_mode = "demo" if args.demo else None
    app = StravaTuiApp(default_mode=default_mode)
    app.run()


def run_headless(args):
    """Run in non-interactive terminal mode: compute totals and export HTML."""
    year = args.year or datetime.now().year
    phrase = args.phrase or ""
    sport = args.sport

    creds_mgr = CredentialsManager()
    if args.demo:
        client = MockStravaClient()
    else:
        auth_mode = creds_mgr.get_auth_mode()
        if auth_mode == "api":
            client = StravaApiClient(creds_mgr)
        elif auth_mode == "session":
            client = StravaWebClient(creds_mgr)
        else:
            print("No Strava credentials configured. Use --demo or run without --export to log in via TUI.")
            sys.exit(1)

    athlete = client.get_athlete()
    print(f"Athlete: {athlete.full_name} ({athlete.auth_mode})")
    print(f"Fetching activities for year {year}...")

    activities = client.get_activities_for_year(year)
    stats = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=year,
        phrase=phrase,
        sport_type=sport,
    )

    print("\n" + "=" * 55)
    print(f" STRAVA TRAINING RESULTS FOR {year}")
    print(f" Search Phrase: '{phrase or '(all)'}'")
    print("=" * 55)
    print(f" Total Activities in Year: {stats.total_activities_in_year}")
    print(f" Matching Activities:     {stats.matching_count}")
    print(f" Combined Distance:       {stats.total_distance_km:,.2f} km")
    print(f" Total Moving Time:       {stats.total_moving_time_formatted}")
    print(f" Total Elevation Gain:    {stats.total_elevation_gain_m:,.1f} m")
    print(f" Average Distance:        {stats.avg_distance_km:,.2f} km")
    print(f" Average Speed:           {stats.avg_speed_kmh} km/h")
    print("=" * 55)

    print("\nMonthly Breakdown:")
    for m in stats.monthly_breakdown:
        bar = "█" * int(m.distance_km / max(1, stats.total_distance_km) * 30)
        print(f"  {m.month_name}: {m.distance_km:6.1f} km ({m.count:2d} workouts) {bar}")

    export_path = Path(args.export)
    HtmlExporter.export(stats, athlete, export_path)
    print(f"\n[+] Flashy HTML Report exported to: {export_path.resolve()}")


if __name__ == "__main__":
    main()
