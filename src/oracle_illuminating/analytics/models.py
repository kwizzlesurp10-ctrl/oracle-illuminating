"""
SQLModel definitions backing illumination analytics storage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class IlluminationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source: str = Field(default="api", index=True)
    guardrail_status: str = Field(default="unknown", index=True)
    recursive_question: Optional[str] = Field(default=None)
    input_payload: str = Field(default="{}", sa_column=Column(Text))


class OracleInsightRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="illuminationrun.id", index=True)
    oracle: str = Field(index=True)
    acuity: float = Field(default=0.0)
    summary: Optional[str] = Field(default=None)
    detail: Optional[str] = Field(default=None)
    payload: str = Field(default="{}", sa_column=Column(Text))


class GuardrailAuditRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="illuminationrun.id", index=True)
    layer: str = Field(index=True)
    status: str = Field(default="pass", index=True)
    details: Optional[str] = Field(default=None)

