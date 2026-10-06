import pandas as pd

from research.costs import (
    CostModel,
    CostScenariosUnset,
    SCENARIOS,
    net_of_round_trip,
    per_side_cost,
)
from research.prices import attach_price_fields
from research.sleeves import BenchmarkOverlapError, assert_benchmark_legal, sleeve


def test_adj_return_ignores_split_in_raw_close():
    raw = pd.DataFrame(
        {
            "Open": [100.0, 51.0],
            "Close": [100.0, 50.0],
            "AdjClose": [50.0, 50.0],
        }
    )
    frame = attach_price_fields(raw)
    assert abs(frame.loc[1, "signal_return"]) < 1e-12
    assert frame.loc[0, "fill_next_open"] == 51.0
    assert frame.loc[1, "execution_close"] == 50.0


def test_evidence_costs_are_blocked_until_0c():
    try:
        per_side_cost(SCENARIOS["base"], 0.01)
    except CostScenariosUnset:
        return
    raise AssertionError("expected CostScenariosUnset")


def test_impact_scales_when_numbers_are_explicit():
    model = CostModel("unit", 0.0005, 0.0005, 0.10)
    assert abs(per_side_cost(model, 0.0, for_evidence=False) - 0.001) < 1e-12
    assert abs(per_side_cost(model, 0.10, for_evidence=False) - 0.011) < 1e-12
    assert abs(net_of_round_trip(0.02, model, 0.0, for_evidence=False) - 0.018) < 1e-12


def test_qqq_cannot_be_benchmark():
    assert sleeve("AAPL") == "us_equity"
    assert sleeve("QQQ") == "etf_commodity"
    assert sleeve("BTC-USD") == "crypto"
    try:
        assert_benchmark_legal("QQQ")
    except BenchmarkOverlapError:
        return
    raise AssertionError("expected BenchmarkOverlapError")
