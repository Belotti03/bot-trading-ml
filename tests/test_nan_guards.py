# tests/test_nan_guards.py - Guardie su NaN/Infinity, schema di stato e recency

"""
Test mirati sulle guardie difensive introdotte dopo l'incidente NaN e dopo la
code review che ha richiesto schema di stato completo e policy di recency.

Eseguire con: python tests/test_nan_guards.py
Nessuna dipendenza oltre a pandas/numpy: pytest non e' richiesto e la rete non
viene usata (yfinance e requests sono sostituiti da stub).
"""

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import types

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, REPO_ROOT)

from safe_state import (                                    # noqa: E402
    REQUIRED_STATE_FIELDS,
    SESSION_RULES,
    TICKER_MARKETS,
    asof_problem,
    dump_json_atomic,
    is_finite_number,
    is_session_complete,
    is_valid_cash,
    is_valid_price,
    is_valid_probability,
    is_valid_quantity,
    select_signal_bar,
    to_bar_date_text,
    validate_scout_payload,
    validate_state_payload
)

FEATURES = ["Returns", "SMA_10", "SMA_50", "RSI"]

NAN = float("nan")
INF = float("inf")


def utc(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# Istanti di riferimento fissi: la policy deve essere deterministica e non
# dipendere dall'ora in cui la suite viene eseguita.
# Estate (EDT): chiusura 16:00 ET = 20:00 UTC, consolidata alle 20:15.
SUMMER_MIDSESSION = utc(2026, 7, 15, 17, 0)
SUMMER_CLOSE_MINUS_1 = utc(2026, 7, 15, 20, 14)
SUMMER_AFTER_CLOSE = utc(2026, 7, 15, 20, 15)
# Inverno (EST): chiusura 16:00 ET = 21:00 UTC, consolidata alle 21:15.
WINTER_CRON_2100 = utc(2026, 12, 15, 21, 0)
WINTER_CONSOLIDATED = utc(2026, 12, 15, 21, 15)
# 9 ottobre 2026, EDT: chiusura 16:00 ET = 20:00 UTC, consolidata alle 20:15.
# Il cron 21:00 UTC tratta quindi oggi come sessione USA gia' chiusa.
OCT9_CRON_2100 = utc(2026, 10, 9, 21, 0)

# Riferimento usato da tutte le fixture: mercoledi', sessione USA aperta.
REFERENCE_NOW = SUMMER_MIDSESSION


def days_ago_text(days, reference=None):
    """Data asof relativa all'istante di riferimento, non all'orologio reale."""
    moment = reference or REFERENCE_NOW

    return (moment.date() - timedelta(days=days)).isoformat()


# -------------------------------------------------------------------------
# Costruttori di serie storiche
# -------------------------------------------------------------------------

def make_frame(end_date, periods=10, zone="America/New_York", closes=None):
    """Serie giornaliera con feature valide e indice tz-aware come yfinance."""
    dates = [
        end_date - timedelta(days=offset)
        for offset in range(periods - 1, -1, -1)
    ]

    index = pd.DatetimeIndex(
        [pd.Timestamp(day) for day in dates]
    ).tz_localize(zone)

    if closes is None:
        closes = [100.0 + position for position in range(periods)]

    return pd.DataFrame(
        {
            "Returns": [0.01] * periods,
            "SMA_10": [100.0] * periods,
            "SMA_50": [99.0] * periods,
            "RSI": [55.0] * periods,
            "Close": list(closes),
        },
        index=index
    )


def make_price_history(end_date, periods=300, seed=7):
    """Random walk deterministico, nel formato restituito da yfinance."""
    index = pd.bdate_range(
        end=pd.Timestamp(end_date),
        periods=periods
    ).tz_localize("America/New_York")

    generator = np.random.default_rng(seed)

    closes = 200.0 + np.cumsum(
        generator.normal(0.0, 1.0, size=periods)
    )

    assert closes.min() > 0.0

    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes + 1.0,
            "Low": closes - 1.0,
            "Close": closes,
            "Volume": 1_000_000.0,
        },
        index=index
    )


# -------------------------------------------------------------------------
# Fixture di stato e segnali
# -------------------------------------------------------------------------

def complete_state(cash=10000.0, positions=None, day_start_val=10000.0):
    return {
        "cash": cash,
        "positions": positions if positions is not None else {},
        "initial_balance": 10000.0,
        "day_start_val": day_start_val,
        "last_run_date": "2026-09-29"
    }


def scout_entry(prob, price, days_ago=1):
    return {
        "prob": prob,
        "price": price,
        "asof": days_ago_text(days_ago)
    }


# -------------------------------------------------------------------------
# Harness offline per main.py
# -------------------------------------------------------------------------

