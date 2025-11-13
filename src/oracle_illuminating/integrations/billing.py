"""
Billing provider integration supporting Stripe and Braintree.

The provider abstracts subscription session creation and webhook signature
validation so FastAPI routes can remain implementation-agnostic.  The goal is to
enable experimentation with pricing plans and feature bundles while leaning on
battle-tested payment infrastructure.
"""

from __future__ import annotations

import base64
import hmac
import json
import logging
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class BillingError(RuntimeError):
    """Raised when a billing provider operation fails."""


@dataclass(slots=True)
class BillingSession:
    checkout_url: str
    provider: str
    metadata: Dict[str, Any]


class BillingProvider:
    """
    Unified layer for subscription management.

    This implementation intentionally sticks to raw HTTP requests to avoid
    forcing the Stripe or Braintree SDKs on downstream consumers.  The shape of
    the payloads follows the respective REST APIs which keeps the logic portable.
    """

    def __init__(
        self,
        stripe_api_key: str | None = os.getenv("STRIPE_API_KEY"),
        braintree_merchant_id: str | None = os.getenv("BRAINTREE_MERCHANT_ID"),
        braintree_public_key: str | None = os.getenv("BRAINTREE_PUBLIC_KEY"),
        braintree_private_key: str | None = os.getenv("BRAINTREE_PRIVATE_KEY"),
        webhook_secret: str | None = os.getenv("BILLING_WEBHOOK_SECRET"),
    ) -> None:
        self._stripe_api_key = stripe_api_key
        self._braintree_config = {
            "merchant_id": braintree_merchant_id,
            "public_key": braintree_public_key,
            "private_key": braintree_private_key,
        }
        self._webhook_secret = webhook_secret

    async def create_checkout_session(
        self,
        provider: str,
        plan_reference: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
    ) -> BillingSession:
        if provider == "stripe":
            return await self._create_stripe_session(
                plan_reference, success_url, cancel_url, customer_email
            )
        if provider == "braintree":
            return await self._create_braintree_session(plan_reference)
        raise BillingError(f"Unsupported billing provider: {provider}")

    async def verify_webhook(self, payload: bytes, signature: str | None) -> Dict[str, Any]:
        """
        Simple HMAC-based verification compatible with both Stripe and Braintree.
        """

        if not self._webhook_secret:
            raise BillingError("Webhook secret is not configured")

        if not signature:
            raise BillingError("Missing webhook signature header")

        secret = self._webhook_secret.encode()

        try:
            decoded_body = payload.decode()
        except UnicodeDecodeError as exc:
            raise BillingError("Webhook payload must be UTF-8 encoded") from exc

        def load_json() -> Dict[str, Any]:
            try:
                return json.loads(decoded_body)
            except json.JSONDecodeError as exc:
                raise BillingError("Webhook payload is not valid JSON") from exc

        # Stripe sends comma-delimited key/value pairs that include a timestamp and signature.
        if "v1=" in signature:
            components: Dict[str, str] = {}
            for item in signature.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    components[key.strip()] = value.strip()
            timestamp = components.get("t")
            v1_signature = components.get("v1")
            if not timestamp or not v1_signature:
                raise BillingError("Invalid Stripe signature header")
            signed_payload = f"{timestamp}.{decoded_body}".encode()
            expected = hmac.new(secret, signed_payload, sha256).hexdigest()
            if not hmac.compare_digest(expected, v1_signature):
                raise BillingError("Invalid webhook signature")
            return load_json()

        digest = hmac.new(secret, payload, sha256).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise BillingError("Invalid webhook signature")
        return load_json()

    async def _create_stripe_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None,
    ) -> BillingSession:
        if not self._stripe_api_key:
            raise BillingError("Stripe API key not configured")

        data = {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": 1,
        }
        if customer_email:
            data["customer_email"] = customer_email

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                data=data,
                auth=(self._stripe_api_key, ""),
            )
        if response.status_code >= 400:
            logger.error("Stripe error: %s", response.text)
            raise BillingError("Stripe checkout session creation failed")
        payload = response.json()
        return BillingSession(
            checkout_url=payload.get("url"),
            provider="stripe",
            metadata={"session_id": payload.get("id"), "price_id": price_id},
        )

    async def _create_braintree_session(self, plan_id: str) -> BillingSession:
        merchant_id = self._braintree_config["merchant_id"]
        public_key = self._braintree_config["public_key"]
        private_key = self._braintree_config["private_key"]
        if not all([merchant_id, public_key, private_key]):
            raise BillingError("Braintree credentials not configured")

        auth = base64.b64encode(f"{public_key}:{private_key}".encode()).decode()
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                "https://payments.sandbox.braintree-api.com/graphql",
                headers={
                    "Content-Type": "application/json",
                    "Braintree-Version": "2018-05-10",
                    "Authorization": f"Basic {auth}",
                },
                json={
                    "query": (
                        "mutation CreateClientToken { "
                        "createClientToken(clientTokenInput: { merchantAccountId: "
                        '"%s" }) { clientToken } }'
                    )
                    % merchant_id
                },
            )
        if response.status_code >= 400:
            logger.error("Braintree error: %s", response.text)
            raise BillingError("Braintree client token retrieval failed")

        payload = response.json()
        token = (
            payload.get("data", {})
            .get("createClientToken", {})
            .get("clientToken")
        )
        metadata = {"plan_id": plan_id, "client_token": token}
        return BillingSession(
            checkout_url="https://payments.braintreegateway.com/tokenized-checkout",
            provider="braintree",
            metadata=metadata,
        )


_billing_provider: BillingProvider | None = None


def get_billing_provider() -> BillingProvider:
    global _billing_provider
    if _billing_provider is None:
        _billing_provider = BillingProvider()
    return _billing_provider

