import math
from pathlib import Path
import pandas as pd
import portfolio_backtest as base

# ============================================================
# ML ON vs ML OFF
# Same portfolio engine, same OOS dates, same risk parameters.
#
# ML ON  = existing walk-forward ML probabilities.
# ML OFF = simple non-ML momentum/trend signal:
#          20-day return + price vs SMA20.
#
# The goal is diagnostic: measure whether ML adds value over
# a simple transparent baseline. This is NOT a live strategy.
# ============================================================

RESULTS_DIR = Path("portfolio_ml_ab_test_results")
ML_OFF_PROBABILITY = {
    "BULLISH": 0.60,
    "NEUTRAL": 0.50,
    "BEARISH": 0.40,
}


def generate_non_ml_predictions(df):
    """Create a deterministic, non-ML probability-like signal.

    0.60: 20d momentum positive AND close above SMA20
    0.50: mixed conditions
    0.40: 20d momentum negative AND close below SMA20

    This is only used to feed the SAME portfolio engine as ML ON.
    No model fitting or future information is used.
    """
    data = df.copy()
    data["SMA20"] = data["Close"].rolling(20).mean()
    data["RET20"] = data["Close"].pct_change(20)

    rows = []
    for i in range(len(data) - 1):
        row = data.iloc[i]

        if pd.isna(row["SMA20"]) or pd.isna(row["RET20"]):
            continue

        bullish = row["Close"] > row["SMA20"] and row["RET20"] > 0
        bearish = row["Close"] < row["SMA20"] and row["RET20"] < 0

        if bullish:
            probability = ML_OFF_PROBABILITY["BULLISH"]
        elif bearish:
            probability = ML_OFF_PROBABILITY["BEARISH"]
        else:
            probability = ML_OFF_PROBABILITY["NEUTRAL"]

        # Match the structure consumed by run_portfolio_backtest().
        signal_date = data.index[i]
        rows.append({
            "Date": signal_date,
            "Probability": probability,
        })

    if not rows:
        return pd.DataFrame(columns=["Probability"])

    out = pd.DataFrame(rows).set_index("Date")
    out.index = pd.to_datetime(out.index)
    return out[["Probability"]]


def generate_signal_sets():
    ml_predictions = {}
    non_ml_predictions = {}

    print("=" * 70)
    print("ML ON vs ML OFF A/B TEST")
    print("=" * 70)
    print(f"Fixed ATR stop    : {base.STOP_ATR_MULTIPLIER:.1f}x")
    print(f"Trailing ATR stop : {base.TRAILING_ATR_MULTIPLIER:.1f}x")
    print("ML ON             : existing walk-forward model")
    print("ML OFF            : 20d momentum + SMA20 baseline")
    print("-" * 70)

    for ticker in base.ASSETS:
        print(f"Downloading {ticker}...")
        df = base.download_data(ticker)

        print(f"  Generating ML OOS predictions: {ticker}")
        ml_predictions[ticker] = base.generate_oos_predictions(df)

        print(f"  Generating non-ML baseline: {ticker}")
        non_ml_predictions[ticker] = generate_non_ml_predictions(df)

    return ml_predictions, non_ml_predictions


def run_test(name, predictions):
    test_dir = RESULTS_DIR / name
    test_dir.mkdir(parents=True, exist_ok=True)

    summary, equity_df, trades_df = base.run_portfolio_backtest(predictions)

    summary_row = dict(summary)
    summary_row["Test"] = name
    summary_row["SignalType"] = (
        "Walk-forward ML"
        if name == "ML_ON"
        else "Non-ML momentum/SMA20"
    )

    pd.DataFrame([summary_row]).to_csv(
        test_dir / "portfolio_summary.csv", index=False
    )
    equity_df.to_csv(test_dir / "portfolio_equity.csv", index=False)
    trades_df.to_csv(test_dir / "portfolio_trades.csv", index=False)

    print()
    print(f"TEST: {name}")
    print(f"  Initial capital : €{summary['InitialCapital']:,.2f}")
    print(f"  Final equity    : €{summary['FinalEquity']:,.2f}")
    print(f"  Total return    : {summary['TotalReturn']:.2%}")
    print(f"  Max drawdown    : {summary['MaxDrawdown']:.2%}")
    print(f"  Sharpe          : {summary['Sharpe']:.2f}")
    print(f"  Trades          : {summary['Trades']}")
    print(f"  Win rate        : {summary['WinRate']:.2%}")
    print(f"  Profit factor   : {summary['ProfitFactor']:.3f}")

    return summary_row


def main():
    # Keep the same risk settings used in the recent robustness test.
    base.STOP_ATR_MULTIPLIER = 3.0
    base.TRAILING_ATR_MULTIPLIER = 3.0

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ml_predictions, non_ml_predictions = generate_signal_sets()

    summaries = []
    summaries.append(run_test("ML_ON", ml_predictions))
    summaries.append(run_test("ML_OFF", non_ml_predictions))

    summary_df = pd.DataFrame(summaries)
    summary_df = summary_df[
        [
            "Test",
            "SignalType",
            "InitialCapital",
            "FinalEquity",
            "TotalReturn",
            "MaxDrawdown",
            "Sharpe",
            "Trades",
            "WinRate",
            "ProfitFactor",
        ]
    ]

    summary_df.to_csv(
        RESULTS_DIR / "portfolio_ml_ab_test_summary.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("FINAL A/B SUMMARY")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
