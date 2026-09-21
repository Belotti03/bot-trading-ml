from pathlib import Path
import pandas as pd
import portfolio_backtest as base

# ============================================================
# CORRECTED BUY & HOLD BENCHMARK
#
# Same 18 assets and same OOS window as the diagnostic tests.
# One COMMON entry date is used for all assets:
# the first date on which every asset has an available OPEN
# inside the requested OOS window.
#
# €10,000 is split equally across the 18 assets.
# No ML, stops, trailing stops, rebalancing or additional trades.
# Holdings are marked to market daily using each asset's latest
# available close.
# ============================================================

INITIAL_CAPITAL = 10_000.0
OOS_START = pd.Timestamp("2025-03-08")
OOS_END = pd.Timestamp("2026-09-19")
RESULTS_DIR = Path("portfolio_buy_hold_benchmark_results")


def load_data():
    data = {}

    print("=" * 70)
    print("CORRECTED BUY & HOLD BENCHMARK")
    print("=" * 70)
    print(f"Requested OOS window : {OOS_START.date()} -> {OOS_END.date()}")
    print(f"Initial capital      : €{INITIAL_CAPITAL:,.2f}")
    print(f"Assets               : {len(base.ASSETS)}")
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
                f"No data for {ticker} in the requested OOS window."
            )

        data[ticker] = period

    return data


def find_common_entry_date(data):
    common_dates = None

    for ticker in base.ASSETS:
        dates = set(pd.to_datetime(data[ticker].index))
        if common_dates is None:
            common_dates = dates
        else:
            common_dates &= dates

    if not common_dates:
        raise ValueError("No common trading date exists for all 18 assets.")

    common_dates = sorted(common_dates)

    # We use the first common date in the requested OOS window.
    return pd.Timestamp(common_dates[0])


def run_benchmark(data, entry_date):
    allocation = INITIAL_CAPITAL / len(base.ASSETS)

    holdings = []
    positions = {}

    for ticker in base.ASSETS:
        df = data[ticker]

        if entry_date not in df.index:
            raise ValueError(
                f"{ticker} has no data on common entry date {entry_date.date()}."
            )

        entry_row = df.loc[entry_date]
        entry_price = float(entry_row["Open"])

        if entry_price <= 0:
            raise ValueError(f"Invalid entry price for {ticker}.")

        shares = allocation / entry_price

        positions[ticker] = {
            "shares": shares,
            "entry_price": entry_price,
            "allocation": allocation,
        }

    # Common dates after entry. We mark every fixed position to the
    # latest available close, so weekends/asset-specific holidays
    # do not create artificial losses.
    all_dates = sorted(
        set().union(
            *[
                set(
                    data[ticker].loc[
                        data[ticker].index >= entry_date
                    ].index
                )
                for ticker in base.ASSETS
            ]
        )
    )

    last_close = {}
    equity_rows = []

    # Explicit initial point immediately before entry.
    equity_rows.append({
        "Date": entry_date - pd.Timedelta(days=1),
        "Equity": INITIAL_CAPITAL,
    })

    for date in all_dates:
        date = pd.Timestamp(date)
        equity = 0.0

        for ticker in base.ASSETS:
            df = data[ticker]

            if date in df.index:
                last_close[ticker] = float(df.loc[date, "Close"])

            if ticker not in last_close:
                # This should not occur after the common entry date.
                raise ValueError(
                    f"Missing first close for {ticker} on {date.date()}."
                )

            equity += positions[ticker]["shares"] * last_close[ticker]

        equity_rows.append({
            "Date": date,
            "Equity": equity,
        })

    equity_df = (
        pd.DataFrame(equity_rows)
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )

    # Final value is the last common/available marked-to-market value.
    final_equity = float(equity_df.iloc[-1]["Equity"])
    total_return = final_equity / INITIAL_CAPITAL - 1.0

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

    # Per-asset holdings report.
    for ticker in base.ASSETS:
        position = positions[ticker]
        final_price = last_close[ticker]
        final_value = position["shares"] * final_price

        holdings.append({
            "Ticker": ticker,
            "EntryDate": entry_date.date().isoformat(),
            "ExitDate": pd.Timestamp(all_dates[-1]).date().isoformat(),
            "EntryPrice": position["entry_price"],
            "ExitPrice": final_price,
            "InitialAllocation": position["allocation"],
            "Shares": position["shares"],
            "FinalValue": final_value,
            "PnL": final_value - position["allocation"],
            "Return": final_value / position["allocation"] - 1.0,
        })

    holdings_df = pd.DataFrame(holdings)

    summary = {
        "InitialCapital": INITIAL_CAPITAL,
        "FinalEquity": final_equity,
        "TotalReturn": total_return,
        "MaxDrawdown": max_drawdown,
        "Sharpe": sharpe,
        "Assets": len(base.ASSETS),
        "Benchmark": "Equal-weight Buy & Hold",
        "RequestedStartDate": str(OOS_START.date()),
        "RequestedEndDate": str(OOS_END.date()),
        "CommonEntryDate": str(entry_date.date()),
        "FinalMarkDate": str(pd.Timestamp(all_dates[-1]).date()),
    }

    return summary, equity_df, holdings_df


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    data = load_data()
    entry_date = find_common_entry_date(data)

    print()
    print(f"COMMON ENTRY DATE: {entry_date.date()}")

    summary, equity_df, holdings_df = run_benchmark(
        data,
        entry_date,
    )

    pd.DataFrame([summary]).to_csv(
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
    print("CORRECTED BUY & HOLD RESULT")
    print("=" * 70)
    print(f"Common entry date : {summary['CommonEntryDate']}")
    print(f"Final mark date   : {summary['FinalMarkDate']}")
    print(f"Initial capital   : €{summary['InitialCapital']:,.2f}")
    print(f"Final equity      : €{summary['FinalEquity']:,.2f}")
    print(f"Total return      : {summary['TotalReturn']:.2%}")
    print(f"Max drawdown      : {summary['MaxDrawdown']:.2%}")
    print(f"Sharpe            : {summary['Sharpe']:.2f}")
    print(f"Assets            : {summary['Assets']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
