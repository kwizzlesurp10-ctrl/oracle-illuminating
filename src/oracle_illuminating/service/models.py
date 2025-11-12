"""
Pydantic models for service interactions.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class IlluminationInput(BaseModel):
    payload: Dict = Field(default_factory=dict, description="Input data for illumination.")


class OracleInsight(BaseModel):
    oracle: str
    acuity: float
    insight: Dict


class GuardrailFindingModel(BaseModel):
    layer: str
    status: str
    details: str


class IlluminationResponse(BaseModel):
    insights: List[OracleInsight]
    guardrails: List[GuardrailFindingModel]


class OracleAcuitySummary(BaseModel):
    oracle: str
    count: int
    avg_acuity: float


class GuardrailStatusSummary(BaseModel):
    status: str
    count: int


class RecentRunSummary(BaseModel):
    id: int
    created_at: str
    source: str
    guardrail_status: str
    recursive_question: str | None = None
    insights: List[Dict] = Field(default_factory=list)
    guardrails: List[Dict] = Field(default_factory=list)


class AnalyticsSummaryResponse(BaseModel):
    oracles: List[OracleAcuitySummary]
    guardrails: List[GuardrailStatusSummary]
    recent_runs: List[RecentRunSummary]

