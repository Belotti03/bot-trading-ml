import json
import os
import sys
from datetime import datetime
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ ERRORE: Credenziali Telegram mancanti nei Secrets.")
    sys.exit(1)

STATE_FILE = "portfolio_state.json"
SCOUT_FILE = "scout_signals.json"

def get_atr(ticker, period=14):
    """Calcola l'ATR in dollari per un dato ticker."""
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < period:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
        atr_val = tr.rolling(window=period).mean().iloc[-1]
        if isinstance(atr_val, pd.Series):
            atr_val = atr_val.item()
        return float(atr_val)
    except Exception as e:
        print(f"Errore calcolo ATR per {ticker}: {e}")
        return None

def check_macro_filter():
    """Filtro Macro: verifica se S&P 500 (SPY) è sopra la sua SMA 200."""
    try:
        spy = yf.download("SPY", period="1y", interval="1d", progress=False)
        if spy.empty or len(spy) < 200:
            return True, "Dati SPY insufficienti (Fallback: OK)"
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        close = spy['Close']
        sma200 = close.rolling(window=200).mean().iloc[-1]
        curr_spy = close.iloc[-1]
        
        if isinstance(sma200, pd.Series):
            sma200 = sma200.item()
        if isinstance(curr_spy, pd.Series):
            curr_spy = curr_spy.item()
            
        is_bullish = float(curr_spy) >= float(sma200)
        status_str = f"SPY ${curr_spy:.2f} >= SMA200 ${sma200:.2f}" if is_bullish else f"SPY ${curr_spy:.2f} < SMA200 ${sma200:.2f}"
        return is_bullish, status_str
    except Exception as e:
        print(f"Errore Macro Filter (SPY): {e}")
        return True, "Errore calcolo SPY (Fallback: OK)"

# Caricamento Stato Portafoglio
state = {
    "cash": 10000.0, 
    "positions": {}, 
    "initial_balance": 10000.0,
    "day_start_val": 10000.0,
    "last_run_date": ""
}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            state.update(json.load(f))
    except Exception as e:
        print(f"Errore lettura stato: {e}")

# Caricamento Segnali Scout
scout = {}
if os.path.exists(SCOUT_FILE):
    try:
        with open(SCOUT_FILE, "r") as f:
            scout = json.load(f)
    except Exception as e:
        print(f"Errore lettura scout: {e}")

ranked = sorted(scout.items(), key=lambda x: x[1].get('prob', 0), reverse=True)
top_candidates = [ticker for ticker, data in ranked if data.get('prob', 0) > 0.55][:5]

events = []
updated_positions = {}
stopped_today = set()
current_cash = float(state.get("cash", 10000.0))

# 1. GESTIONE POSIZIONI ESISTENTI (CON STOP DINAMICI ATR)
for ticker, pos in state.get("positions", {}).items():
    if not isinstance(pos, dict):
        continue
        
    curr_price = scout.get(ticker, {}).get("price", pos.get("entry_price", 1.0))
    entry_price = pos.get("entry_price", curr_price)
    peak_price = max(pos.get("peak_price", curr_price), curr_price)
    qty = pos.get("qty", 0.0)
    prob = scout.get(ticker, {}).get("prob", 0.5)
    
    if qty <= 0:
        continue

    atr = get_atr(ticker)
    if atr and curr_price > 0:
        sl_delta = atr * 2.0
        ts_delta = atr * 2.5
        stop_loss_price = entry_price - sl_delta
        trailing_stop_price = peak_price - ts_delta
    else:
        stop_loss_price = entry_price * 0.98
        trailing_stop_price = peak_price * 0.975

    if curr_price <= trailing_stop_price and curr_price > entry_price:
        p_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        stopped_today.add(ticker)
        events.append(f"🎯 TRAILING-STOP ATR ({p_pct:+.1f}%) su {ticker} (${curr_price:.2f})")
    elif curr_price <= stop_loss_price:
        p_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        stopped_today.add(ticker)
        events.append(f"🛡️ STOP-LOSS ATR ({p_pct:+.1f}%) su {ticker} (${curr_price:.2f})")
    elif prob < 0.45:
        p_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        stopped_today.add(ticker)
        events.append(f"📉 SEGNALE ML DEBOLE ({prob*100:.1f}%) -> Uscita da {ticker} ({p_pct:+.1f}%)")
    else:
        updated_positions[ticker] = {
            "qty": qty,
            "entry_price": entry_price,
            "peak_price": peak_price
        }