HARNESS = '''
import runpy
import sys
import types

import pandas as pd

REPO_ROOT = sys.argv[1]
sys.path.insert(0, REPO_ROOT)

# Orologio fissato per il test: patchato su safe_state prima che main.py venga
# eseguito, cosi' main.py riceve l'istante voluto senza backdoor nel codice.
if len(sys.argv) > 2:
    import datetime as _datetime
    import safe_state as _safe_state

    _FIXED_NOW = _datetime.datetime.fromisoformat(sys.argv[2])
    _safe_state.utc_now = lambda: _FIXED_NOW


def _frame(periods=400):
    index = pd.date_range("2025-01-01", periods=periods, freq="D")
    close = pd.Series(range(periods), index=index).astype(float) + 100.0
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1000.0,
        },
        index=index,
    )


requests_stub = types.ModuleType("requests")


def _post(url, json=None, **kwargs):
    with open("telegram_calls.txt", "a") as handle:
        handle.write("sent\\n")

    class Response:
        status_code = 200

    return Response()


requests_stub.post = _post
sys.modules["requests"] = requests_stub

yfinance_stub = types.ModuleType("yfinance")


def _download(ticker, **kwargs):
    return _frame()


class _Ticker:
    def __init__(self, ticker):
        self.ticker = ticker

    def history(self, **kwargs):
        return _frame()


yfinance_stub.download = _download
yfinance_stub.Ticker = _Ticker
sys.modules["yfinance"] = yfinance_stub

runpy.run_path(REPO_ROOT + "/main.py", run_name="__main__")
'''


def run_main(state_payload, scout_payload, now=None):
    """
    Esegue main.py in una sandbox e riporta esito e stato finale.

    I payload possono essere dict (serializzati) o testo grezzo, per poter
    scrivere NaN letterali che json.dumps rifiuterebbe. L'istante `now` viene
    imposto a main.py tramite l'harness, per rendere deterministica la policy
    di recency.
    """
    workdir = tempfile.mkdtemp(prefix="nanguard_")

    try:
        def materialise(payload, filename):
            if payload is None:
                return None

            text = (
                payload if isinstance(payload, str)
                else json.dumps(payload, indent=4)
            )

            with open(os.path.join(workdir, filename), "w") as handle:
                handle.write(text)

            return text

        state_text = materialise(state_payload, "portfolio_state.json")
        materialise(scout_payload, "scout_signals.json")

        harness_path = os.path.join(workdir, "_harness.py")

        with open(harness_path, "w") as handle:
            handle.write(HARNESS)

        environment = dict(os.environ)
        environment["TELEGRAM_BOT_TOKEN"] = "dummy-token"
        environment["TELEGRAM_CHAT_ID"] = "dummy-chat"

        command = [sys.executable, harness_path, REPO_ROOT]
        command.append((now or REFERENCE_NOW).isoformat())

        completed = subprocess.run(
            command,
            cwd=workdir,
            env=environment,
            capture_output=True,
            text=True,
            timeout=300
        )

        state_path = os.path.join(workdir, "portfolio_state.json")
        state_after = None

        if os.path.exists(state_path):
            with open(state_path) as handle:
                state_after = handle.read()

        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "state_before": state_text,
            "state_after": state_after,
            "unchanged": state_after == state_text,
            "telegram_sent": os.path.exists(
                os.path.join(workdir, "telegram_calls.txt")
            ),
            "leftovers": [
                name for name in os.listdir(workdir)
                if name.endswith(".tmp")
            ]
        }

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def import_model_engine():
    """Importa model_engine; lightgbm viene sostituito solo se assente."""
    try:
        import lightgbm                                     # noqa: F401

    except ImportError:
        from sklearn.tree import DecisionTreeClassifier

        stub = types.ModuleType("lightgbm")

        class LGBMClassifier:
            """Sostituto deterministico con la stessa interfaccia minima."""

            def __init__(self, max_depth=3, random_state=42, **kwargs):
                self._model = DecisionTreeClassifier(
                    max_depth=max_depth,
                    random_state=random_state
                )

            def fit(self, X, y):
                self._model.fit(X, y)
                return self

            def predict_proba(self, X):
                return self._model.predict_proba(X)

        stub.LGBMClassifier = LGBMClassifier
        sys.modules["lightgbm"] = stub

    import model_engine

    return model_engine


# =========================================================================
# 1. CALENDARIO DI SESSIONE
# =========================================================================

def test_us_equity_completeness_follows_dst():
    summer = date(2026, 7, 15)

    # EDT: chiusura 20:00 UTC, completa dalle 20:15 UTC.
    assert not is_session_complete(summer, "us_equity", now=utc(2026, 7, 15, 20, 14))
    assert is_session_complete(summer, "us_equity", now=utc(2026, 7, 15, 20, 15))

    winter = date(2026, 12, 15)

    # EST: chiusura 21:00 UTC, quindi il cron delle 21:00 non basta.
    assert not is_session_complete(winter, "us_equity", now=WINTER_CRON_2100)
    assert is_session_complete(winter, "us_equity", now=utc(2026, 12, 15, 21, 15))


