"""
Persistence and aggregation utilities for illumination analytics.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlmodel import Session

from oracle_illuminating.analytics.database import get_engine, get_session, init_db
from oracle_illuminating.analytics.models import (
    GuardrailAuditRecord,
    IlluminationRun,
    OracleInsightRecord,
)


class InsightRecorder:
    """
    Records illumination outputs for downstream analytics and reporting.
    """

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine or get_engine()
        init_db(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    def record(
        self,
        *,
        source: str,
        payload: Dict,
        insights: Iterable[Dict],
        guardrails: Iterable[Dict],
        recursive: Optional[Dict] = None,
    ) -> int:
        with Session(self._engine) as session:
            run = IlluminationRun(
                source=source,
                guardrail_status=(recursive or {}).get("status", "unknown"),
                recursive_question=(recursive or {}).get("question"),
                input_payload=json.dumps(payload or {}),
            )
            session.add(run)
            session.flush()

            for insight in insights or []:
                insight_payload = insight.get("insight", {})
                summary = insight_payload.get("summary") if isinstance(insight_payload, dict) else None
                detail = (
                    insight_payload.get("insight")
                    or insight_payload.get("action")
                    or insight_payload.get("recommendation")
                    if isinstance(insight_payload, dict)
                    else None
                )
                session.add(
                    OracleInsightRecord(
                        run_id=run.id,
                        oracle=insight.get("oracle", "unknown"),
                        acuity=float(insight.get("acuity", 0.0)),
                        summary=summary,
                        detail=detail,
                        payload=json.dumps(insight_payload),
                    )
                )

            for finding in guardrails or []:
                session.add(
                    GuardrailAuditRecord(
                        run_id=run.id,
                        layer=finding.get("layer", "unknown"),
                        status=finding.get("status", "pass"),
                        details=finding.get("details"),
                    )
                )

            session.commit()
            return run.id

    def oracle_acuity_summary(self) -> List[Dict]:
        with Session(self._engine) as session:
            statement = (
                select(
                    OracleInsightRecord.oracle,
                    func.count(OracleInsightRecord.id),
                    func.avg(OracleInsightRecord.acuity),
                )
                .group_by(OracleInsightRecord.oracle)
                .order_by(func.avg(OracleInsightRecord.acuity).desc())
            )
            results = session.exec(statement).all()

        return [
            {
                "oracle": oracle,
                "count": int(count),
                "avg_acuity": round(avg_acuity or 0.0, 3),
            }
            for oracle, count, avg_acuity in results
        ]

    def guardrail_status_distribution(self) -> Dict[str, int]:
        with Session(self._engine) as session:
            statement = select(GuardrailAuditRecord.status, func.count(GuardrailAuditRecord.id)).group_by(
                GuardrailAuditRecord.status
            )
            results = session.exec(statement).all()
        return {status: int(count) for status, count in results}

    def recent_runs(self, limit: int = 10) -> List[Dict]:
        with Session(self._engine) as session:
            run_rows = session.exec(
                select(IlluminationRun).order_by(IlluminationRun.created_at.desc()).limit(limit)
            ).all()

            runs: List[IlluminationRun] = []
            for row in run_rows:
                runs.append(row if isinstance(row, IlluminationRun) else row[0])

            if not runs:
                return []

            run_ids = [run.id for run in runs]

            insight_rows = session.exec(
                select(OracleInsightRecord).where(OracleInsightRecord.run_id.in_(run_ids))
            ).all()
            guardrail_rows = session.exec(
                select(GuardrailAuditRecord).where(GuardrailAuditRecord.run_id.in_(run_ids))
            ).all()

            insights: List[OracleInsightRecord] = []
            for row in insight_rows:
                insights.append(row if isinstance(row, OracleInsightRecord) else row[0])

            guardrails: List[GuardrailAuditRecord] = []
            for row in guardrail_rows:
                guardrails.append(row if isinstance(row, GuardrailAuditRecord) else row[0])

        insight_map: Dict[int, List[Dict]] = defaultdict(list)
        guardrail_map: Dict[int, List[Dict]] = defaultdict(list)

        for insight in insights:
            insight_map[insight.run_id].append(
                {
                    "oracle": insight.oracle,
                    "acuity": insight.acuity,
                    "summary": insight.summary,
                    "detail": insight.detail,
                }
            )

        for finding in guardrails:
            guardrail_map[finding.run_id].append(
                {"layer": finding.layer, "status": finding.status, "details": finding.details}
            )

        formatted: List[Dict] = []
        for run in runs:
            formatted.append(
                {
                    "id": run.id,
                    "created_at": run.created_at.isoformat(),
                    "source": run.source,
                    "guardrail_status": run.guardrail_status,
                    "recursive_question": run.recursive_question,
                    "insights": insight_map.get(run.id, []),
                    "guardrails": guardrail_map.get(run.id, []),
                }
            )
        return formatted


_singleton_recorder: InsightRecorder | None = None


def get_insight_recorder() -> InsightRecorder:
    global _singleton_recorder
    if _singleton_recorder is None:
        _singleton_recorder = InsightRecorder()
    return _singleton_recorder

