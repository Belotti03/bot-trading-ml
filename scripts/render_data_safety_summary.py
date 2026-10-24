# scripts/render_data_safety_summary.py
# Riepilogo osservabilita' del report diagnostico. Non decide il trading.

"""
Legge data_safety_report.json, assegna PASS/WARNING/FAIL di osservabilita'
e scrive il Job Summary di GitHub Actions.

Non chiama Yahoo, non tocca portfolio_state.json / scout_signals.json,
non cambia Telegram e non fa fallire il job del bot: l'uscita e' sempre 0.
"""

import json
import os
import sys


DEFAULT_REPORT_FILE = "data_safety_report.json"
DEFAULT_LOG_FILE = "bot_run.log"
ABORT_PREFIXES = ("ABORT:", "ABORT model_engine")


def report_path():
    return os.environ.get("DATA_SAFETY_REPORT_FILE") or DEFAULT_REPORT_FILE


def log_path():
    return os.environ.get("BOT_RUN_LOG") or DEFAULT_LOG_FILE


def last_abort_line(path):
    """Ultima riga ABORT da un log opzionale, senza inventare numeri."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return None
    found = None
    for line in lines:
        text = line.strip()
        if text.startswith(ABORT_PREFIXES):
            found = text
    return found


def load_report(path):
    if not os.path.isfile(path):
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.loads(handle.read())
    except Exception:
        return None, "UNREADABLE"
    if not isinstance(payload, dict):
        return None, "UNREADABLE"
    return payload, "OK"


def build_observability(payload, run_outcome, abort_line=None):
    """Verdetto di osservabilita', distinto dalle decisioni operative."""
    reasons = []

    if run_outcome == "MISSING":
        reasons.append("Report non emesso: file assente")
        if abort_line:
            reasons.append(abort_line)
        else:
            reasons.append("reason=no_report_file")
        return {
            "verdict": "FAIL",
            "reasons": reasons,
            "run_outcome": "MISSING",
        }

    if run_outcome == "UNREADABLE":
        reasons.append("Report non interpretabile: JSON illeggibile")
        if abort_line:
            reasons.append(abort_line)
        return {
            "verdict": "FAIL",
            "reasons": reasons,
            "run_outcome": "UNREADABLE",
        }

    payload = payload or {}
    if not payload.get("report_complete"):
        reasons.append("report_complete e' false: controlli dati non chiusi")
        return {
            "verdict": "FAIL",
            "reasons": reasons,
            "run_outcome": run_outcome,
        }

    macro = payload.get("macro") or {}
    if macro.get("check") == "FAIL":
        status = macro.get("status") or "INVALID"
        reasons.append(
            "Macro FAIL (%s): ingressi congelati per dati macro"
            % status
        )

    stops = payload.get("stops") or {}
    for item in stops.get("positions") or []:
        if item.get("atr_check") == "FAIL":
            ticker = item.get("ticker") or "?"
            source = item.get("source") or "?"
            reasons.append(
                "ATR FAIL su %s (source=%s): stop in fallback"
                % (ticker, source)
            )

    if reasons:
        return {
            "verdict": "WARNING",
            "reasons": reasons,
            "run_outcome": run_outcome,
        }

    return {
        "verdict": "PASS",
        "reasons": ["Controlli dati chiusi"],
        "run_outcome": run_outcome,
    }


def render_markdown(payload, observability):
    payload = payload or {}
    macro = payload.get("macro") or {}
    stops = payload.get("stops") or {}
    commit = payload.get("commit") or {}
    positions = list(stops.get("positions") or [])
    lines = [
        "## Data safety observability",
        "",
        "- verdict: %s" % observability.get("verdict"),
        "- run_outcome: %s" % observability.get("run_outcome"),
        "- report_complete: %s" % payload.get("report_complete"),
        "- commit: %s (%s)" % (commit.get("sha"), commit.get("check")),
        "- macro: %s / %s" % (macro.get("status"), macro.get("check")),
        "- entries_allowed: %s" % macro.get("entries_allowed"),
        "- stops: %s" % stops.get("check"),
        "- open_positions: %s" % len(positions),
        "",
        "Motivazioni:",
    ]
    for reason in observability.get("reasons") or []:
        lines.append("- %s" % reason)
    invalid = payload.get("invalid_values") or []
    if invalid:
        lines.append("")
        lines.append("Valori non usabili:")
        for item in invalid:
            lines.append(
                "- %s %s: %s"
                % (
                    item.get("ticker") or "",
                    item.get("field"),
                    item.get("observed"),
                )
            )
    lines.append("")
    return "\n".join(lines)


def write_json(path, payload):
    text = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


def append_step_summary(text):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def fallback_payload(observability, abort_line=None):
    payload = {
        "report_complete": False,
        "run_outcome": observability.get("run_outcome"),
        "reason": "no_report_file",
        "observability": observability,
    }
    if abort_line:
        payload["abort"] = abort_line
    return payload


def render(report_file=None, log_file=None):
    path = report_file or report_path()
    abort_line = last_abort_line(log_file or log_path())
    payload, run_outcome = load_report(path)
    observability = build_observability(payload, run_outcome, abort_line)

    if run_outcome == "MISSING":
        payload = fallback_payload(observability, abort_line)
        try:
            write_json(path, payload)
        except Exception as error:
            print("DATA_SAFETY_SUMMARY_WRITE_ERROR " + str(error))
    elif run_outcome == "OK":
        payload = dict(payload)
        payload["observability"] = observability
        try:
            write_json(path, payload)
        except Exception as error:
            print("DATA_SAFETY_SUMMARY_WRITE_ERROR " + str(error))

    markdown = render_markdown(payload, observability)
    try:
        append_step_summary(markdown)
    except Exception as error:
        print("DATA_SAFETY_SUMMARY_ERROR " + str(error))

    print(
        "OBSERVABILITY_VERDICT %s %s"
        % (observability.get("verdict"), observability.get("run_outcome"))
    )
    return observability


def main():
    try:
        render()
    except Exception as error:
        print("DATA_SAFETY_SUMMARY_ERROR " + str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