state["cash"] = current_cash
state["positions"] = updated_positions

# Calcolo valore totale attuale per verifica Circuit Breaker
total_portfolio_val = state["cash"] + sum(
    pos["qty"] * scout.get(t, {}).get("price", pos["entry_price"]) 
    for t, pos in state["positions"].items()
)

# Gestione tracciamento valore di inizio giornata
today_str = datetime.utcnow().strftime("%Y-%m-%d")
if state.get("last_run_date") != today_str:
    state["day_start_val"] = total_portfolio_val
    state["last_run_date"] = today_str

day_start_val = state.get("day_start_val", total_portfolio_val)
daily_drawdown = ((total_portfolio_val - day_start_val) / day_start_val) * 100

# 2. VERIFICA CONTROLLI DI RISCHIO MACRO E CIRCUIT BREAKER
macro_ok, macro_msg = check_macro_filter()
circuit_breaker_active = daily_drawdown <= -4.0

if circuit_breaker_active:
    events.append(f"🚨 CIRCUIT BREAKER ATTIVATO! Perdita giornaliera {daily_drawdown:.2f}% (soglia -4.0%). Nuovi ingressi congelati.")

if not macro_ok:
    events.append(f"🐻 MACRO FILTER ORSACCIONE: {macro_msg}. Ingressi congelati.")

# 3. INGRESSI AGENTE SCOUT (CON TETTO 30% + FILTRI DI RISCHIO)
eligible_candidates = [t for t in top_candidates if t not in stopped_today]

if eligible_candidates and state["cash"] > 500 and macro_ok and not circuit_breaker_active:
    max_per_asset = total_portfolio_val * 0.30
    alloc_per_asset = min(state["cash"] / len(eligible_candidates), max_per_asset)

    for ticker in eligible_candidates:
        if ticker not in state["positions"] and ticker in scout:
            curr_price = scout[ticker].get("price", 0)
            if curr_price > 0 and state["cash"] >= alloc_per_asset:
                qty = alloc_per_asset / curr_price
                state["positions"][ticker] = {
                    "qty": qty,
                    "entry_price": curr_price,
                    "peak_price": curr_price
                }
                state["cash"] -= alloc_per_asset
                events.append(f"🚀 ENTRATA SCOUT: {ticker} a ${curr_price:.2f} (Prob: {scout[ticker].get('prob',0)*100:.1f}%)")

# 4. REPORT FINALE
pos_report = []

for ticker, pos in state["positions"].items():
    c_price = scout.get(ticker, {}).get("price", pos.get("entry_price", 1.0))
    val = pos["qty"] * c_price
    p_pct = ((c_price - pos["entry_price"]) / pos["entry_price"]) * 100
    prob = scout.get(ticker, {}).get("prob", 0.5) * 100
    pos_report.append(f"🟢 {ticker}: LONG (${val:,.2f} | P&L: {p_pct:+.1f}% | Prob: {prob:.1f}%)")

for ticker, data in scout.items():
    if ticker not in state["positions"] and ticker in [t for t, _ in ranked[:6]]:
        pos_report.append(f"⚪ {ticker}: CASH (Prob: {data.get('prob',0)*100:.1f}% | ${data.get('price',0):.2f})")

initial_bal = float(state.get("initial_balance", 10000.0))
pnl_tot = ((total_portfolio_val - initial_bal) / initial_bal) * 100

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=4)

msg = f"🤖 REPORT AGENTE SCOUT (18 ASSET)\n\n"
msg += "\n".join(pos_report) + "\n\n"
if events:
    msg += "⚡ EVENTI GIORNALIERI:\n" + "\n".join(events) + "\n\n"
msg += f"💼 CAPITALE PORTAFOGLIO:\n${total_portfolio_val:,.2f} (Daily P&L: {daily_drawdown:+.2f}%)\n"
msg += f"📈 P&L Totale: {pnl_tot:+.2f}%\n"
msg += f"🌐 Macro Status: {'BULLISH 🟢' if macro_ok else 'BEARISH 🔴'}"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
