"""
Database configuration helpers for analytics persistence.
"""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine


def _default_db_url() -> str:
    return os.getenv("ORACLE_ILLUMINATING_DB_URL", "sqlite:///./oracle_data.db")


@lru_cache(maxsize=1)
def get_engine(db_url: str | None = None) -> Engine:
    url = db_url or _default_db_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=False, connect_args=connect_args)


def init_db(engine: Engine | None = None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())


def get_session(engine: Engine | None = None) -> Session:
    return Session(engine or get_engine())

