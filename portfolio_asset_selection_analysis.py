import pandas as pd
from pathlib import Path
import portfolio_backtest as base


# ============================================================
# CONFIG
# ============================================================

STOP_ATR = 3.0
TRAILING_ATR = 3.0

OUTPUT_DIR = Path("portfolio_asset_selection_results")

PERIODS = [
    ("P1", "2024-10-12", "2025-04-07"),
    ("P2", "2025-04-08", "2025-10-02"),
    ("P3", "2025-10-03", "2026-03-29"),
    ("P4", "2026-03-30", "2026-09-22"),
]


# ============================================================
# TIE-SAFE ML-OFF
# ============================================================

def add_tie_safe_probabilities(predictions):
    """
    ML-OFF baseline:
      bullish if Close > SMA20 and 20d return > 0

    Instead of assigning exactly 0.60 to every bullish asset,
    create a small cross-sectional ranking so the top-5 selection
    is deterministic and not dependent on asset ordering.
    """

    df = predictions.copy()

    df["RET20"] = df["Close"].pct_change(20)
    df["SMA20"] = df["Close"].rolling(20).mean()

    df["Probability"] = 0.40

    bullish = (
        (df["Close"] > df["SMA20"]) &
        (df["RET20"] > 0)
    )

    for date in df.loc[bullish, "Date"].dropna().unique():

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
            df.loc[idx, "Probability"] = value

    df["PreviousProbability"] = (
        df.groupby("Ticker")["Probability"].shift(1)
    )

    df["PreviousATR"] = (
        df.groupby("Ticker")["ATR"].shift(1)
    )

    return df


# ============================================================
# LOAD OOS DATA
# ============================================================

def load_predictions():
    print("Downloading data and generating OOS predictions...")

    predictions = {}

    for ticker in base.ASSETS:

        print(f"  {ticker}")

        data = base.download_data(ticker)

        if data is None or data.empty:
            print(f"  WARNING: no data for {ticker}")
            continue

        pred = base.generate_oos_predictions(data)

        if pred is None or pred.empty:
            print(f"  WARNING: no predictions for {ticker}")
            continue

        pred = pred.copy()
        pred["Ticker"] = ticker

        pred = add_tie_safe_probabilities(pred)

        predictions[ticker] = pred

    return predictions


# ============================================================
# RUN FULL BACKTEST
# ============================================================

def run_full_backtest(predictions):

    base.STOP_ATR_MULTIPLIER = STOP_ATR
    base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

    summary, equity_df, trades_df = (
        base.run_portfolio_backtest(predictions)
    )

    return summary, equity_df, trades_df


# ============================================================
# PERIOD FILTER
# ============================================================

def filter_predictions(predictions, start_date, end_date):

    filtered = {}

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    for ticker, df in predictions.items():

        x = df.copy()

        x["Date"] = pd.to_datetime(x["Date"])

        x = x[
            (x["Date"] >= start) &
            (x["Date"] <= end)
        ].copy()

        if not x.empty:
            filtered[ticker] = x

    return filtered


# ============================================================
# TRADE ANALYSIS
# ============================================================

def analyze_trades(trades_df, period_name):

    if trades_df is None or trades_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    trades = trades_df.copy()

    trades["Ticker"] = trades["Ticker"].astype(str)
    trades["PnL"] = pd.to_numeric(
        trades["PnL"],
        errors="coerce"
    )

    trades["Return"] = pd.to_numeric(
        trades["Return"],
        errors="coerce"
    )

    trades = trades.dropna(
        subset=["Ticker", "PnL"]
    )

    total_pnl = trades["PnL"].sum()

    rows = []

    for ticker, group in trades.groupby("Ticker"):

        pnl = group["PnL"].sum()

        wins = group.loc[group["PnL"] > 0, "PnL"]
        losses = group.loc[group["PnL"] < 0, "PnL"]

        gross_profit = wins.sum()
        gross_loss = abs(losses.sum())

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = float("inf") if gross_profit > 0 else 0.0

        rows.append({
            "Period": period_name,
            "Ticker": ticker,
            "Trades": len(group),
            "PnL": pnl,
            "AvgPnL": group["PnL"].mean(),
            "MedianPnL": group["PnL"].median(),
            "WinRate": (
                (group["PnL"] > 0).mean()
                if len(group)
                else 0
            ),
            "ProfitFactor": profit_factor,
            "AvgReturn": group["Return"].mean(),
            "MedianReturn": group["Return"].median(),
            "ContributionPct": (
                pnl / total_pnl * 100
                if total_pnl != 0
                else 0
            ),
        })

    ticker_df = pd.DataFrame(rows)

    ticker_df = ticker_df.sort_values(
        "PnL",
        ascending=False
    )

    # --------------------------------------------------------
    # Reason analysis
    # --------------------------------------------------------

    if "Reason" in trades.columns:

        reason_rows = []

        for reason, group in trades.groupby("Reason"):

            pnl = group["PnL"].sum()

            reason_rows.append({
                "Period": period_name,
                "Reason": reason,
                "Trades": len(group),
                "PnL": pnl,
                "AvgPnL": group["PnL"].mean(),
                "WinRate": (
                    group["PnL"] > 0
                ).mean(),
            })

        reason_df = pd.DataFrame(reason_rows)

    else:

        reason_df = pd.DataFrame()

    return ticker_df, reason_df


