from pathlib import Path
import warnings
import pandas as pd
import portfolio_backtest as base

FIXED_STOP = 3.0
TRAILING_STOP = 3.0
N_PERIODS = 4
RESULTS_DIR = Path("portfolio_temporal_robustness_results")

warnings.filterwarnings(
    "ignore",
    message="`sklearn.utils.parallel.delayed` should be used with",
)


def build_periods(all_predictions):
    dates = []
    for df in all_predictions.values():
        if df is not None and not df.empty:
            dates.extend(pd.to_datetime(df["Date"]).tolist())

    if not dates:
        raise RuntimeError("No OOS prediction dates available.")

    unique_dates = pd.DatetimeIndex(sorted(set(dates)))
    groups = pd.qcut(
        range(len(unique_dates)),
        q=N_PERIODS,
        labels=False,
        duplicates="drop",
    )

    periods = []
    for group in sorted(set(groups)):
        values = unique_dates[groups == group]
        periods.append((f"P{group + 1}", values.min(), values.max()))

    return periods


def filter_predictions(all_predictions, start_date, end_date):
    filtered = {}
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    for ticker, df in all_predictions.items():
        if df is None or df.empty:
            filtered[ticker] = df
            continue

        temp = df.copy()
        temp["Date"] = pd.to_datetime(temp["Date"])
        mask = (temp["Date"] >= start) & (temp["Date"] <= end)
        filtered[ticker] = temp.loc[mask].copy()

    return filtered


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    base.STOP_ATR_MULTIPLIER = FIXED_STOP
    base.TRAILING_ATR_MULTIPLIER = TRAILING_STOP

    print("=" * 70)
    print("PORTFOLIO OOS TEMPORAL ROBUSTNESS TEST")
    print("=" * 70)
    print(f"Fixed ATR stop    : {FIXED_STOP}x")
    print(f"Trailing ATR stop : {TRAILING_STOP}x")
    print("OOS model training: ONCE")
    print()

    all_predictions = {}

    for ticker in base.ASSETS:
        print(f"Generating OOS predictions: {ticker}")
        df = base.download_data(ticker)
        all_predictions[ticker] = base.generate_oos_predictions(df)

    periods = build_periods(all_predictions)

    print()
    print("Actual OOS periods:")
    for name, start, end in periods:
        print(f"  {name}: {start.date()} -> {end.date()}")

    summaries = []

    for period_name, start_date, end_date in periods:
        print()
        print("-" * 70)
        print(f"TEST {period_name}: {start_date.date()} -> {end_date.date()}")
        print("-" * 70)

        period_predictions = filter_predictions(
            all_predictions, start_date, end_date
        )

        summary, equity_df, trades_df = base.run_portfolio_backtest(
            period_predictions
        )

        summary_row = dict(summary)
        summary_row["Period"] = period_name
        summary_row["StartDate"] = str(start_date.date())
        summary_row["EndDate"] = str(end_date.date())
        summary_df = pd.DataFrame([summary_row])

        period_dir = RESULTS_DIR / period_name
        period_dir.mkdir(parents=True, exist_ok=True)

        equity_df.to_csv(period_dir / "portfolio_equity.csv", index=False)
        trades_df.to_csv(period_dir / "portfolio_trades.csv", index=False)
        summary_df.to_csv(period_dir / "portfolio_summary.csv", index=False)

        summaries.append(summary_df)

        print(f"Initial capital: €{summary_row['InitialCapital']:,.2f}")
        print(f"Final equity   : €{summary_row['FinalEquity']:,.2f}")
        print(f"Total return   : {summary_row['TotalReturn']:.2%}")
        print(f"Max drawdown   : {summary_row['MaxDrawdown']:.2%}")
        print(f"Sharpe         : {summary_row['Sharpe']:.2f}")
        print(f"Trades         : {int(summary_row['Trades'])}")
        print(f"Win rate       : {summary_row['WinRate']:.2%}")
        print(f"Profit factor  : {summary_row['ProfitFactor']:.3f}")

    final_summary = pd.concat(summaries, ignore_index=True)

    preferred = [
        "Period", "StartDate", "EndDate", "InitialCapital", "FinalEquity",
        "TotalReturn", "MaxDrawdown", "Sharpe", "Trades", "WinRate",
        "ProfitFactor",
    ]
    columns = [c for c in preferred if c in final_summary.columns]
    columns += [c for c in final_summary.columns if c not in columns]

    final_summary[columns].to_csv(
        RESULTS_DIR / "portfolio_temporal_robustness_summary.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("TEMPORAL ROBUSTNESS TEST COMPLETED")
    print("=" * 70)
    print(final_summary[columns].to_string(index=False))


if __name__ == "__main__":
    main()
