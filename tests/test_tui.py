"""Test Textual TUI application in headless mode using App.run_test()."""
import pytest
from strava_tui.app import StravaTuiApp
from strava_tui.ui.screens.main_screen import MainScreen
from strava_tui.ui.widgets.stat_card import StatCard


@pytest.mark.asyncio
async def test_tui_app_lifecycle():
    app = StravaTuiApp(default_mode="demo")
    async with app.run_test(size=(140, 40)) as pilot:
        # Give UI a moment to mount and load mock activities
        await pilot.pause(0.5)

        # Check that MainScreen is loaded
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Check that activities were loaded
        assert len(main_screen.all_activities_in_year) > 0

        # Change filter phrase to 'Interval' and trigger filter
        main_screen.query_one("#search-phrase").value = "Interval"
        main_screen.apply_filter()
        await pilot.pause(0.2)

        # Verify that combined distance card is updated
        km_card = main_screen.query_one("#card-km", StatCard)
        assert km_card.value_text != "0.0"
        assert main_screen.current_stats.matching_count > 0
        assert main_screen.current_stats.total_distance_km > 0

        # Test opening AuthScreen
        await pilot.click("#btn-switch-account")
        await pilot.pause(0.2)
        from strava_tui.ui.screens.auth_screen import AuthScreen
        assert isinstance(app.screen, AuthScreen)

        # Switch to Demo tab in TabbedContent and click Demo button
        auth_screen = app.screen
        from textual.widgets import TabbedContent
        auth_screen.query_one(TabbedContent).active = "tab-demo"
        await pilot.pause(0.2)
        await pilot.click("#btn-demo")
        await pilot.pause(0.5)
        assert isinstance(app.screen, MainScreen)


@pytest.mark.asyncio
async def test_activity_modal_screen():
    from strava_tui.ui.screens.activity_modal import ActivityDetailModal
    from strava_tui.data.models import Activity
    from datetime import datetime, timezone

    act = Activity(
        id="12345",
        name="Test Interval Run",
        distance_meters=10000.0,
        moving_time_seconds=3000,
        elapsed_time_seconds=3200,
        total_elevation_gain=120.0,
        sport_type="Run",
        start_date=datetime(2025, 5, 10, 8, 0, 0, tzinfo=timezone.utc),
    )
    app = StravaTuiApp(default_mode="demo")
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        app.push_screen(ActivityDetailModal(act))
        await pilot.pause(0.2)
        assert isinstance(app.screen, ActivityDetailModal)
        await pilot.click("#btn-close")
        await pilot.pause(0.2)
        assert not isinstance(app.screen, ActivityDetailModal)

