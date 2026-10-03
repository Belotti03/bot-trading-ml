# safe_state.py - Validazione dati, policy di recency e scrittura atomica

"""
Guardie difensive condivise da model_engine.py e main.py.

Esistono perche' un prezzo non finito proveniente dal data provider si e'
propagato silenziosamente in cash ed equity persistiti, e perche' una barra
incompleta poteva diventare un segnale tradabile.

Qui non vive nessuna logica di strategia: soglie, modelli, feature set,
universo e gestione del rischio non sono toccati.
"""

import json
import os
import math
import tempfile

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


# -------------------------------------------------------------------------
# SCHEMA DELLO STATO
#
# Uno stato esistente deve essere completo: un file parziale non va mai
# completato con i default, altrimenti un portfolio_state.json vuoto
# equivarrebbe a un reset silenzioso del portafoglio.
# -------------------------------------------------------------------------

REQUIRED_STATE_FIELDS = (
    "cash",
    "positions",
    "initial_balance",
    "day_start_val",
    "last_run_date"
)


# -------------------------------------------------------------------------
# POLICY DI RECENCY
#
# I giorni di contrattazione vengono dedotti dall'indice dei dati, che
# contiene solo sessioni realmente avvenute: non serve una lista di
# festivita'. Dal calendario serve solo l'orario di chiusura, che fissa il
# momento in cui una barra giornaliera e' completa.
#
# SETTLEMENT_MARGIN assorbe il ritardo di consolidamento del provider ed
# erra sempre verso l'esclusione della barra.
# -------------------------------------------------------------------------

SETTLEMENT_MARGIN = timedelta(minutes=15)

SESSION_RULES = {
    "us_equity": {
        "timezone": "America/New_York",
        "close": time(16, 0),
        "closes_next_day": False,
        # Massima eta' prodotta da un calendario US normale: venerdi' usato
        # martedi' dopo un lunedi' di festa, o un cluster natalizio.
        "max_bar_age_days": 5
    },
    "crypto_24_7": {
        "timezone": "UTC",
        "close": time(0, 0),
        "closes_next_day": True,
        # Contrattazione continua: la barra attesa e' sempre quella di ieri.
        "max_bar_age_days": 2
    }
}

# Proprieta' di cadenza del dato, non definizione dell'universo. Un ticker
# non mappato viene rifiutato: aggiungere un asset richiede una decisione
# esplicita sul suo calendario.
TICKER_MARKETS = {
    "BTC-USD": "crypto_24_7",
    "ETH-USD": "crypto_24_7",
    "NVDA": "us_equity",
    "AMD": "us_equity",
    "MSTR": "us_equity",
    "COIN": "us_equity",
    "TSM": "us_equity",
    "PLTR": "us_equity",
    "ARM": "us_equity",
    "SMCI": "us_equity",
    "TSLA": "us_equity",
    "META": "us_equity",
    "AMZN": "us_equity",
    "GOOGL": "us_equity",
    "AAPL": "us_equity",
    "MSFT": "us_equity",
    "QQQ": "us_equity",
    "GLD": "us_equity"
}


def market_for_ticker(ticker):
    """Mercato di riferimento del ticker, oppure None se non configurato."""
    return TICKER_MARKETS.get(ticker)


def utc_now():
    return datetime.now(timezone.utc)


def session_close_instant(bar_date, market):
    """Istante UTC in cui la sessione datata bar_date si chiude."""
    rule = SESSION_RULES[market]

    zone = ZoneInfo(rule["timezone"])

    local_date = bar_date

    if rule["closes_next_day"]:
        local_date = bar_date + timedelta(days=1)

    local_close = datetime.combine(
        local_date,
        rule["close"],
        tzinfo=zone
    )

    return local_close.astimezone(timezone.utc)


def is_session_complete(bar_date, market, now=None):
    """True se la sessione datata bar_date e' chiusa e consolidata."""
    if now is None:
        now = utc_now()

    deadline = session_close_instant(bar_date, market) + SETTLEMENT_MARGIN

    return now >= deadline


def to_bar_date(label):
    """Data della barra a partire da un'etichetta di indice pandas."""
    date_method = getattr(label, "date", None)

    if callable(date_method):
        return date_method()

    return datetime.strptime(str(label)[:10], "%Y-%m-%d").date()


def to_bar_date_text(label):
    """Testo YYYY-MM-DD della barra, usato come campo asof."""
    return to_bar_date(label).isoformat()


