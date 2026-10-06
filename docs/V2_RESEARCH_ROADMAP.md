# V2 RESEARCH ROADMAP

Version 4, revised 2026-10-06.

## Status

**Adopted as a plan on 2026-10-06**, after independent audit 004
verdict APPROVED. Not an executable protocol. Not authority to run
candidates, change V1, or skip the 0A–0C freeze.

Filippo adopted the plan. Mandates in §11 (drawdown, split, branch
default, eligibility numbers) remain proposals until he closes them in
0A/0B. Until those close, the research hierarchy in
`docs/BOT_TRADING_V2_MASTER_CONTEXT.md` remains the operational
checklist, read together with this plan.

| Version | Audit | Verdict |
| --- | --- | --- |
| v1 | `docs/audits/AUDIT_RESULT_001.md` (reconstruction) | APPROVED WITH CHANGES, 8 blockers |
| v2 | `docs/audits/AUDIT_RESULT_002.md` (verbatim) | **REJECTED**, 10 blocking corrections |
| v3 | `docs/audits/AUDIT_RESULT_003.md` (verbatim) | APPROVED WITH CHANGES, 6 residual blockers |
| v4 | `docs/audits/AUDIT_RESULT_004.md` (verbatim) | **APPROVED** as a plan. Adopted 2026-10-06. |

## What this document is, and what it is not

This document is **a plan to construct the protocol**, plus a set of
**proposed positions** on every decision the protocol requires. It is
not an executable statistical protocol. The protocol becomes executable
only when Phases 0A, 0B and 0C have closed the decisions in section 11
and frozen the thresholds in section 7. No candidate result may be
computed before that freeze. Phase 0A cannot start on this text until
v4 is approved.

Audit 003 accepted this as the right category: refusing the document
because it is not yet a protocol would be a category error. Approval as
a plan still requires that decision gates be true constraints, that
positions not contradict the gates, and that aligned documents not
readmit withdrawn claims.

Governance: Claude proposes a motivated position, Filippo decides the
mandates, the auditor attempts to falsify the proposal.

## 0. Revision record

### v3 to v4, blocking corrections from audit 003

| # | Required | Where in v4 |
| --- | --- | --- |
| 1 | Shadow infrastructure ≠ confirmatory shadow cohort | §1, §5.2, §5.4, §9 |
| 2 | Placebo is an upper-tail test on the primary metric | §7.2, D10 |
| 3 | D1 / D15 / gate 0B no longer contradictory | D1, D15, §4.2, §9 |
| 4 | Master context and research log aligned to §1 and §2.1 | done outside this file, 2026-10-06 |
| 5 | D4 eligibility list and D22 numeric split | D4, D22 |
| 6 | Close-by of D8 / D9 / D10 aligned with the phase table | §9, D8, D9, D10 |

### Improvements adopted

| Required | Where |
| --- | --- |
| Blocking vs annotative flags | §3.3 |
| Kill for freeze-rule violation | §8 |
| Walk-forward trial counting; no family-budget reallocation | D5, §8 |
| Pre-registered regime as a gate if the mandate requires it | §7.1 |
| Double TopK-18 row explained, not UNRESOLVED | §12.3 |
| Q7 no longer rests on +87.15% as buy & hold | research log, outside this file |
| Implicit decisions declared | D26, D27, D28 |

### What audit 003 already accepted and v4 does not reopen

Evidence hierarchy in the body; DSR ≠ PSR ≠ paired test; data contract;
branches A/B with H1 incompatible with B; plugin lifecycle for code;
canonical trend baseline distinct from H2; volatility sizing as overlay;
individual adjudication; Appendix A; R0.1 independent; governance.

## 1. Evidence hierarchy

Three categories, never interchangeable.

| Category | What it can establish | What it cannot |
| --- | --- | --- |
| **Development evidence** | hypothesis generation, specification, parameter ranges, diagnostics, experimental paper runs | any claim of edge used for promotion to `validated` or `deployable` |
| **Robustness evidence** | that a result is not an artefact of one asset, one period, one cost assumption or one implementation choice | that the result is real; it is conditional on the development result being real |
| **Confirmatory evidence** | a pre-registered claim tested once on data not used to design or select the claim | anything, once the data has been observed |

Classification of sources:

