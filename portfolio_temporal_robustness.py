from pathlib import Path
import pandas as pd
import portfolio_backtest as base

FIXED_STOP = 3.0
TRAILING_STOP = 3.0

PERIODS = [
    ("P1", "2024-09-01", "2025-02-28"),
    ("P2", "2025-03-01", "2025-08-31"),
    ("P3", "2025-09-01", "2026-02-28"),
    ("P4", "2026-03-01", "2026-08-31"),
]

RESULTS_DIR = Path("portfolio_temporal_robustness_results")


def filter_predictions(all_predictions, start_date, end_date):
    filtered = {}
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    for ticker, df in all_predictions.items():
        if df is None or df.empty:
            filtered[ticker] = df
            continue

        temp = df.copy()
        temp.index = pd.to_datetime(temp.index)
        mask = (temp.index >= start) & (temp.index <= end)
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
    print()

    all_predictions = {}

    print("Generating walk-forward OOS predictions...")
    for ticker in base.ASSETS:
        print(f"  {ticker}")
        df = base.download_data(ticker)
        all_predictions[ticker] = base.generate_oos_predictions(df)

    summaries = []

    for period_name, start_date, end_date in PERIODS:
        print()
        print("-" * 70)
        print(f"TEST {period_name}: {start_date} -> {end_date}")
        print("-" * 70)

        period_predictions = filter_predictions(
            all_predictions, start_date, end_date
        )

        summary, equity_df, trades_df = base.run_portfolio_backtest(
            period_predictions
        )

        summary = summary.copy()
        summary["Period"] = period_name
        summary["StartDate"] = start_date
        summary["EndDate"] = end_date

        period_dir = RESULTS_DIR / period_name
        period_dir.mkdir(parents=True, exist_ok=True)

        equity_df.to_csv(period_dir / "portfolio_equity.csv", index=False)
        trades_df.to_csv(period_dir / "portfolio_trades.csv", index=False)
        summary.to_csv(period_dir / "portfolio_summary.csv", index=False)

        summaries.append(summary)

        print(f"Initial capital: €{summary['InitialCapital'].iloc[0]:,.2f}")
        print(f"Final equity   : €{summary['FinalEquity'].iloc[0]:,.2f}")
        print(f"Total return   : {summary['TotalReturn'].iloc[0]:.2%}")
        print(f"Max drawdown   : {summary['MaxDrawdown'].iloc[0]:.2%}")
        print(f"Sharpe         : {summary['Sharpe'].iloc[0]:.2f}")
        print(f"Trades         : {int(summary['Trades'].iloc[0])}")
        print(f"Win rate       : {summary['WinRate'].iloc[0]:.2%}")
        print(f"Profit factor  : {summary['ProfitFactor'].iloc[0]:.3f}")

    final_summary = pd.concat(summaries, ignore_index=True)

    preferred = [
        "Period", "StartDate", "EndDate", "InitialCapital", "FinalEquity",
        "TotalReturn", "MaxDrawdown", "Sharpe", "Trades", "WinRate",
        "ProfitFactor",
    ]
    columns = [c for c in preferred if c in final_summary.columns]
    columns += [c for c in final_summary.columns if c not in columns]
    final_summary = final_summary[columns]

    final_summary.to_csv(
        RESULTS_DIR / "portfolio_temporal_robustness_summary.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("TEMPORAL ROBUSTNESS TEST COMPLETED")
    print("=" * 70)
    print(final_summary.to_string(index=False))


if __name__ == "__main__":
    main()