def test_crypto_completeness_at_utc_midnight():
    day = date(2026, 7, 15)

    assert not is_session_complete(day, "crypto_24_7", now=utc(2026, 7, 15, 23, 59))
    assert not is_session_complete(day, "crypto_24_7", now=utc(2026, 7, 16, 0, 10))
    assert is_session_complete(day, "crypto_24_7", now=utc(2026, 7, 16, 0, 15))


def test_every_scout_pool_ticker_has_a_market():
    engine = import_model_engine()

    unmapped = [
        ticker for ticker in engine.SCOUT_POOL
        if ticker not in TICKER_MARKETS
    ]

    assert unmapped == [], unmapped

    unknown_market = [
        ticker for ticker, market in TICKER_MARKETS.items()
        if market not in SESSION_RULES
    ]

    assert unknown_market == [], unknown_market


# =========================================================================
# 2. SELEZIONE DELLA BARRA DI SEGNALE
# =========================================================================

def test_last_bar_incomplete_selects_previous_session():
    frame = make_frame(date(2026, 7, 15), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-07-14"
    assert float(row["Close"].iloc[0]) == float(frame["Close"].iloc[-2])


def test_complete_last_bar_is_used():
    frame = make_frame(date(2026, 7, 15), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_AFTER_CLOSE
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-07-15"
    assert float(row["Close"].iloc[0]) == float(frame["Close"].iloc[-1])


def test_winter_2100_cron_falls_back_to_previous_session():
    frame = make_frame(date(2026, 12, 15), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=WINTER_CRON_2100
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-12-14"


def test_last_bar_with_nan_close_does_not_poison_the_signal():
    closes = [100.0 + position for position in range(10)]
    closes[-1] = NAN

    frame = make_frame(date(2026, 7, 15), periods=10, closes=closes)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-07-14"
    assert is_valid_price(row["Close"].iloc[0])


def _unsettled_last_session_frame(end_date, periods=10, zone="America/New_York"):
    """Ultima riga come Yahoo dopo close EDT: Returns paddati, SMA_10 e Close NaN."""
    frame = make_frame(end_date, periods=periods, zone=zone)
    frame.iloc[-1, frame.columns.get_loc("Returns")] = 0.0
    frame.iloc[-1, frame.columns.get_loc("SMA_10")] = NAN
    frame.iloc[-1, frame.columns.get_loc("Close")] = NAN
    return frame


def test_oct9_2100_unsettled_last_bar_falls_back_to_previous_session():
    frame = _unsettled_last_session_frame(date(2026, 10, 9))
    previous_close = float(frame["Close"].iloc[-2])

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=OCT9_CRON_2100
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-10-08"
    assert float(row["Close"].iloc[0]) == previous_close
    assert is_valid_price(row["Close"].iloc[0])
    assert is_finite_number(row["SMA_10"].iloc[0])


def test_crypto_oct9_2100_uses_previous_session():
    frame = _unsettled_last_session_frame(date(2026, 10, 9), zone="UTC")

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "BTC-USD", now=OCT9_CRON_2100
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-10-08"


def test_unsettled_last_closed_session_does_not_walk_past_previous():
    frame = _unsettled_last_session_frame(date(2026, 7, 15))
    frame.iloc[-2, frame.columns.get_loc("RSI")] = NAN
    older_close = float(frame["Close"].iloc[-3])

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_AFTER_CLOSE
    )

    assert label is None
    assert row is None
    assert "2026-07-15" in rejection
    assert "SMA_10" in rejection
    assert "sessione precedente inutilizzabile" in rejection
    assert "2026-07-14" in rejection
    assert "RSI" in rejection
    assert "2026-07-13" not in rejection
    assert older_close != 0.0


def test_unsettled_last_session_without_previous_is_rejected():
    frame = _unsettled_last_session_frame(date(2026, 7, 15), periods=1)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_AFTER_CLOSE
    )

    assert label is None
    assert row is None
    assert "2026-07-15" in rejection
    assert "SMA_10" in rejection
    assert "sessione precedente" not in rejection


def test_fallback_previous_over_age_cap_is_rejected():
    # 15/07 dopo close: ultima barra 10/07 (eta' 5, al cap) invalida;
    # la precedente 09/07 ha eta' 6 e non puo' essere usata.
    frame = _unsettled_last_session_frame(date(2026, 7, 10))

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_AFTER_CLOSE
    )

    assert label is None
    assert row is None
    assert "2026-07-10" in rejection
    assert "sessione precedente inutilizzabile" in rejection
    assert "obsoleta" in rejection
    assert "2026-07-09" in rejection


def test_no_backward_search_when_expected_bar_is_invalid():
    frame = make_frame(date(2026, 7, 15), periods=10)

    # La barra attesa (14/07) e' inutilizzabile, le precedenti sono valide:
    # il ticker va rifiutato, non sostituito con una barra piu' vecchia.
    frame.iloc[-2, frame.columns.get_loc("RSI")] = NAN

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert row is None
    assert "RSI" in rejection
    assert "2026-07-14" in rejection