| Source | Category | Note |
| --- | --- | --- |
| Nested walk-forward | robustness | estimates the selection process; does not decontaminate data used to design the hypothesis |
| Unused historical block | confirmatory **if and only if** R0.1 proves it was quarantined | UNKNOWN until R0.1. A quarantined block is confirmatory, not robustness |
| Frozen external markets | robustness | aids generalisation, may introduce selection bias and domain shift |
| Leave-one-cohort / asset-class-out | robustness | not an independent temporal holdout |
| Pre-registered paired test on data **already used** to design the hypothesis | comparative inference | does not decontaminate observed data |
| Pre-registered paired test on data **not used** to design the hypothesis | confirmatory | same rule as any other confirmatory test: once |
| Experimental paper runs, including multiple live candidates | development | occupy the paper adapter; they are **not** the confirmatory shadow |
| **Confirmatory shadow cohort** | confirmatory | at most one frozen strategy, append-only, peeking sealed until Filippo's reveal. The only unconditionally clean live source |

Consequence, restated after audit 003:

- Promotion to `validated` or `deployable` requires confirmatory
  evidence. Robustness evidence can only **block** that promotion, never
  grant it.
- In development, robustness evidence may kill a candidate (for example
  a leave-one-asset-out collapse). That is not a promotion.

## 2. Statistical protocol

### 2.1 Sharpe standard error

For an annualised Sharpe with `q` observations per year over `T` years:

    SE(SR_annual) ~= sqrt((1 + SR_annual^2 / (2q)) / T_years)

Worked on the one case where the inputs are known, the 487-observation
row of `dynamic_universe_fair_summary.csv` from 2024-10-15 to
2026-09-24, i.e. `T = 1.941`:

| | SE | 95% interval |
| --- | --- | --- |
| SR 1.155, q 252, T 1.941 | **0.7187** | **[-0.254, 2.564]** |

Constraints:

1. The plural claim "the individual Sharpes of this period are not
   distinguishable from zero" is **INFERRED, not VERIFIED**. It was
   demonstrated only for SR 1.155. Every other quoted Sharpe must be
   recomputed with its own duration, frequency and dependence before any
   statement is made about it.
2. `q = 252` is an equity-calendar approximation and is **not** a global
   constant. The 487-day row mixes an equity-style observation count
   with crypto in the basket. See §2.3 and D22.
3. Any IID interval is an approximation and is not sufficient. See §2.4.

### 2.2 Three distinct criteria, never conflated

| Criterion | Question | Reference | Requires |
| --- | --- | --- | --- |
| **PSR** | is this strategy's Sharpe above a stated benchmark Sharpe, given non-normality? | one declared benchmark Sharpe | skewness, excess kurtosis, sample length |
| **DSR** | does it survive the selection process that produced it? | the **expected maximum** Sharpe across the trials attempted | PSR inputs plus the effective number of correlated trials from the ledger |
| **Paired difference test** | is this strategy better than its primary comparator? | the joint distribution of the two return series | same-day paired returns, HAC or block bootstrap |

A candidate must satisfy DSR and the paired test. PSR alone is never
sufficient. The explicit Bailey / López de Prado formulae are written in
Phase 0C.

### 2.3 Observation frequency and mixed calendars

One `q` cannot be applied across sleeves. Equity sleeves use their
trading calendar, crypto uses its own. Portfolio-level metrics are
computed on the intersection of trading days; sleeve-level metrics on
native calendars. Every reported Sharpe carries its `q` and its
observation count.

### 2.4 Trials, dependence and correction

- A **trial** is defined in D5, including how walk-forward folds count.
- Correction is **hierarchical**: within a family, control the
  family-wise error rate; across families, use the effective number of
  trials in DSR. See D19.
- Intervals use HAC and block bootstrap, not IID. See D20.
- The D24 channel (legacy artefacts used to design the protocol) is
  counted in DSR **conservatively**, because a retrospective count of
  mental trials will be incomplete.

### 2.5 Threshold freezing

Power analysis determines the minimum detectable effect. It does **not**
determine risk tolerance, utility, maximum drawdown or what cost level
is economically acceptable. Those come from the Phase 0A economic
mandate.

Statistical thresholds are derived in Phase 0C from power analysis;
economic thresholds are set in Phase 0A by Filippo. Both are frozen,
using only development data or declared simulations, **before any
candidate result exists**. A threshold set or changed after a candidate
result is observed invalidates that candidate. Violation is a kill
criterion, §8.

The paired-difference gate ("interval excludes zero") and the economic
effect-size gate are **different**. With T ≈ 2 years the first will
often be INCONCLUSIVE. That is not a KILL. Killing underpowered
hypotheses for failing the paired CI is forbidden.

## 3. Data contract

### 3.1 Reproducibility, currently absent

VERIFIED: there is no raw dataset in the repository, the workflow
installs unpinned packages, and nothing records data or library
versions. Required before any experiment, still absent in the repo:

1. Immutable raw snapshots, append-only, with provider, endpoint,
   parameters, download timestamp and content hash.
