import math
from pathlib import Path

import numpy as np
import pandas as pd

import portfolio_backtest as base


# ============================================================
# ML TARGET HORIZON ANALYSIS
# ============================================================
# Purpose:
# Test whether the ML target horizon itself is mismatched with
# the swing-trading objective.
#
# Horizons tested in this first pass:
#   1, 3, 5, 10 trading days
#
# We keep EVERYTHING else fixed:
#   - same 18-asset universe
#   - same features
#   - same models/hyperparameters
#   - same walk-forward structure
#   - same 120-row minimum train size
#   - same 20-row test blocks
#   - same portfolio engine
#   - same thresholds / sizing / ATR stops / costs
#   - same 5-year historical data
#
# Only the target changes:
#   Target_H = 1 if Close[t+H] > Close[t], else 0
#
# IMPORTANT:
# This is an experiment, not a parameter optimization.
# Do not select a horizon from these results alone.
# ============================================================

HORIZONS = [1, 3, 5, 10]

STOP_ATR = 3.0
TRAILING_ATR = 3.0

OUTPUT_DIR = Path("portfolio_target_horizon_results")

# The official analysis windows used by the current V1 research.
PERIODS = [
    ("P1", "2024-10-15", "2025-04-10"),
    ("P2", "2025-04-11", "2025-10-05"),
    ("P3", "2025-10-06", "2026-04-01"),
    ("P4", "2026-04-02", "2026-09-25"),
]


def calculate_horizon_target(df, horizon):
    """Build the target using only future close relative to current close."""
    data = base.calculate_features(df)

    future_close = data["Close"].shift(-horizon)

    data["Target"] = np.where(
        future_close.notna(),
        (future_close > data["Close"]).astype(int),
        np.nan,
    )

    return data


