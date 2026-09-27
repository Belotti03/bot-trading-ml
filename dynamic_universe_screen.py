
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

ASSETS = [
    "BTC-USD","ETH-USD","NVDA","AMD","MSTR","COIN","TSM","PLTR","ARM",
    "SMCI","TSLA","META","AMZN","GOOGL","AAPL","MSFT","QQQ","GLD"
]
LOOKBACK = "5y"
TOP_KS = [4, 6, 8, 10, 12]
FEE = 0.001
SLIPPAGE = 0.0005
COST_PER_SIDE = FEE + SLIPPAGE
MIN_HISTORY = 60

def download():
    raw = yf.download(
        ASSETS, period=LOOKBACK, auto_adjust=False,
        progress=False, group_by="ticker", threads=True
    )
    out = {}
    for a in ASSETS:
        try:
            df = raw[a].copy()
        except Exception:
            continue
        if df.empty:
            continue
        cols = {c.lower(): c for c in df.columns}
        close = df[cols.get("close", "Close")].astype(float)
        volume = df[cols.get("volume", "Volume")].astype(float)
        x = pd.DataFrame({"Close": close, "Volume": volume}).replace([np.inf, -np.inf], np.nan)
        x = x.dropna(subset=["Close"]).copy()
        x["Return_1d"] = x["Close"].pct_change()
        x["Return_5d"] = x["Close"].pct_change(5)
        x["Return_20d"] = x["Close"].pct_change(20)
        x["Return_60d"] = x["Close"].pct_change(60)
        x["SMA_20"] = x["Close"].rolling(20).mean()
        x["SMA_50"] = x["Close"].rolling(50).mean()
        x["Dist_SMA20"] = x["Close"] / x["SMA_20"] - 1
        x["Dist_SMA50"] = x["Close"] / x["SMA_50"] - 1
        x["Vol_20d"] = x["Return_1d"].rolling(20).std() * np.sqrt(252)
        x["DollarVolume"] = x["Close"] * x["Volume"]
        x["DollarVolume20"] = x["DollarVolume"].rolling(20).median()
        x = x.dropna(subset=[
            "Return_20d","Return_60d","Dist_SMA20","Dist_SMA50",
            "Vol_20d","DollarVolume20"
        ])
        out[a] = x
    return out

def pct_rank(s):
    return s.rank(pct=True, method="average")

def build_panel(data):
    rows = []
    for a, df in data.items():
        z = df.copy()
        z["Asset"] = a
        rows.append(z.reset_index(names="Date"))
    panel = pd.concat(rows, ignore_index=True)
    panel["Date"] = pd.to_datetime(panel["Date"]).dt.tz_localize(None)
    return panel.sort_values(["Date","Asset"])

def score_date(g):
    g = g.copy()
    # Selection score uses only information known at today's close.
    # No future return is included in the score.
    g["r20"] = pct_rank(g["Return_20d"])
    g["r60"] = pct_rank(g["Return_60d"])
    g["trend20"] = pct_rank(g["Dist_SMA20"])
    g["trend50"] = pct_rank(g["Dist_SMA50"])
    g["lowvol"] = pct_rank(-g["Vol_20d"])
    g["liquidity"] = pct_rank(np.log1p(g["DollarVolume20"]))
    g["score"] = (
        0.25*g["r20"] +
        0.25*g["r60"] +
        0.15*g["trend20"] +
        0.15*g["trend50"] +
        0.10*g["lowvol"] +
        0.10*g["liquidity"]
    )
    return g

