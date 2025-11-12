"""
Oracle framework assembling illumination oracles and producing insight summaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol


class InsightOracle(Protocol):
    """Protocol for oracles that produce insights from an input payload."""

    name: str

    def analyze(self, payload: Dict) -> Dict:
        """Process an input payload and return structured insight."""


@dataclass
class OracleResult:
    oracle: str
    insight: Dict
    acuity: float


class OracleOrchestrator:
    """
    Dispatches payloads through registered oracles and aggregates their results.
    """

    def __init__(self, oracles: List[InsightOracle]) -> None:
        if not oracles:
            raise ValueError("At least one oracle must be registered.")
        self._oracles = oracles

    def evaluate(self, payload: Dict) -> List[OracleResult]:
        results: List[OracleResult] = []
        for oracle in self._oracles:
            insight = oracle.analyze(payload)
            results.append(
                OracleResult(
                    oracle=oracle.name,
                    insight=insight,
                    acuity=float(insight.get("acuity", 0.0)),
                )
            )
        return results

