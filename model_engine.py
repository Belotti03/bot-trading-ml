import yfinance as yf
import pandas as pd
import numpy as np
import json
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier

SCOUT_POOL = [
    'BTC-USD', 'ETH-USD', 'NVDA', 'AMD', 'MSTR', 'COIN',
    'TSM', 'PLTR', 'ARM', 'SMCI', 'TSLA', 'META',
    'AMZN', 'GOOGL', 'AAPL', 'MSFT', 'QQQ', 'GLD'
]

def calculate_features(df):
    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df

def run_scout_and_train():
    scout_results = {}
    
    for ticker in SCOUT_POOL:
        print(f"Scansione Agente Scout per {ticker}...")
        try:
            data = yf.Ticker(ticker).history(period="2y")
            if data.empty or len(data) < 60:
                continue
            
            df = calculate_features(data)
            last_price = float(df['Close'].iloc[-1])
            
            df_train = df.dropna(subset=['Returns', 'SMA_10', 'SMA_50', 'RSI', 'Target'])
            if len(df_train) < 50:
                continue
                
            features = ['Returns', 'SMA_10', 'SMA_50', 'RSI']
            X = df_train[features]
            y = df_train['Target']
            
            m_xgb = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
            m_xgb.fit(X, y)
            
            m_lgb = LGBMClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
            m_lgb.fit(X, y)
            
            m_rf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
            m_rf.fit(X, y)
            
            df_features = df.dropna(subset=features)
            last_features = df_features[features].iloc[[-1]]
            
            prob_xgb = m_xgb.predict_proba(last_features)[0][1]
            prob_lgb = m_lgb.predict_proba(last_features)[0][1]
            prob_rf = m_rf.predict_proba(last_features)[0][1]
            
            prob_ensemble = float((prob_xgb + prob_lgb + prob_rf) / 3.0)
            
            scout_results[ticker] = {
                'prob': prob_ensemble,
                'price': last_price
            }
        except Exception as e:
            print(f"Errore su {ticker}: {e}")
            
    with open('scout_signals.json', 'w') as f:
        json.dump(scout_results, f, indent=4)
        
    print(f"Scansione completata per {len(scout_results)} asset.")

if __name__ == "__main__":
    run_scout_and_train()
