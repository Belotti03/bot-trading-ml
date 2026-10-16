import json
import os
import sys
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import requests
import yfinance as yf
import pandas as pd

from research.calendars import nyse_sessions
from safe_state import (
    SETTLEMENT_MARGIN,
    asof_problem,
    dump_json_atomic,
    is_finite_number,
    is_session_complete,
    is_valid_cash,
    is_valid_price,
    is_valid_probability,
    market_for_ticker,
    to_bar_date,
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
DATA_SAFETY_REPORT_FILE = "data_safety_report.json"

# Istante unico di riferimento: tutti i segnali vengono valutati contro lo
# stesso momento, altrimenti ticker diversi potrebbero cadere ai due lati del
# margine di consolidamento.
RUN_NOW = utc_now()

MACRO_BULLISH = "BULLISH"
MACRO_BEARISH = "BEARISH"
MACRO_INVALID = "INVALID"
CHECK_PASS = "PASS"
CHECK_FAIL = "FAIL"
CHECK_NOT_CHECKED = "NOT_CHECKED"
CHECK_NOT_APPLICABLE = "NOT_APPLICABLE"
SMA200_WINDOW = 200
ATR_PERIOD = 14
STOP_ATR_MULTIPLIER = 2.0
TRAILING_ATR_MULTIPLIER = 2.5
STOP_PCT_FALLBACK = 0.98
TRAILING_PCT_FALLBACK = 0.975

# Chiusure anticipate NYSE (13:00 ET). research.calendars le lascia nel
# calendario delle sedute ma non ne distingue l'orario.
US_EQUITY_EARLY_CLOSE_DATES = frozenset((
    date(2024, 7, 3),
    date(2024, 11, 29),
    date(2024, 12, 24),
    date(2025, 7, 3),
    date(2025, 11, 28),
    date(2025, 12, 24),
    date(2026, 7, 2),
    date(2026, 11, 27),
    date(2026, 12, 24),
    date(2027, 7, 2),
    date(2027, 11, 26),
    date(2027, 12, 24),
))


def abort(message):
    """Interrompe il run senza toccare lo stato persistito."""
    # Messaggio in ASCII: lo stdout del runner non e' garantito UTF-8.
    print(f"ABORT: {message}", file=sys.stderr)
    sys.exit(1)


def _invalid_observed(value):
    """Etichetta diagnostica per un valore non utilizzabile, senza inventare numeri."""
    if value is None:
        return "missing"
    if not is_finite_number(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "invalid"
        if number == float("inf") or number == float("-inf"):
            return "inf"
        return "nan"
    if not is_valid_price(value):
        return "non_positive"
    return "invalid"


def _macro_result(allow_entries, status, reason, spy=None, sma=None):
    """Tupla operativa invariata più dettagli diagnostici."""
    spy_ok = is_valid_price(spy)
    sma_ok = is_valid_price(sma)
    details = {
        "status": status,
        "reason": reason,
        "spy_close": float(spy) if spy_ok else None,
        "sma200": float(sma) if sma_ok else None,
        "spy_close_valid": bool(spy_ok),
        "sma200_valid": bool(sma_ok),
    }
    return allow_entries, status, reason, details


def _safety_summary_markdown(payload):
    macro = payload.get("macro") or {}
    stops = payload.get("stops") or {}
    commit = payload.get("commit") or {}
    lines = [
        "## Data safety report",
        "",
        "- report_complete: %s" % payload.get("report_complete"),
        "- commit: %s (%s)" % (commit.get("sha"), commit.get("check")),
        "- macro: %s / %s" % (macro.get("status"), macro.get("check")),
        "- spy_close_valid: %s sma200_valid: %s" % (
            macro.get("spy_close_valid"),
            macro.get("sma200_valid"),
        ),
        "- entries_allowed: %s" % macro.get("entries_allowed"),
        "- stops: %s" % stops.get("check"),
        "",
    ]
    for item in stops.get("positions") or []:
        lines.append(
            "- ATR %s: atr=%s source=%s stop_loss=%s trailing=%s"
            % (
                item.get("ticker"),
                item.get("atr_check"),
                item.get("source"),
                item.get("stop_loss_check"),
                item.get("trailing_check"),
            )
        )
    for item in payload.get("invalid_values") or []:
        lines.append(
            "- invalid %s %s: %s"
            % (item.get("ticker") or "", item.get("field"), item.get("observed"))
        )
    lines.append("")
    return "\n".join(lines)


def _emit_data_safety_report(payload):
    """Stdout, file e job summary. Qualsiasi errore resta diagnostico."""
    try:
        text = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    except Exception as error:
        print("DATA_SAFETY_REPORT_ERROR " + str(error))
        return
    try:
        print("DATA_SAFETY_REPORT " + text)
    except Exception:
        pass
    try:
        with open(DATA_SAFETY_REPORT_FILE, "w", encoding="utf-8") as handle:
            handle.write(text)
    except Exception as error:
        print("DATA_SAFETY_REPORT_WRITE_ERROR " + str(error))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write(_safety_summary_markdown(payload))
        except Exception as error:
            print("DATA_SAFETY_REPORT_SUMMARY_ERROR " + str(error))


def _publish_data_safety_report(
    macro_allow_entries,
    macro_status,
    macro_details,
    stop_diagnostics,
):
    """Costruisce il report dalle decisioni già prese. Non ricalcola nulla."""
    invalid_values = []
    spy_ok = bool(macro_details.get("spy_close_valid"))
    sma_ok = bool(macro_details.get("sma200_valid"))
    if not spy_ok:
        invalid_values.append(
            {"field": "spy_close", "observed": "missing" if macro_details.get("spy_close") is None else "invalid"}
        )
    if not sma_ok:
        invalid_values.append(
            {"field": "sma200", "observed": "missing" if macro_details.get("sma200") is None else "invalid"}
        )

    if macro_status in (MACRO_BULLISH, MACRO_BEARISH) and spy_ok and sma_ok:
        macro_check = CHECK_PASS
    elif macro_status == MACRO_INVALID:
        macro_check = CHECK_FAIL
    else:
        macro_check = CHECK_NOT_CHECKED

    if not stop_diagnostics:
        stops = {
            "check": CHECK_NOT_APPLICABLE,
            "reason": "no_open_positions",
            "positions": [],
        }
        stops_complete = True
    else:
        positions = []
        stops_complete = True
        for item in stop_diagnostics:
            positions.append(item)
            for key in ("atr_check", "stop_loss_check", "trailing_check"):
                if item.get(key) not in (CHECK_PASS, CHECK_FAIL):
                    stops_complete = False
            if item.get("atr_check") == CHECK_FAIL:
                invalid_values.append(
                    {
                        "ticker": item.get("ticker"),
                        "field": "atr",
                        "observed": item.get("atr_observed") or "missing",
                    }
                )
            if item.get("stop_loss_check") == CHECK_FAIL:
                invalid_values.append(
                    {
                        "ticker": item.get("ticker"),
                        "field": "stop_loss",
                        "observed": "invalid",
                    }
                )
            if item.get("trailing_check") == CHECK_FAIL:
                invalid_values.append(
                    {
                        "ticker": item.get("ticker"),
                        "field": "trailing_stop",
                        "observed": "invalid",
                    }
                )
        stops = {
            "check": "APPLICABLE",
            "positions": [
                {
                    "ticker": item.get("ticker"),
                    "atr_check": item.get("atr_check"),
                    "atr": item.get("atr"),
                    "source": item.get("source"),
                    "stop_loss_check": item.get("stop_loss_check"),
                    "trailing_check": item.get("trailing_check"),
                }
                for item in positions
            ],
        }

    sha = os.environ.get("GITHUB_SHA") or None
    if isinstance(sha, str):
        sha = sha.strip() or None
    commit = {
        "sha": sha,
        "check": CHECK_PASS if sha else CHECK_NOT_CHECKED,
    }
    report_complete = (
        macro_check in (CHECK_PASS, CHECK_FAIL) and stops_complete
    )
    payload = {
        "report_complete": report_complete,
        "commit": commit,
        "macro": {
            "check": macro_check,
            "status": macro_status,
            "reason": macro_details.get("reason"),
            "spy_close": macro_details.get("spy_close"),
            "sma200": macro_details.get("sma200"),
            "spy_close_valid": spy_ok,
            "sma200_valid": sma_ok,
            "entries_allowed": bool(macro_allow_entries),
        },
        "stops": stops,
        "invalid_values": invalid_values,
    }
    _emit_data_safety_report(payload)


def _as_scalar(value):
    """Un solo numero da una cella pandas, oppure None se ambiguo."""
    if isinstance(value, pd.DataFrame):
        return None
    if isinstance(value, pd.Series):
        if value.size != 1:
            return None
        value = value.iloc[0]
    return value


def _column_series(df, name):
    column = df[name]
    if isinstance(column, pd.DataFrame):
        column = column.iloc[:, 0]
    return column


def _flatten_ohlc_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def _is_us_equity_session_day(bar_date):
    day = pd.Timestamp(bar_date).normalize()
    return len(nyse_sessions(day, day)) == 1


def _us_equity_bar_complete(bar_date, now):
    """True se la seduta USA datata bar_date e' chiusa e consolidata."""
    close_clock = (
        time(13, 0) if bar_date in US_EQUITY_EARLY_CLOSE_DATES else time(16, 0)
    )
    local_close = datetime.combine(
        bar_date,
        close_clock,
        tzinfo=ZoneInfo("America/New_York"),
    )
    deadline = local_close.astimezone(timezone.utc) + SETTLEMENT_MARGIN
    return now >= deadline


def _bar_is_usable(df, position, now, market, required):
    """Barra consolidata, non futura, con i campi richiesti finiti e positivi."""
    bar_date = to_bar_date(df.index[position])
    if bar_date > now.date():
        return False

    if market == "us_equity":
        if not _is_us_equity_session_day(bar_date):
            return False
        if not _us_equity_bar_complete(bar_date, now):
            return False
    elif market == "crypto_24_7":
        if not is_session_complete(bar_date, market, now=now):
            return False
    else:
        return False

    for column in required:
        if column not in df.columns:
            return False
        value = _as_scalar(_column_series(df, column).iloc[position])
        if not is_valid_price(value):
            return False
    return True


def _usable_bar_positions(df, now, market, required):
    """Ultima seduta usabile e al massimo una precedente usabile.

    Si saltano placeholder di festivita' o barre incomplete, ma non si
    risale la serie: al piu' cinque righe dal fondo, due sedute valide.
    """
    positions = []
    count = len(df)
    examined = 0
    for position in range(count - 1, -1, -1):
        examined += 1
        if examined > 5:
            break
        if _bar_is_usable(df, position, now, market, required):
            positions.append(position)
            if len(positions) == 2:
                break
    return positions


def get_atr(ticker, period=ATR_PERIOD, now=None):
    """Calcola l'ATR in dollari per un dato ticker."""
    if now is None:
        now = RUN_NOW
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < period:
            return None
        df = _flatten_ohlc_columns(df)
        market = market_for_ticker(ticker) or "us_equity"
        high = _column_series(df, "High")
        low = _column_series(df, "Low")
        close = _column_series(df, "Close")
        previous_close = close.shift(1)
        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr_series = true_range.rolling(window=period, min_periods=period).mean()
        for position in _usable_bar_positions(
            df, now, market, ("High", "Low", "Close")
        ):
            atr_val = _as_scalar(atr_series.iloc[position])
            if is_valid_price(atr_val):
                return float(atr_val)
        print(
            f"ATR non valido per {ticker}: uso fallback percentuale."
        )
        return None
    except Exception as e:
        print(f"Errore calcolo ATR per {ticker}: {e}")
        return None


def check_macro_filter(now=None):
    """Filtro Macro: SPY contro SMA200 sulla barra USA consolidata."""
    if now is None:
        now = RUN_NOW
    try:
        spy = yf.download("SPY", period="1y", interval="1d", progress=False)
        if spy.empty:
            return _macro_result(
                False,
                MACRO_INVALID,
                "DATI MACRO NON VALIDI: serie SPY vuota",
            )
        spy = _flatten_ohlc_columns(spy)
        if "Close" not in spy.columns:
            return _macro_result(
                False,
                MACRO_INVALID,
                "DATI MACRO NON VALIDI: colonna Close assente",
            )
        close = _column_series(spy, "Close")
        for position in _usable_bar_positions(
            spy, now, "us_equity", ("Close",)
        ):
            if position < SMA200_WINDOW - 1:
                continue
            selected_close = close.iloc[: position + 1]
            sma200 = selected_close.rolling(
                window=SMA200_WINDOW,
                min_periods=SMA200_WINDOW,
            ).mean().iloc[-1]
            curr_spy = _as_scalar(close.iloc[position])
            sma200 = _as_scalar(sma200)
            if not is_valid_price(curr_spy) or not is_valid_price(sma200):
                continue
            curr_spy = float(curr_spy)
            sma200 = float(sma200)
            if curr_spy >= sma200:
                return _macro_result(
                    True,
                    MACRO_BULLISH,
                    f"SPY ${curr_spy:.2f} >= SMA200 ${sma200:.2f}",
                    spy=curr_spy,
                    sma=sma200,
                )
            return _macro_result(
                False,
                MACRO_BEARISH,
                f"SPY ${curr_spy:.2f} < SMA200 ${sma200:.2f}",
                spy=curr_spy,
                sma=sma200,
            )
        return _macro_result(
            False,
            MACRO_INVALID,
            "DATI MACRO NON VALIDI: nessuna barra SPY consolidata con SMA200",
        )
    except Exception as e:
        print(f"Errore Macro Filter (SPY): {e}")
        return _macro_result(
            False,
            MACRO_INVALID,
            "DATI MACRO NON VALIDI: errore calcolo SPY",
        )

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
stop_diagnostics = []

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

    atr = get_atr(ticker, now=RUN_NOW)
    if is_valid_price(atr) and curr_price > 0:
        stop_loss_price = entry_price - (float(atr) * STOP_ATR_MULTIPLIER)
        trailing_stop_price = peak_price - (float(atr) * TRAILING_ATR_MULTIPLIER)
        stop_label = "ATR"
    else:
        stop_loss_price = entry_price * STOP_PCT_FALLBACK
        trailing_stop_price = peak_price * TRAILING_PCT_FALLBACK
        stop_label = "%"

    trailing_usable = is_valid_price(trailing_stop_price)
    stop_usable = is_valid_price(stop_loss_price)
    atr_valid = is_valid_price(atr)
    stop_diagnostics.append(
        {
            "ticker": ticker,
            "atr_check": CHECK_PASS if atr_valid else CHECK_FAIL,
            "atr": float(atr) if atr_valid else None,
            "atr_observed": None if atr_valid else _invalid_observed(atr),
            "source": stop_label,
            "stop_loss_check": CHECK_PASS if stop_usable else CHECK_FAIL,
            "trailing_check": CHECK_PASS if trailing_usable else CHECK_FAIL,
        }
    )

    if (
        trailing_usable
        and curr_price <= trailing_stop_price
        and curr_price > entry_price
    ):
        p_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        stopped_today.add(ticker)
        events.append(
            f"🎯 TRAILING-STOP {stop_label} ({p_pct:+.1f}%) su {ticker} (${curr_price:.2f})"
        )
    elif stop_usable and curr_price <= stop_loss_price:
        p_pct = ((curr_price - entry_price) / entry_price) * 100
        current_cash += qty * curr_price
        stopped_today.add(ticker)
        events.append(
            f"🛡️ STOP-LOSS {stop_label} ({p_pct:+.1f}%) su {ticker} (${curr_price:.2f})"
        )
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
macro_allow_entries, macro_status, macro_msg, macro_details = check_macro_filter(now=RUN_NOW)
circuit_breaker_active = daily_drawdown <= -4.0

if circuit_breaker_active:
    events.append(f"🚨 CIRCUIT BREAKER ATTIVATO! Perdita giornaliera {daily_drawdown:.2f}% (soglia -4.0%). Nuovi ingressi congelati.")

if macro_status == MACRO_BEARISH:
    events.append(f"🐻 MACRO FILTER ORSACCIONE: {macro_msg}. Ingressi congelati.")
elif macro_status == MACRO_INVALID:
    events.append(f"⚠️ {macro_msg}. Ingressi congelati.")

# 3. INGRESSI AGENTE SCOUT (CON TETTO DINAMICO 30%/40% + FILTRI DI RISCHIO)
eligible_candidates = [t for t in top_candidates if t not in stopped_today]

if eligible_candidates and state["cash"] > 500 and macro_allow_entries and not circuit_breaker_active:
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
if macro_status == MACRO_BULLISH:
    macro_status_text = f"BULLISH 🟢 ({macro_msg})"
elif macro_status == MACRO_BEARISH:
    macro_status_text = f"BEARISH 🔴 ({macro_msg})"
else:
    macro_status_text = "DATI MACRO NON VALIDI"
msg += f"🌐 Macro Status: {macro_status_text}"

try:
    _publish_data_safety_report(
        macro_allow_entries,
        macro_status,
        macro_details,
        stop_diagnostics,
    )
except Exception as safety_error:
    print("DATA_SAFETY_REPORT_ERROR " + str(safety_error))

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