2. Dependency lock. Exact pins plus a lock file; the environment is
   installed from the lock. See D23.
3. Data-version contract. Every result file records the snapshot hash,
   the lock hash, the interpreter version and the commit.

A result without these three is not admissible evidence.

### 3.2 Adjustment convention

VERIFIED: one explicit `auto_adjust=True`, seven explicit `False`, four
calls with no explicit value (`model_engine.py` `.history()`, `main.py`
ATR, `main.py` SPY, `data_loader.py`), while live uses the default. One
convention, applied everywhere, is set in D16.

### 3.3 Quality flags, orthogonal, blocking vs annotative

Independent boolean flags, any combination of which may hold for one
bar. Two classes, pre-registered.

**Blocking** — no signal is generated for that asset-date:
`bar_missing`, `bar_incomplete`, `market_closed`, `trading_halted`,
`invalid_ohlc`, `duplicate_row`, `out_of_order_timestamp`,
`timezone_or_session_mismatch`, `provider_outage`, `ticker_change`,
`currency_or_unit_change`, `volume_suspect`.

**Annotative** — signal is permitted, flag is stored:
`corporate_action` when the D16 adjustment has been applied;
`half_day_session`; `provider_revision`.

**Mixed:** `stale_value` permits valuation and blocks execution.

Rules: the panel is reindexed onto the expected per-market calendar
before any computation; flags are computed once in the data layer and
stored with the snapshot. A correctly adjusted split does not zero the
signal.

The list is INFERRED complete, not demonstrated complete.

### 3.4 Return computation

VERIFIED: 31 `pct_change()` calls across 15 Python files, none specifying
`fill_method`. `fill_method=None` is necessary but insufficient. Returns
are computed only after calendar reindexing and flag evaluation, and
never across a blocking-flag gap.

## 4. Universe

### 4.1 What is established

- VERIFIED: no point-in-time rule for the 18 tickers is documented in
  the repository.
- UNKNOWN: whether some rule was used outside the repository.
- The claim that retrospective selection explains a historical buy &
  hold cannot currently be tested, because the figure it referred to is
  not a buy & hold. See §12.3. The selection-bias question remains; it
  no longer rests on +87.15%.

### 4.2 Two mutually exclusive branches

Exactly one is chosen in Phase 0B, recorded as the **current branch**,
and not revisited without a new audit. Phase 0C does **not** start until
the branch is chosen. Vendor evaluation is not an open parallel to an
uncommitted branch.

**Branch A, point-in-time universe.** Requires a provider with
historical membership, delistings and corporate actions. Three sleeves,
membership and liquidity as known at `t-1` with declared information
lags, quarterly rebalance (D2), eligibility per D4, delisted assets
retained with delisting returns, no retroactive removal.

**Branch B, declared case study.** The current 18 tickers are used as a
fixed, acknowledged non-representative basket. Recorded with a
pre-registered review date. Switching later to A is a new decision and
requires a new audit.

Consequences of Branch B, binding:

- No claim of cross-sectional generalisation is permitted.
- **H1 cannot run.** No caveat, no "run with a disclaimer".
- Every reported result carries the case-study restriction in its
  header.
- H2, H3 and H4 remain case-study results. An edge specific to this
  basket is not promotable as a general V2 edge.

## 5. Engine, and the plugin lifecycle

### 5.1 What was wrong

v2 gated implementation. v3 allowed experimental plugins to "run in
shadow" and started shadow from Phase 1, while classifying forward
shadow as confirmatory. Audit 003: more than one live candidate on the
same period destroys confirmatory status. Infrastructure ≠ cohort.

### 5.2 Lifecycle of code

Three states. Implementation is permitted early; only **promotion** is
gated.

| State | May be | Requires | Live occupancy |
| --- | --- | --- | --- |
| `experimental` | implemented, backtested, run as a **development paper run** | pre-registration card | many, on the paper adapter; **not** the confirmatory cohort |
| `validated` | cited as evidence | confirmatory evidence per §1 and all gates in §7 | none, until selected for the confirmatory cohort |
| `deployable` | allocated real capital | `validated`, plus conformance suite, plus Filippo's explicit approval | live capital |

### 5.3 Conformance suite

Compares **pre-execution intent** where fill adapters must legitimately
diverge. Covers: data availability timing, partial bars, calendars and
corporate actions, event ordering, state transitions, fills and
slippage, error handling, and divergence between signal intent and
executed order. Until the suite passes, "one identical core" remains
UNKNOWN.

### 5.4 Shadow infrastructure vs confirmatory shadow cohort

Two objects, never the same.

