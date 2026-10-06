# RESEARCH LOG / DECISION LEDGER

## Status --- 2026-10-06

NaN incident closed. V1 cron resumed. V2 research **plan** version 4
adopted 2026-10-06 after audit 004 APPROVED. Not an executable protocol.
No candidate before the 0A–0C freeze. R0.1 is authorised as forensic
work, independent of Phase 0A.

### V2 roadmap: two audits, verdicts v1 APPROVED WITH CHANGES, v2 REJECTED

Roadmap v1 was submitted to independent adversarial audit by GPT-5.6 Sol
on 2026-10-06. Verdict: APPROVED WITH CHANGES, eight blockers. Two of
them invalidated statements this log had recorded as findings, and those
entries are corrected below.

Roadmap v2 addressed all eight and was submitted to a second audit the
same day. Verdict: **REJECTED**. Core reason: several blockers were
moved to Phase 0C or to a list of open decisions rather than resolved,
the architectural blocker on the plugin lifecycle persists, and new
defects were found in the historical results used as context. The
auditor also noted that a strictly forensic activity such as R0.1 could
be authorised separately without adopting the roadmap.

Governance correction accepted from audit 002: open decisions must not
be handed to the auditor. Claude proposes a motivated position, Filippo
decides the mandates, the auditor attempts to falsify the proposal.

Roadmap v3 was written the same day. Audit 003 verdict: **APPROVED WITH
CHANGES**. The recategorisation as a plan rather than a protocol was
accepted. Six residual blockers: confirmatory shadow occupancy, placebo
two-sided test, D1 vs D15/0B, aligned documents vs §1 and §2.1, D4 and
D22 incomplete, Close-by table mismatch. R0.1 independently
authorisable.

Roadmap v4 addresses those six plus the listed improvements, including
the explained TopK-18 double row. Audit 004 verdict: **APPROVED** as a
plan. Adopted 2026-10-06 by Filippo. Three non-blocking improvements
applied the same day (D4 Branch A only; D22 quarterly split rebalance;
placebo tail follows the improving direction of the metric).

Audit trail: `docs/audits/AUDIT_RESULT_001.md` (reconstruction),
`docs/audits/AUDIT_REQUEST_002.md`,
`docs/audits/AUDIT_RESULT_002.md` (verbatim),
`docs/audits/AUDIT_REQUEST_003.md`,
`docs/audits/AUDIT_RESULT_003.md` (verbatim),
`docs/audits/AUDIT_REQUEST_004.md`,
`docs/audits/AUDIT_RESULT_004.md` (verbatim). Operating procedure in
`docs/CURSOR_CLAUDE_WORKFLOW.md`.

### V1 cron pause revoked

The pause recorded on 2026-09-30 was conditional on the NaN corruption
being unresolved. That condition no longer holds: the causal chain is
proven, the guards are merged, the state is reconstructed from verified
history, and the fix has been validated in production. The pause is
therefore revoked and `run_bot.yml` is active again as of
2026-10-05. `retrain.yml` remains `disabled_manually`.

VERIFIED, 2026-10-06, via the GitHub Actions API and commit inspection:
17 of 18 workflows `active`; two scheduled runs executed successfully
(`259eba1` at 2026-10-05T21:12Z and `640ca0e` at 2026-10-06T01:50Z),
both auto-pushing to main.

### Production validation of the NaN fix

The run at 2026-10-06T01:50Z corresponds to 21:50 ET, which is exactly
the post-20:00 ET window that previously produced 16 NaN prices out of
18. Result: zero NaN, `asof` present on all 18 tickers, resulting state
passing `validate_state_payload(require_complete=True)`.

The `asof` split also confirms the calendar policy behaves as designed:
16 equity tickers reported `2026-10-05` while the 2 crypto tickers
reported `2026-10-04`, because the 2026-10-05 crypto bar had not yet
settled at run time. Different dates for different market calendars is
the correct outcome.

State on `origin/main` at `640ca0e`: cash 2287.02, positions NVDA, COIN,
AMZN, PLTR, total equity 10439.08 (+4.39% versus 10000).

### Status --- 2026-09-30 (superseded)

V1 is frozen for research. V1 cron should remain paused while NaN
corruption is unresolved. V2 is not implemented.

## Decisions

1.  V1 is a benchmark, not a template to blindly patch.
2.  V2 is a clean reconstruction informed by V1 lessons.
3.  V2 objective: search for genuine robust quantitative/predictive
    edge.
