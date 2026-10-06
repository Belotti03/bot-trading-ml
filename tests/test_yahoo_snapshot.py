import hashlib
from pathlib import Path

import pandas as pd

from research.yahoo_snapshot import sha256_file, verify_snapshot, write_ticker_csv


def test_sha256_file(tmp_path: Path):
    path = tmp_path / "a.csv"
    path.write_bytes(b"abc")
    assert sha256_file(path) == hashlib.sha256(b"abc").hexdigest()


def test_verify_detects_tamper(tmp_path: Path):
    frame = pd.DataFrame(
        {
            "Open": [1.0],
            "High": [1.0],
            "Low": [1.0],
            "Close": [1.0],
            "AdjClose": [1.0],
            "Volume": [10],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )
    csv_path = tmp_path / "AAA.csv"
    write_ticker_csv(frame, csv_path)
    digest = sha256_file(csv_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"tickers": {"AAA": {"path": "AAA.csv", "sha256": "%s"}}}' % digest,
        encoding="utf-8",
    )
    assert verify_snapshot(tmp_path) == []
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "x", encoding="utf-8")
    problems = verify_snapshot(tmp_path)
    assert problems and "sha256 mismatch" in problems[0]
