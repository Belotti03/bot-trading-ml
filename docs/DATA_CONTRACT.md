# Data-version contract (Phase 0B)

Status: first slice, 2026-10-06. Does not yet bind V1 live.

## Snapshots

- Provider: Yahoo Finance via `yfinance.download`.
- `auto_adjust` is always explicit `False`.
- `Close` is unadjusted (execution).
- `AdjClose` is split/dividend adjusted (signals and performance).
- Each snapshot lives in `data/snapshots/yahoo_<UTC stamp>/`.
- `manifest.json` records provider, parameters, download time, per-file
  SHA-256, row counts, and library versions.
- Snapshots are append-only. A new download creates a new directory.

## Environment

Live and research install from `requirements/runtime.txt` (exact pins).
`python -m pip install -r requirements/runtime.txt`.

A result without snapshot hash, lock hash, interpreter version and commit
is not admissible evidence (roadmap §3.1). This slice creates the lock
and the snapshotter; it does not yet rewrite historical CSVs.

## Live V1

`model_engine.py` and `main.py` still download at run time. Wiring live
to a snapshot is a later 0B/1 step and needs its own check because it
can change V1 fills.
