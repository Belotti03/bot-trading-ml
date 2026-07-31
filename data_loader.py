# data_loader.py - Download Dati Multi-Asset

import yfinance as yf
import pandas as pd
import config

def download_data(ticker):
    """Scarica lo storico dati per un singolo asset del portafoglio"""
    print(f"Scaricamento dati per {ticker}...")
    df = yf.download(ticker, period="4y", interval=config.TIMEFRAME, progress=False)
    
    # Gestione colonne MultiIndex restituite da yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    print(f"Dati {ticker} scaricati! Totale giorni: {len(df)}")
    return df

if __name__ == "__main__":
    download_data("NVDA")