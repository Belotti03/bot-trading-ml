import json
import os
import sys
from datetime import datetime
import requests
import yfinance as yf
import pandas as pd

from safe_state import (
    asof_problem,
    dump_json_atomic,
    is_finite_number,
    is_valid_cash,
    is_valid_price,
    is_valid_probability,
    utc_now,
    validate_state_payload
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ ERRORE: Credenziali Telegram mancanti nei Secrets.")
    sys.exit(1)

STATE_FILE = "portfolio_state.json"
SCOUT_FILE = "scout_signals.json"

# Istante unico di riferimento: tutti i segnali vengono valutati contro lo
# stesso momento, altrimenti ticker diversi potrebbero cadere ai due lati del
# margine di consolidamento.
RUN_NOW = utc_now()

def abort(message):
    """Interrompe il run senza toccare lo stato persistito."""
    # Messaggio in ASCII: lo stdout del runner non e' garantito UTF-8.
    print(f"ABORT: {message}", file=sys.stderr)
    sys.exit(1)

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
        if not is_valid_price(atr_val):
            print(f"ATR non valido per {ticker} ({atr_val!r}): uso fallback percentuale.")
            return None
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
# I default valgono SOLO se il file non esiste. Uno stato esistente non viene
# mai completato o corretto con i default: un file vuoto o parziale sarebbe un
# reset silenzioso del portafoglio e distruggerebbe l'unica evidenza.
DEFAULT_STATE = {
    "cash": 10000.0, 
    "positions": {}, 
    "initial_balance": 10000.0,
    "day_start_val": 10000.0,
    "last_run_date": ""
}

if os.path.exists(STATE_FILE):
    loaded_state = None
    try:
        with open(STATE_FILE, "r") as f:
            loaded_state = json.load(f)
    except Exception as e:
        abort(f"stato non leggibile ({e}). File non modificato.")

    if not isinstance(loaded_state, dict):
        abort("stato: il payload non è un oggetto JSON. File non modificato.")

    state_problems = validate_state_payload(loaded_state, require_complete=True)
    if state_problems:
        abort(
            "stato corrotto o incompleto: " + "; ".join(state_problems)
            + ". Nessuna operazione eseguita, file non modificato."
        )

    state = loaded_state
else:
    print(f"{STATE_FILE} assente: inizializzazione dallo stato di default.")
    state = dict(DEFAULT_STATE)

# Caricamento Segnali Scout
if not os.path.exists(SCOUT_FILE):
    abort(f"{SCOUT_FILE} assente: nessun segnale su cui operare.")

try:
    with open(SCOUT_FILE, "r") as f:
        raw_scout = json.load(f)
except Exception as e:
    abort(f"segnali scout non leggibili ({e}). File di stato non modificato.")

if not isinstance(raw_scout, dict):
    abort("segnali scout: il payload non è un oggetto JSON.")

# Dati non finiti e barre non autorizzate dalla policy di recency vengono
# scartati qui, prima di entrare in qualunque calcolo di cassa o equity.
# asof_problem riapplica la policy completa del producer: non ci si fida del
# fatto che il payload sia stato prodotto da model_engine.py.
scout = {}
rejected = {}
for ticker, entry in raw_scout.items():
    if not isinstance(entry, dict):
        rejected[ticker] = "voce non valida"
        continue
    if not is_valid_probability(entry.get("prob")):
        rejected[ticker] = f"prob {entry.get('prob')!r}"
        continue
    if not is_valid_price(entry.get("price")):
        rejected[ticker] = f"price {entry.get('price')!r}"
        continue
    recency_problem = asof_problem(entry.get("asof"), ticker, now=RUN_NOW)
    if recency_problem is not None:
        rejected[ticker] = recency_problem
        continue
    scout[ticker] = entry

if rejected:
    print("ATTENZIONE: segnali scartati: " + "; ".join(
        f"{ticker} ({reason})" for ticker, reason in sorted(rejected.items())
    ))

# Fail-closed: senza un segnale valido e recente una posizione aperta non è
# valutabile.
held_tickers = [
    ticker for ticker, pos in state.get("positions", {}).items()
    if isinstance(pos, dict)
]
unpriced = sorted(t for t in held_tickers if t not in scout)
if unpriced:
    details = ", ".join(
        f"{ticker} ({rejected.get(ticker, 'segnale assente')})"
        for ticker in unpriced
    )
    abort(
        "segnale non utilizzabile per posizioni aperte: " + details
        + ". Nessuna operazione eseguita, file di stato non modificato."
    )

ranked = sorted(scout.items(), key=lambda x: x[1].get('prob', 0), reverse=True)
top_candidates = [ticker for ticker, data in ranked if data.get('prob', 0) > 0.55][:5]

events = []
updated_positions = {}
stopped_today = set()
current_cash = float(state.get("cash", 10000.0))

# 1. GESTIONE POSIZIONI ESISTENTI (CON STOP DINAMICI ATR REATTIVI 2.0x)
for ticker, pos in state.get("positions", {}).items():
    if not isinstance(pos, dict):
        continue
        
    # I prezzi delle posizioni aperte sono già stati validati sopra.
    curr_price = float(scout[ticker]["price"])
    entry_price = pos.get("entry_price", curr_price)
    peak_price = max(pos.get("peak_price", curr_price), curr_price)
    qty = pos.get("qty", 0.0)
    prob = scout[ticker].get("prob", 0.5)
    
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

if not is_valid_cash(current_cash):
    abort(f"cassa non valida dopo la gestione posizioni ({current_cash!r}).")

state["cash"] = current_cash
state["positions"] = updated_positions

# Calcolo valore totale attuale per verifica Circuit Breaker
total_portfolio_val = state["cash"] + sum(
    pos["qty"] * scout.get(t, {}).get("price", pos["entry_price"]) 
    for t, pos in state["positions"].items()
)

if not is_finite_number(total_portfolio_val):
    abort(f"equity di portafoglio non finita ({total_portfolio_val!r}).")

# Gestione tracciamento valore di inizio giornata
today_str = datetime.utcnow().strftime("%Y-%m-%d")
if state.get("last_run_date") != today_str:
    state["day_start_val"] = total_portfolio_val
    state["last_run_date"] = today_str

day_start_val = state.get("day_start_val", total_portfolio_val)

if not is_valid_price(day_start_val):
    abort(f"day_start_val non utilizzabile ({day_start_val!r}).")

daily_drawdown = ((total_portfolio_val - day_start_val) / day_start_val) * 100

# 2. VERIFICA CONTROLLI DI RISCHIO MACRO E CIRCUIT BREAKER
macro_ok, macro_msg = check_macro_filter()
circuit_breaker_active = daily_drawdown <= -4.0

if circuit_breaker_active:
    events.append(f"🚨 CIRCUIT BREAKER ATTIVATO! Perdita giornaliera {daily_drawdown:.2f}% (soglia -4.0%). Nuovi ingressi congelati.")

if not macro_ok:
    events.append(f"🐻 MACRO FILTER ORSACCIONE: {macro_msg}. Ingressi congelati.")

# 3. INGRESSI AGENTE SCOUT (CON TETTO DINAMICO 30%/40% + FILTRI DI RISCHIO)
eligible_candidates = [t for t in top_candidates if t not in stopped_today]

if eligible_candidates and state["cash"] > 500 and macro_ok and not circuit_breaker_active:
    for ticker in eligible_candidates:
        if ticker not in state["positions"] and ticker in scout:
            curr_price = scout[ticker].get("price", 0)
            prob = scout[ticker].get("prob", 0.0)
            
            # Tetto Dinamico: 40% se probabilità >= 60%, altrimenti 30%
            cap_pct = 0.40 if prob >= 0.60 else 0.30
            max_per_asset = total_portfolio_val * cap_pct
            
            # Quota calcolata in base alla cassa residua e al Cap specifico del titolo
            remaining_slots = len([t for t in eligible_candidates if t not in state["positions"]])
            alloc_per_asset = min(state["cash"] / max(remaining_slots, 1), max_per_asset)

            if curr_price > 0 and state["cash"] >= alloc_per_asset and alloc_per_asset > 100:
                qty = alloc_per_asset / curr_price
                state["positions"][ticker] = {
                    "qty": qty,
                    "entry_price": curr_price,
                    "peak_price": curr_price
                }
                state["cash"] -= alloc_per_asset
                events.append(f"🚀 ENTRATA SCOUT: {ticker} a ${curr_price:.2f} (Prob: {prob*100:.1f}% | Cap: {int(cap_pct*100)}%)")

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

if not is_valid_price(initial_bal):
    abort(f"initial_balance non utilizzabile ({initial_bal!r}).")

pnl_tot = ((total_portfolio_val - initial_bal) / initial_bal) * 100

# Persistenza: il nuovo stato viene validato e serializzato per intero prima di
# sostituire il file, che non viene mai aperto in troncamento.
new_state_problems = validate_state_payload(state)
if new_state_problems:
    abort(
        "nuovo stato non valido: " + "; ".join(new_state_problems)
        + ". File di stato non modificato."
    )

try:
    dump_json_atomic(STATE_FILE, state)
except ValueError as e:
    abort(f"serializzazione stato rifiutata ({e}). File di stato non modificato.")

msg = f"🤖 REPORT AGENTE SCOUT (18 ASSET)\n\n"
msg += "\n".join(pos_report) + "\n\n"
if events:
    msg += "⚡ EVENTI GIORNALIERI:\n" + "\n".join(events) + "\n\n"
msg += f"💼 CAPITALE PORTAFOGLIO:\n${total_portfolio_val:,.2f} (Daily P&L: {daily_drawdown:+.2f}%)\n"
msg += f"📈 P&L Totale: {pnl_tot:+.2f}%\n"
msg += f"🌐 Macro Status: {'BULLISH 🟢' if macro_ok else 'BEARISH 🔴'}"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
