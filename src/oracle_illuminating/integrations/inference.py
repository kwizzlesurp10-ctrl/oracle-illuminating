"""
Inference gateway for external model providers such as Hugging Face Inference API
and Replicate.

The gateway normalises input/output payloads for downstream consumers so that the
application can swap providers without code changes.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InferenceRequest:
    provider: str
    model: str
    payload: Dict[str, Any]
    stream: bool = False


@dataclass(slots=True)
class InferenceResponse:
    provider: str
    model: str
    output: Dict[str, Any]


class InferenceGateway:
    def __init__(
        self,
        huggingface_api_key: str | None = os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        replicate_api_key: str | None = os.getenv("REPLICATE_API_TOKEN"),
    ) -> None:
        self._huggingface_api_key = huggingface_api_key
        self._replicate_api_key = replicate_api_key

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        if request.provider == "huggingface":
            return await self._invoke_huggingface(request)
        if request.provider == "replicate":
            return await self._invoke_replicate(request)
        raise ValueError(f"Unsupported inference provider: {request.provider}")

    async def _invoke_huggingface(self, request: InferenceRequest) -> InferenceResponse:
        if not self._huggingface_api_key:
            raise RuntimeError("Hugging Face API token is not configured")
        headers = {
            "Authorization": f"Bearer {self._huggingface_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{request.model}",
                headers=headers,
                json=request.payload,
                params={"stream": str(request.stream).lower()},
            )
            response.raise_for_status()
            body = response.json()
        return InferenceResponse(provider="huggingface", model=request.model, output=body)

    async def _invoke_replicate(self, request: InferenceRequest) -> InferenceResponse:
        if not self._replicate_api_key:
            raise RuntimeError("Replicate API token is not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self._replicate_api_key}",
                    "Content-Type": "application/json",
                },
                json={"version": request.model, "input": request.payload},
            )
            response.raise_for_status()
            body = response.json()
        return InferenceResponse(provider="replicate", model=request.model, output=body)


_inference_gateway: InferenceGateway | None = None


def get_inference_gateway() -> InferenceGateway:
    global _inference_gateway
    if _inference_gateway is None:
        _inference_gateway = InferenceGateway()
    return _inference_gateway

