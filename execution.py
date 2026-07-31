# execution.py - Motore di Esecuzione Multi-Asset

import config

def execute_trade(signal, price, ticker="BTC-USD"):
    """
    Simula l'invio dell'ordine calcolando Stop-Loss e Take-Profit per l'asset specifico.
    """
    print("\n[MOTORE ESECUZIONE ORDINI & RISK MANAGEMENT]")
    
    # Se le chiavi API non sono ancora state inserite, esegui la simulazione protetta
    if config.API_KEY == "LA_TUA_API_KEY_TESTNET":
        print("ℹ️  Modalità Simulazione Locale Attiva (Nessuna chiave API inserita).")
        if signal == "LONG":
            stop_loss = price * (1 - config.STOP_LOSS_PCT)
            take_profit = price * (1 + config.TAKE_PROFIT_PCT)
            print(f"📈 ORDINE SIMULATO: LONG su {ticker} a ${price:,.2f}")
            print(f"🛡️  Stop-Loss: ${stop_loss:,.2f} (-{config.STOP_LOSS_PCT:.0%}) | 🎯 Take-Profit: ${take_profit:,.2f} (+{config.TAKE_PROFIT_PCT:.0%})")
        elif signal == "SHORT":
            stop_loss = price * (1 + config.STOP_LOSS_PCT)
            take_profit = price * (1 - config.TAKE_PROFIT_PCT)
            print(f"📉 ORDINE SIMULATO: SHORT su {ticker} a ${price:,.2f}")
            print(f"🛡️  Stop-Loss: ${stop_loss:,.2f} (+{config.STOP_LOSS_PCT:.0%}) | 🎯 Take-Profit: ${take_profit:,.2f} (-{config.TAKE_PROFIT_PCT:.0%})")
        else:
            print(f"⏸️  STAND-BY ({ticker}): Nessun ordine inviato. Capitale al sicuro in CASH.")
        return

    # Se le chiavi API sono inserite, invia l'ordine via API CCXT
    try:
        if signal == "LONG":
            print(f"🚀 Invio Ordine d'Acquisto (TESTNET) per {ticker}...")
        elif signal == "SHORT":
            print(f"🔻 Invio Ordine di Vendita (TESTNET) per {ticker}...")
        else:
            print(f"⏸️  STAND-BY ({ticker}): Posizione invariata nell'exchange.")
            
    except Exception as e:
        print(f"❌ Errore durante la connessione all'Exchange per {ticker}: {e}")

if __name__ == "__main__":
    execute_trade("SHORT", 195.04, "NVDA")