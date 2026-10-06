"""Bar quality flags on an immutable snapshot. Research-only; not wired to V1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.yahoo_snapshot import TICKERS

CRYPTO = {"BTC-USD", "ETH-USD"}
BLOCKING = (
    "bar_missing",
    "invalid_ohlc",
    "volume_suspect",
)


def sleeve(ticker: str) -> str:
    if ticker in CRYPTO:
        return "crypto"
    if ticker in {"QQQ", "GLD"}:
        return "etf"
    return "us_equity"


def expected_index(dates: pd.DatetimeIndex, ticker: str) -> pd.DatetimeIndex:
    start, end = dates.min(), dates.max()
    if ticker in CRYPTO:
        return pd.date_range(start, end, freq="D")
    return pd.bdate_range(start, end)


def flag_frame(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    raw = raw.copy()
    raw["Date"] = pd.to_datetime(raw["Date"])
    raw = raw.drop_duplicates(subset=["Date"], keep="last")
    raw = raw.set_index("Date").sort_index()
    calendar = expected_index(raw.index, ticker)
    frame = raw.reindex(calendar)
    close = pd.to_numeric(frame["Close"], errors="coerce")
    high = pd.to_numeric(frame["High"], errors="coerce")
    low = pd.to_numeric(frame["Low"], errors="coerce")
    open_ = pd.to_numeric(frame["Open"], errors="coerce")
    volume = pd.to_numeric(frame["Volume"], errors="coerce")

    frame["bar_missing"] = close.isna()
    invalid = (
        (high < low)
        | (close <= 0)
        | (open_ <= 0)
        | (high <= 0)
        | (low <= 0)
    )
    frame["invalid_ohlc"] = invalid.fillna(False) & ~frame["bar_missing"]
    frame["volume_suspect"] = (volume.isna() | (volume <= 0)) & ~frame["bar_missing"]
    frame["corporate_action"] = False
    if "AdjClose" in frame.columns:
        adj = pd.to_numeric(frame["AdjClose"], errors="coerce")
        frame["corporate_action"] = (
            close.notna()
            & adj.notna()
            & (np.abs(adj - close) > 1e-12)
        )
    ret_none = close.pct_change(fill_method=None)
    frame["return_blocked"] = frame["bar_missing"] | frame["invalid_ohlc"]
    frame["return_adj"] = np.where(frame["return_blocked"], np.nan, ret_none)
    return frame


def summarise(frame: pd.DataFrame, ticker: str) -> dict:
    n = int(len(frame))
    missing = int(frame["bar_missing"].sum())
    invalid = int(frame["invalid_ohlc"].sum())
    vol = int(frame["volume_suspect"].sum())
    corp = int(frame["corporate_action"].sum())
    present = n - missing
    return {
        "ticker": ticker,
        "sleeve": sleeve(ticker),
        "calendar_note": (
            "all calendar days" if ticker in CRYPTO else "weekdays only; holidays not yet excluded"
        ),
        "calendar_rows": n,
        "bars_present": present,
        "bar_missing": missing,
        "invalid_ohlc": invalid,
        "volume_suspect": vol,
        "corporate_action_annotative": corp,
        "returns_finite": int(np.isfinite(frame["return_adj"]).sum()),
    }


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def run_snapshot(snapshot_dir: Path) -> dict:
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for ticker in TICKERS:
        meta = manifest["tickers"][ticker]
        frame = flag_frame(load_csv(snapshot_dir / meta["path"]), ticker)
        rows.append(summarise(frame, ticker))
    report = {
        "snapshot_id": manifest["snapshot_id"],
        "calendar_limitation": (
            "US equity/ETF calendar is weekdays only. Exchange holidays "
            "are not yet in the expected index (0B incomplete)."
        ),
        "tickers": rows,
    }
    out = snapshot_dir / "quality_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir")
    args = parser.parse_args(argv)
    report = run_snapshot(Path(args.snapshot_dir))
    missing = sum(t["bar_missing"] for t in report["tickers"])
    print(f"WROTE quality_summary.json missing_bars={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
