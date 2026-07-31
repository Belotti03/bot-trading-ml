# logger.py - Registro Storico Operazioni con P&L (v5.0)

import csv
import os

LOG_FILE = "trading_log.csv"

def log_trade(date, ticker, price, probability, signal, status, total_val=0.0, pnl_usd=0.0, pnl_pct=0.0):
    """Registra l'operazione e lo stato del portafoglio nel file CSV"""
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Data", "Ticker", "Prezzo", "Probabilita_IA", 
                "Segnale", "Stato", "Capitale_Totale_USD", "PnL_USD", "PnL_PCT"
            ])
        writer.writerow([
            date, ticker, f"{price:.2f}", f"{probability:.4f}", 
            signal, status, f"{total_val:.2f}", f"{pnl_usd:.2f}", f"{pnl_pct:.2f}%"
        ])
    print("📄 Operazione registrata su 'trading_log.csv'")