def test_expected_bar_with_non_positive_price_is_rejected():
    closes = [100.0 + position for position in range(10)]
    closes[-2] = 0.0

    frame = make_frame(date(2026, 7, 15), periods=10, closes=closes)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "non positivo" in rejection


def test_stale_series_is_rejected():
    frame = make_frame(date(2026, 7, 1), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "obsoleta" in rejection
    assert "cap 5" in rejection


def test_us_equity_age_cap_boundary():
    # Barra attesa a 5 giorni: accettata.
    frame = make_frame(date(2026, 7, 10), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-07-10"

    # Barra attesa a 6 giorni: rifiutata.
    frame = make_frame(date(2026, 7, 9), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "6 giorni" in rejection


def test_crypto_age_cap_is_tighter():
    # Barra attesa a 2 giorni: accettata per un asset 24/7.
    frame = make_frame(date(2026, 7, 13), periods=10, zone="UTC")

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "BTC-USD", now=SUMMER_MIDSESSION
    )

    assert rejection is None
    assert to_bar_date_text(label) == "2026-07-13"

    # A 3 giorni viene rifiutata, mentre per un'azione sarebbe accettabile.
    frame = make_frame(date(2026, 7, 12), periods=10, zone="UTC")

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "BTC-USD", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "cap 2" in rejection

    frame = make_frame(date(2026, 7, 12), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert rejection is None


def test_future_dated_bar_is_rejected():
    frame = make_frame(date(2026, 7, 17), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "futuro" in rejection


def test_single_incomplete_bar_without_history_is_rejected():
    frame = make_frame(date(2026, 7, 15), periods=1)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "nessuna sessione precedente" in rejection


def test_unmapped_ticker_is_rejected():
    frame = make_frame(date(2026, 7, 15), periods=10)

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "SOMETHING-NEW", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "mercato non configurato" in rejection


def test_missing_columns_are_rejected():
    frame = make_frame(date(2026, 7, 15), periods=10).drop(columns=["RSI"])

    label, row, rejection = select_signal_bar(
        frame, FEATURES, "NVDA", now=SUMMER_MIDSESSION
    )

    assert label is None
    assert "RSI" in rejection


# =========================================================================
# 3. ASOF LATO CONSUMER
# =========================================================================

def test_missing_asof_is_rejected():
    for value in [None, "", 20260715, "2026-7-1", "ieri", "2026-07-15T00:00:00"]:
        assert asof_problem(value, "NVDA", now=REFERENCE_NOW) is not None, value


def test_stale_asof_is_rejected():
    assert asof_problem(days_ago_text(6), "NVDA", now=REFERENCE_NOW) is not None
    assert asof_problem(days_ago_text(5), "NVDA", now=REFERENCE_NOW) is None

    assert asof_problem(days_ago_text(3), "BTC-USD", now=REFERENCE_NOW) is not None
    assert asof_problem(days_ago_text(2), "BTC-USD", now=REFERENCE_NOW) is None


def test_future_asof_is_rejected():
    problem = asof_problem(days_ago_text(-1), "NVDA", now=REFERENCE_NOW)

    assert problem is not None
    assert "futuro" in problem


def test_asof_for_unmapped_ticker_is_rejected():
    assert asof_problem(
        days_ago_text(1), "SOMETHING-NEW", now=REFERENCE_NOW
    ) is not None


def test_consumer_rejects_equity_asof_during_open_session():
    # Payload esterno o alterato con la data di oggi a sessione aperta.
    problem = asof_problem("2026-07-15", "NVDA", now=SUMMER_MIDSESSION)

    assert problem is not None
    assert "non ancora consolidata" in problem

    # Il motivo deve distinguersi dall'obsolescenza.
    assert "obsoleto" not in problem


def test_consumer_equity_settlement_margin_boundary():
    asof = "2026-07-15"

    # 20:14 UTC: chiusura avvenuta ma margine di 15 minuti non trascorso.
    assert asof_problem(asof, "NVDA", now=SUMMER_CLOSE_MINUS_1) is not None

    # 20:15 UTC: consolidata.
    assert asof_problem(asof, "NVDA", now=SUMMER_AFTER_CLOSE) is None


def test_consumer_equity_margin_follows_dst():
    asof = "2026-12-15"

    # In inverno la chiusura e' alle 21:00 UTC: il cron delle 21:00 e' presto.
    assert asof_problem(asof, "NVDA", now=WINTER_CRON_2100) is not None
    assert asof_problem(asof, "NVDA", now=utc(2026, 12, 15, 21, 14)) is not None
    assert asof_problem(asof, "NVDA", now=WINTER_CONSOLIDATED) is None


def test_consumer_rejects_crypto_asof_before_utc_close():
    asof = "2026-07-15"

    # Giornata UTC ancora in corso.
    assert asof_problem(asof, "BTC-USD", now=utc(2026, 7, 15, 17, 0)) is not None
    assert asof_problem(asof, "BTC-USD", now=utc(2026, 7, 15, 23, 59)) is not None

    # Mezzanotte UTC passata ma margine non trascorso.
    assert asof_problem(asof, "BTC-USD", now=utc(2026, 7, 16, 0, 14)) is not None

    # Consolidata.
    assert asof_problem(asof, "BTC-USD", now=utc(2026, 7, 16, 0, 15)) is None


def test_crypto_and_equity_differ_at_the_same_instant():
    # Stessa data, stesso istante: l'azione e' consolidata, il crypto no.
    moment = utc(2026, 7, 15, 20, 15)

    assert asof_problem("2026-07-15", "NVDA", now=moment) is None
    assert asof_problem("2026-07-15", "BTC-USD", now=moment) is not None


def test_producer_output_always_passes_the_consumer_gate():
    """La barra scelta dal producer deve essere autorizzata dal consumer."""
    instants = [
        SUMMER_MIDSESSION,
        SUMMER_CLOSE_MINUS_1,
        SUMMER_AFTER_CLOSE,
        WINTER_CRON_2100,
        WINTER_CONSOLIDATED,
        utc(2026, 7, 16, 0, 10),
        utc(2026, 7, 16, 0, 20),
    ]

    checked = 0

    for moment in instants:
        for ticker, zone in [
            ("NVDA", "America/New_York"),
            ("BTC-USD", "UTC"),
        ]:
            frame = make_frame(moment.date(), periods=10, zone=zone)

            label, row, rejection = select_signal_bar(
                frame, FEATURES, ticker, now=moment
            )

            if rejection is not None:
                continue

            problem = asof_problem(
                to_bar_date_text(label), ticker, now=moment
            )

            assert problem is None, (ticker, moment.isoformat(), problem)
            checked += 1

    assert checked > 0


# =========================================================================
# 4. VALIDATORI
# =========================================================================

def test_scalar_validators():
    for bad in [NAN, INF, -INF, None, "5", True, "nan"]:
        assert not is_finite_number(bad), bad

    assert is_finite_number(0.0)
    assert is_finite_number(-3)

    for bad in [NAN, INF, 0.0, -1.0, None]:
        assert not is_valid_price(bad), bad

    assert is_valid_price(0.01)

    for bad in [NAN, INF, 0.0, -2.0]:
        assert not is_valid_quantity(bad), bad

    assert is_valid_quantity(1.5)

    for bad in [NAN, INF, -0.01, 1.01]:
        assert not is_valid_probability(bad), bad

    assert is_valid_probability(0.0)
    assert is_valid_probability(1.0)

    assert is_valid_cash(0.0)
    assert not is_valid_cash(NAN)
    assert not is_valid_cash(-1.0)


def test_scout_payload_validation():
    assert validate_scout_payload({}) == ["il payload scout e' vuoto"]
    assert validate_scout_payload([]) != []

    assert validate_scout_payload(
        {"TSLA": scout_entry(0.42, 300.0)}, now=REFERENCE_NOW
    ) == []

    for entry in [
        {"prob": 0.42, "price": NAN, "asof": days_ago_text(1)},
        {"prob": 0.42, "price": INF, "asof": days_ago_text(1)},
        {"prob": 0.42, "price": 0.0, "asof": days_ago_text(1)},
        {"prob": NAN, "price": 300.0, "asof": days_ago_text(1)},
        {"prob": 1.5, "price": 300.0, "asof": days_ago_text(1)},
        {"price": 300.0, "asof": days_ago_text(1)},
        {"prob": 0.42, "asof": days_ago_text(1)},
        {"prob": 0.42, "price": 300.0},
        {"prob": 0.42, "price": 300.0, "asof": 7},
        {"prob": 0.42, "price": 300.0, "asof": days_ago_text(30)},
        {"prob": 0.42, "price": 300.0, "asof": days_ago_text(-2)},
        # Data di oggi con sessione ancora aperta.
        {"prob": 0.42, "price": 300.0, "asof": days_ago_text(0)},
    ]:
        assert validate_scout_payload(
            {"TSLA": entry}, now=REFERENCE_NOW
        ), entry


def test_state_payload_requires_every_field():
    good = complete_state(
        positions={
            "PLTR": {
                "qty": 1.94,
                "entry_price": 174.34,
                "peak_price": 192.59
            }
        }
    )

    assert validate_state_payload(good) == []

    # Stato vuoto: tutti i campi obbligatori mancanti.
    problems = validate_state_payload({})

    assert len(problems) == len(REQUIRED_STATE_FIELDS)

    # Stato parziale.
    assert validate_state_payload({"cash": 500.0})

    # Ogni singolo campo mancante deve essere segnalato.
    for field in REQUIRED_STATE_FIELDS:
        partial = {
            key: value for key, value in good.items() if key != field
        }

        problems = validate_state_payload(partial)

        assert problems, field
        assert any(field in problem for problem in problems), field

    # Senza require_complete i campi assenti sono tollerati.
    assert validate_state_payload({}, require_complete=False) == []


def test_state_payload_value_checks():
    good = complete_state()

    for key in ("cash", "day_start_val", "initial_balance"):
        assert validate_state_payload(dict(good, **{key: NAN}))
        assert validate_state_payload(dict(good, **{key: INF}))

    assert validate_state_payload(dict(good, last_run_date="30-09-2026"))
    assert validate_state_payload(dict(good, last_run_date=20260930))
    assert validate_state_payload(dict(good, last_run_date="")) == []

    assert validate_state_payload(dict(good, positions="nope"))

    for position in [
        {"qty": NAN, "entry_price": 1.0, "peak_price": 1.0},
        {"qty": 1.0, "entry_price": NAN, "peak_price": 1.0},
        {"qty": 1.0, "entry_price": 1.0, "peak_price": NAN},
        {"qty": 0.0, "entry_price": 1.0, "peak_price": 1.0},
        {"entry_price": 1.0, "peak_price": 1.0},
    ]:
        assert validate_state_payload(
            dict(good, positions={"PLTR": position})
        ), position


# =========================================================================
# 5. SERIALIZZAZIONE E SCRITTURA ATOMICA
# =========================================================================

def test_atomic_write_refuses_nan_and_preserves_previous_file():
    workdir = tempfile.mkdtemp(prefix="nanguard_io_")

    try:
        path = os.path.join(workdir, "state.json")

        dump_json_atomic(path, {"cash": 1234.5})

        with open(path) as handle:
            before = handle.read()

        for payload in [
            {"cash": NAN},
            {"cash": INF},
            {"cash": -INF},
            {"positions": {"TSLA": {"qty": NAN}}},
        ]:
            raised = False

            try:
                dump_json_atomic(path, payload)
            except ValueError:
                raised = True

            assert raised, payload

        with open(path) as handle:
            assert handle.read() == before

        assert [n for n in os.listdir(workdir) if n.endswith(".tmp")] == []

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_written_json_never_contains_nan_tokens():
    workdir = tempfile.mkdtemp(prefix="nanguard_tokens_")

    try:
        path = os.path.join(workdir, "scout.json")

        payload = {
            "BTC-USD": {
                "prob": 0.4319702841450643,
                "price": 83485.1328125,
                "asof": "2026-09-30"
            }
        }

        dump_json_atomic(path, payload)

        with open(path) as handle:
            text = handle.read()

        for token in ["NaN", "Infinity", "-Infinity"]:
            assert token not in text

        assert json.loads(text) == payload

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# =========================================================================
# 6. main.py END-TO-END, FAIL-CLOSED
# =========================================================================

def test_empty_state_aborts_without_touching_file():
    result = run_main("{}", {"GLD": scout_entry(0.75, 250.0)})

    assert result["returncode"] != 0
    assert "campo obbligatorio assente" in result["stderr"]
    assert result["unchanged"]
    assert result["state_after"] == "{}"
    assert not result["telegram_sent"]


def test_partial_state_aborts_without_touching_file():
    partial = json.dumps({"cash": 500.0}, indent=4)

    result = run_main(partial, {"GLD": scout_entry(0.75, 250.0)})

    assert result["returncode"] != 0
    assert "incompleto" in result["stderr"]
    assert result["unchanged"]
    assert not result["telegram_sent"]


def test_each_missing_required_state_field_aborts():
    base = complete_state()

    for field in REQUIRED_STATE_FIELDS:
        payload = {
            key: value for key, value in base.items() if key != field
        }

        result = run_main(payload, {"GLD": scout_entry(0.75, 250.0)})

        assert result["returncode"] != 0, field
        assert field in result["stderr"], field
        assert result["unchanged"], field
        assert not result["telegram_sent"], field


def test_invalid_last_run_date_aborts():
    payload = dict(complete_state(), last_run_date="30/09/2026")

    result = run_main(payload, {"GLD": scout_entry(0.75, 250.0)})

    assert result["returncode"] != 0
    assert "last_run_date" in result["stderr"]
    assert result["unchanged"]


def test_corrupted_state_is_not_replaced_by_defaults():
    state_text = (
        '{\n'
        '    "cash": NaN,\n'
        '    "positions": {\n'
        '        "PLTR": {\n'
        '            "qty": 1.94,\n'
        '            "entry_price": 174.34,\n'
        '            "peak_price": 192.59\n'
        '        }\n'
        '    },\n'
        '    "initial_balance": 10000.0,\n'
        '    "day_start_val": NaN,\n'
        '    "last_run_date": "2026-09-30"\n'
        '}\n'
    )

    result = run_main(state_text, {"PLTR": scout_entry(0.51, 180.0)})

    assert result["returncode"] != 0
    assert "corrotto" in result["stderr"]
    assert result["unchanged"]
    assert not result["telegram_sent"]


def test_unreadable_state_aborts_instead_of_resetting():
    result = run_main("{ this is not json", {})

    assert result["returncode"] != 0
    assert result["unchanged"]
    assert not result["telegram_sent"]


def test_absent_state_file_uses_defaults_and_succeeds():
    result = run_main(None, {"GLD": scout_entry(0.75, 250.0)})

    assert result["returncode"] == 0, result["stderr"]
    assert "assente" in result["stdout"]

    persisted = json.loads(result["state_after"])

    assert validate_state_payload(persisted) == []
    assert "GLD" in persisted["positions"]


def test_missing_scout_file_aborts():
    result = run_main(complete_state(), None)

    assert result["returncode"] != 0
    assert "scout_signals.json" in result["stderr"]
    assert result["unchanged"]


def test_tsla_exit_with_nan_price_aborts_without_touching_state():
    state = complete_state(
        cash=500.0,
        day_start_val=3500.0,
        positions={
            "TSLA": {
                "qty": 10.0,
                "entry_price": 300.0,
                "peak_price": 350.0
            }
        }
    )

    # prob < 0.45 forzerebbe l'uscita ML: qty * NaN contaminava cash ed equity.
    scout_text = (
        '{\n'
        '    "TSLA": {\n'
        '        "prob": 0.4,\n'
        '        "price": NaN,\n'
        f'        "asof": "{days_ago_text(1)}"\n'
        '    },\n'
        '    "GLD": {\n'
        '        "prob": 0.75,\n'
        '        "price": 250.0,\n'
        f'        "asof": "{days_ago_text(1)}"\n'
        '    }\n'
        '}\n'
    )

    result = run_main(state, scout_text)

    assert result["returncode"] != 0, result["stdout"]
    assert "TSLA" in result["stderr"]
    assert result["unchanged"]
    assert "NaN" not in (result["state_after"] or "")
    assert not result["telegram_sent"]
    assert result["leftovers"] == []


def test_held_position_with_stale_asof_aborts():
    state = complete_state(
        cash=500.0,
        day_start_val=3500.0,
        positions={
            "TSLA": {
                "qty": 10.0,
                "entry_price": 300.0,
                "peak_price": 350.0
            }
        }
    )

    scout = {
        "TSLA": scout_entry(0.60, 310.0, days_ago=40),
        "GLD": scout_entry(0.75, 250.0)
    }

    result = run_main(state, scout)

    assert result["returncode"] != 0
    assert "TSLA" in result["stderr"]
    assert "obsoleto" in result["stderr"]
    assert result["unchanged"]
    assert not result["telegram_sent"]


def test_held_position_with_unconsolidated_asof_aborts():
    """asof di oggi mentre la sessione USA e' ancora aperta: fail-closed."""
    state = complete_state(
        cash=500.0,
        day_start_val=3500.0,
        positions={
            "TSLA": {
                "qty": 10.0,
                "entry_price": 300.0,
                "peak_price": 350.0
            }
        }
    )

    scout = {
        "TSLA": scout_entry(0.60, 310.0, days_ago=0),
        "GLD": scout_entry(0.75, 250.0)
    }

    result = run_main(state, scout, now=SUMMER_MIDSESSION)

    assert result["returncode"] != 0
    assert "TSLA" in result["stderr"]
    assert "non ancora consolidata" in result["stderr"]
    assert result["unchanged"]
    assert not result["telegram_sent"]


def test_candidate_with_unconsolidated_asof_is_skipped():
    scout = {
        # Supererebbe la soglia, ma la sessione di oggi e' ancora aperta.
        "GLD": scout_entry(0.75, 250.0, days_ago=0),
        "QQQ": scout_entry(0.70, 500.0)
    }

    result = run_main(complete_state(), scout, now=SUMMER_MIDSESSION)

    assert result["returncode"] == 0, result["stderr"]
    assert "non ancora consolidata" in result["stdout"]

    persisted = json.loads(result["state_after"])

    assert validate_state_payload(persisted) == []
    assert "GLD" not in persisted["positions"]
    assert "QQQ" in persisted["positions"]


def test_todays_equity_asof_is_accepted_once_settled():
    scout = {"GLD": scout_entry(0.75, 250.0, days_ago=0)}

    # 20:14 UTC: ancora rifiutato, nessun ingresso.
    early = run_main(complete_state(), scout, now=SUMMER_CLOSE_MINUS_1)

    assert early["returncode"] == 0, early["stderr"]
    assert "GLD" not in json.loads(early["state_after"])["positions"]

    # 20:15 UTC: consolidato, ingresso consentito.
    settled = run_main(complete_state(), scout, now=SUMMER_AFTER_CLOSE)

    assert settled["returncode"] == 0, settled["stderr"]
    assert "GLD" in json.loads(settled["state_after"])["positions"]


def test_candidate_with_stale_asof_is_skipped_but_run_completes():
    scout = {
        # Supererebbe la soglia di ingresso, ma la barra e' obsoleta.
        "GLD": scout_entry(0.75, 250.0, days_ago=40),
        "ETH-USD": scout_entry(0.57, 2671.37)
    }

    result = run_main(complete_state(), scout)

    assert result["returncode"] == 0, result["stderr"]
    assert "GLD" in result["stdout"]

    persisted = json.loads(result["state_after"])

    assert validate_state_payload(persisted) == []
    assert "GLD" not in persisted["positions"]
    assert "ETH-USD" in persisted["positions"]


def test_candidate_with_future_asof_is_skipped():
    scout = {
        "GLD": scout_entry(0.75, 250.0, days_ago=-3),
        "ETH-USD": scout_entry(0.57, 2671.37)
    }

    result = run_main(complete_state(), scout)

    assert result["returncode"] == 0, result["stderr"]

    persisted = json.loads(result["state_after"])

    assert "GLD" not in persisted["positions"]
    assert "ETH-USD" in persisted["positions"]


def test_candidate_with_missing_asof_is_skipped():
    scout = {
        "GLD": {"prob": 0.75, "price": 250.0},
        "ETH-USD": scout_entry(0.57, 2671.37)
    }

    result = run_main(complete_state(), scout)

    assert result["returncode"] == 0, result["stderr"]

    persisted = json.loads(result["state_after"])

    assert "GLD" not in persisted["positions"]
    assert "ETH-USD" in persisted["positions"]


def test_valid_run_still_persists_finite_state():
    scout = {
        "GLD": scout_entry(0.75, 250.0),
        "QQQ": scout_entry(0.33, 500.0)
    }

    result = run_main(complete_state(), scout)

    assert result["returncode"] == 0, result["stderr"]

    text = result["state_after"]

    for token in ["NaN", "Infinity"]:
        assert token not in text

    persisted = json.loads(text)

    assert validate_state_payload(persisted) == []
    assert result["telegram_sent"]
    assert result["leftovers"] == []

    # Le soglie non sono state toccate: 0.75 entra, 0.33 no.
    assert "GLD" in persisted["positions"]
    assert "QQQ" not in persisted["positions"]


# =========================================================================
# 7. INTEGRAZIONE run_scout_and_train()
# =========================================================================

def test_run_scout_and_train_ties_features_price_and_asof_to_one_bar():
    engine = import_model_engine()

    now = utc(2026, 10, 2, 17, 0)            # sessione del 2/10 ancora aperta
    history = make_price_history(date(2026, 10, 2), periods=300)

    # La barra odierna e' incompleta e il provider restituisce Close NaN:
    # esattamente lo scenario dell'incidente.
    history.iloc[-1, history.columns.get_loc("Close")] = NAN

    expected_date = "2026-10-01"
    expected_close = float(history["Close"].iloc[-2])

    yfinance_stub = types.ModuleType("yfinance")

    class Ticker:
        def __init__(self, ticker):
            self.ticker = ticker

        def history(self, **kwargs):
            return history.copy()

    yfinance_stub.Ticker = Ticker
    yfinance_stub.download = lambda ticker, **kwargs: history.copy()

    original_yf = engine.yf
    original_pool = engine.SCOUT_POOL
    workdir = tempfile.mkdtemp(prefix="nanguard_engine_")
    cwd = os.getcwd()

    try:
        engine.yf = yfinance_stub
        engine.SCOUT_POOL = ["NVDA"]

        os.chdir(workdir)

        engine.run_scout_and_train(now=now)

        with open("scout_signals.json") as handle:
            raw = handle.read()

        signals = json.loads(raw)

    finally:
        os.chdir(cwd)
        engine.yf = original_yf
        engine.SCOUT_POOL = original_pool
        shutil.rmtree(workdir, ignore_errors=True)

    for token in ["NaN", "Infinity"]:
        assert token not in raw

    assert list(signals) == ["NVDA"]

    entry = signals["NVDA"]

    # asof e prezzo provengono dalla stessa barra attesa.
    assert entry["asof"] == expected_date
    assert entry["price"] == expected_close
    assert is_valid_probability(entry["prob"])

    # La probabilita' proviene dalla stessa riga: la ricalcoliamo dai modelli
    # finali addestrati sullo stesso dataset e confrontiamo il valore esatto.
    featured = engine.calculate_features(history.copy())

    trainable = featured.dropna(
        subset=engine.FEATURES + ["Target"]
    ).copy()

    models = engine.train_final_models(
        trainable[engine.FEATURES],
        trainable["Target"].astype(int)
    )

    label, row, rejection = select_signal_bar(
        featured, engine.FEATURES, "NVDA", now=now
    )

    assert rejection is None
    assert to_bar_date_text(label) == expected_date

    expected_prob = float(
        np.mean([
            model.predict_proba(row[engine.FEATURES])[0][1]
            for model in models.values()
        ])
    )

    assert math.isclose(
        entry["prob"], expected_prob, rel_tol=0.0, abs_tol=1e-12
    ), (entry["prob"], expected_prob)


# =========================================================================

def main():
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]

    failures = []

    for test in tests:

        try:
            test()
            print(f"PASS  {test.__name__}")

        except Exception as error:
            failures.append(test.__name__)
            print(f"FAIL  {test.__name__}: {error!r}")

    print(f"\n{len(tests) - len(failures)}/{len(tests)} test superati.")

    if failures:
        print("Falliti: " + ", ".join(failures))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
