#!/usr/bin/env python3
"""Market calendar utilities for NSE/BSE."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from importlib.util import find_spec
from zoneinfo import ZoneInfo


def _load_calendar():
    if find_spec("pandas_market_calendars"):
        import pandas_market_calendars as mcal

        return mcal.get_calendar("NSE")
    return None


def _next_weekday(start: date) -> date:
    candidate = start
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


@dataclass
class MarketCalendarResult:
    as_of: str
    timezone: str
    is_trading_day: bool
    is_market_open: bool
    market_open: str
    market_close: str
    next_trading_day: str
    calendar_source: str


def build_calendar_result(now: datetime) -> MarketCalendarResult:
    ist = ZoneInfo("Asia/Kolkata")
    now = now.astimezone(ist)
    calendar = _load_calendar()
    market_open_time = time(9, 15)
    market_close_time = time(15, 30)

    if calendar is None:
        is_trading_day = now.weekday() < 5
        next_trading_day = _next_weekday(now.date() + timedelta(days=1))
        calendar_source = "weekend-only"
    else:
        schedule = calendar.schedule(
            start_date=now.date() - timedelta(days=5),
            end_date=now.date() + timedelta(days=10),
        )
        trading_days = set(schedule.index.date)
        is_trading_day = now.date() in trading_days
        upcoming = [d for d in schedule.index.date if d >= now.date()]
        next_trading_day = upcoming[0] if upcoming else _next_weekday(now.date())
        calendar_source = "pandas_market_calendars"

    is_market_open = is_trading_day and market_open_time <= now.time() <= market_close_time

    return MarketCalendarResult(
        as_of=now.isoformat(),
        timezone=str(ist),
        is_trading_day=is_trading_day,
        is_market_open=is_market_open,
        market_open=market_open_time.strftime("%H:%M"),
        market_close=market_close_time.strftime("%H:%M"),
        next_trading_day=next_trading_day.isoformat(),
        calendar_source=calendar_source,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate NSE/BSE market calendar status.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    parser.add_argument(
        "--as-of",
        help="ISO datetime in Asia/Kolkata. Defaults to now.",
    )
    args = parser.parse_args()

    if args.as_of:
        now = datetime.fromisoformat(args.as_of)
    else:
        now = datetime.now(tz=ZoneInfo("Asia/Kolkata"))

    result = build_calendar_result(now)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(asdict(result), handle, indent=2)


if __name__ == "__main__":
    main()