def generate_horizon_oos_predictions(df, horizon):
    """
    Same walk-forward protocol as portfolio_backtest.generate_oos_predictions,
    but with a configurable target horizon.

    No future information is used in features.
    The target is only used for training.
    """

    data = calculate_horizon_target(df, horizon)

    data = data.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    data = data.dropna(
        subset=base.MODEL_FEATURES
        + [
            "ATR",
            "Target",
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ).copy()

    if len(data) <= base.MIN_TRAIN_SIZE:
        return pd.DataFrame()

    predictions = []

    test_start = base.MIN_TRAIN_SIZE

    while test_start < len(data):
        test_end = min(
            test_start + base.STEP_SIZE,
            len(data),
        )

        train = data.iloc[:test_start]
        test = data.iloc[test_start:test_end]

        models = base.train_models(train)

        for index, row in test.iterrows():

            probability = base.predict_probability(
                models,
                row,
            )

            predictions.append(
                {
                    "Date": pd.Timestamp(index),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "ATR": float(row["ATR"]),
                    "Probability": probability,
                    "Actual": int(row["Target"]),
                }
            )

        test_start = test_end

    result = pd.DataFrame(predictions)

    if result.empty:
        return result

    result = (
        result
        .sort_values("Date")
        .reset_index(drop=True)
    )

    result["PreviousProbability"] = (
        result["Probability"].shift(1)
    )

    result["PreviousATR"] = (
        result["ATR"].shift(1)
    )

    result["NextAvailableDate"] = (
        result["Date"].shift(-1)
    )

    return result


def evaluate_oos(predictions):
    """Model-level OOS diagnostics."""
    if predictions.empty:
        return {}

    from sklearn.metrics import (
        accuracy_score,
        brier_score_loss,
        log_loss,
    )

    actual = predictions["Actual"].astype(int).to_numpy()
    probability = predictions["Probability"].astype(float).to_numpy()

    classification = (
        probability >= 0.50
    ).astype(int)

    return {
        "Samples": int(len(actual)),
        "PositiveRate": float(actual.mean()),
        "PredictedPositiveRate": float(classification.mean()),
        "Accuracy": float(
            accuracy_score(actual, classification)
        ),
        "Brier": float(
            brier_score_loss(actual, probability)
        ),
        "LogLoss": float(
            log_loss(
                actual,
                probability,
                labels=[0, 1],
            )
        ),
    }


def classify_period(date_value):
    date = pd.Timestamp(date_value)

    for name, start, end in PERIODS:
        if (
            pd.Timestamp(start)
            <= date
            <= pd.Timestamp(end)
        ):
            return name

    return "OUTSIDE"


def calculate_period_metrics(trades):
    rows = []

    for period, start, end in PERIODS:
        group = trades[
            trades["Period"] == period
        ]

        if group.empty:
            rows.append(
                {
                    "Period": period,
                    "StartDate": start,
                    "EndDate": end,
                    "Trades": 0,
                    "PnL": 0.0,
                    "WinRate": 0.0,
                    "ProfitFactor": 0.0,
                }
            )
            continue

        gross_profit = group.loc[
            group["PnL"] > 0,
            "PnL",
        ].sum()

        gross_loss = abs(
            group.loc[
                group["PnL"] < 0,
                "PnL",
            ].sum()
        )

        pf = (
            gross_profit / gross_loss
            if gross_loss > 0
            else float("inf")
            if gross_profit > 0
            else 0.0
        )

        rows.append(
            {
                "Period": period,
                "StartDate": start,
                "EndDate": end,
                "Trades": int(len(group)),
                "PnL": float(group["PnL"].sum()),
                "WinRate": float(
                    (group["PnL"] > 0).mean()
                ),
                "ProfitFactor": float(pf),
            }
        )

    return pd.DataFrame(rows)


def run_one_horizon(horizon, raw_data):
    print()
    print("=" * 70)
    print(f"TARGET HORIZON = {horizon} DAYS")
    print("=" * 70)

    predictions = {}
    validation_rows = []

    for ticker in base.ASSETS:
        print(f"  {ticker} | horizon={horizon}")

        data = raw_data.get(ticker)

        if data is None or data.empty:
            print(f"    WARNING: no data")
            continue

        pred = generate_horizon_oos_predictions(
            data,
            horizon,
        )

        if pred.empty:
            print(f"    WARNING: no OOS predictions")
            continue

        pred["Ticker"] = ticker

        predictions[ticker] = pred

        metrics = evaluate_oos(pred)

        validation_rows.append(
            {
                "Horizon": horizon,
                "Ticker": ticker,
                **metrics,
            }
        )

    if not predictions:
        raise RuntimeError(
            f"No predictions generated for horizon {horizon}."
        )

    # Same risk configuration for every horizon.
    base.STOP_ATR_MULTIPLIER = STOP_ATR
    base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

    print()
    print(
        f"Running ONE full portfolio backtest for "
        f"horizon={horizon}..."
    )

    summary, equity_df, trades_df = (
        base.run_portfolio_backtest(predictions)
    )

    horizon_dir = OUTPUT_DIR / f"horizon_{horizon}d"
    horizon_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame([summary]).to_csv(
        horizon_dir / "summary.csv",
        index=False,
    )

    equity_df.to_csv(
        horizon_dir / "equity.csv",
        index=False,
    )

    trades_df.to_csv(
        horizon_dir / "trades.csv",
        index=False,
    )

    pd.DataFrame(validation_rows).to_csv(
        horizon_dir / "model_oos_metrics.csv",
        index=False,
    )

    trades = trades_df.copy()

    if not trades.empty:
        trades["EntryDate"] = pd.to_datetime(
            trades["EntryDate"],
            errors="coerce",
        )
        trades["PnL"] = pd.to_numeric(
            trades["PnL"],
            errors="coerce",
        )
        trades["Period"] = trades["EntryDate"].apply(
            classify_period
        )

        period_metrics = calculate_period_metrics(
            trades
        )
    else:
        period_metrics = pd.DataFrame()

    period_metrics.to_csv(
        horizon_dir / "period_metrics.csv",
        index=False,
    )

    return {
        "Horizon": horizon,
        "InitialCapital": float(
            summary["InitialCapital"]
        ),
        "FinalEquity": float(
            summary["FinalEquity"]
        ),
        "TotalReturn": float(
            summary["TotalReturn"]
        ),
        "MaxDrawdown": float(
            summary["MaxDrawdown"]
        ),
        "Sharpe": float(
            summary["Sharpe"]
        ),
        "Trades": int(
            summary["Trades"]
        ),
        "WinRate": float(
            summary["WinRate"]
        ),
        "ProfitFactor": float(
            summary["ProfitFactor"]
        ),
        "ModelSamples": int(
            sum(row["Samples"] for row in validation_rows)
        ),
        "ModelAccuracyMean": float(
            np.mean(
                [row["Accuracy"] for row in validation_rows]
            )
        ),
        "ModelBrierMean": float(
            np.mean(
                [row["Brier"] for row in validation_rows]
            )
        ),
        "ModelLogLossMean": float(
            np.mean(
                [row["LogLoss"] for row in validation_rows]
            )
        ),
    }


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 5y is required so P1 is genuinely covered.
    base.LOOKBACK_PERIOD = "5y"

    print("=" * 70)
    print("ML TARGET HORIZON ANALYSIS")
    print("=" * 70)
    print()
    print(
        "Loading 5 years of data once for all assets..."
    )

    raw_data = {}

    for ticker in base.ASSETS:
        data = base.download_data(ticker)

        if data is None or data.empty:
            print(f"{ticker}: NO DATA")
            continue

        raw_data[ticker] = data

    if not raw_data:
        raise RuntimeError(
            "No historical data available."
        )

    all_results = []

    for horizon in HORIZONS:
        result = run_one_horizon(
            horizon,
            raw_data,
        )
        all_results.append(result)

    comparison = pd.DataFrame(
        all_results
    ).sort_values("Horizon")

    comparison.to_csv(
        OUTPUT_DIR / "horizon_comparison.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("TARGET HORIZON COMPARISON")
    print("=" * 70)
    print(
        comparison[
            [
                "Horizon",
                "FinalEquity",
                "TotalReturn",
                "MaxDrawdown",
                "Sharpe",
                "Trades",
                "WinRate",
                "ProfitFactor",
                "ModelAccuracyMean",
                "ModelBrierMean",
                "ModelLogLossMean",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 70)
    print("TARGET HORIZON ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
