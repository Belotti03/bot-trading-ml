# main.py - Direttore d'Orchestra con Tracciamento P&L (v5.0)

import joblib
import config
from data_loader import download_data
from features import create_features
from execution import execute_trade
from logger import log_trade
from notifier import send_telegram_alert
from portfolio_tracker import update_portfolio, get_portfolio_summary

def run_bot():
    print("=== AVVIO BOT DI TRADING MULTI-ASSET CON TRACCIAMENTO P&L (v5.0) ===")
    
    summary_reports = []
    
    for ticker in config.PORTFOLIO:
        print("\n" + "="*45)
        print(f"🔍 ANALISI ASSET: {ticker}")
        print("="*45)
        
        clean_name = ticker.replace('-', '_').replace('=', '_')
        model_filename = f"model_{clean_name}.joblib"
        
        try:
            model = joblib.load(model_filename)
        except Exception:
            print(f"❌ Modello {model_filename} non trovato. Esegui prima 'python model_engine.py'.")
            continue

        raw_data = download_data(ticker)
        df = create_features(raw_data)
        
        feature_cols = ['return_1d', 'return_5d', 'volatility_7d', 'sma_ratio', 'rsi_14', 'volume_change']
        latest_features = df[feature_cols].iloc[[-1]]
        latest_date = df.index[-1].strftime('%Y-%m-%d')
        latest_price = df['Close'].iloc[-1]
        
        prob_up = model.predict_proba(latest_features)[0][1]
        
        if prob_up >= config.LONG_THRESHOLD:
            action = "LONG"
            emoji = "🟢"
        elif prob_up <= config.SHORT_THRESHOLD:
            action = "SHORT"
            emoji = "🔴"
        else:
            action = "CASH"
            emoji = "⚪"
        
        print(f"💰 Prezzo attuale: ${latest_price:,.2f}")
        print(f"🤖 Probabilità Rialzo IA: {prob_up:.2%}")
        print(f"{emoji} DECISIONE FINALE: {action}")
        
        # Aggiornamento posizione e calcolo P&L simulato
        pos_info, event_note = update_portfolio(ticker, action, latest_price)
        
        # Esecuzione simulata
        execute_trade(action, latest_price, ticker)
        
        # Riga report per Telegram
        summary_reports.append(
            f"{emoji} <b>{ticker}</b>: <code>{action}</code> (Prob: {prob_up:.1%} | ${latest_price:,.2f}){event_note}"
        )

    # Calcolo bilancio finale del portafoglio
    total_val, pnl_usd, pnl_pct = get_portfolio_summary()
    
    # Registrazione su CSV per ogni ciclo
    log_trade(latest_date, "PORTFOLIO", 0.0, 0.0, "SUMMARY", "OK", total_val, pnl_usd, pnl_pct)

    # Inserimento sezione Bilancio nella notifica Telegram
    pnl_sign = "+" if pnl_usd >= 0 else ""
    pnl_emoji = "📈" if pnl_usd >= 0 else "📉"
    
    balance_text = (
        f"\n💼 <b>CAPITALE PORTAFOGLIO</b>: <code>${total_val:,.2f}</code>\n"
        f"{pnl_emoji} <b>P&amp;L Totale</b>: <code>{pnl_sign}${pnl_usd:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</code>"
    )

    if summary_reports:
        full_message = "🤖 <b>REPORT PORTAFOGLIO GIORNALIERO</b>\n\n" + "\n".join(summary_reports) + "\n" + balance_text
        send_telegram_alert(full_message)

if __name__ == "__main__":
    run_bot()