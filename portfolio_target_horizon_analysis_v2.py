import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import portfolio_backtest as base


# ============================================================
# ML TARGET HORIZON ANALYSIS — ONE HORIZON PER JOB
# ============================================================
# This script intentionally tests ONE horizon at a time.
# GitHub Actions runs horizons 1/3/5/10 in parallel.
#
# The statistical protocol remains unchanged:
# - same 18 assets
# - same 5y data
# - same features
# - same XGB/LGBM/RandomForest models
# - same MIN_TRAIN_SIZE / STEP_SIZE
# - same portfolio engine
# - same thresholds, sizing, stops, fees and slippage
#
# Only the target horizon changes:
# Target_H = 1 when Close[t+H] > Close[t]
# ============================================================

HORIZONS = [1, 3, 5, 10]

STOP_ATR = 3.0
TRAILING_ATR = 3.0

OUTPUT_ROOT = Path("portfolio_target_horizon_results")

PERIODS = [
    ("P1", "2024-10-15", "2025-04-10"),
    ("P2", "2025-04-11", "2025-10-05"),
    ("P3", "2025-10-06", "2026-04-01"),
    ("P4", "2026-04-02", "2026-09-25"),
]


def calculate_horizon_target(df, horizon):
    data = base.calculate_features(df)

    future_close = data["Close"].shift(-horizon)

    data["Target"] = np.where(
        future_close.notna(),
        (future_close > data["Close"]).astype(int),
        np.nan,
    )

    return data


def predict_batch(models, test):
    """
    Same ensemble probability as base.predict_probability,
    but vectorized over the whole test block.

    This does NOT change the model or prediction rule.
    It only avoids thousands of one-row predict_proba calls.
    """
    X = test[base.MODEL_FEATURES]

    probabilities = []

    for model in models:
        probabilities.append(
            model.predict_proba(X)[:, 1]
        )

    return np.mean(
        np.vstack(probabilities),
        axis=0,
    )


def generate_horizon_oos_predictions(df, horizon):
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

        # Exactly the same model training as V1.
        models = base.train_models(train)

        # Vectorized inference only.
        probabilities = predict_batch(
            models,
            test,
        )

        for (index, row), probability in zip(
            test.iterrows(),
            probabilities,
        ):
            predictions.append(
                {
                    "Date": pd.Timestamp(index),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "ATR": float(row["ATR"]),
                    "Probability": float(probability),
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

        if gross_loss > 0:
            pf = gross_profit / gross_loss
        elif gross_profit > 0:
            pf = float("inf")
        else:
            pf = 0.0

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


def run(horizon):
    if horizon not in HORIZONS:
        raise ValueError(
            f"Unsupported horizon={horizon}. "
            f"Allowed: {HORIZONS}"
        )

    # The target-horizon experiment must cover P1-P4.
    base.LOOKBACK_PERIOD = "5y"

    # Keep portfolio risk parameters identical.
    base.STOP_ATR_MULTIPLIER = STOP_ATR
    base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

    output_dir = (
        OUTPUT_ROOT
        / f"horizon_{horizon}d"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print(
        f"TARGET HORIZON ANALYSIS | {horizon} DAYS"
    )
    print("=" * 70)
    print(
        "Loading 5 years of data once..."
    )

    raw_data = {}

    for ticker in base.ASSETS:
        data = base.download_data(ticker)

        if data is None or data.empty:
            print(
                f"WARNING: {ticker} has no data"
            )
            continue

        raw_data[ticker] = data

    if not raw_data:
        raise RuntimeError(
            "No historical data available."
        )

    predictions = {}
    validation_rows = []

    for ticker in base.ASSETS:
        print(
            f"Generating OOS: {ticker} | "
            f"horizon={horizon}"
        )

        data = raw_data.get(ticker)

        if data is None or data.empty:
            continue

        pred = generate_horizon_oos_predictions(
            data,
            horizon,
        )

        if pred.empty:
            print(
                f"WARNING: no predictions for {ticker}"
            )
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

    print()
    print(
        f"Running ONE full portfolio backtest "
        f"for horizon={horizon}..."
    )

    summary, equity_df, trades_df = (
        base.run_portfolio_backtest(
            predictions
        )
    )

    pd.DataFrame([summary]).to_csv(
        output_dir / "summary.csv",
        index=False,
    )

    equity_df.to_csv(
        output_dir / "equity.csv",
        index=False,
    )

    trades_df.to_csv(
        output_dir / "trades.csv",
        index=False,
    )

    validation_df = pd.DataFrame(
        validation_rows
    )

    validation_df.to_csv(
        output_dir / "model_oos_metrics.csv",
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
        trades["Period"] = trades[
            "EntryDate"
        ].apply(classify_period)

        period_metrics = (
            calculate_period_metrics(
                trades
            )
        )
    else:
        period_metrics = pd.DataFrame()

    period_metrics.to_csv(
        output_dir / "period_metrics.csv",
        index=False,
    )

    model_metrics = (
        validation_df
        .select_dtypes(include=[np.number])
        .mean(numeric_only=True)
        if not validation_df.empty
        else pd.Series()
    )

    comparison_row = {
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
            validation_df["Samples"].sum()
        ),
        "ModelAccuracyMean": float(
            model_metrics.get(
                "Accuracy",
                np.nan,
            )
        ),
        "ModelBrierMean": float(
            model_metrics.get(
                "Brier",
                np.nan,
            )
        ),
        "ModelLogLossMean": float(
            model_metrics.get(
                "LogLoss",
                np.nan,
            )
        ),
    }

    pd.DataFrame(
        [comparison_row]
    ).to_csv(
        output_dir / "comparison_row.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print(
        f"HORIZON {horizon} DAYS COMPLETE"
    )
    print("=" * 70)
    print(
        pd.DataFrame(
            [comparison_row]
        ).to_string(index=False)
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--horizon",
        type=int,
        required=True,
        choices=HORIZONS,
    )

    args = parser.parse_args()

    run(args.horizon)


if __name__ == "__main__":
    main()
