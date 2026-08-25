import yfinance as yf
import pandas as pd
import numpy as np
import json
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier

# Paniere Ibrido ad Alto Momentum: Crypto, Big Tech, Semiconduttori e Beni Rifugio
SCOUT_POOL = [
    'BTC-USD', 'ETH-USD', 'NVDA', 'AMD', 'MSTR', 'COIN',
    'TSM', 'PLTR', 'ARM', 'SMCI', 'TSLA', 'META',
    'AMZN', 'GOOGL', 'AAPL', 'MSFT', 'QQQ', 'GLD'
]

def calculate_features(df):
    df['Returns'] = df['Close'].pct_change()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df.dropna()

def run_scout_and_train():
    scout_results = {}
    
    for ticker in SCOUT_POOL:
        print(f"Scansione Agente Scout per {ticker}...")
        try:
            data = yf.Ticker(ticker).history(period="2y")
            if len(data) < 100:
                continue
            df = calculate_features(data)
            
            features = ['Returns', 'SMA_10', 'SMA_50', 'RSI']
            X = df[features]
            y = df['Target']
            
            m_xgb = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
            m_xgb.fit(X, y)
            
            m_lgb = LGBMClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
            m_lgb.fit(X, y)
            
            m_rf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
            m_rf.fit(X, y)
            
            last_features = X.iloc[[-1]]
            prob_xgb = m_xgb.predict_proba(last_features)[0][1]
            prob_lgb = m_lgb.predict_proba(last_features)[0][1]
            prob_rf = m_rf.predict_proba(last_features)[0][1]
            
            prob_ensemble = float((prob_xgb + prob_lgb + prob_rf) / 3.0)
            last_price = float(df['Close'].iloc[-1])
            
            scout_results[ticker] = {
                'prob': prob_ensemble,
                'price': last_price
            }
        except Exception as e:
            print(f"Errore su {ticker}: {e}")
            
    with open('scout_signals.json', 'w') as f:
        json.dump(scout_results, f, indent=4)
        
    print("Scansione Agente Scout completata con successo!")

if __name__ == "__main__":
    run_scout_and_train()
