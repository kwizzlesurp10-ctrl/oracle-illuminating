"""
Feature flag client abstraction.

Supports LaunchDarkly via REST and open-source alternatives such as Flipt.  The
client uses simple HTTP calls so it can run without the full SDKs and will cache
flag evaluations for the lifetime of the process to minimise latency.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FeatureFlagState:
    key: str
    enabled: bool
    variant: Optional[str] = None
    context: Dict[str, Any] | None = None


class FeatureFlagClient:
    def __init__(
        self,
        endpoint: str | None = os.getenv("FEATURE_FLAG_ENDPOINT"),
        sdk_key: str | None = os.getenv("FEATURE_FLAG_SDK_KEY"),
        cache_ttl_seconds: int = 60,
    ) -> None:
        self._endpoint = endpoint
        self._sdk_key = sdk_key
        self._cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, FeatureFlagState] = {}
        self._lock = asyncio.Lock()

    async def evaluate(self, key: str, context: Dict[str, Any] | None = None) -> FeatureFlagState:
        if key in self._cache:
            return self._cache[key]

        if not self._endpoint:
            # Default to enabled in local development to surface new features.
            state = FeatureFlagState(key=key, enabled=True, variant="default", context=context)
            self._cache[key] = state
            return state

        headers = {"Content-Type": "application/json"}
        if self._sdk_key:
            headers["Authorization"] = self._sdk_key

        payload = {"key": key, "context": context or {}}
        try:
            async with self._lock:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.post(self._endpoint, json=payload, headers=headers)
                    response.raise_for_status()
                    body = response.json()
        except Exception as exc:  # pragma: no cover - network path
            logger.debug("Feature flag evaluation failed, defaulting to disabled: %s", exc)
            state = FeatureFlagState(key=key, enabled=False, variant=None, context=context)
        else:
            state = FeatureFlagState(
                key=key,
                enabled=body.get("enabled", False),
                variant=body.get("variant"),
                context=context,
            )
        self._cache[key] = state
        return state


_feature_flag_client: FeatureFlagClient | None = None


def get_feature_flag_client() -> FeatureFlagClient:
    global _feature_flag_client
    if _feature_flag_client is None:
        _feature_flag_client = FeatureFlagClient()
    return _feature_flag_client