# ============================================================
# CONCENTRATION ANALYSIS
# ============================================================

def concentration_analysis(ticker_df, period_name):

    if ticker_df.empty:
        return {
            "Period": period_name,
            "TotalPnL": 0,
            "Top3PnL": 0,
            "Top5PnL": 0,
            "Bottom3PnL": 0,
            "Top3ContributionPct": 0,
            "Top5ContributionPct": 0,
        }

    pnl = ticker_df["PnL"]

    total = pnl.sum()

    top3 = ticker_df.nlargest(3, "PnL")["PnL"].sum()
    top5 = ticker_df.nlargest(5, "PnL")["PnL"].sum()

    bottom3 = ticker_df.nsmallest(3, "PnL")["PnL"].sum()

    return {
        "Period": period_name,
        "TotalPnL": total,
        "Top3PnL": top3,
        "Top5PnL": top5,
        "Bottom3PnL": bottom3,
        "Top3ContributionPct": (
            top3 / total * 100
            if total != 0 else 0
        ),
        "Top5ContributionPct": (
            top5 / total * 100
            if total != 0 else 0
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions = load_predictions()

    print()
    print("Running full tie-safe ML-OFF backtest...")

    summary, equity_df, trades_df = (
        run_full_backtest(predictions)
    )

    print()
    print("FULL BACKTEST")
    print(summary)

    # --------------------------------------------------------
    # FULL TRADE ANALYSIS
    # --------------------------------------------------------

    full_ticker_df, full_reason_df = analyze_trades(
        trades_df,
        "FULL"
    )

    full_ticker_df.to_csv(
        OUTPUT_DIR / "asset_selection_full.csv",
        index=False
    )

    if not full_reason_df.empty:
        full_reason_df.to_csv(
            OUTPUT_DIR / "exit_reason_full.csv",
            index=False
        )

    # --------------------------------------------------------
    # CONCENTRATION
    # --------------------------------------------------------

    concentration_rows = []

    concentration_rows.append(
        concentration_analysis(
            full_ticker_df,
            "FULL"
        )
    )

    # --------------------------------------------------------
    # PERIOD ANALYSIS
    # --------------------------------------------------------

    all_period_assets = []

    for period_name, start_date, end_date in PERIODS:

        print()
        print(
            f"Analyzing {period_name}: "
            f"{start_date} -> {end_date}"
        )

        period_predictions = filter_predictions(
            predictions,
            start_date,
            end_date
        )

        if not period_predictions:
            print("  No predictions.")
            continue

        base.STOP_ATR_MULTIPLIER = STOP_ATR
        base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

        period_summary, period_equity, period_trades = (
            base.run_portfolio_backtest(
                period_predictions
            )
        )

        ticker_df, reason_df = analyze_trades(
            period_trades,
            period_name
        )

        if not ticker_df.empty:

            all_period_assets.append(
                ticker_df
            )

            ticker_df.to_csv(
                OUTPUT_DIR /
                f"asset_selection_{period_name}.csv",
                index=False
            )

        if not reason_df.empty:

            reason_df.to_csv(
                OUTPUT_DIR /
                f"exit_reason_{period_name}.csv",
                index=False
            )

        concentration_rows.append(
            concentration_analysis(
                ticker_df,
                period_name
            )
        )

    # --------------------------------------------------------
    # COMBINED PERIOD FILE
    # --------------------------------------------------------

    if all_period_assets:

        combined = pd.concat(
            all_period_assets,
            ignore_index=True
        )

        combined.to_csv(
            OUTPUT_DIR /
            "asset_selection_all_periods.csv",
            index=False
        )

    # --------------------------------------------------------
    # CONCENTRATION FILE
    # --------------------------------------------------------

    concentration_df = pd.DataFrame(
        concentration_rows
    )

    concentration_df.to_csv(
        OUTPUT_DIR /
        "asset_concentration.csv",
        index=False
    )

    # --------------------------------------------------------
    # FINAL RANKING
    # --------------------------------------------------------

    if all_period_assets:

        combined = pd.concat(
            all_period_assets,
            ignore_index=True
        )

        ranking = (
            combined
            .groupby("Ticker")
            .agg(
                Periods=("Period", "nunique"),
                TotalTrades=("Trades", "sum"),
                TotalPnL=("PnL", "sum"),
                AvgPnL=("AvgPnL", "mean"),
                AvgWinRate=("WinRate", "mean"),
                AvgProfitFactor=("ProfitFactor", "mean"),
                AvgReturn=("AvgReturn", "mean"),
            )
            .reset_index()
        )

        ranking = ranking.sort_values(
            "TotalPnL",
            ascending=False
        )

        ranking.to_csv(
            OUTPUT_DIR /
            "asset_selection_ranking.csv",
            index=False
        )

        print()
        print("FINAL ASSET RANKING")
        print(ranking.to_string(index=False))

    print()
    print("==========================================")
    print("ASSET SELECTION ANALYSIS COMPLETE")
    print("==========================================")
    print()
    print(f"Results saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
