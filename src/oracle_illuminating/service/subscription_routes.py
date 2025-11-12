"""
Routes to expose subscription and billing functionality.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from oracle_illuminating.integrations import BillingProvider, BillingSession, get_billing_provider
from oracle_illuminating.service.models import (
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    SubscriptionPlan,
    WebhookVerificationResponse,
)

router = APIRouter(tags=["subscriptions"])


def get_billing() -> BillingProvider:
    return get_billing_provider()


@router.get("/plans", response_model=list[SubscriptionPlan])
async def list_subscription_plans() -> list[SubscriptionPlan]:
    """
    Returns curated subscription levels that align with the recommended tech stack.
    """

    return [
        SubscriptionPlan(
            id="price_basic_data",
            name="Explorer",
            description="Daily curated open-data drops with AI summaries.",
            price_usd=29.0,
            features=[
                "NASA imagery and alerts (via NASA Open APIs)",
                "Open-Meteo forecast digests",
                "Weekly Census demographic snapshots",
            ],
        ),
        SubscriptionPlan(
            id="price_growth_personalization",
            name="Growth",
            description="Feature-flagged personalization and alert automations.",
            price_usd=79.0,
            features=[
                "Everything in Explorer",
                "Realtime Kafka ingestion with DuckDB replay",
                "Hugging Face inference credits for stylized engagement",
                "Feature flag orchestration for experiments",
            ],
        ),
        SubscriptionPlan(
            id="price_enterprise_fullstack",
            name="Enterprise",
            description="End-to-end pipeline with SLA-backed support.",
            price_usd=249.0,
            features=[
                "Dedicated ClickHouse sink for streaming analytics",
                "Replicate-powered model deployments",
                "Private PostHog endpoint & compliance exports",
                "Premium Stripe/Braintree webhook support and rollbacks",
            ],
        ),
    ]


@router.post(
    "/checkout/session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkout_session(
    payload: CreateCheckoutSessionRequest,
    billing: BillingProvider = Depends(get_billing),
) -> CheckoutSessionResponse:
    try:
        session: BillingSession = await billing.create_checkout_session(
            provider=payload.provider,
            plan_reference=payload.plan_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            customer_email=payload.customer_email,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CheckoutSessionResponse(
        checkout_url=session.checkout_url, provider=session.provider, metadata=session.metadata
    )


@router.post("/checkout/webhook", response_model=WebhookVerificationResponse)
async def verify_webhook(
    raw_body: bytes,
    billing: BillingProvider = Depends(get_billing),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    braintree_signature: str | None = Header(default=None, alias="BT-Signature"),
) -> WebhookVerificationResponse:
    signature = stripe_signature or braintree_signature
    try:
        payload = await billing.verify_webhook(raw_body, signature=signature)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return WebhookVerificationResponse(valid=True, payload=payload)

