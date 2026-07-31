
# features.py - Indicatori Avanzati (Versione 2.0)

import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    """Calcola l'indicatore di forza relativa (RSI)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def create_features(df):
    """Calcola le feature avanzate per l'IA"""
    df = df.copy()
    
    # 1. Rendimenti e Volatilità
    df['return_1d'] = df['Close'].pct_change(1)
    df['return_5d'] = df['Close'].pct_change(5)
    df['volatility_7d'] = df['return_1d'].rolling(7).std()
    
    # 2. Medie Mobili
    df['sma_10'] = df['Close'].rolling(10).mean()
    df['sma_50'] = df['Close'].rolling(50).mean()
    df['sma_ratio'] = df['sma_10'] / df['sma_50']
    
    # 3. RSI (Relative Strength Index)
    df['rsi_14'] = calculate_rsi(df['Close'], 14)
    
    # 4. Variazione del Volume di scambio
    df['volume_change'] = df['Volume'].pct_change(1)
    
    # 5. Target per l'IA
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    df = df.dropna()
    print(f"Feature avanzate (v2.0) create! Candele: {len(df)}")
    return df