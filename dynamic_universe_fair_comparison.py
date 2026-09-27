import pandas as pd
import numpy as np
import yfinance as yf

ASSETS = [
    "BTC-USD","ETH-USD","NVDA","AMD","MSTR","COIN","TSM","PLTR","ARM",
    "SMCI","TSLA","META","AMZN","GOOGL","AAPL","MSFT","QQQ","GLD"
]
TOP_KS = [8, 12, 18]
LOOKBACK = "5y"
FEE = 0.001
SLIPPAGE = 0.0005
COST_PER_SIDE = FEE + SLIPPAGE  # 0.0015

START = "2024-10-15"
END = "2026-09-25"

def download():
    data = {}
    for a in ASSETS:
        df = yf.download(a, period=LOOKBACK, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        if "Volume" not in df:
            df["Volume"] = np.nan
        data[a] = df
    return data

def prepare(data):
    rows = []
    for a, df in data.items():
        x = df.copy()
        close = x["Close"].astype(float)
        vol = x["Volume"].astype(float)
        x["Return_20d"] = close.pct_change(20)
        x["Return_60d"] = close.pct_change(60)
        x["SMA_20"] = close.rolling(20).mean()
        x["SMA_50"] = close.rolling(50).mean()
        x["Dist_SMA20"] = close / x["SMA_20"] - 1
        x["Dist_SMA50"] = close / x["SMA_50"] - 1
        x["Vol_20d"] = close.pct_change().rolling(20).std() * np.sqrt(252)
        x["DollarVolume"] = close * vol
        x["DollarVolume20"] = x["DollarVolume"].rolling(20).median()
        x["Asset"] = a
        x = x.reset_index()
        x["Date"] = pd.to_datetime(x["Date"]).dt.tz_localize(None)
        rows.append(x[["Date","Asset","Close","Return_20d","Return_60d",
                       "Dist_SMA20","Dist_SMA50","Vol_20d","DollarVolume20"]])
    return pd.concat(rows, ignore_index=True)

def score_and_returns(panel):
    p = panel.copy()
    # Cross-sectional ranks within each date. Higher score = preferred.
    for col in ["Return_20d","Return_60d","Dist_SMA20","Dist_SMA50","DollarVolume20"]:
        p[col+"_rank"] = p.groupby("Date")[col].rank(pct=True)
    p["Vol_inv_rank"] = p.groupby("Date")["Vol_20d"].rank(pct=True, ascending=False)
    p["Score"] = (
        0.25*p["Return_20d_rank"] +
        0.25*p["Return_60d_rank"] +
        0.15*p["Dist_SMA20_rank"] +
        0.15*p["Dist_SMA50_rank"] +
        0.10*p["Vol_inv_rank"] +
        0.10*p["DollarVolume20_rank"]
    )
    # Next-day close-to-close return, shifted within each asset.
    p["NextRet"] = p.groupby("Asset")["Close"].shift(-1) / p["Close"] - 1
    p = p[(p["Date"] >= START) & (p["Date"] <= END)].copy()
    return p

def simulate(panel, k, with_costs=True):
    daily = []
    prev = set()
    dates = sorted(panel["Date"].dropna().unique())
    for d in dates:
        day = panel[panel["Date"] == d].dropna(subset=["Score","NextRet"])
        if len(day) < k:
            continue
        selected = set(day.nlargest(k, "Score")["Asset"])
        ret = day[day["Asset"].isin(selected)]["NextRet"].mean()
        turnover = len(prev.symmetric_difference(selected)) / k if prev else 1.0
        cost = turnover * COST_PER_SIDE if with_costs else 0.0
        daily.append((d, ret - cost, turnover))
        prev = selected
    out = pd.DataFrame(daily, columns=["Date","Return","Turnover"])
    if out.empty:
        return None
    out["Equity"] = 10000 * (1 + out["Return"]).cumprod()
    total = out["Equity"].iloc[-1] / 10000 - 1
    years = (out["Date"].iloc[-1] - out["Date"].iloc[0]).days / 365.25
    cagr = (out["Equity"].iloc[-1] / 10000) ** (1/years) - 1 if years > 0 else np.nan
    peak = out["Equity"].cummax()
    dd = out["Equity"] / peak - 1
    sharpe = np.sqrt(252) * out["Return"].mean() / out["Return"].std(ddof=1) if out["Return"].std(ddof=1) else np.nan
    return {
        "TopK": k,
        "WithCosts": with_costs,
        "FinalEquity": out["Equity"].iloc[-1],
        "TotalReturn": total,
        "CAGR": cagr,
        "MaxDrawdown": dd.min(),
        "Sharpe": sharpe,
        "AvgDailyTurnover": out["Turnover"].mean(),
        "Observations": len(out),
        "StartDate": out["Date"].iloc[0],
        "EndDate": out["Date"].iloc[-1],
    }

data = download()
panel = score_and_returns(prepare(data))

results = []
for k in TOP_KS:
    results.append(simulate(panel, k, True))
    results.append(simulate(panel, k, False))

# Static equal-weight 18-asset benchmark, both gross and with comparable
# daily turnover assumptions (static has zero turnover after initial allocation).
# To keep the comparison clean, the static benchmark uses the same available
# asset set and date intersection.
def static_18(panel, with_costs):
    x = panel.dropna(subset=["NextRet"]).copy()
    g = x.groupby("Date")["NextRet"].mean().reset_index(name="Return")
    if with_costs:
        # One initial allocation cost only; no subsequent turnover.
        g["Return"] -= COST_PER_SIDE
    else:
        g["Return"] = g["Return"]
    g["Equity"] = 10000 * (1 + g["Return"]).cumprod()
    total = g["Equity"].iloc[-1] / 10000 - 1
    years = (g["Date"].iloc[-1] - g["Date"].iloc[0]).days / 365.25
    cagr = (g["Equity"].iloc[-1] / 10000) ** (1/years) - 1 if years > 0 else np.nan
    peak = g["Equity"].cummax()
    dd = g["Equity"]/peak - 1
    sd = g["Return"].std(ddof=1)
    sharpe = np.sqrt(252)*g["Return"].mean()/sd if sd else np.nan
    return {
        "TopK":18, "WithCosts":with_costs,
        "FinalEquity":g["Equity"].iloc[-1],
        "TotalReturn":total, "CAGR":cagr, "MaxDrawdown":dd.min(),
        "Sharpe":sharpe, "AvgDailyTurnover":0.0,
        "Observations":len(g), "StartDate":g["Date"].iloc[0],
        "EndDate":g["Date"].iloc[-1]
    }

results.append(static_18(panel, True))
results.append(static_18(panel, False))

res = pd.DataFrame(results)
res.to_csv("dynamic_universe_fair_comparison.csv", index=False)

# A compact apples-to-apples table.
fair = res[res["WithCosts"] == True].copy()
fair["TotalReturnPct"] = fair["TotalReturn"]*100
fair["CAGRPct"] = fair["CAGR"]*100
fair["MaxDDPct"] = fair["MaxDrawdown"]*100
fair["Sharpe"] = fair["Sharpe"].round(4)
fair["FinalEquity"] = fair["FinalEquity"].round(2)
fair[["TopK","FinalEquity","TotalReturnPct","CAGRPct","MaxDDPct","Sharpe",
      "AvgDailyTurnover","Observations","StartDate","EndDate"]].to_csv(
          "dynamic_universe_fair_summary.csv", index=False)

print(res.to_string(index=False))
