"""D16 price fields. Research-only; not wired to V1.

AdjClose: signals and performance. Close/Open: execution. auto_adjust
is never implicit because these series come from the snapshot.
"""

from __future__ import annotations

import pandas as pd


def signal_return(adj_close: pd.Series) -> pd.Series:
    return pd.to_numeric(adj_close, errors="coerce").pct_change(fill_method=None)


def next_open_fill(open_: pd.Series) -> pd.Series:
    """Fill for a decision on bar t is the next session's unadjusted Open."""
    return pd.to_numeric(open_, errors="coerce").shift(-1)


def attach_price_fields(frame: pd.DataFrame) -> pd.DataFrame:
    if "AdjClose" not in frame.columns or "Close" not in frame.columns:
        raise ValueError("D16 requires both Close and AdjClose")
    if "Open" not in frame.columns:
        raise ValueError("D18 next-open fill requires Open")
    out = frame.copy()
    out["signal_return"] = signal_return(out["AdjClose"])
    out["execution_close"] = pd.to_numeric(out["Close"], errors="coerce")
    out["fill_next_open"] = next_open_fill(out["Open"])
    return out
