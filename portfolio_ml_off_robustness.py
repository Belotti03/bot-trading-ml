import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import portfolio_backtest as base


# ============================================================
# CONFIG
# ============================================================

FIXED_STOP = 3.0
TRAILING_STOP = 3.0

N_PERIODS = 4

RESULTS_DIR = Path("portfolio_ml_off_robustness_results")

# Original ML-OFF test:
# bullish = 0.60, bearish = 0.40.
# The portfolio engine therefore treats bullish signals as
# high-conviction positions.
ORIGINAL_BULLISH_PROB = 0.60
ORIGINAL_BEARISH_PROB = 0.40

# Tie-safe variant:
# same bullish/bearish signal logic, but bullish candidates get
# a continuous score so the top-5 ranking is not determined by
# asset-list order.
TIE_SAFE_MIN_PROB = 0.6001
TIE_SAFE_MAX_PROB = 0.6499


def calculate_baseline_features(df):
    data = base.calculate_features(df).copy()

    data["SMA20"] = data["Close"].rolling(20).mean()
    data["RET20"] = data["Close"].pct_change(20)

    data = data.replace([np.inf, -np.inf], np.nan)

    data = data.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
            "ATR",
            "SMA20",
            "RET20",
        ]
    ).copy()

    return data


def build_original_ml_off_predictions(df):
    data = calculate_baseline_features(df)

    rows = []

    for index, row in data.iterrows():
        bullish = (
            float(row["Close"]) > float(row["SMA20"])
            and float(row["RET20"]) > 0.0
        )

        probability = (
            ORIGINAL_BULLISH_PROB
            if bullish
            else ORIGINAL_BEARISH_PROB
        )

        rows.append(
            {
                "Date": pd.Timestamp(index),
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "ATR": float(row["ATR"]),
                "Probability": probability,
                "RET20": float(row["RET20"]),
                "SMA20": float(row["SMA20"]),
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result = result.sort_values("Date").reset_index(drop=True)

    result["PreviousProbability"] = result["Probability"].shift(1)
    result["PreviousATR"] = result["ATR"].shift(1)
    result["NextAvailableDate"] = result["Date"].shift(-1)

    return result


def build_tie_safe_ml_off_predictions(df):
    data = calculate_baseline_features(df)

    # Same signal rule as the original ML-OFF baseline.
    data["Bullish"] = (
        (data["Close"] > data["SMA20"])
        & (data["RET20"] > 0.0)
    )

    # Cross-sectional ranking is calculated later, on each signal
    # date, using only information available on that date.
    data["Strength"] = np.nan

    rows = []

    for index, row in data.iterrows():
        rows.append(
            {
                "Date": pd.Timestamp(index),
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "ATR": float(row["ATR"]),
                "RET20": float(row["RET20"]),
                "SMA20": float(row["SMA20"]),
                "Bullish": bool(row["Bullish"]),
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result = result.sort_values("Date").reset_index(drop=True)

    # Since this function is called one ticker at a time, the
    # continuous score is completed after all assets are loaded.
    return result


def add_tie_safe_probabilities(predictions):
    # Preserve the exact same bullish/bearish signal condition.
    # Only replace equal bullish probabilities with a continuous
    # cross-sectional ranking to avoid asset-order tie breaking.
    frames = []

    for ticker, df in predictions.items():
        work = df.copy()
        work["Ticker"] = ticker
        frames.append(work)

    if not frames:
        return {}

    combined = pd.concat(frames, ignore_index=True)
    combined["Probability"] = ORIGINAL_BEARISH_PROB

    # Avoid groupby().apply(): newer pandas versions can exclude the
    # grouping column from the applied frame, which caused KeyError: Date.
    for signal_date in combined["Date"].dropna().unique():
        mask = combined["Date"] == signal_date
        candidates = combined[mask & combined["Bullish"]].copy()

        if candidates.empty:
            continue

        ret_rank = candidates["RET20"].rank(method="average", pct=True)
        sma_distance = candidates["Close"] / candidates["SMA20"] - 1.0
        sma_rank = sma_distance.rank(method="average", pct=True)
        strength = 0.5 * ret_rank + 0.5 * sma_rank

        combined.loc[candidates.index, "Probability"] = (
            TIE_SAFE_MIN_PROB
            + strength * (TIE_SAFE_MAX_PROB - TIE_SAFE_MIN_PROB)
        )

    output = {}

    for ticker in predictions:
        work = (
            combined[combined["Ticker"] == ticker]
            .drop(columns=["Ticker", "Bullish"])
            .sort_values("Date")
            .reset_index(drop=True)
        )

        work["PreviousProbability"] = work["Probability"].shift(1)
        work["PreviousATR"] = work["ATR"].shift(1)
        work["NextAvailableDate"] = work["Date"].shift(-1)
        output[ticker] = work

    return output


def load_predictions():
    original = {}
    tie_safe_base = {}

    for ticker in base.ASSETS:
        print(f"Downloading {ticker}...")
        df = base.download_data(ticker)

        if df.empty:
            print(f"WARNING: no data for {ticker}")
            continue

        # One download per ticker; both variants use identical data.
        original[ticker] = build_original_ml_off_predictions(df)
        tie_safe_base[ticker] = build_tie_safe_ml_off_predictions(df)

    tie_safe = add_tie_safe_probabilities(tie_safe_base)
    return original, tie_safe


def get_periods(all_predictions):
    all_dates = sorted(
        {
            pd.Timestamp(date)
            for df in all_predictions.values()
            for date in df["Date"]
        }
    )

    if not all_dates:
        raise RuntimeError("No dates available.")

    positions = np.array_split(
        np.arange(len(all_dates)),
        N_PERIODS,
    )

    periods = []

    for i, idx in enumerate(positions, start=1):
        if len(idx) == 0:
            continue

        start = all_dates[int(idx[0])]
        end = all_dates[int(idx[-1])]

        periods.append(
            (f"P{i}", start, end)
        )

    return periods


def slice_period(all_predictions, start_date, end_date):
    result = {}

    for ticker, df in all_predictions.items():
        work = df[
            (df["Date"] >= start_date)
            & (df["Date"] <= end_date)
        ].copy()

        if work.empty:
            continue

        work = (
            work
            .sort_values("Date")
            .reset_index(drop=True)
        )

        # Independent period:
        # do not carry the previous period's exit signal/ATR.
        work.loc[
            work.index[0],
            "PreviousProbability",
        ] = np.nan

        work.loc[
            work.index[0],
            "PreviousATR",
        ] = np.nan

        # Never create an entry that executes after the period.
        work.loc[
            work.index[-1],
            "NextAvailableDate",
        ] = pd.NaT

        result[ticker] = work

    return result


def run_variant(
    name,
    all_predictions,
    periods,
):
    rows = []

    variant_dir = RESULTS_DIR / name
    variant_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for period_name, start_date, end_date in periods:
        print(
            f"\n=== {name} | {period_name} | "
            f"{start_date.date()} -> {end_date.date()} ==="
        )

        period_predictions = slice_period(
            all_predictions,
            start_date,
            end_date,
        )

        summary, equity_df, trades_df = (
            base.run_portfolio_backtest(
                period_predictions
            )
        )

        row = dict(summary)
        row["Variant"] = name
        row["Period"] = period_name
        row["StartDate"] = str(start_date.date())
        row["EndDate"] = str(end_date.date())

        rows.append(row)

        period_dir = (
            variant_dir
            / period_name
        )
        period_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        pd.DataFrame([row]).to_csv(
            period_dir / "portfolio_summary.csv",
            index=False,
        )
        equity_df.to_csv(
            period_dir / "portfolio_equity.csv",
            index=False,
        )
        trades_df.to_csv(
            period_dir / "portfolio_trades.csv",
            index=False,
        )

    return rows


def main():
    warnings.filterwarnings(
        "ignore",
        message="X does not have valid feature names",
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Use the stop configuration from the best diagnostic found
    # so far, without modifying portfolio_backtest.py.
    base.STOP_ATR_MULTIPLIER = FIXED_STOP
    base.TRAILING_ATR_MULTIPLIER = TRAILING_STOP

    print(
        f"Fixed stop: {FIXED_STOP} ATR"
    )
    print(
        f"Trailing stop: {TRAILING_STOP} ATR"
    )

    original, tie_safe = load_predictions()

    periods = get_periods(original)

    print("\nActual OOS periods:")
    for name, start, end in periods:
        print(
            f"  {name}: "
            f"{start.date()} -> {end.date()}"
        )

    all_rows = []

    all_rows.extend(
        run_variant(
            "original_binary_ml_off",
            original,
            periods,
        )
    )

    all_rows.extend(
        run_variant(
            "tie_safe_ml_off",
            tie_safe,
            periods,
        )
    )

    summary = pd.DataFrame(all_rows)

    summary.to_csv(
        RESULTS_DIR
        / "portfolio_ml_off_robustness_summary.csv",
        index=False,
    )

    print("\n============================================================")
    print("ML-OFF ROBUSTNESS SUMMARY")
    print("============================================================")

    print(
        summary[
            [
                "Variant",
                "Period",
                "TotalReturn",
                "MaxDrawdown",
                "Sharpe",
                "Trades",
                "WinRate",
                "ProfitFactor",
            ]
        ].to_string(index=False)
    )

    print("\nResults saved to:")
    print(RESULTS_DIR)


if __name__ == "__main__":
    main()
