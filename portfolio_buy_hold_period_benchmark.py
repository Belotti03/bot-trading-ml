import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ASSETS = [
    "BTC-USD", "ETH-USD", "NVDA", "AMD", "MSTR", "COIN",
    "TSM", "PLTR", "ARM", "SMCI", "TSLA", "META", "AMZN",
    "GOOGL", "AAPL", "MSFT", "QQQ", "GLD",
]

INITIAL_CAPITAL = 10_000.0

# Same trading-cost assumptions as portfolio_backtest.py.
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

# EXACT same periods used by the ML-OFF robustness test.
PERIODS = [
    ("P1", "2024-10-12", "2025-04-07"),
    ("P2", "2025-04-08", "2025-10-02"),
    ("P3", "2025-10-03", "2026-03-29"),
    ("P4", "2026-03-30", "2026-09-22"),
]

RESULTS_DIR = Path("portfolio_buy_hold_period_benchmark_results")


def download_asset(ticker):
    df = yf.download(
        ticker,
        period="4y",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "Close"]

    if any(col not in df.columns for col in required):
        return pd.DataFrame()

    df = df[required].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)

    df = (
        df.replace([np.inf, -np.inf], np.nan)
        .dropna()
        .sort_index()
    )

    return df


def portfolio_value(shares, cash, prices):
    value = float(cash)

    for ticker, qty in shares.items():
        price = prices.get(ticker)

        if price is not None and np.isfinite(price):
            value += float(qty) * float(price)

    return value


def max_drawdown(equity):
    if equity.empty:
        return np.nan

    peak = equity.cummax()
    drawdown = equity / peak - 1.0

    return float(drawdown.min())


def sharpe_ratio(equity):
    if len(equity) < 3:
        return np.nan

    returns = equity.pct_change().dropna()

    if len(returns) < 2:
        return np.nan

    std = returns.std(ddof=1)

    if std == 0:
        return np.nan

    return float(
        np.sqrt(252.0)
        * returns.mean()
        / std
    )


