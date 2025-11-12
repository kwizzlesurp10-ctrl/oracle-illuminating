"""
Reference oracle implementations for the service entrypoint.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Dict, Iterable, List

from oracle_illuminating.core.oracle_framework import InsightOracle


def _extract_numeric_series(raw: Iterable) -> List[float]:
    series: List[float] = []
    for item in raw or []:
        if isinstance(item, (int, float)):
            series.append(float(item))
        elif isinstance(item, dict) and "value" in item:
            value = item["value"]
            if isinstance(value, (int, float)):
                series.append(float(value))
    return series


def _trend_direction(series: List[float]) -> str:
    if len(series) < 2:
        return "insufficient-data"
    delta = series[-1] - series[0]
    threshold = max(abs(series[0]) * 0.05, 1e-3)
    if delta > threshold:
        return "upward"
    if delta < -threshold:
        return "downward"
    return "stable"


def _detect_anomalies(series: List[float], sigma: float = 2.0) -> List[int]:
    if len(series) < 3:
        return []
    avg = mean(series)
    deviation = pstdev(series)
    if deviation == 0:
        return []
    return [idx for idx, value in enumerate(series) if abs(value - avg) > sigma * deviation]


class DatasetOracle:
    name = "dataset"

    def analyze(self, payload: Dict) -> Dict:
        summary = payload.get("summary", "dataset perspective")
        metrics = payload.get("metrics", {})
        series = _extract_numeric_series(payload.get("timeseries", []))

        coverage = len(metrics)
        samples = len(series)
        anomalies = _detect_anomalies(series)
        trend = _trend_direction(series)
        avg = mean(series) if series else None

        acuity = 0.3
        if coverage:
            acuity += min(0.2, coverage * 0.05)
        if samples >= 5:
            acuity += min(0.2, samples * 0.02)
        if not anomalies:
            acuity += 0.05

        return {
            "summary": summary,
            "trend": trend,
            "statistics": {"samples": samples, "mean": avg, "anomalies": anomalies},
            "metrics": metrics,
            "acuity": round(min(acuity, 0.8), 3),
        }


class InterpretOracle:
    name = "interpret"

    def analyze(self, payload: Dict) -> Dict:
        hypothesis = payload.get("hypothesis") or "emergent interpretation"
        signals = payload.get("signals", [])

        weighted = [
            (
                item.get("label", f"signal-{idx}"),
                float(item.get("strength", 0.0)),
                item.get("evidence"),
            )
            for idx, item in enumerate(signals)
            if isinstance(item, dict)
        ]
        weighted.sort(key=lambda item: item[1], reverse=True)

        top_signal = weighted[0] if weighted else None
        confidence = top_signal[1] if top_signal else 0.25
        narrative = (
            f"Dominant signal `{top_signal[0]}` supports the hypothesis."
            if top_signal
            else "No dominant signals detected; hypothesis remains exploratory."
        )

        acuity = 0.35 + min(0.3, confidence * 0.4)
        alignment_gap = 1.0 - confidence

        return {
            "summary": hypothesis,
            "insight": narrative,
            "supporting_signals": [
                {"label": label, "strength": strength, "evidence": evidence}
                for label, strength, evidence in weighted[:3]
            ],
            "alignment_gap": round(alignment_gap, 3),
            "acuity": round(min(acuity, 0.85), 3),
        }


class AdaptOracle:
    name = "adapt"

    def analyze(self, payload: Dict) -> Dict:
        recommendation = payload.get("recommendation") or "iterate protocols"
        constraints = payload.get("constraints", [])
        risk_level = payload.get("risk_level", "moderate")
        guardrail_status = payload.get("guardrail_status", "unknown")

        strategy = self._derive_strategy(recommendation, risk_level, guardrail_status)
        priority = self._priority_score(risk_level, guardrail_status)

        acuity = 0.4 + min(0.15, priority * 0.1)

        return {
            "summary": recommendation,
            "action": strategy,
            "constraints": constraints,
            "priority": priority,
            "acuity": round(min(acuity, 0.9), 3),
        }

    @staticmethod
    def _priority_score(risk_level: str, guardrail_status: str) -> float:
        risk_map = {"critical": 1.0, "high": 0.8, "moderate": 0.6, "low": 0.3}
        guardrail_map = {"pass": 0.3, "review": 0.6, "fail": 0.9, "unknown": 0.5}
        return round((risk_map.get(risk_level, 0.5) + guardrail_map.get(guardrail_status, 0.5)) / 2, 2)

    @staticmethod
    def _derive_strategy(recommendation: str, risk_level: str, guardrail_status: str) -> str:
        posture = "stabilize" if risk_level in {"critical", "high"} else "optimize"
        guardrail_note = (
            "after guardrail remediation" if guardrail_status in {"review", "fail"} else "with guardrails intact"
        )
        return f"{posture} pathways to {recommendation} while operating {guardrail_note}."


class VulnerabilityOracle:
    name = "vulnerability"

    def analyze(self, payload: Dict) -> Dict:
        exposures = payload.get("exposures", [])
        coverage = payload.get("guardrail_coverage", 0.5)

        exposure_count = len(exposures)
        top_exposure = exposures[0] if exposures else None

        acuity = 0.45 + min(0.25, exposure_count * 0.05) + (0.1 if coverage >= 0.7 else 0.0)

        recommendations = []
        if top_exposure:
            recommendations.append(f"Prioritize mitigation for {top_exposure.get('vector', 'primary vector')}.")
        if coverage < 0.6:
            recommendations.append("Increase guardrail coverage to at least 60%.")
        if not recommendations:
            recommendations.append("Maintain current guardrail posture and monitor drift.")

        return {
            "summary": "emergent vulnerability landscape",
            "exposures": exposures,
            "coverage": coverage,
            "recommendations": recommendations,
            "acuity": round(min(acuity, 0.95), 3),
        }


def default_oracles() -> list[InsightOracle]:
    return [DatasetOracle(), InterpretOracle(), AdaptOracle(), VulnerabilityOracle()]

