"""
Routes exposing real-time ingestion controls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from oracle_illuminating.integrations import KafkaStreamIngestor, StreamingStatus, get_streaming_manager
from oracle_illuminating.service.models import StreamingJobRequest, StreamingJobStatus

router = APIRouter(tags=["realtime"])


def get_streaming() -> KafkaStreamIngestor:
    return get_streaming_manager()


@router.post(
    "/jobs",
    response_model=StreamingJobStatus,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_ingest(
    request: StreamingJobRequest, manager: KafkaStreamIngestor = Depends(get_streaming)
) -> StreamingJobStatus:
    status_obj = await manager.start_ingest(topic=request.topic, sink=request.sink)
    return StreamingJobStatus(
        topic=status_obj.topic,
        running=status_obj.running,
        last_event_at=status_obj.last_event_at,
        records_processed=status_obj.records_processed,
    )


@router.get("/jobs/{topic}", response_model=StreamingJobStatus)
async def get_job_status(topic: str, manager: KafkaStreamIngestor = Depends(get_streaming)) -> StreamingJobStatus:
    try:
        status_obj: StreamingStatus = await manager.get_status(topic)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StreamingJobStatus(
        topic=status_obj.topic,
        running=status_obj.running,
        last_event_at=status_obj.last_event_at,
        records_processed=status_obj.records_processed,
    )


@router.delete("/jobs/{topic}", response_model=StreamingJobStatus)
async def stop_ingest(topic: str, manager: KafkaStreamIngestor = Depends(get_streaming)) -> StreamingJobStatus:
    try:
        status_obj: StreamingStatus = await manager.stop_ingest(topic)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StreamingJobStatus(
        topic=status_obj.topic,
        running=status_obj.running,
        last_event_at=status_obj.last_event_at,
        records_processed=status_obj.records_processed,
    )

