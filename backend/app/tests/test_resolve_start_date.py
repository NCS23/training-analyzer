"""Tests für _resolve_start_date aus chat_tool_handlers."""

from datetime import date

from app.services.chat_tool_handlers import _resolve_start_date


class TestResolveStartDate:
    """Startdatum-Auflösung: Montag derselben Woche."""

    def test_no_input_returns_monday_of_current_week(self) -> None:
        # Mittwoch 2026-04-01 → Montag 2026-03-30
        wednesday = date(2026, 4, 1)
        assert _resolve_start_date(None, wednesday) == date(2026, 3, 30)

    def test_no_input_on_monday_returns_same_day(self) -> None:
        monday = date(2026, 3, 30)
        assert _resolve_start_date(None, monday) == monday

    def test_no_input_on_sunday_returns_monday_of_same_week(self) -> None:
        sunday = date(2026, 4, 5)
        assert _resolve_start_date(None, sunday) == date(2026, 3, 30)

    def test_explicit_monday_returns_same_date(self) -> None:
        today = date(2026, 3, 30)
        assert _resolve_start_date("2026-03-30", today) == date(2026, 3, 30)

    def test_explicit_wednesday_returns_monday_of_that_week(self) -> None:
        today = date(2026, 3, 30)
        assert _resolve_start_date("2026-04-01", today) == date(2026, 3, 30)

    def test_past_date_returns_monday_of_that_week(self) -> None:
        today = date(2026, 4, 15)
        # 2026-03-25 ist ein Mittwoch → Montag 2026-03-23
        assert _resolve_start_date("2026-03-25", today) == date(2026, 3, 23)

    def test_future_date_returns_monday_of_that_week(self) -> None:
        today = date(2026, 3, 30)
        # 2026-05-07 ist ein Donnerstag → Montag 2026-05-04
        assert _resolve_start_date("2026-05-07", today) == date(2026, 5, 4)

    def test_invalid_date_string_falls_back_to_current_week(self) -> None:
        wednesday = date(2026, 4, 1)
        assert _resolve_start_date("not-a-date", wednesday) == date(2026, 3, 30)

    def test_empty_string_falls_back_to_current_week(self) -> None:
        wednesday = date(2026, 4, 1)
        assert _resolve_start_date("", wednesday) == date(2026, 3, 30)

    def test_today_is_used_returns_monday_of_current_week(self) -> None:
        today = date(2026, 4, 3)  # Freitag
        result = _resolve_start_date(str(today), today)
        assert result == date(2026, 3, 30)  # Montag derselben Woche
