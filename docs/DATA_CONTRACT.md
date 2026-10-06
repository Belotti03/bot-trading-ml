# Data-version contract (Phase 0B)

Status: snapshots, pins, quality flags, session calendars, D16 price
fields, and D18 cost *formula* as of 2026-10-06. Does not bind V1 live.
D18 scenario numbers are not frozen.

## Snapshots

- Provider: Yahoo Finance via `yfinance.download`.
- `auto_adjust` is always explicit `False`.
- `Close` is unadjusted (execution). D16 closed.
- `AdjClose` is split/dividend adjusted (signals and performance). D16 closed.
- Next-open fill uses unadjusted `Open` of the following session (D18).
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

## Calendars

- Crypto (`BTC-USD`, `ETH-USD`): every calendar day.
- US equity and ETF: NYSE-like weekdays. Regular holidays are a frozen
  pandas rule set (New Year, MLK from 1998, Presidents Day, Good Friday,
  Memorial Day, Juneteenth from 2022, Independence Day, Labor Day,
  Thanksgiving, Christmas, with weekend observance). Extra full-session
  closures are a frozen date list in `research/calendars.py`.
- Half-day sessions still have a daily bar, so they stay expected.
- Residual on snapshot `yahoo_20261006T1106Z`: AMD `1980-11-04` is the
  only missing expected equity bar after the calendar; treated as a
  provider hole, not a holiday.

## Costs (D18)

Formula: per-side cost = commission + spread + linear impact ×
participation. Three scenarios exist by name only. Using them as
evidence before 0C numbers is an error (`CostScenariosUnset`).

## Live V1

`model_engine.py` and `main.py` still download at run time. Wiring live
to a snapshot is a later 0B/1 step and needs its own check because it
can change V1 fills.
