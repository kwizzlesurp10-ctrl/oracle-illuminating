"""
FastAPI application factory for Oracle Illuminating.
"""

from __future__ import annotations

from fastapi import FastAPI

from oracle_illuminating.service.analytics_routes import router as analytics_router
from oracle_illuminating.service.realtime_routes import router as realtime_router
from oracle_illuminating.service.routes import router as illumination_router
from oracle_illuminating.service.subscription_routes import router as subscription_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Oracle Illuminating",
        description="Agentic AI illumination service implementing the Oracle Overseer framework.",
        version="0.1.0",
    )
    app.include_router(illumination_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(realtime_router, prefix="/api/realtime")
    app.include_router(subscription_router, prefix="/api/subscriptions")
    return app


app = create_app()

