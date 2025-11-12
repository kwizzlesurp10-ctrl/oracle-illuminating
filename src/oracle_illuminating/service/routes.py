"""
API routes exposing illumination workflows.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from oracle_illuminating.analytics.repository import InsightRecorder, get_insight_recorder
from oracle_illuminating.core.agentic_layer import AgenticEnhancementLayer
from oracle_illuminating.core.guardrails import GuardrailSystem
from oracle_illuminating.core.oracle_framework import OracleOrchestrator
from oracle_illuminating.service.models import (
    GuardrailFindingModel,
    IlluminationInput,
    IlluminationResponse,
    OracleInsight,
)
from oracle_illuminating.service.oracles import default_oracles

router = APIRouter()


def get_orchestrator() -> OracleOrchestrator:
    return OracleOrchestrator(default_oracles())


def get_agentic_layer() -> AgenticEnhancementLayer:
    return AgenticEnhancementLayer()


def get_guardrail_system() -> GuardrailSystem:
    return GuardrailSystem()


def get_recorder() -> InsightRecorder:
    return get_insight_recorder()


@router.post("/illuminate", response_model=IlluminationResponse)
async def illuminate(
    data: IlluminationInput,
    orchestrator: OracleOrchestrator = Depends(get_orchestrator),
    enhancement: AgenticEnhancementLayer = Depends(get_agentic_layer),
    guardrails: GuardrailSystem = Depends(get_guardrail_system),
    recorder: InsightRecorder = Depends(get_recorder),
) -> IlluminationResponse:
    base_results = orchestrator.evaluate(data.payload)
    boosted = enhancement.boost_results(base_results)
    guardrail_findings = guardrails.audit(boosted)

    insights_payload = [
        {"oracle": result.oracle, "acuity": result.acuity, "insight": result.insight}
        for result in boosted
    ]
    guardrail_payload = [
        {"layer": finding.layer, "status": finding.status, "details": finding.details}
        for finding in guardrail_findings
    ]
    recursive_payload = {
        "status": "pass" if all(item["status"] == "pass" for item in guardrail_payload) else "review",
        "question": next(
            (
                insight["insight"].get("follow_up_question")
                for insight in insights_payload
                if isinstance(insight.get("insight"), dict)
                and insight["insight"].get("follow_up_question")
            ),
            None,
        ),
    }

    recorder.record(
        source="api",
        payload=data.payload,
        insights=insights_payload,
        guardrails=guardrail_payload,
        recursive=recursive_payload,
    )

    return IlluminationResponse(
        insights=[OracleInsight(**insight) for insight in insights_payload],
        guardrails=[GuardrailFindingModel(**finding) for finding in guardrail_payload],
    )

