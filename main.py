import json
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "portfolio_state.json"
SCOUT_FILE = "scout_signals.json"

if not os.path.exists(STATE_FILE):
    state = {
        "cash": 10000.0,
        "positions": {},
        "initial_balance": 10000.0
    }
else:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

with open(SCOUT_FILE, "r") as f:
    scout = json.load(f)

ranked = sorted(scout.items(), key=lambda x: x[1]['prob'], reverse=True)
top_candidates = [ticker for ticker, data in ranked if data['prob'] > 0.55][:5]

events = []
updated_positions = {}
current_cash = state.get("cash", 10000.0)

# 1. Trailing Stop (-2.5% dal picco massimo) & Stop Loss (-2% dall'ingresso)
for ticker, pos in state.get("positions", {}).items():
    if ticker in scout:
        curr_price = scout[ticker]["price"]
        entry_price = pos.get("entry_price", curr_price)
        peak_price = max(pos.get("peak_price", curr_price), curr_price)
        qty = pos["qty"]
        
        trailing_stop_price = peak_price * 0.975 # Trailing Stop dinamico
        stop_loss_price = entry_price * 0.98     # Protezione del capitale
        
        if curr_price <= trailing_stop_price and curr_price > entry_price:
            profit_pct = ((curr_price - entry_price) / entry_price) * 100
            current_cash += qty * curr_price
            events.append(f"🎯 **TRAILING-STOP ({profit_pct:+.1f}%) su {ticker}** (Incassato a ${curr_price:.2f})")
        elif curr_price <= stop_loss_price:
            loss_pct = ((curr_price - entry_price) / entry_price) * 100
            current_cash += qty * curr_price
            events.append(f"🛡️ **STOP-LOSS ({loss_pct:+.1f}%) su {ticker}** (Uscita a ${curr_price:.2f})")
        else:
            pos["peak_price"] = peak_price
            updated_positions[ticker] = pos

state["cash"] = current_cash
state["positions"] = updated_positions

# 2. Allocazione sui Top 5 Asset dello Scout
if top_candidates and state["cash"] > 500:
    alloc_per_asset = state["cash"] / len(top_candidates)
    for ticker in top_candidates:
        if ticker not in state["positions"]:
            curr_price = scout[ticker]["price"]
            qty = alloc_per_asset / curr_price
            state["positions"][ticker] = {
                "qty": qty,
                "entry_price": curr_price,
                "peak_price": curr_price
            }
            state["cash"] -= alloc_per_asset
            events.append(f"🚀 **ENTRATA AGENTE SCOUT:** {ticker} a ${curr_price:.2f} (Prob: {scout[ticker]['prob']*100:.1f}%)")

# 3. Generazione Report Telegram
total_val = state["cash"]
pos_report = []

for ticker, pos in state["positions"].items():
    c_price = scout[ticker]["price"] if ticker in scout else pos["entry_price"]
    val = pos["qty"] * c_price
    total_val += val
    p_pct = ((c_price - pos["entry_price"]) / pos["entry_price"]) * 100
    prob = scout[ticker]["prob"] * 100 if ticker in scout else 50.0
    pos_report.append(f"🟢 **{ticker}**: LONG (${val:,.2f} | P&L: {p_pct:+.1f}% | Prob: {prob:.1f}%)")

for ticker, data in scout.items():
    if ticker not in state["positions"] and ticker in [t for t, _ in ranked[:6]]:
        pos_report.append(f"⚪ **{ticker}**: CASH (Prob: {data['prob']*100:.1f}% | ${data['price']:.2f})")

pnl_tot = ((total_val - state["initial_balance"]) / state["initial_balance"]) * 100

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=4)

msg = f"🤖 **REPORT AGENTE SCOUT (18-20 ASSET)**\n\n"
msg += "\n".join(pos_report) + "\n\n"
if events:
    msg += "⚡ **EVENTI GIORNALIERI:**\n" + "\n".join(events) + "\n\n"
msg += f"💼 **CAPITALE PORTAFOGLIO:**\n${total_val:,.2f}\n"
msg += f"📈 **P&L Totale:** {pnl_tot:+.2f}%"

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