**Shadow infrastructure** (Phase 1). The paper adapter, append-only
store, logging, and peeking controls. Building it does not occupy the
confirmatory slot.

**Development paper runs.** Any number of `experimental` plugins may
run on the paper adapter. Their live results are development evidence.
They do not count as confirmatory shadow.

**Confirmatory shadow cohort** (Phase 6). At most **one** strategy,
frozen before the first live bar, append-only, peeking sealed until
Filippo's reveal (D17). No second candidate may occupy the same live
window. Promotion to `deployable` waits on D7.

## 6. Baselines, diagnostics and attribution

### 6.1 Baselines, comparable candidates

Share data, dates, universe, fill model, costs, target volatility and
exposure.

- cash at the T-bill rate, not zero
- equal-weight buy-and-hold
- equal-weight rebalanced at a declared frequency, as a distinct entry
- cap-weighted or liquidity-weighted point-in-time, Branch A only
- inverse-volatility and risk parity
- volatility-matched SPY, volatility-matched QQQ, subject to D21
- per-sleeve benchmarks, aggregated by the D22 capital split
- V1 without the ML gate
- V1 with the ML gate
- **canonical trend baseline**, a single fixed, pre-registered trend
  rule, distinct from H2 research
- **volatility sizing**, applied to the same signal as its comparator
  with static sizing

### 6.2 Diagnostics

Reported, never a comparator: placebo distribution (also an inferential
gate per §7.2), leave-one-asset-out, HHI and risk contribution,
parameter and cost sensitivity, regime breakdown.

### 6.3 Attribution

Factor and beta attribution, exit-reason decomposition, turnover and
cost decomposition. Explains a result; never establishes one.

## 7. Acceptance criteria

Three tiers.

### 7.1 Hard gates, risk mandates

Non-negotiable. Values set in Phase 0A, see D13 and D14.

- maximum drawdown within mandate
- single-asset weight and concentration within mandate
- leverage and shorting within mandate
- data-contract compliance per §3.1
- **pre-registered regimes:** if the 0A mandate names required regimes,
  failing all of them is a hard gate, not a diagnostic. If the mandate
  names none, regime breakdown stays a diagnostic

### 7.2 Inferential gates

All must pass. Thresholds frozen per §2.5.

| Gate | Definition |
| --- | --- |
| DSR | survives the selection process, using the effective trial count; §2.2 |
| Paired difference | interval on the paired difference versus the **pre-registered primary comparator** excludes zero, HAC or block bootstrap. Failure at pre-registered power is INCONCLUSIVE, not KILL; see §2.5 |
| Placebo | the candidate's primary metric lies beyond the pre-registered quantile in the **improving** direction. One-sided. For a higher-is-better metric (paired Sharpe difference) that is the upper tail; for a loss (QLIKE) it is the **lower** tail. A result worse than the null does not pass. The distribution preserves autocorrelation, cross-sectional structure and realised trade frequency. The tail direction is written on the pre-registration card |
| Out-of-sample level | an absolute OOS threshold, with an interval on the IS-to-OOS degradation |
| Cost robustness | measured costs, three scenarios, reported break-even cost above the economically acceptable level from the mandate |
| Economic effect size | the point estimate exceeds the minimum economically useful effect from Phase 0A, a different quantity from the statistically detectable effect |

### 7.3 Diagnostics

Stability across pre-registered blocks and regimes with intervals
(unless §7.1 promotes regimes to a hard gate), leave-one-asset-out, HHI
and risk contribution, parameter sensitivity, turnover and capacity.

## 8. Stop criteria

**KILL**

1. Breach of a hard gate in §7.1.
2. Failure of an inferential gate in §7.2, other than an underpowered
   paired-difference interval, which is INCONCLUSIVE.
3. Exceeding the declared trial budget.
4. Demonstrated leakage or look-ahead.
5. Non-reproducible data or environment per §3.1.
6. Conformance or parity failure per §5.3.
7. Violation of the §2.5 freeze: any threshold set or changed after a
   candidate result was observed.

**INCONCLUSIVE / UNDERPOWERED**

The data cannot decide at the pre-registered power. Not a failure and
not a pass. One INCONCLUSIVE outcome **consumes one trial**. Re-queuing
the same hypothesis with more data is a **new trial**, counted against
the family budget. Family budgets are not reallocated to new targets
without a new audit.

**PASS** — all gates, with confirmatory evidence per §1.

Pre-registered tuning inside nested validation is legitimate. What is
penalised is exceeding the budget, and re-specifying after observing
results.

## 9. Phases

Each phase has a decision gate. The listed decisions must be closed
before the phase starts. Phase 0C does not start until the 0B branch
choice (D1 and D15) is recorded.

