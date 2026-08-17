import yfinance as yf
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier

ASSETS = ['BTC-USD', 'NVDA', 'QQQ', 'GLD']

def calculate_features(df):
    df['Returns'] = df['Close'].pct_change()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Target: 1 se il prezzo sale domani, 0 se scende
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df.dropna()

def train_ensemble():
    models = {}
    
    for ticker in ASSETS:
        print(f"Addestramento Ensemble per {ticker}...")
        data = yf.Ticker(ticker).history(period="2y")
        df = calculate_features(data)
        
        features = ['Returns', 'SMA_10', 'SMA_50', 'RSI']
        X = df[features]
        y = df['Target']
        
        # 1. XGBoost
        m_xgb = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
        m_xgb.fit(X, y)
        
        # 2. LightGBM
        m_lgb = LGBMClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
        m_lgb.fit(X, y)
        
        # 3. Random Forest
        m_rf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
        m_rf.fit(X, y)
        
        # Calcolo votazione per l'ultimo dato disponibile
        last_features = X.iloc[[-1]]
        prob_xgb = m_xgb.predict_proba(last_features)[0][1]
        prob_lgb = m_lgb.predict_proba(last_features)[0][1]
        prob_rf = m_rf.predict_proba(last_features)[0][1]
        
        # Media delle probabilità
        prob_ensemble = (prob_xgb + prob_lgb + prob_rf) / 3.0
        
        models[ticker] = {
            'xgb': m_xgb,
            'lgb': m_lgb,
            'rf': m_rf,
            'last_prob': prob_ensemble
        }
        
    joblib.dump(models, 'ensemble_models.pkl')
    print("Addestramento Ensemble completato e salvato!")

if __name__ == "__main__":
    train_ensemble()
