"""Download an immutable Yahoo daily snapshot for the Branch B basket.

This is Phase 0B infrastructure. It does not change V1 live trading.
D16: store raw Close (execution) and Adj Close (signals/performance)
in the same file. auto_adjust is always explicit False.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = (
    "BTC-USD",
    "ETH-USD",
    "NVDA",
    "AMD",
    "MSTR",
    "COIN",
    "TSM",
    "PLTR",
    "ARM",
    "SMCI",
    "TSLA",
    "META",
    "AMZN",
    "GOOGL",
    "AAPL",
    "MSFT",
    "QQQ",
    "GLD",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = REPO_ROOT / "data" / "snapshots"
PROVIDER = "yahoo_finance"
INTERVAL = "1d"
PERIOD = "max"
AUTO_ADJUST = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    return out


def download_ticker(ticker: str) -> pd.DataFrame:
    raw = yf.download(
        ticker,
        period=PERIOD,
        interval=INTERVAL,
        auto_adjust=AUTO_ADJUST,
        actions=False,
        progress=False,
        threads=False,
    )
    if raw is None or raw.empty:
        raise RuntimeError(f"{ticker}: empty Yahoo download")
    raw = _flatten_columns(raw)
    if "Close" not in raw.columns:
        raise RuntimeError(f"{ticker}: Close missing after download")
    frame = pd.DataFrame(index=pd.to_datetime(raw.index).tz_localize(None))
    frame["Open"] = pd.to_numeric(raw["Open"], errors="coerce")
    frame["High"] = pd.to_numeric(raw["High"], errors="coerce")
    frame["Low"] = pd.to_numeric(raw["Low"], errors="coerce")
    frame["Close"] = pd.to_numeric(raw["Close"], errors="coerce")
    adj = raw["Adj Close"] if "Adj Close" in raw.columns else raw["Close"]
    frame["AdjClose"] = pd.to_numeric(adj, errors="coerce")
    if "Volume" in raw.columns:
        frame["Volume"] = pd.to_numeric(raw["Volume"], errors="coerce")
    else:
        frame["Volume"] = pd.NA
    frame = frame.sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    return frame


def write_ticker_csv(frame: pd.DataFrame, path: Path) -> None:
    out = frame.reset_index()
    date_col = out.columns[0]
    out = out.rename(columns={date_col: "Date"})
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)


def build_snapshot(tickers=TICKERS, root: Path = SNAPSHOT_ROOT) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    snapshot_id = f"yahoo_{stamp}"
    dest = root / snapshot_id
    dest.mkdir(parents=True, exist_ok=False)

    env = {
        "python": sys.version.split()[0],
        "yfinance": getattr(yf, "__version__", ""),
        "pandas": pd.__version__,
    }
    files = {}
    for ticker in tickers:
        frame = download_ticker(ticker)
        rel_name = f"{ticker.replace('/', '-')}.csv"
        path = dest / rel_name
        write_ticker_csv(frame, path)
        files[ticker] = {
            "path": rel_name,
            "sha256": sha256_file(path),
            "rows": int(len(frame)),
            "first": frame.index.min().strftime("%Y-%m-%d"),
            "last": frame.index.max().strftime("%Y-%m-%d"),
        }

    manifest = {
        "snapshot_id": snapshot_id,
        "provider": PROVIDER,
        "endpoint": "yfinance.download",
        "parameters": {
            "period": PERIOD,
            "interval": INTERVAL,
            "auto_adjust": AUTO_ADJUST,
            "actions": False,
        },
        "downloaded_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "tickers": files,
        "environment": env,
        "notes": (
            "Close is unadjusted (execution). AdjClose is split/dividend "
            "adjusted (signals and performance). Snapshot is append-only; "
            "do not rewrite files in place."
        ),
    }
    manifest_path = dest / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dest / "MANIFEST.sha256").write_text(
        sha256_file(manifest_path) + "  manifest.json\n",
        encoding="utf-8",
    )
    return dest


def verify_snapshot(dest: Path) -> list[str]:
    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    for ticker, meta in manifest["tickers"].items():
        path = dest / meta["path"]
        if not path.is_file():
            problems.append(f"{ticker}: missing {meta['path']}")
            continue
        digest = sha256_file(path)
        if digest != meta["sha256"]:
            problems.append(f"{ticker}: sha256 mismatch")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        metavar="DIR",
        help="Verify an existing snapshot directory instead of downloading",
    )
    args = parser.parse_args(argv)
    if args.verify:
        problems = verify_snapshot(Path(args.verify))
        if problems:
            print("VERIFY FAIL")
            for item in problems:
                print(item)
            return 1
        print("VERIFY OK")
        return 0
    dest = build_snapshot()
    print(f"WROTE {dest}")
    problems = verify_snapshot(dest)
    if problems:
        print("VERIFY FAIL")
        return 1
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