| Phase | Content | Decision gate |
| --- | --- | --- |
| **0A** Mandate and governance | economic mandate, risk budget, estimand, trial ledger, contamination map, reveal and peeking policy. R0.1 may run independently of this phase | 12, 13, 14, 17, 24, 26, 27, 28 |
| **0B** Data and universe | snapshots, lock, data-version contract, flags, adjustment, **branch choice A or B recorded as current branch** | 1, 2, 3, 4, 15, 16, 18, 21, 22, 23 |
| **0C** Statistical protocol | power analysis, HAC/bootstrap, trial definition, correction hierarchy, regime definition, threshold freeze, comparators, placebo scheme, H6 merge | 5, 6, 7, 8, 9, 10, 19, 20, 25 |
| **1** Engine and baselines | deterministic core, adapters, conformance suite, **shadow infrastructure**, all baselines of §6.1. Development paper runs may start. Confirmatory cohort does **not** start | — |
| **2** V1 characterisation | R1.1 as internal consistency of artefacts, not reproduction from source; R1.2; R1.3 | — |
| **3** Candidate families | H2, H1 (Branch A only), H3, H4 | — |
| **4** Confirmation | nested walk-forward as robustness; confirmatory test once, no tuning after reveal | — |
| **5** Incremental ML | only if a named baseline or Phase 3 family has passed, against that specific comparator | — |
| **6** Confirmatory shadow cohort | at most one frozen strategy, append-only, peeking sealed | 7 |

R0.1 may be authorised independently of adopting this roadmap. It is
not Phase 0A. It adopts no threshold, universe or engine.

## 10. Hypotheses

Every pre-registration card states: hypothesis; **null**; **estimand**;
primary comparator; data, universe and branch; splits; complete parameter
grid; trial budget; primary metric; cost model; seeds; gates; kill
criterion; **placebo tail direction** (improving side of the primary
metric: upper for paired Sharpe difference, lower for QLIKE).

| Family | Estimand | Primary metric | Status |
| --- | --- | --- | --- |
| **H2** trend, time series | paired net Sharpe difference versus canonical trend baseline and versus the pre-registered comparator | paired difference with interval | first; **H6 merged in**, D9 |
| **H1** cross-sectional momentum | paired net Sharpe difference at matched exposure | paired difference | **Branch A only**; blocked under Branch B; D8 comparator is a dormant specification under B |
| **H3** regime gating | incremental effect over volatility sizing, not over an unconditional baseline | paired difference versus the volatility-scaled version of the same signal | after the sizing baseline exists |
| **H4** short-horizon mean reversion | paired net Sharpe difference after next-open fills and measured costs | paired difference, with break-even cost | last |
| **volatility sizing** | forecast loss versus rolling-variance or EWMA, and realised risk-adjusted return at **equal ex-ante target volatility** | QLIKE; paired difference | Phase 1 overlay, not an alpha family |

Sizing comparison, all fixed in 0C: target volatility, forecast
benchmark, maximum leverage, rebalance frequency, turnover and costs,
forecast loss, one declared comparison rule.

ML: failure of one formulation closes only that formulation. It closes
the directional branch only if family, model space and trial budget were
pre-registered as an exhaustive test. Every ML target draws from one
hierarchical hypothesis budget (D5). Family budgets are not reallocated
to new targets without audit. A panel adds rows, not independent
observations.

## 11. Decisions, with proposed positions

**Twenty-seven** decisions, numbered D1 to D28. The gap at D11 is
deliberate. D26–D28 are implicit decisions that audit 003 found
undeclared. Walk-forward counting and family-budget freeze are folded
into D5. Peeking policy is folded into D17.

### Mandates, owner Filippo

**D12. Estimand and primary economic objective.**
**CLOSED 2026-10-06 by Filippo:** expected annualised net Sharpe versus
the pre-registered primary comparator, after measured costs. Objective:
maximise risk-adjusted net return subject to the risk mandate.

**D13. Long-only, leverage, base currency.**
**CLOSED 2026-10-06 by Filippo:** long-only, no leverage, spot crypto
only, base EUR.

**D14. Risk budget.**
**CLOSED 2026-10-06 by Filippo:** maximum drawdown 25% as a hard gate,
annualised volatility target 15%, maximum single-asset weight 20%,
cluster limits at the risk layer.

**D15. Data provider, version, licence.**
**CLOSED 2026-10-06 with D1:** Yahoo with pinned immutable snapshots.
No paid survivorship-free vendor is committed. A later switch to
Branch A is a new decision and a new audit.

