from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine

from oracle_illuminating.analytics.repository import InsightRecorder
from oracle_illuminating.service import analytics_routes, routes
from oracle_illuminating.service.app import create_app


def _test_client() -> tuple[TestClient, InsightRecorder]:
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    recorder = InsightRecorder(engine=engine)

    def override_recorder() -> InsightRecorder:
        return recorder

    app.dependency_overrides[routes.get_recorder] = override_recorder
    app.dependency_overrides[analytics_routes.get_recorder] = override_recorder
    return TestClient(app), recorder


def test_illuminate_endpoint_returns_insights_and_guardrails() -> None:
    client, _ = _test_client()

    response = client.post("/api/illuminate", json={"payload": {"summary": "test insight"}})

    assert response.status_code == 200
    data = response.json()

    assert "insights" in data and len(data["insights"]) > 0
    assert "guardrails" in data and len(data["guardrails"]) > 0


def test_analytics_summary_endpoint_reflects_recorded_runs() -> None:
    client, _ = _test_client()

    client.post(
        "/api/illuminate",
        json={
            "payload": {
                "summary": "analytics check",
                "metrics": {"delta": 0.3},
                "signals": [{"label": "alpha", "strength": 0.7}],
            }
        },
    )

    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["oracles"]
    assert data["guardrails"]
    assert data["recent_runs"]

