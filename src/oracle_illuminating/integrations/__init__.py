"""
Unified integration layer for external services leveraged by Oracle Illuminating.

This package provides light-touch, optionally asynchronous clients that wrap
external infrastructure described in the recommended tech stack: real-time
streaming into analytical stores, third-party inference providers, billing
gateways, feature-flag orchestration, and privacy-first analytics telemetry.

All integrations degrade gracefully when the associated third-party SDK is not
installed so the core application can continue to operate in constrained
environments (e.g. local development or CI).  Each client exposes a minimal
interface that is exercised by FastAPI routes while keeping the rest of the code
base decoupled from vendor-specific implementations.
"""

from .analytics import TelemetryClient, TelemetryEvent, get_telemetry_client
from .billing import BillingProvider, BillingSession, get_billing_provider
from .feature_flags import FeatureFlagClient, FeatureFlagState, get_feature_flag_client
from .inference import InferenceGateway, InferenceRequest, InferenceResponse, get_inference_gateway
from .streaming import KafkaStreamIngestor, StreamingJob, StreamingStatus, get_streaming_manager

__all__ = [
    "TelemetryClient",
    "get_telemetry_client",
    "TelemetryEvent",
    "BillingProvider",
    "BillingSession",
    "get_billing_provider",
    "FeatureFlagClient",
    "FeatureFlagState",
    "get_feature_flag_client",
    "InferenceGateway",
    "InferenceRequest",
    "InferenceResponse",
    "get_inference_gateway",
    "KafkaStreamIngestor",
    "StreamingJob",
    "StreamingStatus",
    "get_streaming_manager",
]

