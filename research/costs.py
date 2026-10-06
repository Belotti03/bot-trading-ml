"""D18 fill and cost model. Research-only.

The formula is frozen in 0B. Cheap / base / expensive numbers freeze in
0C. Until then, any path marked as evidence must fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass


class CostScenariosUnset(RuntimeError):
    pass


@dataclass(frozen=True)
class CostModel:
    name: str
    commission_per_side: float | None
    spread_per_side: float | None
    impact_coef: float | None


SCENARIOS = {
    "cheap": CostModel("cheap", None, None, None),
    "base": CostModel("base", None, None, None),
    "expensive": CostModel("expensive", None, None, None),
}

# Flip only when 0C writes the three numbers and an audit accepts them.
FROZEN_FOR_EVIDENCE = False


def per_side_cost(
    model: CostModel,
    participation: float,
    *,
    for_evidence: bool = True,
) -> float:
    if for_evidence and not FROZEN_FOR_EVIDENCE:
        raise CostScenariosUnset("D18 scenario numbers are not frozen until 0C")
    if (
        model.commission_per_side is None
        or model.spread_per_side is None
        or model.impact_coef is None
    ):
        raise CostScenariosUnset(f"{model.name} numbers unset")
    if participation < 0:
        raise ValueError("participation must be >= 0")
    return (
        model.commission_per_side
        + model.spread_per_side
        + model.impact_coef * participation
    )


def net_of_round_trip(
    gross_return: float,
    model: CostModel,
    participation: float,
    *,
    for_evidence: bool = True,
) -> float:
    cost = per_side_cost(model, participation, for_evidence=for_evidence)
    return gross_return - 2.0 * cost
