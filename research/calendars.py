"""Expected session calendars for Branch B. Research-only; no extra deps.

Equity/ETF sessions follow a frozen NYSE-like holiday set plus a frozen
list of extra full-session closures. Crypto sessions are every calendar
day. Half-day sessions still produce a daily bar, so they stay in the
expected index.
"""

from __future__ import annotations

import pandas as pd
from pandas import DateOffset
from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    MO,
    USLaborDay,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
)

CRYPTO = {"BTC-USD", "ETH-USD"}

# Full-session NYSE closures that are not regular holidays.
# Dates are inclusive session dates. Half-days are omitted on purpose.
EXTRA_CLOSED = frozenset(
    pd.Timestamp(d)
    for d in (
        "1985-09-27",  # Hurricane Gloria
        "1994-04-27",  # Nixon funeral
        "2001-09-11",  # 9/11
        "2001-09-12",
        "2001-09-13",
        "2001-09-14",
        "2004-06-11",  # Reagan funeral
        "2007-01-02",  # Ford funeral
        "2012-10-29",  # Hurricane Sandy
        "2012-10-30",
        "2018-12-05",  # George H.W. Bush funeral
        "2025-01-09",  # Jimmy Carter national day of mourning
    )
)


class NYSEHolidayCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("NewYearsDay", month=1, day=1, observance=nearest_workday),
        Holiday(
            "MLK",
            month=1,
            day=1,
            offset=DateOffset(weekday=MO(3)),
            start_date=pd.Timestamp("1998-01-01"),
        ),
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday(
            "Juneteenth",
            month=6,
            day=19,
            start_date=pd.Timestamp("2022-01-01"),
            observance=nearest_workday,
        ),
        Holiday("IndependenceDay", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
    ]


def nyse_sessions(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    start = pd.Timestamp(start).normalize()
    end = pd.Timestamp(end).normalize()
    holidays = NYSEHolidayCalendar().holidays(start, end)
    closed = set(pd.DatetimeIndex(holidays).normalize()) | {
        d for d in EXTRA_CLOSED if start <= d <= end
    }
    bdays = pd.bdate_range(start, end)
    return bdays[~bdays.isin(closed)]


def expected_index(dates: pd.DatetimeIndex, ticker: str) -> pd.DatetimeIndex:
    start, end = dates.min(), dates.max()
    if ticker in CRYPTO:
        return pd.date_range(start, end, freq="D")
    return nyse_sessions(start, end)