**D17. Development cut-off, reveal authority, peeking.**
**CLOSED 2026-10-06 by Filippo:** confirmatory reveal authorised by
Filippo only, once per candidate, append-only ledger. Claude may not
reveal. Confirmatory shadow peeking sealed until that reveal.
Development data cut-off date remains to be frozen when 0C defines the
windows; the authority is closed, the calendar date is not.

**D1. Branch choice.**
**CLOSED 2026-10-06 by Filippo:** **Branch B**, current universe. H1
off. Pre-registered review date: twelve months from this close, or
sooner if Filippo opens a vendor decision. Switching to A is a new
audit. 0C must not start on an unrecorded branch; the branch is now
recorded.

### Methodology, owner Claude plus audit

**D2. Sleeves and rebalance frequency.**
**CLOSED 2026-10-06 by Filippo:** under Branch B, three sleeves as D22
(US equities / crypto / ETF-commodity). Quarterly **capital** rebalance.
The 18 names stay fixed; there is no universe reconstitution. Seasoning
(252 days) and trailing-60-day liquidity filters remain specified for
Branch A only and are not applied now.

**D3. History span and panel weighting.**
**CLOSED 2026-10-06 by Filippo:** maximum available history per asset;
unbalanced panel; equal weight inside a sleeve; sleeve weights from
D22; every cross-sectional claim also reported on the common-period
subsample.

**D4. Eligibility, including MSTR-like objects.**
**CLOSED 2026-10-06 by Filippo:** not applied under Branch B. The 18
tickers are a fixed basket and are not silently dropped. The Branch A
filter list below stays on file for a future branch switch (new audit).
*Proposal (Branch A only):* these filters apply to **Branch A only**. Under Branch B
the 18 tickers are a fixed basket; D4 is not applied and does not
silently drop names. No ex-post special case and no break detection.
At every Branch A rebalance date, every asset must satisfy **all** of:

1. Seasoning: 252 completed trading days on the eligible venue.
2. Liquidity: trailing 60-day median traded value above the 0C
   threshold.
3. Venue: listed on a pre-registered venue list.
4. Price: last eligible close above a pre-registered minimum (proposed
   1 unit of base currency).
5. Economic object: an equity is ineligible if, as known at `t-1`, a
   single non-operating asset (crypto, commodity, or another listed
   equity) has exceeded 50% of reported NAV for 6 consecutive months.
   This is a general rule, not an MSTR clause. UNKNOWN whether it would
   exclude MSTR; that is an empirical output of applying the rule, not
   a reason to write the rule.

Delistings remain in the panel with their delisting return. Failed
eligibility drops the asset from the *new* cohort only.
*Not in force under Branch B.*
*Alternatives (Branch A):* a pre-registered break-detection rule; manual
MSTR exclusion, which is snooping and is not recommended.

**D5. Trial definition and budget.**
*Proposal:* one trial is one evaluation of a (hypothesis, parameter
vector, universe, period) tuple that produces **one** performance
metric used for a decision.

Walk-forward: if the reported metric is a single aggregated evaluation
of that tuple, the walk-forward counts as **one** trial. If a fold is
selected on, or a fold-level metric is used to choose, each selected
fold is a trial.

The full sensitivity grid is written to the ledger even when "never
selected on". Omitting it understates DSR.

Budget is hierarchical: a total across V2, divided across families,
divided within a family between one primary configuration and the
declared grid. Family budgets are **frozen** in 0C. They are not
reallocated to new targets or new families without a new audit.

Every trial is written automatically by the runner.
*Close by:* 0C. *If unresolved:* DSR is uncomputable.

**D6. Threshold derivation.**
*Proposal:* statistical thresholds from the 0C power analysis; economic
thresholds from the 0A mandate. Both frozen before any candidate
result. *Close by:* 0C.

**D7. Confirmatory shadow minimum.**
*Proposal:* no promotion to `deployable` before all three of twelve
months elapsed, a pre-registered minimum number of closed trades, and
coverage of at least two distinct volatility regimes; the trade count
comes from the 0C power analysis. Applies to the confirmatory cohort,
not to development paper runs. *Close by:* 0C for the numbers, 6 for
application.

**D8. Primary comparator per hypothesis.**
*Proposal:* one comparator per hypothesis, frozen in **0C** before any
candidate result. H2 against the canonical trend baseline; H1 against
equal-weight rebalanced at matched exposure (dormant specification
under Branch B); H3 against the volatility-scaled version of the same
signal; H4 against equal-weight buy-and-hold; volatility sizing against
the same signal with static sizing. *Close by:* 0C.
*If unresolved:* no paired test can be specified.