def run(panel, k):
    # Shift next-day return by asset, so the return earned after today's
    # selection cannot leak into today's ranking.
    panel = panel.copy()
    panel["NextReturn"] = panel.groupby("Asset")["Return_1d"].shift(-1)

    dates = sorted(panel["Date"].unique())
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    daily = []
    turnover_rows = []
    prev_set = set()

    for d in dates:
        g = panel[panel["Date"] == d].copy()
        g = g.dropna(subset=["NextReturn"])
        if len(g) < max(8, k):
            continue
        g = score_date(g)
        selected = set(g.nlargest(k, "score")["Asset"])
        ret = g[g["Asset"].isin(selected)]["NextReturn"].mean()

        # Approximate one-way portfolio turnover by membership changes.
        # A changed membership implies one sell and one buy.
        turnover = len(selected.symmetric_difference(prev_set)) / max(1, k)
        trading_cost = turnover * COST_PER_SIDE
        net_ret = ret - trading_cost

        equity *= (1.0 + net_ret)
        peak = max(peak, equity)
        dd = equity / peak - 1.0
        max_dd = min(max_dd, dd)

        daily.append((d, net_ret, equity, dd))
        turnover_rows.append((d, turnover, len(selected)))
        prev_set = selected

    eq = pd.DataFrame(daily, columns=["Date","Return","Equity","Drawdown"])
    if eq.empty:
        return None, None
    sharpe = np.sqrt(252) * eq["Return"].mean() / eq["Return"].std() if eq["Return"].std() > 0 else np.nan
    years = max((eq["Date"].iloc[-1] - eq["Date"].iloc[0]).days / 365.25, 1/365.25)
    cagr = (eq["Equity"].iloc[-1] / 10000.0) ** (1/years) - 1
    turnover = pd.DataFrame(turnover_rows, columns=["Date","Turnover","SelectedCount"])
    return {
        "TopK": k,
        "FinalEquity": eq["Equity"].iloc[-1],
        "TotalReturn": eq["Equity"].iloc[-1]/10000.0 - 1,
        "CAGR": cagr,
        "MaxDrawdown": eq["Drawdown"].min(),
        "Sharpe": sharpe,
        "AvgDailyTurnover": turnover["Turnover"].mean(),
        "Observations": len(eq),
    }, eq

def main():
    data = download()
    if len(data) < 12:
        raise RuntimeError(f"Too few assets downloaded: {len(data)}")
    panel = build_panel(data)

    results = []
    curves = {}
    for k in TOP_KS:
        r, eq = run(panel, k)
        if r:
            results.append(r)
            curves[k] = eq

    # Static 18-asset equal-weight benchmark with the same cost convention.
    benchmark = panel.copy()
    benchmark["NextReturn"] = benchmark.groupby("Asset")["Return_1d"].shift(-1)
    b = benchmark.groupby("Date")["NextReturn"].mean().dropna()
    b_eq = (1+b).cumprod()*10000
    b_dd = b_eq / b_eq.cummax() - 1
    b_sharpe = np.sqrt(252)*b.mean()/b.std() if b.std() > 0 else np.nan

    results.append({
        "TopK": 18,
        "FinalEquity": b_eq.iloc[-1],
        "TotalReturn": b_eq.iloc[-1]/10000-1,
        "CAGR": (b_eq.iloc[-1]/10000)**(365.25/max((b.index[-1]-b.index[0]).days,1))-1,
        "MaxDrawdown": b_dd.min(),
        "Sharpe": b_sharpe,
        "AvgDailyTurnover": 0.0,
        "Observations": len(b),
    })

    res = pd.DataFrame(results).sort_values("TopK")
    res.to_csv("dynamic_universe_screen_results.csv", index=False)

    # Save selected assets on the latest date for transparency.
    latest = panel[panel["Date"] == panel["Date"].max()].copy()
    latest = score_date(latest).sort_values("score", ascending=False)
    latest[[
        "Asset","score","Return_20d","Return_60d","Dist_SMA20",
        "Dist_SMA50","Vol_20d","DollarVolume20"
    ]].to_csv("dynamic_universe_latest_ranking.csv", index=False)

    for k, eq in curves.items():
        eq.to_csv(f"dynamic_universe_equity_k{k}.csv", index=False)

    print("\nDYNAMIC UNIVERSE SCREEN")
    print(res.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print("\nLatest ranking:")
    print(latest[["Asset","score"]].to_string(index=False, float_format=lambda x: f"{x:.4f}"))

if __name__ == "__main__":
    main()
