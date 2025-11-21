"""Async SQLAlchemy engine factory intialization, helpers and health checks."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.config import Config, DatabaseConfig, load_config

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EngineConfig:
    """
    Dataclass for SQLAlchemy engine config
    """
    dsn: URL
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    echo_sql: bool = False
    connect_timeout: int = 10
    statement_timeout_ms: int = 30_000


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_engine_config: Optional[EngineConfig] = None


def _build_dsn(
    db_cfg: DatabaseConfig,
    connect_timeout: int,
    statement_timeout_ms: int,
) -> URL:
    query = {"connect_timeout": str(connect_timeout)}
    if statement_timeout_ms > 0:
        query["options"] = f"-c statement_timeout={statement_timeout_ms}"

    return URL.create(
        drivername="postgresql+psycopg_async",
        username=db_cfg.user,
        password=db_cfg.password,
        host=db_cfg.host,
        port=db_cfg.port,
        database=db_cfg.database,
        query=query,
    )


def _load_engine_config(config: Config) -> EngineConfig:
    global _engine_config # pylint: disable=global-statement
    if _engine_config is not None:
        return _engine_config

    db_cfg = config.db
    eng_cfg = config.sqlalchemy_eng

    pool_size = int(getattr(eng_cfg, "db_pool_size", 5))
    max_overflow = int(getattr(eng_cfg, "db_pool_max_overflow", 10))
    pool_timeout = float(getattr(eng_cfg, "db_pool_timeout", 30.0))
    statement_timeout_ms = int(getattr(eng_cfg, "db_statement_timeout_ms", 30_000))
    connect_timeout = int(getattr(eng_cfg, "db_connect_timeout", 10))
    echo_sql = bool(getattr(eng_cfg, "db_echo_sql", False))

    _engine_config = EngineConfig(
        dsn=_build_dsn(db_cfg, connect_timeout, statement_timeout_ms),
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        echo_sql=echo_sql,
        connect_timeout=connect_timeout,
        statement_timeout_ms=statement_timeout_ms,
    )
    return _engine_config


def get_engine() -> AsyncEngine:
    """
    Function to get eninge from module level or initialize it
    """
    global _engine, _session_factory # pylint: disable=global-statement
    if _engine is not None:
        return _engine

    config = load_config()
    engine_cfg = _load_engine_config(config)

    logger.info(
        "Creating SQLAlchemy AsyncEngine (pool_size=%d, max_overflow=%d, timeout=%.1fs)",
        engine_cfg.pool_size,
        engine_cfg.max_overflow,
        engine_cfg.pool_timeout,
    )

    _engine = create_async_engine(
        engine_cfg.dsn,
        echo=engine_cfg.echo_sql,
        pool_size=engine_cfg.pool_size,
        max_overflow=engine_cfg.max_overflow,
        pool_timeout=engine_cfg.pool_timeout,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        autoflush=False,
    )

    _register_events(_engine)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Assert that session factory exists or else initialize engine 
    """
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield session factory for getting AsyncSession object. Passed to dispacther at the bot init. 
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def dispose_engine() -> None:
    """
    Destroy engine and drop all connections
    """
    global _engine, _session_factory, _engine_config # pylint: disable=global-statement
    if _engine is not None:
        await _engine.dispose() # Here is the main disposal method of AsyncEngine
        _engine = None
    _session_factory = None
    _engine_config = None
    logger.info("SQLAlchemy AsyncEngine disposed")


async def healthcheck() -> bool:
    """
    Check connection to the database. 
    """
    try:
        async with session_scope() as session:
            await session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:  # pragma: no cover - used in runtime checks
        logger.critical("Database healthcheck failed: %s", exc)
        return False


def _register_events(engine: AsyncEngine) -> None:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _before_cursor_execute(_, __, ___, ____, context, _____) -> None:  # type: ignore[override]
        setattr(context, "_query_start_time", time.perf_counter())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def _after_cursor_execute(
        _, __, statement, ___, context, ____
    ) -> None:  # type: ignore[override]
        start = getattr(context, "_query_start_time", None)
        if start is None:
            return
        delattr(context, "_query_start_time")
        duration_ms = (time.perf_counter() - start) * 1000
        logger.sqlalchemy_debug("SQL %.1f ms: %s", duration_ms, statement.splitlines()[0].strip())


__all__ = [
    "EngineConfig",
    "get_engine",
    "get_session_factory",
    "session_scope",
    "dispose_engine",
    "healthcheck",
]
