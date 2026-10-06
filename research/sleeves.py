"""D2 / D21 / D22 sleeve map for Branch B. Research-only."""

from __future__ import annotations

from research.yahoo_snapshot import TICKERS

US_EQUITY = frozenset(
    {
        "NVDA",
        "AMD",
        "MSTR",
        "COIN",
        "TSM",
        "PLTR",
        "ARM",
        "SMCI",
        "TSLA",
        "META",
        "AMZN",
        "GOOGL",
        "AAPL",
        "MSFT",
    }
)
ETF_COMMODITY = frozenset({"QQQ", "GLD"})
CRYPTO = frozenset({"BTC-USD", "ETH-USD"})

SLEEVE_WEIGHT = {
    "us_equity": 0.70,
    "crypto": 0.20,
    "etf_commodity": 0.10,
}

# Names in the basket that are also Nasdaq-100 constituents.
QQQ_COMPONENTS_IN_BASKET = frozenset(
    {
        "NVDA",
        "AMD",
        "PLTR",
        "ARM",
        "SMCI",
        "TSLA",
        "META",
        "AMZN",
        "GOOGL",
        "AAPL",
        "MSFT",
    }
)


class BenchmarkOverlapError(ValueError):
    pass


def sleeve(ticker: str) -> str:
    if ticker in CRYPTO:
        return "crypto"
    if ticker in ETF_COMMODITY:
        return "etf_commodity"
    if ticker in US_EQUITY:
        return "us_equity"
    raise KeyError(f"ticker not in Branch B map: {ticker}")


def assert_benchmark_legal(benchmark: str, investable=TICKERS) -> None:
    """An investable ticker cannot also be the official benchmark (D21)."""
    if benchmark in set(investable):
        raise BenchmarkOverlapError(
            f"{benchmark} is investable under Branch B and cannot be the benchmark"
        )
