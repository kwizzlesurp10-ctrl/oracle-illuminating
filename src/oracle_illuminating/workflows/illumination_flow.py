"""
Prefect workflow orchestrating the illumination lifecycle.
"""

from __future__ import annotations

from typing import Dict, List

from prefect import flow, task

from oracle_illuminating.analytics.repository import get_insight_recorder
from oracle_illuminating.core import AgenticEnhancementLayer, GuardrailSystem, OracleOrchestrator
from oracle_illuminating.core.guardrails import GuardrailFinding
from oracle_illuminating.core.oracle_framework import OracleResult
from oracle_illuminating.service.oracles import default_oracles


@task(name="run-oracles")
def run_oracles(payload: Dict) -> List[OracleResult]:
    orchestrator = OracleOrchestrator(default_oracles())
    return orchestrator.evaluate(payload)


@task(name="agentic-boost")
def apply_agentic_boost(results: List[OracleResult]) -> List[OracleResult]:
    layer = AgenticEnhancementLayer()
    return layer.boost_results(results)


@task(name="guardrail-audit")
def apply_guardrails(results: List[OracleResult]) -> List[GuardrailFinding]:
    guardrails = GuardrailSystem()
    return guardrails.audit(results)


@task(name="recursive-question")
def derive_recursive_question(
    results: List[OracleResult], guardrails: List[GuardrailFinding]
) -> Dict:
    if results:
        highest = max(results, key=lambda result: result.acuity)
        summary = highest.insight.get("summary", "core insight")
        question = f"What evidence would increase confidence in the {summary} perspective?"
    else:
        question = "What new data source should be illuminated next?"

    guardrail_status = "pass" if all(finding.status == "pass" for finding in guardrails) else "review"
    return {"status": guardrail_status, "question": question}


@flow(name="oracle-illuminating-cycle")
def illumination_cycle(payload: Dict) -> Dict:
    base_results_future = run_oracles.submit(payload)
    boosted_results_future = apply_agentic_boost.submit(base_results_future)
    guardrail_findings_future = apply_guardrails.submit(boosted_results_future)

    boosted_results = boosted_results_future.result()
    guardrail_findings = guardrail_findings_future.result()
    recursion_insight = derive_recursive_question.submit(boosted_results, guardrail_findings).result()

    result_payload = {
        "insights": [
            {
                "oracle": result.oracle,
                "acuity": result.acuity,
                "insight": result.insight,
            }
            for result in boosted_results
        ],
        "guardrails": [
            {"layer": finding.layer, "status": finding.status, "details": finding.details}
            for finding in guardrail_findings
        ],
        "recursive": recursion_insight,
    }

    recorder = get_insight_recorder()
    recorder.record(
        source="workflow",
        payload=payload,
        insights=result_payload["insights"],
        guardrails=result_payload["guardrails"],
        recursive=result_payload["recursive"],
    )

    return result_payload

