# portfolio_tracker.py - Tracciamento Portafoglio Virtuale e P&L (v1.0)

import json
import os
import config

STATE_FILE = "portfolio_state.json"

def load_portfolio_state():
    """Carica lo stato del portafoglio da file JSON o lo inizializza con $10,000"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Inizializzazione capitale ($10.000 divisi equamente tra gli asset)
    num_assets = len(config.PORTFOLIO)
    capital_per_asset = config.INITIAL_CAPITAL / num_assets
    
    state = {
        "initial_capital": config.INITIAL_CAPITAL,
        "positions": {}
    }
    for ticker in config.PORTFOLIO:
        state["positions"][ticker] = {
            "action": "CASH",
            "entry_price": 0.0,
            "allocated_capital": capital_per_asset,
            "current_value": capital_per_asset
        }
    return state

def save_portfolio_state(state):
    """Salva lo stato attuale del portafoglio"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def update_portfolio(ticker, new_action, current_price):
    """
    Aggiorna la posizione, il bilancio dell'asset e controlla Stop-Loss / Take-Profit
    """
    state = load_portfolio_state()
    pos = state["positions"].get(ticker, {
        "action": "CASH",
        "entry_price": 0.0,
        "allocated_capital": config.INITIAL_CAPITAL / len(config.PORTFOLIO),
        "current_value": config.INITIAL_CAPITAL / len(config.PORTFOLIO)
    })
    
    prev_action = pos["action"]
    prev_entry = pos["entry_price"]
    alloc = pos["allocated_capital"]
    note = ""
    
    # 1. Calcolo rendimento della posizione aperta in precedenza
    if prev_action in ["LONG", "SHORT"] and prev_entry > 0:
        if prev_action == "LONG":
            ret = (current_price - prev_entry) / prev_entry
        else: # SHORT
            ret = (prev_entry - current_price) / prev_entry
            
        # Controllo Take Profit e Stop Loss
        if ret >= config.TAKE_PROFIT_PCT:
            ret = config.TAKE_PROFIT_PCT
            note = " 🎯 TAKE-PROFIT (+4%)"
            alloc = alloc * (1 + ret)
            prev_action = "CASH"
        elif ret <= -config.STOP_LOSS_PCT:
            ret = -config.STOP_LOSS_PCT
            note = " 🛡️ STOP-LOSS (-2%)"
            alloc = alloc * (1 + ret)
            prev_action = "CASH"
        else:
            alloc = alloc * (1 + ret)

    # 2. Aggiornamento posizione per il nuovo segnale
    if new_action == "CASH":
        pos["action"] = "CASH"
        pos["entry_price"] = 0.0
        pos["allocated_capital"] = alloc
        pos["current_value"] = alloc
    elif new_action in ["LONG", "SHORT"]:
        pos["action"] = new_action
        pos["entry_price"] = current_price
        pos["allocated_capital"] = alloc
        pos["current_value"] = alloc
        
    state["positions"][ticker] = pos
    save_portfolio_state(state)
    return pos, note

def get_portfolio_summary():
    """Calcola il saldo totale del portafoglio e il P&L ($ e %)"""
    state = load_portfolio_state()
    total_val = sum(p["current_value"] for p in state["positions"].values())
    init_cap = state.get("initial_capital", config.INITIAL_CAPITAL)
    pnl_usd = total_val - init_cap
    pnl_pct = (pnl_usd / init_cap) * 100 if init_cap > 0 else 0.0
    return total_val, pnl_usd, pnl_pct