def parse_bar_date(text):
    """Data da un testo YYYY-MM-DD, oppure None se non interpretabile."""
    if not isinstance(text, str) or len(text) != 10:
        return None

    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def asof_problem(asof_text, ticker, now=None):
    """
    Motivo per cui un asof non e' utilizzabile, oppure None se valido.

    Applica la stessa policy del producer: formato, data non futura, cap di
    eta' per mercato e chiusura di sessione consolidata secondo calendario e
    DST. E' l'unico punto in cui la policy e' implementata, cosi' consumer e
    producer non possono divergere: un payload esterno o alterato con un asof
    non ancora consolidato viene rifiutato anche se la data e' di oggi.
    """
    market = market_for_ticker(ticker)

    if market is None:
        return "mercato non configurato"

    bar_date = parse_bar_date(asof_text)

    if bar_date is None:
        return f"asof mancante o non valido ({asof_text!r})"

    if now is None:
        now = utc_now()

    today = now.date()

    if bar_date > today:
        return f"asof nel futuro ({asof_text})"

    age_days = (today - bar_date).days

    max_age = SESSION_RULES[market]["max_bar_age_days"]

    if age_days > max_age:
        return (
            f"asof obsoleto ({asof_text}: {age_days} giorni, "
            f"cap {max_age} per {market})"
        )

    if not is_session_complete(bar_date, market, now=now):
        margin_minutes = int(SETTLEMENT_MARGIN.total_seconds() // 60)

        return (
            f"sessione {asof_text} non ancora consolidata per {market} "
            f"(chiusura {session_close_instant(bar_date, market).isoformat()} "
            f"+ {margin_minutes} min)"
        )

    return None


# -------------------------------------------------------------------------
# VALIDATORI SCALARI
# -------------------------------------------------------------------------

def is_finite_number(value):
    """True solo per numeri reali finiti (NaN, Infinity, bool e stringhe esclusi)."""
    if value is None:
        return False

    if isinstance(value, (bool, str)):
        return False

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False

    return math.isfinite(number)


def is_valid_price(value):
    return is_finite_number(value) and float(value) > 0.0


def is_valid_quantity(value):
    return is_finite_number(value) and float(value) > 0.0


def is_valid_probability(value):
    return is_finite_number(value) and 0.0 <= float(value) <= 1.0


def is_valid_cash(value):
    return is_finite_number(value) and float(value) >= 0.0


# -------------------------------------------------------------------------
# SELEZIONE DELLA BARRA DI SEGNALE
# -------------------------------------------------------------------------

def ordered_session_dates(labels):
    """Date di sessione distinte, nell'ordine in cui compaiono nei dati."""
    dates = []

    for label in labels:
        bar_date = to_bar_date(label)

        if not dates or dates[-1] != bar_date:
            dates.append(bar_date)

    return dates


def select_signal_bar(df, feature_columns, ticker, price_column="Close", now=None):
    """
    Barra da cui derivano feature, probabilita', prezzo e asof.

    Restituisce (etichetta, frame di una riga, motivo_di_rifiuto).

    La barra attesa e' una sola e viene calcolata, non cercata:

        - l'ultima sessione presente nei dati, se il calendario conferma
          che e' chiusa e consolidata;
        - altrimenti la sessione immediatamente precedente.

    Se la riga attesa non e' utilizzabile il ticker viene rifiutato. Non si
    risale indietro in cerca di una barra qualsiasi: una barra piu' vecchia
    non e' un sostituto accettabile.
    """
    market = market_for_ticker(ticker)

    if market is None:
        return None, None, f"mercato non configurato per {ticker}"

    required = list(feature_columns) + [price_column]

    missing_columns = [
        column for column in required if column not in df.columns
    ]

    if missing_columns:
        return None, None, (
            "colonne assenti: " + ", ".join(missing_columns)
        )

    if df.empty:
        return None, None, "serie storica vuota"

    if now is None:
        now = utc_now()

    today = now.date()

    labels = list(df.index)
    session_dates = ordered_session_dates(labels)

    latest_date = session_dates[-1]

    if latest_date > today:
        return None, None, (
            f"ultima barra datata nel futuro ({latest_date.isoformat()})"
        )

    if is_session_complete(latest_date, market, now=now):
        expected_date = latest_date
        provenance = "ultima sessione chiusa"

    else:
        if len(session_dates) < 2:
            return None, None, (
                f"sessione {latest_date.isoformat()} non ancora chiusa e "
                f"nessuna sessione precedente disponibile"
            )

        expected_date = session_dates[-2]
        provenance = "sessione precedente"

        if not is_session_complete(expected_date, market, now=now):
            return None, None, (
                f"nessuna sessione chiusa disponibile "
                f"(ultima: {latest_date.isoformat()})"
            )

    age_days = (today - expected_date).days

    max_age = SESSION_RULES[market]["max_bar_age_days"]

    if age_days > max_age:
        return None, None, (
            f"barra obsoleta: {expected_date.isoformat()} "
            f"({age_days} giorni, cap {max_age} per {market})"
        )

    row_positions = [
        position for position, label in enumerate(labels)
        if to_bar_date(label) == expected_date
    ]

    if not row_positions:
        return None, None, (
            f"barra attesa {expected_date.isoformat()} assente dai dati"
        )

    position = row_positions[-1]
    row = df.iloc[[position]]

    for column in required:
        value = row[column].iloc[0]

        if not is_finite_number(value):
            return None, None, (
                f"barra {expected_date.isoformat()} ({provenance}): "
                f"{column} non finito ({value!r})"
            )

    price = row[price_column].iloc[0]

    if not is_valid_price(price):
        return None, None, (
            f"barra {expected_date.isoformat()} ({provenance}): "
            f"{price_column} non positivo ({price!r})"
        )

    return labels[position], row, None


# -------------------------------------------------------------------------
# VALIDATORI DI PAYLOAD
# -------------------------------------------------------------------------

def validate_scout_payload(payload, now=None):
    """Problemi nel payload dei segnali; lista vuota significa utilizzabile."""
    if not isinstance(payload, dict):
        return ["il payload scout non e' un oggetto JSON"]

    if not payload:
        return ["il payload scout e' vuoto"]

    problems = []

    for ticker, entry in payload.items():

        if not isinstance(entry, dict):
            problems.append(f"{ticker}: la voce non e' un oggetto")
            continue

        if not is_valid_probability(entry.get("prob")):
            problems.append(
                f"{ticker}: prob non valida ({entry.get('prob')!r})"
            )

        if not is_valid_price(entry.get("price")):
            problems.append(
                f"{ticker}: price non valido ({entry.get('price')!r})"
            )

        reason = asof_problem(entry.get("asof"), ticker, now=now)

        if reason is not None:
            problems.append(f"{ticker}: {reason}")

    return problems


def validate_metrics_payload(payload):
    """Problemi nel report di validazione; un report vuoto e' ammesso."""
    if not isinstance(payload, dict):
        return ["il report di validazione non e' un oggetto JSON"]

    problems = []

    for ticker, metrics in payload.items():

        if not isinstance(metrics, dict):
            problems.append(f"{ticker}: le metriche non sono un oggetto")
            continue

        for name, value in metrics.items():

            if not is_finite_number(value):
                problems.append(
                    f"{ticker}.{name}: valore non finito ({value!r})"
                )

    return problems


def validate_state_payload(state, require_complete=True):
    """
    Problemi negli invarianti dello stato di portafoglio.

    Con require_complete tutti i campi di REQUIRED_STATE_FIELDS devono essere
    presenti: uno stato esistente ma parziale va rifiutato, non completato.
    """
    if not isinstance(state, dict):
        return ["lo stato non e' un oggetto JSON"]

    problems = []

    if require_complete:

        for field in REQUIRED_STATE_FIELDS:

            if field not in state:
                problems.append(f"campo obbligatorio assente: {field}")

    if "cash" in state and not is_valid_cash(state["cash"]):
        problems.append(f"cash non valido ({state['cash']!r})")

    for key in ("initial_balance", "initial_capital", "day_start_val"):

        if key in state and not is_valid_price(state[key]):
            problems.append(f"{key} non valido ({state[key]!r})")

    if "last_run_date" in state:
        last_run_date = state["last_run_date"]

        if not isinstance(last_run_date, str):
            problems.append(
                f"last_run_date non e' una stringa ({last_run_date!r})"
            )

        elif last_run_date != "" and parse_bar_date(last_run_date) is None:
            problems.append(
                f"last_run_date non valido ({last_run_date!r})"
            )

    if "positions" in state and not isinstance(state["positions"], dict):
        return problems + ["positions non e' un oggetto JSON"]

    for ticker, position in state.get("positions", {}).items():

        if not isinstance(position, dict):
            problems.append(f"posizione {ticker}: non e' un oggetto")
            continue

        if not is_valid_quantity(position.get("qty")):
            problems.append(
                f"posizione {ticker}: qty non valida ({position.get('qty')!r})"
            )

        for key in ("entry_price", "peak_price"):

            if not is_valid_price(position.get(key)):
                problems.append(
                    f"posizione {ticker}: {key} non valido "
                    f"({position.get(key)!r})"
                )

    return problems


# -------------------------------------------------------------------------
# PERSISTENZA
# -------------------------------------------------------------------------

def dump_json_atomic(path, payload, indent=4):
    """
    Serializza prima, poi sostituisce il file in un'unica operazione.

    allow_nan=False rende NaN/Infinity un errore bloccante; poiche' il testo
    viene prodotto prima di toccare il file, un fallimento lascia intatto il
    contenuto precedente invece di troncarlo.
    """
    text = json.dumps(payload, indent=indent, allow_nan=False)

    directory = os.path.dirname(os.path.abspath(path)) or "."

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        prefix=os.path.basename(path) + ".",
        suffix=".tmp",
        delete=False
    )

    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(handle.name, path)

    except BaseException:

        try:
            os.unlink(handle.name)
        except OSError:
            pass

        raise