**D9. H6 breakout.**
*Proposal:* merge H6 into H2 as a parameterisation inside the same
family budget. *Close by:* 0C.

**D10. Permutation scheme for the placebo.**
*Proposal:* stationary block bootstrap on the signal series with
expected block length matched to the measured signal autocorrelation,
preserving cross-sectional date alignment, matching realised trade
frequency, replication count set in 0C. The **test** is the improving tail in §7.2, not a two-sided
"outside quantile". *Close by:* 0C.

**D16. Adjustment convention.**
**CLOSED 2026-10-06 by Filippo:** split- and dividend-adjusted total
return (`AdjClose`) for signals and for performance; unadjusted Close
and Open for execution; `auto_adjust` never left implicit.

**D18. Fill, slippage, capacity, market impact.**
**CLOSED 2026-10-06 by Filippo (model only):** next-open fills; per-side
cost = commission + spread + linear impact × participation; three
named scenarios (cheap / base / expensive). Scenario **numbers** and
break-even cost freeze in 0C. Until then the evidence path raises.

**D19. Correction hierarchy.**
*Proposal:* family-wise error rate within each family using a step-down
procedure; across-family selection through the effective trial count in
DSR; report both uncorrected and corrected results. D24 counted
conservatively. *Close by:* 0C.

**D20. HAC and bootstrap specification.**
*Proposal:* Newey-West with an automatic bandwidth rule for point
inference; stationary bootstrap for intervals with mean block length
from measured autocorrelation; both reported for every primary metric.
*Close by:* 0C.

**D21. Instrument and benchmark overlap.**
**CLOSED 2026-10-06 by Filippo:** no investable ticker may also be the
official benchmark. QQQ remains in the Branch B 18 as an instrument and
is therefore forbidden as benchmark. MSTR remains; crypto-cluster
concentration (BTC, ETH, MSTR, COIN) is reported, not used to drop
names. The Branch A alternative (drop QQQ from the investable set and
keep it only as benchmark) is not in force.

**D22. Calendar synchronisation and capital allocation.**
**CLOSED 2026-10-06 by Filippo:** native calendars; portfolio metrics on
the intersection of trading days; crypto unchanged on equity-closed
days, no synthetic returns. Capital split **70% US equities / 20%
crypto / 10% ETF and commodity**, rebalanced quarterly.

**D23. Dependency lock.**
*Proposal:* exact pins plus a lock file committed to the repository;
the workflow installs from the lock; interpreter and library versions
recorded in every result. *Close by:* 0B.

**D24. Permitted use of legacy results.**
**CLOSED 2026-10-06 by Filippo:** legacy artefacts may generate
hypotheses and help design the protocol, never as evidence. Counted
conservatively in DSR. Individual admission via R0.1.

**D25. Sufficient breadth for H1.**
*Proposal:* H1 requires a pre-registered minimum number of eligible
assets at each rebalance date, sustained across a pre-registered
majority of the test period, numbers set in 0C. Below that, H1 is not
run. Under Branch B it is not run, without caveat. *Close by:* 0C.

**D26. Timeframe.**
**CLOSED 2026-10-06 by Filippo:** daily bars. Intraday out of scope.

**D27. Signal horizon.**
**CLOSED 2026-10-06 by Filippo:** V2 horizon independent of V1's 1-day
ML target. First families: next-open to next-open, at least one
session; exact horizon on each pre-registration card.

**D28. Instruments in scope.**
**CLOSED 2026-10-06 by Filippo:** cash equities, QQQ and GLD in the
Branch B basket, spot crypto. No futures, options, leveraged or inverse
ETFs, or OTC.

### Reclassified

v2's eleventh item, whether any decidable pairwise comparison already
exists in the legacy results, is not a decision. It is an empirical
question for R0.1.

## 12. Legacy results

### 12.1 Admission rule

**Individual adjudication.** R0.1 admits or excludes each artefact on
its own evidence. No 50% rule.

### 12.2 Provenance ledger scope

Per file, not aggregated: exact first and last date, observation count,
commit, feature set, parameter values, cost assumptions, producing
script, adjustment setting, snapshot reference where one exists.
First cut: `docs/R01_PROVENANCE.md` (2026-10-06).
VERIFIED inventory: 20 in `backtest_results`, 21 in
`portfolio_backtest_results`, 10 dynamic-universe artefacts in the
root, 1 production `trading_log.csv`.

R0.1 also records the attribution of the two TopK-18 rows in §12.3. It
does not choose a "true" static benchmark; it attributes each row to
the function that produced it.

### 12.3 Invalidated and restricted artefacts

