import json, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
warnings.filterwarnings("ignore")

ASSETS=["BTC-USD","ETH-USD","NVDA","AMD","MSTR","COIN","TSM","PLTR","ARM","SMCI","TSLA","META","AMZN","GOOGL","AAPL","MSFT","QQQ","GLD"]
HORIZONS=[1,3,5,10]
LOOKBACK="5y"; MIN_TRAIN_SIZE=120; STEP_SIZE=60
FEATURES=["Return_1d","Return_5d","SMA_10","SMA_50","SMA_ratio","RSI"]
OUT_DIR=Path("horizon_screen_results"); OUT_DIR.mkdir(exist_ok=True)

def rsi(s,p=14):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.rolling(p).mean(); al=l.rolling(p).mean()
    return 100-(100/(1+ag/al.replace(0,np.nan)))

def load_asset(t):
    df=yf.download(t,period=LOOKBACK,interval="1d",auto_adjust=True,progress=False,threads=False)
    if df is None or df.empty: return None
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    if "Close" not in df.columns: return None
    df=df[["Close"]].copy(); df["Close"]=pd.to_numeric(df["Close"],errors="coerce")
    df=df.replace([np.inf,-np.inf],np.nan).dropna()
    df=df[~df.index.duplicated(keep="last")]
    df["Return_1d"]=df.Close.pct_change()
    df["Return_5d"]=df.Close.pct_change(5)
    df["SMA_10"]=df.Close.rolling(10).mean()
    df["SMA_50"]=df.Close.rolling(50).mean()
    df["SMA_ratio"]=df.SMA_10/df.SMA_50
    df["RSI"]=rsi(df.Close)
    return df

def dataset(df,h):
    x=df.copy(); f=x.Close.shift(-h)
    x["Target"]=np.where(f.notna(),(f>x.Close).astype(int),np.nan)
    x=x.dropna(subset=FEATURES+["Target"])
    X=x[FEATURES].replace([np.inf,-np.inf],np.nan); y=x.Target.astype(int)
    v=X.notna().all(axis=1); return X.loc[v],y.loc[v]

def model():
    return Pipeline([("scale",StandardScaler()),("model",LogisticRegression(max_iter=300,random_state=42))])

def evaluate(t,df,h):
    X,y=dataset(df,h)
    if len(X)<MIN_TRAIN_SIZE+20:return None
    ps=[]; ys=[]; end=MIN_TRAIN_SIZE
    while end<len(X):
        stop=min(end+STEP_SIZE,len(X)); yt=y.iloc[:end]; xt=X.iloc[:end]
        if y.iloc[end:stop].empty: break
        if yt.nunique()<2: end=stop; continue
        m=model(); m.fit(xt,yt)
        ps.extend(m.predict_proba(X.iloc[end:stop])[:,1]); ys.extend(y.iloc[end:stop])
        end=stop
    p=np.asarray(ps); a=np.asarray(ys)
    if len(a)==0:return None
    pred=(p>=.5).astype(int)
    return dict(ticker=t,horizon=h,samples=len(a),positive_rate=float(a.mean()),
                predicted_positive_rate=float(pred.mean()),accuracy=float(accuracy_score(a,pred)),
                brier=float(brier_score_loss(a,p)),log_loss=float(log_loss(a,np.clip(p,1e-6,1-1e-6))),
                auc=float(roc_auc_score(a,p)) if len(np.unique(a))==2 else np.nan)

def main():
    data={}
    for i,t in enumerate(ASSETS,1):
        print(f"Downloading [{i}/{len(ASSETS)}] {t}")
        try:
            d=load_asset(t)
            if d is not None:data[t]=d
        except Exception as e: print("ERROR",e)
    rows=[]
    for h in HORIZONS:
        print(f"\n===== HORIZON {h} =====")
        for t,d in data.items():
            try:
                r=evaluate(t,d,h)
                if r:
                    rows.append(r); print(f"{t:8s} acc={r['accuracy']:.3f} auc={r['auc']:.3f} brier={r['brier']:.4f} logloss={r['log_loss']:.4f}")
            except Exception as e: print(t,"ERROR",e)
    if not rows: raise RuntimeError("No results")
    df=pd.DataFrame(rows); df.to_csv(OUT_DIR/"horizon_screen_asset_results.csv",index=False)
    s=df.groupby("horizon").agg(assets=("ticker","count"),samples=("samples","sum"),
        mean_accuracy=("accuracy","mean"),median_accuracy=("accuracy","median"),
        mean_auc=("auc","mean"),median_auc=("auc","median"),
        mean_brier=("brier","mean"),mean_log_loss=("log_loss","mean")).reset_index()
    s.to_csv(OUT_DIR/"horizon_screen_summary.csv",index=False)
    (OUT_DIR/"horizon_screen_summary.json").write_text(json.dumps({
        "method":"lightweight_logistic_walk_forward_screen","lookback":LOOKBACK,
        "min_train_size":MIN_TRAIN_SIZE,"step_size":STEP_SIZE,"horizons":HORIZONS,
        "screen_only":True,"summary":s.to_dict(orient="records")},indent=2),encoding="utf-8")
    print("\n===== SUMMARY =====\n",s.to_string(index=False))

if __name__=="__main__":main()
