import pandas as pd
from pathlib import Path
import portfolio_backtest as base

# ============================================================
# TRAILING STOP SENSITIVITY
# Fixed stop remains 3.0x ATR.
# Only the trailing stop changes.
# OOS predictions are generated ONCE and reused for all tests.
# ============================================================

FIXED_STOP = 3.0
TRAILING_STOPS = [2.0, 2.5, 3.0, 3.5]

RESULTS_DIR = Path("portfolio_trailing_stop_sensitivity_results")


def main():
    base.STOP_ATR_MULTIPLIER = FIXED_STOP

    all_predictions = {}

    print("=" * 60)
    print("GENERATING WALK-FORWARD OOS PREDICTIONS ONCE")
    print("=" * 60)

    for ticker in base.ASSETS:
        print(f"\nDownloading {ticker}...")

        try:
            df = base.download_data(ticker)

            if df.empty:
                print(f"{ticker}: NO DATA")
                continue

            predictions = base.generate_oos_predictions(df)

            if predictions.empty:
                print(f"{ticker}: NO OOS DATA")
                continue

            all_predictions[ticker] = predictions
            print(f"{ticker}: {len(predictions)} OOS rows")

        except Exception as error:
            print(f"{ticker}: ERROR -> {error}")

    if not all_predictions:
        raise RuntimeError("No OOS predictions generated.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []

    for trailing_stop in TRAILING_STOPS:
        base.STOP_ATR_MULTIPLIER = FIXED_STOP
        base.TRAILING_ATR_MULTIPLIER = trailing_stop

        print("\n" + "-" * 60)
        print(
            f"TEST: FIXED ATR STOP = {FIXED_STOP:.1f}x | "
            f"TRAILING ATR STOP = {trailing_stop:.1f}x"
        )
        print("-" * 60)

        summary, equity_df, trades_df = base.run_portfolio_backtest(
            all_predictions
        )

        row = {
            "FixedStopATR": FIXED_STOP,
            "TrailingStopATR": trailing_stop,
            **summary,
        }
        summaries.append(row)

        output_dir = (
            RESULTS_DIR
            / f"fixed_{FIXED_STOP:.1f}_trailing_{trailing_stop:.1f}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        equity_df.to_csv(
            output_dir / "portfolio_equity.csv",
            index=False,
        )
        trades_df.to_csv(
            output_dir / "portfolio_trades.csv",
            index=False,
        )
        pd.DataFrame([row]).to_csv(
            output_dir / "portfolio_summary.csv",
            index=False,
        )

        print(f"Fixed stop     : {FIXED_STOP:.1f}x")
        print(f"Trailing stop  : {trailing_stop:.1f}x")
        print(f"Initial capital: €{summary['InitialCapital']:,.2f}")
        print(f"Final equity   : €{summary['FinalEquity']:,.2f}")
        print(f"Total return   : {summary['TotalReturn']:.2%}")
        print(f"Max drawdown   : {summary['MaxDrawdown']:.2%}")
        print(f"Sharpe         : {summary['Sharpe']:.2f}")
        print(f"Trades         : {summary['Trades']}")
        print(f"Win rate       : {summary['WinRate']:.2%}")
        print(f"Profit factor  : {summary['ProfitFactor']:.3f}")

    summary_df = pd.DataFrame(summaries)

    summary_df = summary_df[
        [
            "FixedStopATR",
            "TrailingStopATR",
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
        "portfolio_trailing_stop_sensitivity_summary.csv",
        index=False,
    )

    print("\n" + "=" * 60)
    print("TRAILING STOP SENSITIVITY COMPLETED")
    print("=" * 60)
    print()
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
