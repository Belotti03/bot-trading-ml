import pandas as pd
from pathlib import Path
import portfolio_backtest as base
# Asset-selection analysis must cover the full official P1-P4 period.
# Do not inherit the 2y production/backtest lookback from portfolio_backtest.py.
base.LOOKBACK_PERIOD = "5y"

# ============================================================
# OFFICIAL V1 BASELINE
# ============================================================
# This diagnostic MUST use the same methodology as the current
# Tie-Safe ML-OFF robustness baseline:
#   STOP = 3.0 ATR
#   TRAILING = 3.0 ATR
#   same portfolio_backtest engine
#
# IMPORTANT:
# We run ONE full portfolio backtest only.
# We do NOT re-run the portfolio separately for each period.
# Period analysis is attribution of the trades produced by that
# single official full backtest.
# ============================================================

STOP_ATR = 3.0
TRAILING_ATR = 3.0

OUTPUT_DIR = Path("portfolio_asset_selection_results_corrected")

PERIODS = [
    ("P1", "2024-10-15", "2025-04-10"),
    ("P2", "2025-04-11", "2025-10-05"),
    ("P3", "2025-10-06", "2026-04-01"),
    ("P4", "2026-04-02", "2026-09-25"),
]


# ============================================================
# TIE-SAFE ML-OFF
# ============================================================

def add_tie_safe_probabilities(predictions):
    """
    Reproduce the Tie-Safe ML-OFF baseline used by the
    robustness test.

    Bullish condition:
        Close > SMA20
        and 20-day return > 0

    Bullish assets receive a continuous probability in
    [0.6001, 0.6499], based on cross-sectional momentum/trend
    ranks for each signal date.

    Bearish/neutral assets receive 0.40.
    """

    df = predictions.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df["RET20"] = df["Close"].pct_change(20)
    df["SMA20"] = df["Close"].rolling(20).mean()

    df["Probability"] = 0.40

    bullish = (
        (df["Close"] > df["SMA20"]) &
        (df["RET20"] > 0)
    )

    bullish_dates = (
        df.loc[bullish, "Date"]
        .dropna()
        .sort_values()
        .unique()
    )

    for date in bullish_dates:

        mask = (
            (df["Date"] == date) &
            bullish
        )

        candidates = df.loc[
            mask,
            ["Ticker", "RET20", "Close", "SMA20"]
        ].copy()

        if candidates.empty:
            continue

        candidates["momentum_rank"] = (
            candidates["RET20"]
            .rank(method="first", pct=True)
        )

        candidates["trend_rank"] = (
            (candidates["Close"] / candidates["SMA20"] - 1)
            .rank(method="first", pct=True)
        )

        candidates["rank_score"] = (
            0.5 * candidates["momentum_rank"] +
            0.5 * candidates["trend_rank"]
        )

        candidates["Probability"] = (
            0.6001 +
            0.0498 * candidates["rank_score"]
        )

        for idx, value in candidates["Probability"].items():
            df.loc[idx, "Probability"] = float(value)

    df["PreviousProbability"] = (
        df.groupby("Ticker")["Probability"].shift(1)
    )

    df["PreviousATR"] = (
        df.groupby("Ticker")["ATR"].shift(1)
    )

    return df


# ============================================================
# LOAD OOS PREDICTIONS
# ============================================================

def load_predictions():

    print("Generating official Tie-Safe ML-OFF predictions...")

    predictions = {}

    for ticker in base.ASSETS:

        print(f"  {ticker}")

        data = base.download_data(ticker)

        if data is None or data.empty:
            print(f"  WARNING: no data for {ticker}")
            continue

        pred = base.generate_oos_predictions(data)

        if pred is None or pred.empty:
            print(f"  WARNING: no OOS predictions for {ticker}")
            continue

        pred = pred.copy()
        pred["Ticker"] = ticker

        pred = add_tie_safe_probabilities(pred)

        predictions[ticker] = pred

    return predictions


# ============================================================
# TRADE ATTRIBUTION
# ============================================================

