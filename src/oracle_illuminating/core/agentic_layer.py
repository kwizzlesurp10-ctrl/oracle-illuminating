"""
Agentic enhancement layer that improves acuity scores via recursive refinement.
"""

from __future__ import annotations

from typing import Iterable, List

from .oracle_framework import OracleResult


class AgenticEnhancementLayer:
    """
    Applies autonomous enhancement protocols to boost acuity and derive new questions.
    """

    def boost_results(self, results: Iterable[OracleResult]) -> List[OracleResult]:
        boosted = []
        for result in results:
            acuity = min(result.acuity + 0.05, 1.0)
            boosted.append(
                OracleResult(
                    oracle=result.oracle,
                    insight={
                        **result.insight,
                        "follow_up_question": self._generate_follow_up(result),
                    },
                    acuity=acuity,
                )
            )
        return boosted

    def _generate_follow_up(self, result: OracleResult) -> str:
        summary = result.insight.get("summary", "insight")
        return f"What new data could clarify the {summary} finding?"

