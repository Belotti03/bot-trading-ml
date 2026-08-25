import json
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "portfolio_state.json"
SCOUT_FILE = "scout_signals.json"

state = {"cash": 10000.0, "positions": {}, "initial_balance": 10000.0}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            loaded_state = json.load(f)
            if isinstance(loaded_state, dict):
                state.update(loaded_state)
    except Exception as e:
        print(f"Errore lettura portfolio_state: {e}")

scout = {}
if os.path.exists(SCOUT_FILE):
    try:
        with open(SCOUT_FILE, "r") as f:
            scout = json.load(f)
    except Exception as e:
        print(f"Errore lettura scout_signals: {e}")

ranked = sorted(scout.items(), key=lambda x: x[1].get('prob', 0), reverse=True)
top_candidates = [ticker for ticker, data in ranked if data.get('prob', 0) > 0.55][:5]

events = []
updated_positions = {}
current_cash = float(state.get("cash", 10000.0))

raw_positions = state.get("positions", {})
if not isinstance(raw_positions, dict):
    raw_positions = {}

for ticker, pos in raw_positions.items():
    if not isinstance(pos, dict):
        continue
        
    curr_price = scout.get(ticker, {}).get("price", pos.get("entry_price", 1.0))
    entry_price = pos.get("entry_price", curr_price)
    peak_price = max(pos.get("peak_price", curr_price), curr_price)
    qty = pos.get("qty", 0.0)
    
    if qty <= 0:
        continue

    trailing_stop_price = peak_price * 0.975
    stop_loss_price = entry_price * 0.98
    
    if curr_price <= trailing_stop_price and curr_price > entry_price:
        profit_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        events.append(f"🎯 **TRAILING-STOP ({profit_pct:+.1f}%) su {ticker}** (${curr_price:.2f})")
    elif curr_price <= stop_loss_price:
        loss_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        events.append(f"🛡️ **STOP-LOSS ({loss_pct:+.1f}%) su {ticker}** (${curr_price:.2f})")
    else:
        updated_positions[ticker] = {
            "qty": qty,
            "entry_price": entry_price,
            "peak_price": peak_price
        }

state["cash"] = current_cash
state["positions"] = updated_positions

if top_candidates and state["cash"] > 500:
    alloc_per_asset = state["cash"] / len(top_candidates)
    for ticker in top_candidates:
        if ticker not in state["positions"] and ticker in scout:
            curr_price = scout[ticker].get("price", 0)
            if curr_price > 0:
                qty = alloc_per_asset / curr_price
                state["positions"][ticker] = {
                    "qty": qty,
                    "entry_price": curr_price,
                    "peak_price": curr_price
                }
                state["cash"] -= alloc_per_asset
                events.append(f"🚀 **ENTRATA SCOUT:** {ticker} a ${curr_price:.2f} (Prob: {scout[ticker].get('prob',0)*100:.1f}%)")

total_val = state["cash"]
pos_report = []

for ticker, pos in state["positions"].items():
    c_price = scout.get(ticker, {}).get("price", pos.get("entry_price", 1.0))
    val = pos["qty"] * c_price
    total_val += val
    entry_p = pos.get("entry_price", c_price)
    p_pct = ((c_price - entry_p) / entry_p) * 100 if entry_p > 0 else 0.0
    prob = scout.get(ticker, {}).get("prob", 0.5) * 100
    pos_report.append(f"🟢 **{ticker}**: LONG (${val:,.2f} | P&L: {p_pct:+.1f}% | Prob: {prob:.1f}%)")

for ticker, data in scout.items():
    if ticker not in state["positions"] and ticker in [t for t, _ in ranked[:6]]:
        pos_report.append(f"⚪ **{ticker}**: CASH (Prob: {data.get('prob',0)*100:.1f}% | ${data.get('price',0):.2f})")

initial_bal = float(state.get("initial_balance", 10000.0))
pnl_tot = ((total_val - initial_bal) / initial_bal) * 100

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=4)

msg = f"🤖 **REPORT AGENTE SCOUT (18 ASSET)**\n\n"
msg += "\n".join(pos_report) + "\n\n"
if events:
    msg += "⚡ **EVENTI GIORNALIERI:**\n" + "\n".join(events) + "\n\n"
msg += f"💼 **CAPITALE PORTAFOGLIO:**\n${total_val:,.2f}\n"
msg += f"📈 **P&L Totale:** {pnl_tot:+.2f}%"

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
