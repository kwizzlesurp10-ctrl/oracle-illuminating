"""
Routes for analytics and visualization endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from oracle_illuminating.analytics.repository import InsightRecorder, get_insight_recorder
from oracle_illuminating.service.models import AnalyticsSummaryResponse, GuardrailStatusSummary, OracleAcuitySummary, RecentRunSummary

router = APIRouter()


def get_recorder() -> InsightRecorder:
    return get_insight_recorder()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(recorder: InsightRecorder = Depends(get_recorder)) -> AnalyticsSummaryResponse:
    oracles = [
        OracleAcuitySummary(**item) for item in recorder.oracle_acuity_summary()
    ]
    guardrails = [
        GuardrailStatusSummary(status=status, count=count)
        for status, count in recorder.guardrail_status_distribution().items()
    ]
    recent = [
        RecentRunSummary(**run)
        for run in recorder.recent_runs()
    ]
    return AnalyticsSummaryResponse(oracles=oracles, guardrails=guardrails, recent_runs=recent)

