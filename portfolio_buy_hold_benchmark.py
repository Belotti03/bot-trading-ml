from pathlib import Path
import pandas as pd
import portfolio_backtest as base

# ============================================================
# BUY & HOLD BENCHMARK
# Same 18 assets and same broad OOS window used by the
# portfolio diagnostics.
#
# Portfolio:
#   - €10,000 initial capital
#   - equal-weight allocation across all 18 assets
#   - buy once at the first available OPEN on/after OOS start
#   - hold until the final available CLOSE
#   - no ML, no stops, no rebalancing
#
# This is a benchmark, not a proposed live strategy.
# ============================================================

INITIAL_CAPITAL = 10_000.0
OOS_START = pd.Timestamp("2025-03-08")
OOS_END = pd.Timestamp("2026-09-19")
RESULTS_DIR = Path("portfolio_buy_hold_benchmark_results")


def load_benchmark_data():
    data = {}

    print("=" * 70)
    print("BUY & HOLD BENCHMARK")
    print("=" * 70)
    print(f"Initial capital : €{INITIAL_CAPITAL:,.2f}")
    print(f"OOS start       : {OOS_START.date()}")
    print(f"OOS end         : {OOS_END.date()}")
    print(f"Assets          : {len(base.ASSETS)}")
    print("-" * 70)

    for ticker in base.ASSETS:
        print(f"Downloading {ticker}...")
        df = base.download_data(ticker).copy()

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        period = df.loc[
            (df.index >= OOS_START) &
            (df.index <= OOS_END)
        ].copy()

        if period.empty:
            raise ValueError(
                f"No data for {ticker} inside benchmark window "
                f"{OOS_START.date()} -> {OOS_END.date()}"
            )

        data[ticker] = period

    return data


def run_buy_and_hold(data):
    # Equal-weight the initial capital across the 18 assets.
    allocation = INITIAL_CAPITAL / len(base.ASSETS)

    rows = []
    total_final = 0.0

    for ticker in base.ASSETS:
        df = data[ticker]

        entry_row = df.iloc[0]
        exit_row = df.iloc[-1]

        entry_date = pd.Timestamp(df.index[0])
        exit_date = pd.Timestamp(df.index[-1])

        entry_price = float(entry_row["Open"])
        exit_price = float(exit_row["Close"])

        if entry_price <= 0 or exit_price <= 0:
            raise ValueError(f"Invalid price for {ticker}")

        shares = allocation / entry_price
        final_value = shares * exit_price
        pnl = final_value - allocation
        asset_return = final_value / allocation - 1.0

        total_final += final_value

        rows.append({
            "Ticker": ticker,
            "EntryDate": entry_date.date().isoformat(),
            "ExitDate": exit_date.date().isoformat(),
            "EntryPrice": entry_price,
            "ExitPrice": exit_price,
            "InitialAllocation": allocation,
            "Shares": shares,
            "FinalValue": final_value,
            "PnL": pnl,
            "Return": asset_return,
        })

    trades_df = pd.DataFrame(rows)

    total_return = total_final / INITIAL_CAPITAL - 1.0

    # Equal-weight buy-and-hold has no intermediate trading.
    # Build an approximate daily portfolio equity curve by valuing
    # the fixed share positions at each asset's latest available
    # close, starting from the initial capital.
    equity_dates = sorted(
        set().union(*[set(df.index) for df in data.values()])
    )

    equity_rows = []

    positions = {
        row["Ticker"]: {
            "shares": row["Shares"],
            "allocation": row["InitialAllocation"],
        }
        for _, row in trades_df.iterrows()
    }

    last_prices = {}

    for date in equity_dates:
        date = pd.Timestamp(date)
        equity = 0.0

        for ticker in base.ASSETS:
            df = data[ticker]

            if date in df.index:
                last_prices[ticker] = float(df.loc[date, "Close"])

            if ticker in last_prices:
                equity += positions[ticker]["shares"] * last_prices[ticker]

        # Until every asset has a first price, this can be below the
        # initial capital. Once all assets have entered, it is the
        # actual marked-to-market portfolio value.
        equity_rows.append({
            "Date": date,
            "Equity": equity,
        })

    equity_df = pd.DataFrame(equity_rows)

    # Add explicit initial point for drawdown/return calculations.
    initial_point = pd.DataFrame([{
        "Date": OOS_START - pd.Timedelta(days=1),
        "Equity": INITIAL_CAPITAL,
    }])

    equity_df = pd.concat([initial_point, equity_df], ignore_index=True)
    equity_df = equity_df.sort_values("Date").drop_duplicates(
        subset=["Date"], keep="last"
    ).reset_index(drop=True)

    running_max = equity_df["Equity"].cummax()
    drawdown = equity_df["Equity"] / running_max - 1.0
    max_drawdown = float(drawdown.min())

    returns = equity_df["Equity"].pct_change().dropna()

    if len(returns) > 1 and returns.std() > 0:
        sharpe = float(
            returns.mean() / returns.std() * (252 ** 0.5)
        )
    else:
        sharpe = 0.0

    summary = {
        "InitialCapital": INITIAL_CAPITAL,
        "FinalEquity": total_final,
        "TotalReturn": total_return,
        "MaxDrawdown": max_drawdown,
        "Sharpe": sharpe,
        "Assets": len(base.ASSETS),
        "Benchmark": "Equal-weight Buy & Hold",
        "StartDate": str(OOS_START.date()),
        "EndDate": str(OOS_END.date()),
    }

    return summary, equity_df, trades_df


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    data = load_benchmark_data()
    summary, equity_df, holdings_df = run_buy_and_hold(data)

    summary_df = pd.DataFrame([summary])

    summary_df.to_csv(
        RESULTS_DIR / "portfolio_buy_hold_summary.csv",
        index=False,
    )
    equity_df.to_csv(
        RESULTS_DIR / "portfolio_buy_hold_equity.csv",
        index=False,
    )
    holdings_df.to_csv(
        RESULTS_DIR / "portfolio_buy_hold_holdings.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("BUY & HOLD RESULT")
    print("=" * 70)
    print(f"Initial capital : €{summary['InitialCapital']:,.2f}")
    print(f"Final equity    : €{summary['FinalEquity']:,.2f}")
    print(f"Total return    : {summary['TotalReturn']:.2%}")
    print(f"Max drawdown    : {summary['MaxDrawdown']:.2%}")
    print(f"Sharpe          : {summary['Sharpe']:.2f}")
    print(f"Assets          : {summary['Assets']}")
    print(f"Period          : {summary['StartDate']} -> {summary['EndDate']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
