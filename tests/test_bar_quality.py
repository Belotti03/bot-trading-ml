import pandas as pd

from research.bar_quality import flag_frame, summarise
from research.calendars import expected_index, nyse_sessions


def _ohlc(dates, **extra):
    n = len(dates)
    payload = {
        "Date": dates,
        "Open": [10.0] * n,
        "High": [10.5] * n,
        "Low": [9.5] * n,
        "Close": [10.0] * n,
        "AdjClose": [10.0] * n,
        "Volume": [100] * n,
    }
    payload.update(extra)
    return pd.DataFrame(payload)


def test_missing_weekday_is_flagged():
    raw = _ohlc(["2024-01-02", "2024-01-04"])
    frame = flag_frame(raw, "AAPL")
    assert bool(frame.loc[pd.Timestamp("2024-01-03"), "bar_missing"])
    assert not bool(frame.loc[pd.Timestamp("2024-01-02"), "bar_missing"])
    summary = summarise(frame, "AAPL")
    assert summary["bar_missing"] == 1
    assert summary["sleeve"] == "us_equity"


def test_invalid_ohlc_and_crypto_keeps_weekend():
    raw = _ohlc(
        ["2024-01-05", "2024-01-06", "2024-01-07"],
        High=[1.0, 0.5, 1.2],
        Low=[1.0, 0.9, 0.9],
        Close=[1.0, 1.0, 1.1],
        AdjClose=[1.0, 1.0, 1.1],
        Open=[1.0, 1.0, 1.0],
        Volume=[1, 1, 1],
    )
    frame = flag_frame(raw, "BTC-USD")
    assert pd.Timestamp("2024-01-06") in frame.index
    assert pd.Timestamp("2024-01-07") in frame.index
    assert bool(frame.loc[pd.Timestamp("2024-01-06"), "invalid_ohlc"])


def test_thanksgiving_is_not_a_missing_bar():
    raw = _ohlc(["2024-11-27", "2024-11-29"])
    frame = flag_frame(raw, "AAPL")
    assert pd.Timestamp("2024-11-28") not in frame.index
    assert summarise(frame, "AAPL")["bar_missing"] == 0


def test_good_friday_and_mlk_excluded():
    sessions = nyse_sessions("2024-01-12", "2024-03-29")
    assert pd.Timestamp("2024-01-15") not in sessions
    assert pd.Timestamp("2024-03-29") not in sessions
    assert pd.Timestamp("2024-01-16") in sessions
    assert pd.Timestamp("2024-03-28") in sessions


def test_juneteenth_observed_2022():
    sessions = nyse_sessions("2022-06-17", "2022-06-21")
    assert pd.Timestamp("2022-06-20") not in sessions
    assert pd.Timestamp("2022-06-21") in sessions


def test_sandy_extra_closure():
    sessions = nyse_sessions("2012-10-26", "2012-10-31")
    assert pd.Timestamp("2012-10-29") not in sessions
    assert pd.Timestamp("2012-10-30") not in sessions
    assert pd.Timestamp("2012-10-31") in sessions


def test_carter_mourning_extra_closure():
    sessions = nyse_sessions("2025-01-08", "2025-01-10")
    assert pd.Timestamp("2025-01-09") not in sessions
    assert pd.Timestamp("2025-01-08") in sessions
    assert pd.Timestamp("2025-01-10") in sessions


def test_crypto_keeps_holiday_weekday():
    idx = expected_index(pd.DatetimeIndex(["2024-11-27", "2024-11-29"]), "BTC-USD")
    assert pd.Timestamp("2024-11-28") in idx
