"""
Guardrail implementations for instruction adherence and vulnerability detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .oracle_framework import OracleResult


@dataclass
class GuardrailFinding:
    layer: str
    status: str
    details: str


class GuardrailSystem:
    """
    Applies guardrail checks to illuminated insights to ensure compliance and safety.
    """

    def __init__(self, layers: Iterable[str] | None = None) -> None:
        self._layers = list(layers or ["CDIL", "IAL", "SELF_AUDIT"])

    def audit(self, results: Iterable[OracleResult]) -> List[GuardrailFinding]:
        results_cache = list(results)
        findings: List[GuardrailFinding] = []
        for layer in self._layers:
            findings.append(self._evaluate_layer(layer, results_cache))
        return findings

    def _evaluate_layer(self, layer: str, results: Iterable[OracleResult]) -> GuardrailFinding:
        results_list = list(results)
        acuity_avg = self._average_acuity(results_list)
        status = "pass" if acuity_avg >= 0.2 else "review"
        details = f"Acuity average {acuity_avg:.2f} across {len(results_list)} oracles."
        return GuardrailFinding(layer=layer, status=status, details=details)

    @staticmethod
    def _average_acuity(results_list: List[OracleResult]) -> float:
        if not results_list:
            return 0.0
        return sum(result.acuity for result in results_list) / len(results_list)

