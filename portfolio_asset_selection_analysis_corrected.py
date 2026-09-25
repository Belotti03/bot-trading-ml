
import pandas as pd
from pathlib import Path
import portfolio_backtest as base

STOP_ATR = 3.0
TRAILING_ATR = 3.0
OUTPUT_DIR = Path("portfolio_asset_selection_results_corrected")

def add_tie_safe_probabilities(predictions):
    df = predictions.copy()
    df["RET20"] = df["Close"].pct_change(20)
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["Probability"] = 0.40

    bullish = (df["Close"] > df["SMA20"]) & (df["RET20"] > 0)

    for date in df.loc[bullish, "Date"].dropna().unique():
        mask = (df["Date"] == date) & bullish
        candidates = df.loc[mask, ["Ticker", "RET20", "Close", "SMA20"]].copy()
        if candidates.empty:
            continue
        candidates["momentum_rank"] = candidates["RET20"].rank(method="first", pct=True)
        candidates["trend_rank"] = (
            (candidates["Close"] / candidates["SMA20"] - 1)
            .rank(method="first", pct=True)
        )
        candidates["rank_score"] = 0.5*candidates["momentum_rank"] + 0.5*candidates["trend_rank"]
        candidates["Probability"] = 0.6001 + 0.0498*candidates["rank_score"]
        for idx, value in candidates["Probability"].items():
            df.loc[idx, "Probability"] = value

    df["PreviousProbability"] = df.groupby("Ticker")["Probability"].shift(1)
    df["PreviousATR"] = df.groupby("Ticker")["ATR"].shift(1)
    return df

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions = {}
    print("Generating the SAME Tie-Safe predictions used by the ML-OFF robustness test...")
    for ticker in base.ASSETS:
        print(f"  {ticker}")
        data = base.download_data(ticker)
        if data is None or data.empty:
            continue
        pred = base.generate_oos_predictions(data)
        if pred is None or pred.empty:
            continue
        pred = pred.copy()
        pred["Ticker"] = ticker
        predictions[ticker] = add_tie_safe_probabilities(pred)

    base.STOP_ATR_MULTIPLIER = STOP_ATR
    base.TRAILING_ATR_MULTIPLIER = TRAILING_ATR

    print("Running ONE full backtest only...")
    summary, equity_df, trades_df = base.run_portfolio_backtest(predictions)

    trades_df = trades_df.copy()
    trades_df["PnL"] = pd.to_numeric(trades_df["PnL"], errors="coerce")
    trades_df["Return"] = pd.to_numeric(trades_df["Return"], errors="coerce")
    trades_df["EntryDate"] = pd.to_datetime(trades_df["EntryDate"])
    trades_df["ExitDate"] = pd.to_datetime(trades_df["ExitDate"])

    # Exact attribution from the single validated full backtest.
    rows = []
    total_pnl = trades_df["PnL"].sum()
    for ticker, g in trades_df.groupby("Ticker"):
        gp = g.loc[g["PnL"] > 0, "PnL"].sum()
        gl = abs(g.loc[g["PnL"] < 0, "PnL"].sum())
        rows.append({
            "Ticker": ticker,
            "Trades": len(g),
            "TotalPnL": g["PnL"].sum(),
            "AvgPnL": g["PnL"].mean(),
            "MedianPnL": g["PnL"].median(),
            "WinRate": (g["PnL"] > 0).mean(),
            "ProfitFactor": gp/gl if gl else (float("inf") if gp else 0),
            "AvgReturn": g["Return"].mean(),
            "ContributionPctOfTotalPnL": g["PnL"].sum()/total_pnl*100 if total_pnl else 0,
            "FirstEntry": g["EntryDate"].min().date(),
            "LastExit": g["ExitDate"].max().date(),
        })

    ranking = pd.DataFrame(rows).sort_values("TotalPnL", ascending=False)
    ranking.to_csv(OUTPUT_DIR/"asset_selection_from_validated_full_backtest.csv", index=False)
    trades_df.to_csv(OUTPUT_DIR/"validated_full_trades.csv", index=False)
    equity_df.to_csv(OUTPUT_DIR/"validated_full_equity.csv", index=False)
    pd.DataFrame([dict(summary)]).to_csv(OUTPUT_DIR/"validated_full_summary.csv", index=False)

    # Period attribution: assign each trade to the period containing its ENTRY date.
    periods = [
        ("P1", "2024-10-12", "2025-04-07"),
        ("P2", "2025-04-08", "2025-10-02"),
        ("P3", "2025-10-03", "2026-03-29"),
        ("P4", "2026-03-30", "2026-09-22"),
    ]
    period_rows=[]
    for name, start, end in periods:
        s,e=pd.Timestamp(start),pd.Timestamp(end)
        g=trades_df[(trades_df.EntryDate>=s)&(trades_df.EntryDate<=e)]
        for ticker,t in g.groupby("Ticker"):
            period_rows.append({
                "Period":name,"Ticker":ticker,"Trades":len(t),
                "PnL":t.PnL.sum(),"AvgPnL":t.PnL.mean(),
                "WinRate":(t.PnL>0).mean()
            })
    pd.DataFrame(period_rows).to_csv(OUTPUT_DIR/"asset_selection_by_period_from_same_full_backtest.csv", index=False)

    print("\nVALIDATED FULL BACKTEST")
    print(summary)
    print("\nASSET ATTRIBUTION")
    print(ranking.to_string(index=False))
    print("\nResults:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
