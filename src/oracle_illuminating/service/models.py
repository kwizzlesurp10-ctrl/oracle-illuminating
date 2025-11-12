"""
Pydantic models for service interactions.
"""

from __future__ import annotations

from typing import Any, Dict, List

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


class StreamingJobRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic (or simulated channel) to ingest from.")
    sink: str = Field(
        default="duckdb",
        description="Analytical sink to persist events into (duckdb or clickhouse).",
    )


class StreamingJobStatus(BaseModel):
    topic: str
    running: bool
    last_event_at: str | None = None
    records_processed: int = 0


class InferenceInvokeRequest(BaseModel):
    provider: str = Field(..., description="Inference provider identifier (huggingface or replicate).")
    model: str = Field(..., description="Model identifier or version.")
    payload: Dict[str, BaseModel | Dict | List | str | int | float | bool | None] = Field(
        default_factory=dict,
        description="Request payload forwarded to the inference provider.",
    )
    stream: bool = Field(False, description="Enable streaming responses when supported.")


class InferenceInvokeResponse(BaseModel):
    provider: str
    model: str
    output: Dict[str, Any]


class SubscriptionPlan(BaseModel):
    id: str
    name: str
    description: str
    price_usd: float
    features: List[str]


class CreateCheckoutSessionRequest(BaseModel):
    provider: str = Field(..., description="Billing provider identifier (stripe or braintree).")
    plan_id: str = Field(..., description="Plan reference for the provider.")
    success_url: str = Field(..., description="URL to redirect to on successful checkout.")
    cancel_url: str = Field(..., description="URL to redirect to if the user cancels checkout.")
    customer_email: str | None = Field(default=None, description="Optional customer email.")


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookVerificationResponse(BaseModel):
    valid: bool
    payload: Dict[str, Any]


class FeatureFlagContext(BaseModel):
    key: str
    value: Any


class FeatureFlagEvaluationResponse(BaseModel):
    key: str
    enabled: bool
    variant: str | None = None
    context: Dict[str, Any] | None = None


class FeatureFlagEvaluationRequest(BaseModel):
    context: List[FeatureFlagContext] = Field(default_factory=list)


class TelemetryEventModel(BaseModel):
    event: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    distinct_id: str | None = None