4.  Trend/momentum are candidate hypotheses and baselines.
5.  ML must demonstrate incremental value.
6.  ~~Dynamic universe is optional, not a mandatory replacement.~~
    SUSPENDED 2026-10-06 by audit 002. The comparison this decision
    rested on is invalid, see Completed research. The decision is
    suspended rather than reversed: nothing shows the dynamic universe
    is better, only that the evidence for preferring the static one does
    not hold.
7.  Highest backtest return is not the selection criterion.
8.  Use OOS/holdout discipline and realistic costs.
9.  ChatGPT and Claude/Cursor review each other's work independently.

## Completed research

-   NaN causal chain proven, 2026-10-04. Last fully valid state
    `0442449` (2026-09-25 18:03Z, cash 0.0, 6 positions). First
    terminal corruption `18d54d7` (2026-09-26 00:02Z), the TSLA exit:
    `curr_price = scout.get(t, {}).get("price", default)` returned the
    present-but-NaN value because the default only fires on a missing
    key, and the ML exit branch (`prob` 0.4403 < 0.45) had no price
    guard, so `cash += qty * NaN`. The stop branches did not fire
    because any comparison with NaN is False. An earlier transient
    corruption at `0c64d3a` (2026-09-22) affected only `day_start_val`
    and self-healed, since that field is recomputed each new day.
-   Provider failure window identified: all 4 corrupted runs occurred
    after 20:00 ET (end of extended hours); all 57 runs before 20:00 ET
    were clean. Not a sufficient condition on its own: two weekday runs
    after 20:00 ET in late August were clean, and all 4 failures fall
    from 2026-09-21 onward, suggesting a provider behaviour change.
-   Portfolio state reconstructed, 2026-10-04, commit `40bba21`. Cash
    6462.649979109016 derived as 0.0 + TSLA 604.4601033559815 + GLD
    2639.9109009564663 + NVDA 3218.2789747965685. The TSLA exit price
    372.11 (official close 2026-09-25) was supplied externally because
    it is absent from the repository; it is temporally correct because
    the exit probability was computed on the 2026-09-25 bar, which is
    the last row surviving `dropna(subset=FEATURES)`. GLD and NVDA
    proceeds were recoverable from scout history. Position fields for
    PLTR, COIN and AMZN were byte-identical across `0442449` and
    `bd4359f`.
-   Git artifact staging closed, 2026-10-04, commit `06006e3`. Seven
    `__pycache__/*.pyc` were tracked and had entered the repository via
    the bot's own `git add .` at `fb0fdcb`; `.gitignore` alone would not
    have covered them, so they were untracked with `git rm --cached`.
-   R0.1 forensic ledger written 2026-10-06 as `docs/R01_PROVENANCE.md`.
    52 CSVs inventoried with windows; two TopK-18 rows attributed to
    `simulate(k=18)` and `static_18(with_costs=True)` plus the daily
    `COST_PER_SIDE` subtraction; `auto_adjust` / feature-set / cost
    inventory; `features.py` whole-frame `dropna()` recorded as a
    live/backtest non-comparability axis. No strategy conclusion.
-   Target-horizon screening completed; 1d was least weak but no
    meaningful skill demonstrated.
-   ~~Dynamic-universe fair comparison completed; static 18 remains the
    reference, dynamic selection is optional.~~ **INVALID, 2026-10-06,
    audit 002.** The comparison is neither fair nor a buy & hold
    benchmark. VERIFIED: `static_equal_weight()` averages the 18 asset
    returns daily, which is a daily-rebalanced equal-weight portfolio,
    then hardcodes turnover to zero, so the static leg is credited 0.21%
    average daily turnover against 21.61% for Top-8 while rebalancing
    the same way; and selection uses day `d` close and volume, selects
    on `d`, and credits the `d` to `d+1` close-to-close return with no
    signal lag or next-open execution. VERIFIED, found 2026-10-06 and
    not raised by the audit: `dynamic_universe_fair_summary.csv` holds
    two different rows for TopK 18, one with 487 observations and
    +87.15% and one with 711 observations and -16.26% with a -57.13%
    drawdown. EXPLAINED 2026-10-06 by audit 003, confirmed in
    `dynamic_universe_fair_comparison.py`: 487 is `simulate(k=18)`;
    711 is `static_18(with_costs=True)` which subtracts `COST_PER_SIDE`
    from every row, not once. The negative sign is almost entirely that
    bug. R0.1 attributes rows to functions and does not elect a true
    benchmark. Both remain invalid as buy & hold. Both the rerun
    protocol and any later use of either figure require their own
    audit.
