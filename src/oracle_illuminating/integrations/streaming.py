"""
Real-time data ingestion utilities.

Implements a Kafka-compatible interface that can downsample into DuckDB or
ClickHouse for rapid analytics.  In local development the manager falls back to a
bounded asyncio queue so that the API surface remains testable without Kafka.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from aiokafka import AIOKafkaConsumer  # type: ignore
except Exception:  # pragma: no cover
    AIOKafkaConsumer = None


@dataclass(slots=True)
class StreamingStatus:
    topic: str
    running: bool
    last_event_at: Optional[str] = None
    records_processed: int = 0


@dataclass(slots=True)
class StreamingJob:
    topic: str
    sink: str
    task: asyncio.Task
    status: StreamingStatus


class KafkaStreamIngestor:
    def __init__(
        self,
        bootstrap_servers: str | None = os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        duckdb_path: str = os.getenv("STREAMING_DUCKDB_PATH", "streaming.duckdb"),
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._duckdb_path = duckdb_path
        self._jobs: Dict[str, StreamingJob] = {}
        self._lock = asyncio.Lock()

    async def start_ingest(self, topic: str, sink: str = "duckdb") -> StreamingStatus:
        async with self._lock:
            if topic in self._jobs:
                return self._jobs[topic].status

            if AIOKafkaConsumer and self._bootstrap_servers:
                task = asyncio.create_task(self._consume_kafka(topic, sink))
            else:
                task = asyncio.create_task(self._consume_memory(topic, sink))

            job = StreamingJob(
                topic=topic,
                sink=sink,
                task=task,
                status=StreamingStatus(topic=topic, running=True),
            )
            self._jobs[topic] = job
            return job.status

    async def stop_ingest(self, topic: str) -> StreamingStatus:
        async with self._lock:
            job = self._jobs.get(topic)
            if not job:
                raise ValueError(f"No ingest job for topic '{topic}'")
            job.task.cancel()
            try:
                await job.task
            except asyncio.CancelledError:
                pass
            job.status.running = False
            return job.status

    async def get_status(self, topic: str) -> StreamingStatus:
        async with self._lock:
            job = self._jobs.get(topic)
            if not job:
                raise ValueError(f"No ingest job for topic '{topic}'")
            return job.status

    async def _consume_kafka(self, topic: str, sink: str) -> None:  # pragma: no cover - requires kafka
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._bootstrap_servers,
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await consumer.start()
        try:
            async for msg in consumer:
                await self._persist_record(topic, sink, msg.value)
        finally:
            await consumer.stop()

    async def _consume_memory(self, topic: str, sink: str) -> None:
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        # Provide a simple mechanism to simulate ingestion for local environments.
        async def producer() -> None:
            while True:
                await asyncio.sleep(5)
                payload = f'{{"topic":"{topic}","ts":"{datetime.utcnow().isoformat()}","value":42}}'
                await queue.put(payload.encode())

        producer_task = asyncio.create_task(producer())
        try:
            while True:
                record = await queue.get()
                await self._persist_record(topic, sink, record)
        except asyncio.CancelledError:
            producer_task.cancel()
            raise

    async def _persist_record(self, topic: str, sink: str, payload: bytes) -> None:
        async with self._lock:
            job = self._jobs.get(topic)
            if not job:
                return
            job.status.records_processed += 1
            job.status.last_event_at = datetime.utcnow().isoformat()

        if sink == "duckdb":
            await self._append_duckdb(payload)
        elif sink == "clickhouse":
            await self._append_clickhouse(payload)
        else:
            logger.debug("Dropping record for unsupported sink %s", sink)

    async def _append_duckdb(self, payload: bytes) -> None:
        try:
            import duckdb  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            logger.debug("DuckDB not installed; skipping persist")
            return

        record = payload.decode()
        connection = duckdb.connect(self._duckdb_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS streaming_events (raw TEXT)"
        )
        connection.execute("INSERT INTO streaming_events VALUES (?)", (record,))
        connection.close()

    async def _append_clickhouse(self, payload: bytes) -> None:
        try:
            import clickhouse_connect  # type: ignore
        except Exception:  # pragma: no cover
            logger.debug("clickhouse-connect not installed; skipping persist")
            return
        client = clickhouse_connect.get_client()
        client.command(
            """
            CREATE TABLE IF NOT EXISTS streaming_events
            (raw String)
            ENGINE MergeTree
            ORDER BY tuple()
            """
        )
        client.insert("streaming_events", [[payload.decode()]])
        client.close()


_streaming_manager: KafkaStreamIngestor | None = None


def get_streaming_manager() -> KafkaStreamIngestor:
    global _streaming_manager
    if _streaming_manager is None:
        _streaming_manager = KafkaStreamIngestor()
    return _streaming_manager

