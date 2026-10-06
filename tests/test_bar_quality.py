from pathlib import Path

import pandas as pd

from research.bar_quality import flag_frame, summarise


def test_missing_weekday_is_flagged():
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-04"],
            "Open": [10.0, 11.0],
            "High": [10.5, 11.5],
            "Low": [9.5, 10.5],
            "Close": [10.0, 11.0],
            "AdjClose": [10.0, 11.0],
            "Volume": [100, 100],
        }
    )
    frame = flag_frame(raw, "AAPL")
    assert bool(frame.loc[pd.Timestamp("2024-01-03"), "bar_missing"])
    assert not bool(frame.loc[pd.Timestamp("2024-01-02"), "bar_missing"])
    summary = summarise(frame, "AAPL")
    assert summary["bar_missing"] == 1
    assert summary["sleeve"] == "us_equity"


def test_invalid_ohlc_and_crypto_keeps_weekend():
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-05", "2024-01-06", "2024-01-07"],
            "Open": [1.0, 1.0, 1.0],
            "High": [1.0, 0.5, 1.2],
            "Low": [1.0, 0.9, 0.9],
            "Close": [1.0, 1.0, 1.1],
            "AdjClose": [1.0, 1.0, 1.1],
            "Volume": [1, 1, 1],
        }
    )
    frame = flag_frame(raw, "BTC-USD")
    assert pd.Timestamp("2024-01-06") in frame.index
    assert pd.Timestamp("2024-01-07") in frame.index
    assert bool(frame.loc[pd.Timestamp("2024-01-06"), "invalid_ohlc"])
