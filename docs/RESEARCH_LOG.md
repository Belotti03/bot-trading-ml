# RESEARCH LOG / DECISION LEDGER

## Status --- 2026-09-30

V1 is frozen for research. V1 cron should remain paused while NaN
corruption is unresolved. V2 is not implemented.

## Decisions

1.  V1 is a benchmark, not a template to blindly patch.
2.  V2 is a clean reconstruction informed by V1 lessons.
3.  V2 objective: search for genuine robust quantitative/predictive
    edge.
4.  Trend/momentum are candidate hypotheses and baselines.
5.  ML must demonstrate incremental value.
6.  Dynamic universe is optional, not a mandatory replacement.
7.  Highest backtest return is not the selection criterion.
8.  Use OOS/holdout discipline and realistic costs.
9.  ChatGPT and Claude/Cursor review each other's work independently.

## Completed research

-   Asset universe diagnostics completed; no final deletion list frozen.
-   Target-horizon screening completed; 1d was least weak but no
    meaningful skill demonstrated.
-   Dynamic-universe fair comparison completed; static 18 remains the
    reference, dynamic selection is optional.
-   V1 portfolio run #10: €10,000 -\> €7,980.02, -20.20%, DD -45.57%,
    Sharpe -0.2496, PF .8787.

## Open questions

1.  Exact NaN causal chain.
2.  Exact provenance of each historical result.
3.  Which signal families have genuine OOS edge.
4.  Whether ML adds value after a strong quantitative baseline.
5.  Best portfolio/risk construction after realistic costs.
6.  How to build a locked holdout and forward/shadow test without
    contamination.

## Do not do

-   Do not keep tuning V1 parameters on the same period.
-   Do not select a strategy because it has the highest backtest return.
-   Do not infer causal stop performance from exit-reason P&L alone.
-   Do not erase evidence of the NaN incident.