def run_period(period_name, requested_start, requested_end, data):
    requested_start = pd.Timestamp(requested_start)
    requested_end = pd.Timestamp(requested_end)

    # Common entry date: all 18 assets must have a valid quote.
    common_dates = None

    for ticker in ASSETS:
        dates = set(
            data[ticker].index[
                (data[ticker].index >= requested_start)
                & (data[ticker].index <= requested_end)
            ]
        )

        if common_dates is None:
            common_dates = dates
        else:
            common_dates &= dates

    common_dates = sorted(common_dates)

    if not common_dates:
        raise RuntimeError(
            f"{period_name}: no common entry date."
        )

    entry_date = common_dates[0]

    # All available dates from entry through requested end.
    union_dates = sorted(
        {
            date
            for ticker in ASSETS
            for date in data[ticker].index
            if entry_date <= date <= requested_end
        }
    )

    if not union_dates:
        raise RuntimeError(
            f"{period_name}: no dates after entry."
        )

    allocation_gross = INITIAL_CAPITAL / len(ASSETS)

    cash = INITIAL_CAPITAL
    shares = {}

    entry_rows = []

    # Equal-weight buy & hold entry.
    for ticker in ASSETS:
        row = data[ticker].loc[entry_date]

        raw_open = float(row["Open"])

        entry_price = raw_open * (1.0 + SLIPPAGE_RATE)

        gross = allocation_gross
        fee = gross * FEE_RATE
        net_invested = gross - fee

        qty = net_invested / entry_price

        shares[ticker] = qty
        cash -= gross

        entry_rows.append(
            {
                "Ticker": ticker,
                "EntryDate": str(entry_date.date()),
                "EntryPrice": entry_price,
                "Shares": qty,
                "GrossAllocation": gross,
                "EntryFee": fee,
            }
        )

    equity_rows = []
    last_prices = {}

    # Daily mark-to-market.
    for current_date in union_dates:
        for ticker in ASSETS:
            df = data[ticker]

            eligible = df.index[
                (df.index >= entry_date)
                & (df.index <= current_date)
            ]

            if len(eligible):
                last_date = eligible[-1]

                last_prices[ticker] = float(
                    df.loc[last_date, "Close"]
                )

        value = portfolio_value(
            shares,
            cash,
            last_prices,
        )

        equity_rows.append(
            {
                "Date": current_date,
                "Equity": value,
            }
        )

    # Final liquidation.
    final_cash = cash
    liquidation_rows = []

    for ticker in ASSETS:
        eligible = data[ticker].index[
            (data[ticker].index >= entry_date)
            & (data[ticker].index <= requested_end)
        ]

        if len(eligible) == 0:
            continue

        last_date = eligible[-1]

        raw_close = float(
            data[ticker].loc[last_date, "Close"]
        )

        exit_price = raw_close * (1.0 - SLIPPAGE_RATE)

        gross_value = shares[ticker] * exit_price
        fee = gross_value * FEE_RATE
        net_value = gross_value - fee

        final_cash += net_value

        liquidation_rows.append(
            {
                "Ticker": ticker,
                "ExitDate": str(last_date.date()),
                "ExitPrice": exit_price,
                "Shares": shares[ticker],
                "GrossValue": gross_value,
                "ExitFee": fee,
                "NetValue": net_value,
            }
        )

    final_equity = final_cash

    equity_df = pd.DataFrame(equity_rows)

    # Add final liquidation point.
    final_mark_date = max(
        data[ticker].index[
            data[ticker].index <= requested_end
        ].max()
        for ticker in ASSETS
    )

    equity_df.loc[len(equity_df)] = {
        "Date": pd.Timestamp(final_mark_date),
        "Equity": final_equity,
    }

    equity_df = (
        equity_df
        .groupby("Date", as_index=False)["Equity"]
        .last()
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # Explicit initial point for drawdown.
    initial_row = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp(entry_date)
                - pd.Timedelta(days=1),
                "Equity": INITIAL_CAPITAL,
            }
        ]
    )

    equity_for_metrics = (
        pd.concat(
            [initial_row, equity_df],
            ignore_index=True,
        )
        .drop_duplicates(
            subset=["Date"],
            keep="last",
        )
        .sort_values("Date")
        .reset_index(drop=True)
    )

    summary = {
        "Benchmark": "Equal-weight Buy & Hold",
        "Period": period_name,
        "RequestedStartDate": str(requested_start.date()),
        "RequestedEndDate": str(requested_end.date()),
        "CommonEntryDate": str(entry_date.date()),
        "FinalMarkDate": str(final_mark_date.date()),
        "InitialCapital": INITIAL_CAPITAL,
        "FinalEquity": final_equity,
        "TotalReturn": final_equity / INITIAL_CAPITAL - 1.0,
        "MaxDrawdown": max_drawdown(
            equity_for_metrics["Equity"]
        ),
        "Sharpe": sharpe_ratio(
            equity_for_metrics["Equity"]
        ),
        "Assets": len(ASSETS),
        "FeeRate": FEE_RATE,
        "SlippageRate": SLIPPAGE_RATE,
    }

    return (
        summary,
        equity_for_metrics,
        pd.DataFrame(entry_rows),
        pd.DataFrame(liquidation_rows),
    )


def main():
    warnings.filterwarnings("ignore")

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Downloading 18 assets once...")

    data = {}

    for ticker in ASSETS:
        print(f"Downloading {ticker}...")

        df = download_asset(ticker)

        if df.empty:
            raise RuntimeError(
                f"No valid data for {ticker}."
            )

        data[ticker] = df

    summaries = []

    for period_name, start, end in PERIODS:
        print(
            f"\n=== {period_name}: "
            f"{start} -> {end} ==="
        )

        summary, equity, entries, exits = run_period(
            period_name,
            start,
            end,
            data,
        )

        summaries.append(summary)

        period_dir = RESULTS_DIR / period_name

        period_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        pd.DataFrame([summary]).to_csv(
            period_dir / "portfolio_summary.csv",
            index=False,
        )

        equity.to_csv(
            period_dir / "portfolio_equity.csv",
            index=False,
        )

        entries.to_csv(
            period_dir / "portfolio_entries.csv",
            index=False,
        )

        exits.to_csv(
            period_dir / "portfolio_exits.csv",
            index=False,
        )

        print(
            f"Return: {summary['TotalReturn']:.2%} | "
            f"Max DD: {summary['MaxDrawdown']:.2%} | "
            f"Sharpe: {summary['Sharpe']:.2f}"
        )

    summary_df = pd.DataFrame(summaries)

    summary_df.to_csv(
        RESULTS_DIR
        / "portfolio_buy_hold_period_summary.csv",
        index=False,
    )

    print(
        "\n============================================================"
    )
    print("BUY & HOLD PERIOD BENCHMARK")
    print(
        "============================================================"
    )

    print(
        summary_df[
            [
                "Period",
                "CommonEntryDate",
                "FinalMarkDate",
                "TotalReturn",
                "MaxDrawdown",
                "Sharpe",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
