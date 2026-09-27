import pandas as pd
import numpy as np
import yfinance as yf

ASSETS = [
    "BTC-USD","ETH-USD","NVDA","AMD","MSTR","COIN","TSM","PLTR","ARM",
    "SMCI","TSLA","META","AMZN","GOOGL","AAPL","MSFT","QQQ","GLD"
]
TOP_KS = [8, 12]
START = "2024-10-15"
END = "2026-09-24"

FEE = 0.001
SLIPPAGE = 0.0005
COST_PER_SIDE = FEE + SLIPPAGE

def dl():
    out = {}
    for a in ASSETS:
        df = yf.download(a, period="5y", auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"]).copy()
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df.get("Volume", np.nan), errors="coerce")
        df = df.dropna(subset=["Close"])
        out[a] = df
    return out

def panelize(data):
    rows=[]
    for a,df in data.items():
        x=df.copy()
        c=x["Close"]
        v=x["Volume"]
        x["Return_20d"]=c.pct_change(20)
        x["Return_60d"]=c.pct_change(60)
        s20=c.rolling(20).mean()
        s50=c.rolling(50).mean()
        x["Dist_SMA20"]=c/s20-1
        x["Dist_SMA50"]=c/s50-1
        x["Vol_20d"]=c.pct_change().rolling(20).std()*np.sqrt(252)
        x["DollarVolume20"]=(c*v).rolling(20).median()
        x["Asset"]=a
        x=x.reset_index()
        x["Date"]=pd.to_datetime(x["Date"]).dt.tz_localize(None)
        rows.append(x[["Date","Asset","Close","Return_20d","Return_60d",
                       "Dist_SMA20","Dist_SMA50","Vol_20d","DollarVolume20"]])
    return pd.concat(rows,ignore_index=True)

def score(p):
    p=p.copy()
    for col in ["Return_20d","Return_60d","Dist_SMA20","Dist_SMA50","DollarVolume20"]:
        p[col+"_rank"]=p.groupby("Date")[col].rank(pct=True)
    # Higher rank = lower volatility.
    p["Vol_inv_rank"]=p.groupby("Date")["Vol_20d"].rank(pct=True,ascending=False)
    p["Score"]=(
        .25*p["Return_20d_rank"]+
        .25*p["Return_60d_rank"]+
        .15*p["Dist_SMA20_rank"]+
        .15*p["Dist_SMA50_rank"]+
        .10*p["Vol_inv_rank"]+
        .10*p["DollarVolume20_rank"]
    )
    p["NextRet"]=p.groupby("Asset")["Close"].shift(-1)/p["Close"]-1
    return p[(p["Date"]>=START)&(p["Date"]<=END)].copy()

def metrics(g):
    eq=10000*(1+g["Return"]).cumprod()
    total=eq.iloc[-1]/10000-1
    years=(g["Date"].iloc[-1]-g["Date"].iloc[0]).days/365.25
    cagr=(eq.iloc[-1]/10000)**(1/years)-1
    dd=(eq/eq.cummax()-1).min()
    sd=g["Return"].std(ddof=1)
    sharpe=np.sqrt(252)*g["Return"].mean()/sd if sd else np.nan
    return eq.iloc[-1],total,cagr,dd,sharpe,len(g)

def dynamic(p,k):
    rows=[]
    prev=set()
    for d in sorted(p["Date"].unique()):
        day=p[p["Date"]==d].dropna(subset=["Score","NextRet"])
        if len(day)<k: continue
        sel=set(day.nlargest(k,"Score")["Asset"])
        gross=day[day["Asset"].isin(sel)]["NextRet"].mean()
        turnover=len(prev.symmetric_difference(sel))/k if prev else 1.0
        net=gross-turnover*COST_PER_SIDE
        rows.append((d,gross,net,turnover))
        prev=sel
    return pd.DataFrame(rows,columns=["Date","GrossReturn","Return","Turnover"])

def static_equal_weight(p):
    # True static 18: every day is equal-weight across the same 18 assets.
    # No selection, no turnover after initial allocation.
    x=p.dropna(subset=["NextRet"]).copy()
    g=x.groupby("Date")["NextRet"].agg(["count","mean"]).reset_index()
    g=g[g["count"]==len(ASSETS)].copy()
    # Initial allocation cost only; thereafter turnover = 0.
    g["GrossReturn"]=g["mean"]
    g["Return"]=g["GrossReturn"]
    if len(g):
        g.loc[g.index[0],"Return"]-=COST_PER_SIDE
    g["Turnover"]=0.0
    return g[["Date","GrossReturn","Return","Turnover"]]

data=dl()
p=score(panelize(data))

rows=[]
for k in TOP_KS:
    g=dynamic(p,k)
    eq,total,cagr,dd,sh,n=metrics(g)
    rows.append(["Dynamic Top-"+str(k),k,eq,total,cagr,dd,sh,g["Turnover"].mean(),n,
                 g["Date"].iloc[0],g["Date"].iloc[-1]])

g=static_equal_weight(p)
eq,total,cagr,dd,sh,n=metrics(g)
rows.append(["Static 18 equal-weight",18,eq,total,cagr,dd,sh,0.0,n,
             g["Date"].iloc[0],g["Date"].iloc[-1]])

out=pd.DataFrame(rows,columns=["Strategy","TopK","FinalEquity","TotalReturn",
"CAGR","MaxDrawdown","Sharpe","AvgDailyTurnover","Observations","StartDate","EndDate"])
out.to_csv("dynamic_universe_final_comparison.csv",index=False)

print(out.to_string(index=False))
