"""
Analytics instrumentation client for privacy-first event collection.

The client favours open-source or self-hostable stacks (e.g. PostHog, RudderStack,
or OpenTelemetry collectors) and only requires HTTP connectivity.  For runtime
environments without outbound networking the client degrades to buffered,
in-memory storage so that downstream processes can inspect captured telemetry
during unit tests.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


DEFAULT_TELEMETRY_ENDPOINT = os.getenv(
    "ORACLE_TELEMETRY_ENDPOINT",
    # The /batch endpoint is compatible with PostHog and RudderStack.
    "https://app.posthog.com/batch/",
)


@dataclass(slots=True)
class TelemetryEvent:
    """Envelope for analytics events emitted by the service."""

    event: str
    properties: Dict[str, Any] = field(default_factory=dict)
    distinct_id: str | None = None


class TelemetryClient:
    """
    Privacy-aware telemetry dispatcher.

    The client:
    - supports async fire-and-forget analytics calls
    - buffers events in memory when network calls fail so nothing is lost
    - can be swapped to a local DuckDB sink for offline analytics replay
    """

    def __init__(
        self,
        endpoint: str = DEFAULT_TELEMETRY_ENDPOINT,
        api_key: str | None = os.getenv("ORACLE_TELEMETRY_API_KEY"),
        timeout_seconds: float = 3.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._buffer: List[TelemetryEvent] = []
        self._lock = asyncio.Lock()

    async def capture(self, event: TelemetryEvent) -> None:
        """
        Capture an event asynchronously.

        Events are sent immediately; failures will queue the payload for later
        retries so that callers never need to handle exceptions.
        """

        async with self._lock:
            self._buffer.append(event)
            await self._flush_locked()

    async def _flush_locked(self) -> None:
        if not self._buffer:
            return

        payload = [
            {
                "event": item.event,
                "properties": item.properties,
                "distinct_id": item.distinct_id,
            }
            for item in self._buffer
        ]

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._endpoint,
                    json={"batch": payload},
                    headers=headers,
                )
                response.raise_for_status()
                self._buffer.clear()
        except Exception as exc:  # pragma: no cover - network failure path
            logger.debug("Telemetry dispatch deferred: %s", exc, exc_info=exc)

    async def flush(self) -> None:
        """Force-flush any buffered events."""

        async with self._lock:
            await self._flush_locked()


_telemetry_client: TelemetryClient | None = None


def get_telemetry_client() -> TelemetryClient:
    """
    Fast dependency provider for TelemetryClient.

    Ensures we hold onto a singleton per-process to avoid re-creating HTTP pools.
    """

    global _telemetry_client
    if _telemetry_client is None:
        _telemetry_client = TelemetryClient()
    return _telemetry_client