-   V1 portfolio run #10: €10,000 -\> €7,980.02, -20.20%, DD -45.57%,
    Sharpe -0.2496, PF .8787.

## Open questions

1.  ~~Exact NaN causal chain.~~ CLOSED 2026-10-04, see Completed
    research.
2.  Exact provenance of each historical result. Roadmap R0.1,
    independent of Phase 0A. Forensic ledger; no strategic conclusions.
3.  Which signal families have genuine OOS edge. Roadmap Phase 3.
4.  Whether ML adds value after a strong quantitative baseline. Roadmap
    Phase 5.
5.  Best portfolio/risk construction after realistic costs. Roadmap
    Phase 1 for the sizing and risk baselines, Phase 0B and 0C for the
    cost model.
6.  How to build a locked holdout and forward/shadow test without
    contamination. Roadmap Phase 0A for the contamination map, Phase 0C
    for the three regimes, Phase 6 for the forward shadow. A partial
    answer recorded on 2026-10-06 was withdrawn after audit 001: it
    claimed forward time is the only clean holdout and promoted shadow
    trading to primary validation mechanism. Corrected position, after
    audits 001–003: sources are not interchangeable. Nested
    walk-forward, frozen external markets and leave-one-cohort-out are
    robustness evidence and cannot promote a candidate to
    validated/deployable. An unused historical block is confirmatory
    only if quarantined. A paired test on already-seen data is
    comparative inference. Experimental paper runs are development. The
    confirmatory shadow cohort is at most one frozen strategy, peeking
    sealed. See roadmap v4 §1.
7.  How much of any valid static-universe result is ex-post selection
    rather than a strategy property. Raised 2026-10-06. The question
    remains; it **cannot** rest on +87.15% as a buy & hold, because that
    figure was declared invalid by audit 002 and is a daily-rebalanced
    equal-weight stream. A corrected rerun, with its own audit, is
    required before the question can be measured.
8.  Extent of the `pct_change(fill_method='pad')` contamination across
    the full history. Roadmap R0.2. Known since 2026-10-01, still
    unquantified and still present in the code.

## Do not do

-   Do not keep tuning V1 parameters on the same period.
-   Do not select a strategy because it has the highest backtest return.
-   Do not infer causal stop performance from exit-reason P&L alone.
-   Do not erase evidence of the NaN incident.
-   Do not quote any Sharpe or return from the 2024-2026 window as
    evidence without its confidence interval. One computed case: SR
    1.155, q 252, T 1.941 gives SE 0.7187 and 95% interval [-0.254,
    2.564], which contains zero. `q = 252` is an equity-calendar
    approximation. Added 2026-10-06; numbers corrected after audits 001
    and 003.
-   Do not generalise that to "individual Sharpes are not
    distinguishable from zero". That plural claim is INFERRED, not
    VERIFIED. It was demonstrated only for SR 1.155. Every other Sharpe
    must be recomputed with its own duration, frequency and dependence.
    Paired differences on the same days can have far smaller variance.
    Added 2026-10-06 after audit 001; wording tightened after audit
    003.
-   Do not quote an IID Sharpe interval as sufficient. Skewness, excess
    kurtosis, autocorrelation and cross-asset dependence require HAC
    standard errors or block bootstrap. Added 2026-10-06 after audit
    001.
-   Do not treat the recent window as a valid holdout. INFERRED, not
    verified: it is contaminated for strategies, assets and parameters
    already explored. The result files do not all share one window, as
    previously stated here: the main OOS files span roughly 2025-03/05
    to 2026-09, the dynamic-universe fair comparison 2024-10 to 2026-09,
    and some dynamic-universe equity files 2021-12 to 2026-09. Full
    extent remains UNKNOWN until R0.1. Added 2026-10-06; corrected
    after audit 001.
-   Do not assume the 18-ticker universe is free of ex-post selection
    bias. No point-in-time rule for it is documented in the repository.
    Note the distinction drawn by audit 002: "no documented rule" is not
    the same as "no rule ever existed", and only the first is verified.
    Added 2026-10-06; refined after audit 002.
-   Do not quote +87.15% as a static Buy & Hold result, and do not quote
    the dynamic-universe comparison as fair. Both were declared invalid
    on 2026-10-06, see Completed research. Added 2026-10-06 after audit
    002.
-   Do not quote the master context drawdown of -38.11% for Static 18.
    That figure is the CAGR mislabelled as a drawdown; the recorded max
    drawdown is -27.20%. Corrected 2026-10-06 after audit 002.