| Artefact | Status |
| --- | --- |
| Dynamic-universe comparison and its +87.15% figure | **INVALID, not comparable.** Not a buy & hold. Two defects push in opposite directions, so the sign of the net error is UNKNOWN. (a) Daily cross-sectional mean of asset returns is a daily-rebalanced equal-weight stream, not buy & hold. (b) Score uses day `d` close and volume, selects on `d`, credits `d`→`d+1` close-to-close, which favours the selecting legs. Not usable as a baseline until a corrected rerun, whose protocol needs its own audit |
| Two TopK-18 rows in `dynamic_universe_fair_summary.csv` | **EXPLAINED, 2026-10-06, audit 003, independently confirmed in `dynamic_universe_fair_comparison.py`.** Row 487 obs, +87.15%, turnover 0.205%: `simulate(panel, k=18)`, which keeps days where all 18 have Score and NextRet; selecting top-18 of 18 is equal-weight on the complete-panel calendar; costs are turnover × 0.0015. Row 711 obs, −16.26%, DD −57.13%, turnover 0: `static_18(with_costs=True)`, which averages NextRet on every date with at least one asset, including crypto weekends. The comment says one initial allocation cost; the code does `g["Return"] -= COST_PER_SIDE` on **all 711 rows**. VERIFIED: `(1-0.0015)**711 ≈ 0.344`; 24321.13 × 0.344 ≈ 8373, matching 8373.71. The negative sign is almost entirely this cost bug. Without costs the two statics still differ (+87.43% vs +143.21%); INFERRED residual is weekend-crypto / incomplete-day mix. The figure cited in documents is the 487-day row. R0.1 attributes rows to functions; it does not elect a true benchmark. Both remain invalid as buy & hold |
| V1 run #10 | internally consistent with its summary. **Not reproducible from raw market data.** R1.1 is internal consistency, not reproduction from source |
| ML ON / OFF, horizon AUC | **UNKNOWN provenance.** Not citable until R0.1 |
| Contamination extent | **UNKNOWN** until R0.1 |

INFERRED further, from audit 003, not yet independently verified here:
`features.py` builds the target then `dropna()` on the whole row, so
the last bar loses the target and volume-NaN bars are dropped unlike
live. Treat as a V1 non-comparability axis for R0.1.

## Appendix A. Withdrawn claims

| Version | Withdrawn claim | Correction |
| --- | --- | --- |
| v1 | `SE(SR) ~= sqrt((1 + SR^2/2)/T)`, SE 0.91 | frequency term omitted; §2.1 |
| v1 | every result on the window is undecidable | paired differences can have smaller variance; §1, §2.1 |
| v1 | forward time is the only clean holdout | cleanest but not the only confirmatory source; §1 |
| v1 | the 52 CSVs all cover the same 2024-2026 window | false; §12.2 |
| v1 | ideally 2010-2024 as a uniform panel | unbalanced panel; D3 |
| v1 | OOS >= 0.5 x IS | deleted; §7.2 |
| v1 and v2 | +87.15% described as static Buy & Hold | invalid; §12.3 |
| v2 | individual Sharpes not distinguishable from zero, marked VERIFIED | demonstrated for one case; INFERRED; §2.1 |
| v2 | all eight audit-001 blockers resolved | architectural blocker persisted |
| v2 | point-in-time methodology is implementable | incomplete without a provider |
| v2 | plugins implemented only after validation, with early shadow | lifecycle of *code* corrected in v3; occupancy of shadow corrected in v4, §5.4 |
| v2 | H6 tested alongside H2 and still undecided | merged, D9 |
| v2 | economic thresholds derived from power analysis | mandate vs MDE; §2.5 |
| v2 | max drawdown 25% as an indicative diagnostic | hard gate; D14 |
| v2 | DSR as `P(DSR/PSR > 0) > 0.95` | three distinct criteria; §2.2 |
| v2 | more than half not reproducible implies all void | individual adjudication; §12.1 |
| v2 | one `q = 252` applied generally | per-sleeve; §2.3 |
| v2 | eleven open decisions, left as questions | proposed positions; §11 |
| v3 | experimental plugins "run in shadow" counted as confirmatory | infrastructure ≠ cohort; §5.4 |
| v3 | placebo as "outside the quantile" | upper tail; §7.2 |
| v3 | start 0C on B while D15 remains open | D1/D15 close in 0B; 0C waits |
| v3 | D4 without an eligibility list | list in D4 |
| v3 | D22 without a numeric split | 70/20/10 proposed in D22 |
| v3 | two TopK-18 rows UNRESOLVED | explained; §12.3 |
| v3 | any flag other than stale_value blocks the signal | blocking vs annotative; §3.3 |