def classify_period(date_value):

    date = pd.Timestamp(date_value)

    for period_name, start_date, end_date in PERIODS:

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        if start <= date <= end:
            return period_name

    return "OUTSIDE"


def calculate_asset_statistics(trades):

    if trades.empty:
        return pd.DataFrame()

    rows = []

    total_pnl = trades["PnL"].sum()

    for ticker, group in trades.groupby("Ticker"):

        pnl = group["PnL"].sum()

        wins = group.loc[group["PnL"] > 0, "PnL"]
        losses = group.loc[group["PnL"] < 0, "PnL"]

        gross_profit = wins.sum()
        gross_loss = abs(losses.sum())

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        rows.append({
            "Ticker": ticker,
            "Trades": len(group),
            "PnL": pnl,
            "AvgPnL": group["PnL"].mean(),
            "MedianPnL": group["PnL"].median(),
            "WinRate": (group["PnL"] > 0).mean(),
            "ProfitFactor": profit_factor,
            "AvgReturn": group["Return"].mean(),
            "MedianReturn": group["Return"].median(),
            "ContributionPct": (
                pnl / total_pnl * 100
                if total_pnl != 0 else 0.0
            ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values("PnL", ascending=False)
        .reset_index(drop=True)
    )


def calculate_period_asset_statistics(trades):

    if trades.empty:
        return pd.DataFrame()

    rows = []

    for (period, ticker), group in trades.groupby(
        ["Period", "Ticker"]
    ):

        pnl = group["PnL"].sum()

        wins = group.loc[group["PnL"] > 0, "PnL"]
        losses = group.loc[group["PnL"] < 0, "PnL"]

        gross_profit = wins.sum()
        gross_loss = abs(losses.sum())

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        rows.append({
            "Period": period,
            "Ticker": ticker,
            "Trades": len(group),
            "PnL": pnl,
            "AvgPnL": group["PnL"].mean(),
            "WinRate": (group["PnL"] > 0).mean(),
            "ProfitFactor": profit_factor,
            "AvgReturn": group["Return"].mean(),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(["Period", "PnL"], ascending=[True, False])
        .reset_index(drop=True)
    )


def calculate_concentration(asset_stats):

    if asset_stats.empty:
        return pd.DataFrame()

    total = asset_stats["PnL"].sum()

    top3 = asset_stats.nlargest(3, "PnL")["PnL"].sum()
    top5 = asset_stats.nlargest(5, "PnL")["PnL"].sum()

    bottom3 = asset_stats.nsmallest(3, "PnL")["PnL"].sum()

    return pd.DataFrame([{
        "TotalPnL": total,
        "Top3PnL": top3,
        "Top5PnL": top5,
        "Bottom3PnL": bottom3,
        "Top3ContributionPct": (
            top3 / total * 100 if total != 0 else 0.0
        ),
        "Top5ContributionPct": (
            top5 / total * 100 if total != 0 else 0.0
        ),
    }])


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 1. Generate exactly the same prediction universe
    # --------------------------------------------------------

    predictions = load_predictions()

    if not predictions:
        raise RuntimeError("No predictions generated.")

    # --------------------------------------------------------
    # 2. Run ONE official full backtest
    # --------------------------------------------------------

    base.STOP_ATR_MULTIPLIER = STOP_ATR
    base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

    print()
    print("Running ONE official full Tie-Safe ML-OFF backtest...")

    summary, equity_df, trades_df = (
        base.run_portfolio_backtest(predictions)
    )

    # --------------------------------------------------------
    # 3. Save official baseline outputs
    # --------------------------------------------------------

    pd.DataFrame([dict(summary)]).to_csv(
        OUTPUT_DIR / "official_full_summary.csv",
        index=False
    )

    equity_df.to_csv(
        OUTPUT_DIR / "official_full_equity.csv",
        index=False
    )

    trades_df.to_csv(
        OUTPUT_DIR / "official_full_trades.csv",
        index=False
    )

    # --------------------------------------------------------
    # 4. Normalize trade dates
    # --------------------------------------------------------

    trades = trades_df.copy()

    if trades.empty:
        raise RuntimeError("Official full backtest returned no trades.")

    trades["EntryDate"] = pd.to_datetime(
        trades["EntryDate"],
        errors="coerce"
    )

    trades["ExitDate"] = pd.to_datetime(
        trades["ExitDate"],
        errors="coerce"
    )

    trades["PnL"] = pd.to_numeric(
        trades["PnL"],
        errors="coerce"
    )

    trades["Return"] = pd.to_numeric(
        trades["Return"],
        errors="coerce"
    )

    trades = trades.dropna(
        subset=["Ticker", "EntryDate", "PnL"]
    ).copy()

    # Attribution is based on ENTRY DATE because that is when
    # the portfolio selected the asset.
    trades["Period"] = trades["EntryDate"].apply(
        classify_period
    )

    # --------------------------------------------------------
    # 5. Full asset attribution
    # --------------------------------------------------------

    asset_stats = calculate_asset_statistics(trades)

    asset_stats.to_csv(
        OUTPUT_DIR / "asset_selection_full.csv",
        index=False
    )

    # --------------------------------------------------------
    # 6. Period x asset attribution
    # --------------------------------------------------------

    period_trades = trades[
        trades["Period"] != "OUTSIDE"
    ].copy()

    period_asset_stats = (
        calculate_period_asset_statistics(period_trades)
    )

    period_asset_stats.to_csv(
        OUTPUT_DIR / "asset_selection_all_periods.csv",
        index=False
    )

    # Individual period files
    for period_name, _, _ in PERIODS:

        x = period_asset_stats[
            period_asset_stats["Period"] == period_name
        ].copy()

        x.to_csv(
            OUTPUT_DIR / f"asset_selection_{period_name}.csv",
            index=False
        )

    # --------------------------------------------------------
    # 7. Concentration
    # --------------------------------------------------------

    concentration = calculate_concentration(
        asset_stats
    )

    concentration.to_csv(
        OUTPUT_DIR / "asset_concentration.csv",
        index=False
    )

    # --------------------------------------------------------
    # 8. Period totals
    # --------------------------------------------------------

    period_totals = []

    for period_name, start_date, end_date in PERIODS:

        x = period_trades[
            period_trades["Period"] == period_name
        ]

        period_totals.append({
            "Period": period_name,
            "StartDate": start_date,
            "EndDate": end_date,
            "Trades": len(x),
            "PnL": x["PnL"].sum(),
            "WinRate": (
                (x["PnL"] > 0).mean()
                if len(x) else 0.0
            ),
        })

    pd.DataFrame(period_totals).to_csv(
        OUTPUT_DIR / "asset_selection_period_totals.csv",
        index=False
    )

    # --------------------------------------------------------
    # 9. Reason x asset
    # --------------------------------------------------------

    if "Reason" in trades.columns:

        reason_asset = (
            trades
            .groupby(["Ticker", "Reason"])
            .agg(
                Trades=("PnL", "size"),
                PnL=("PnL", "sum"),
                AvgPnL=("PnL", "mean"),
                WinRate=("PnL", lambda x: (x > 0).mean()),
            )
            .reset_index()
            .sort_values("PnL", ascending=False)
        )

        reason_asset.to_csv(
            OUTPUT_DIR / "asset_exit_reason_attribution.csv",
            index=False
        )

    # --------------------------------------------------------
    # 10. Console reconciliation
    # --------------------------------------------------------

    official_final = float(summary["FinalEquity"])
    official_return = float(summary["TotalReturn"])
    trade_pnl = float(trades["PnL"].sum())

    print()
    print("==========================================")
    print("OFFICIAL BASELINE RECONCILIATION")
    print("==========================================")
    print(f"Final equity : €{official_final:,.2f}")
    print(f"Return       : {official_return:.2%}")
    print(f"Trade PnL    : €{trade_pnl:,.2f}")
    print(f"Trades       : {len(trades)}")
    print()
    print("Top assets by PnL:")
    print(
        asset_stats.head(10).to_string(index=False)
    )
    print()
    print("==========================================")
    print("ASSET SELECTION ANALYSIS COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()
