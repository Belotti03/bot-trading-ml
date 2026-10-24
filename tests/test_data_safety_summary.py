# tests/test_data_safety_summary.py
# Verdetti di osservabilita' del report diagnostico (P0/P1).

"""
Esegue lo script in una directory temporanea. Non chiama Yahoo Finance,
non scrive portfolio_state.json / scout_signals.json del repository e
non avvia main.py.
"""

import json
import os
import subprocess
import sys
import tempfile


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "render_data_safety_summary.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import render_data_safety_summary as summary  # noqa: E402


def complete_report(**overrides):
    payload = {
        "report_complete": True,
        "commit": {"sha": "abc123", "check": "PASS"},
        "macro": {
            "check": "PASS",
            "status": "BULLISH",
            "reason": "SPY $500.00 >= SMA200 $400.00",
            "spy_close": 500.0,
            "sma200": 400.0,
            "spy_close_valid": True,
            "sma200_valid": True,
            "entries_allowed": True,
        },
        "stops": {
            "check": "NOT_APPLICABLE",
            "reason": "no_open_positions",
            "positions": [],
        },
        "invalid_values": [],
    }
    payload.update(overrides)
    return payload


def run_renderer(workdir, extra_env=None):
    environment = dict(os.environ)
    environment.pop("GITHUB_SHA", None)
    environment.pop("GITHUB_STEP_SUMMARY", None)
    environment["GITHUB_STEP_SUMMARY"] = os.path.join(workdir, "step_summary.md")
    if extra_env:
        environment.update(extra_env)

    completed = subprocess.run(
        [sys.executable, SCRIPT],
        cwd=workdir,
        env=environment,
        capture_output=True,
        text=True,
    )
    report = None
    report_raw = None
    report_path = os.path.join(workdir, "data_safety_report.json")
    if os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as handle:
            report_raw = handle.read()
        try:
            report = json.loads(report_raw)
        except json.JSONDecodeError:
            report = None
    step_summary = None
    summary_path = os.path.join(workdir, "step_summary.md")
    if os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as handle:
            step_summary = handle.read()
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "report": report,
        "report_raw": report_raw,
        "step_summary": step_summary,
        "workdir_names": os.listdir(workdir),
    }


def test_verdict_missing_is_fail():
    result = summary.build_observability(None, "MISSING")
    assert result["verdict"] == "FAIL"
    assert result["run_outcome"] == "MISSING"
    assert any("file assente" in item for item in result["reasons"])


def test_verdict_unreadable_is_fail():
    result = summary.build_observability(None, "UNREADABLE")
    assert result["verdict"] == "FAIL"
    assert result["run_outcome"] == "UNREADABLE"


def test_verdict_incomplete_is_fail():
    result = summary.build_observability(
        {"report_complete": False, "macro": {"check": "NOT_CHECKED"}},
        "OK",
    )
    assert result["verdict"] == "FAIL"


def test_verdict_complete_bullish_is_pass():
    result = summary.build_observability(complete_report(), "OK")
    assert result["verdict"] == "PASS"


def test_verdict_sha_absent_is_still_pass():
    payload = complete_report(
        commit={"sha": None, "check": "NOT_CHECKED"},
    )
    result = summary.build_observability(payload, "OK")
    assert result["verdict"] == "PASS"


def test_verdict_invalid_macro_is_warning():
    payload = complete_report(
        macro={
            "check": "FAIL",
            "status": "INVALID",
            "entries_allowed": False,
        }
    )
    result = summary.build_observability(payload, "OK")
    assert result["verdict"] == "WARNING"
    assert any("Macro FAIL" in item for item in result["reasons"])


def test_verdict_atr_fallback_is_warning():
    payload = complete_report(
        stops={
            "check": "APPLICABLE",
            "positions": [
                {
                    "ticker": "NVDA",
                    "atr_check": "FAIL",
                    "source": "%",
                    "stop_loss_check": "PASS",
                    "trailing_check": "PASS",
                }
            ],
        }
    )
    result = summary.build_observability(payload, "OK")
    assert result["verdict"] == "WARNING"
    assert any("source=%" in item for item in result["reasons"])


def test_missing_json_writes_fallback_and_exits_zero():
    workdir = tempfile.mkdtemp(prefix="safety_summary_")
    result = run_renderer(workdir)
    assert result["returncode"] == 0
    assert result["report"]["report_complete"] is False
    assert result["report"]["run_outcome"] == "MISSING"
    assert result["report"]["reason"] == "no_report_file"
    assert result["report"]["observability"]["verdict"] == "FAIL"
    assert "OBSERVABILITY_VERDICT FAIL MISSING" in result["stdout"]
    assert result["step_summary"]
    assert "verdict: FAIL" in result["step_summary"]
    assert "portfolio_state.json" not in result["workdir_names"]
    assert "scout_signals.json" not in result["workdir_names"]


def test_missing_json_keeps_optional_abort_line():
    workdir = tempfile.mkdtemp(prefix="safety_summary_")
    with open(os.path.join(workdir, "bot_run.log"), "w", encoding="utf-8") as handle:
        handle.write("other line\nABORT: stato corrotto o incompleto.\n")
    result = run_renderer(workdir)
    assert result["returncode"] == 0
    assert result["report"]["abort"] == "ABORT: stato corrotto o incompleto."
    assert any(
        "ABORT:" in item
        for item in result["report"]["observability"]["reasons"]
    )


def test_valid_json_is_pass_and_keeps_original_fields():
    workdir = tempfile.mkdtemp(prefix="safety_summary_")
    original = complete_report()
    with open(
        os.path.join(workdir, "data_safety_report.json"),
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(original, handle)
    result = run_renderer(workdir)
    assert result["returncode"] == 0
    assert result["report"]["macro"]["status"] == "BULLISH"
    assert result["report"]["stops"]["check"] == "NOT_APPLICABLE"
    assert result["report"]["observability"]["verdict"] == "PASS"
    assert "OBSERVABILITY_VERDICT PASS OK" in result["stdout"]
    assert "verdict: PASS" in result["step_summary"]
    assert "portfolio_state.json" not in result["workdir_names"]


def test_unreadable_json_is_fail_and_does_not_replace_file():
    workdir = tempfile.mkdtemp(prefix="safety_summary_")
    raw_path = os.path.join(workdir, "data_safety_report.json")
    with open(raw_path, "w", encoding="utf-8") as handle:
        handle.write("{not-json")
    result = run_renderer(workdir)
    assert result["returncode"] == 0
    assert "OBSERVABILITY_VERDICT FAIL UNREADABLE" in result["stdout"]
    with open(raw_path, encoding="utf-8") as handle:
        assert handle.read() == "{not-json"


def test_renderer_does_not_write_repo_state_files():
    workdir = tempfile.mkdtemp(prefix="safety_summary_")
    result = run_renderer(workdir)
    repo_state = os.path.join(REPO_ROOT, "portfolio_state.json")
    before = os.path.getmtime(repo_state) if os.path.exists(repo_state) else None
    assert result["returncode"] == 0
    after = os.path.getmtime(repo_state) if os.path.exists(repo_state) else None
    assert before == after
    assert "portfolio_state.json" not in result["workdir_names"]


def main():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = []
    for test in tests:
        try:
            test()
            print("PASS  %s" % test.__name__)
        except Exception as error:
            failures.append(test.__name__)
            print("FAIL  %s: %r" % (test.__name__, error))
    print("\n%s/%s test superati." % (len(tests) - len(failures), len(tests)))
    if failures:
        print("Falliti: " + ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
