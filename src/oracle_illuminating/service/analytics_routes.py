"""
Routes for analytics and visualization endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from oracle_illuminating.analytics.repository import InsightRecorder, get_insight_recorder
from oracle_illuminating.integrations import (
    FeatureFlagClient,
    InferenceGateway,
    InferenceRequest,
    TelemetryEvent,
    TelemetryClient,
    get_feature_flag_client,
    get_inference_gateway,
    get_telemetry_client,
)
from oracle_illuminating.service.models import (
    AnalyticsSummaryResponse,
    FeatureFlagEvaluationRequest,
    FeatureFlagEvaluationResponse,
    GuardrailStatusSummary,
    InferenceInvokeRequest,
    InferenceInvokeResponse,
    OracleAcuitySummary,
    RecentRunSummary,
    TelemetryEventModel,
)

router = APIRouter()


def get_recorder() -> InsightRecorder:
    return get_insight_recorder()


def get_inference_gateway_dep() -> InferenceGateway:
    return get_inference_gateway()


def get_feature_flag_client_dep() -> FeatureFlagClient:
    return get_feature_flag_client()


def get_telemetry_client_dep() -> TelemetryClient:
    return get_telemetry_client()


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


@router.post("/inference", response_model=InferenceInvokeResponse)
async def invoke_inference(
    request: InferenceInvokeRequest,
    gateway: InferenceGateway = Depends(get_inference_gateway_dep),
) -> InferenceInvokeResponse:
    try:
        result = await gateway.infer(
            InferenceRequest(
                provider=request.provider,
                model=request.model,
                payload=request.payload,
                stream=request.stream,
            )
        )
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return InferenceInvokeResponse(provider=result.provider, model=result.model, output=result.output)


@router.post("/telemetry", status_code=status.HTTP_202_ACCEPTED)
async def capture_telemetry(
    event: TelemetryEventModel,
    telemetry: TelemetryClient = Depends(get_telemetry_client_dep),
) -> None:
    payload = TelemetryEvent(
        event=event.event,
        properties=event.properties,
        distinct_id=event.distinct_id,
    )
    await telemetry.capture(payload)


@router.post(
    "/feature-flags/{flag_key}",
    response_model=FeatureFlagEvaluationResponse,
)
async def evaluate_feature_flag(
    flag_key: str,
    body: FeatureFlagEvaluationRequest,
    client: FeatureFlagClient = Depends(get_feature_flag_client_dep),
) -> FeatureFlagEvaluationResponse:
    context = {item.key: item.value for item in body.context}
    state = await client.evaluate(flag_key, context=context)
    return FeatureFlagEvaluationResponse(
        key=state.key,
        enabled=state.enabled,
        variant=state.variant,
        context=state.context,
    )

