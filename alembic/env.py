from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if PROJECT_ROOT.as_posix() not in sys.path:
    sys.path.insert(0, PROJECT_ROOT.as_posix())

from app.infrastructure.database.orm.base import Base

# Ensure models are imported so that Alembic can discover them
import app.infrastructure.database.models.users  # noqa: F401
import app.infrastructure.database.models.feedback  # noqa: F401
import app.infrastructure.database.models.user_info  # noqa: F401
import app.infrastructure.database.models.creative_application  # noqa: F401
import app.infrastructure.database.models.broadcasts  # noqa: F401
import app.infrastructure.database.models.user_subscriptions  # noqa: F401
import app.infrastructure.database.models.online_events  # noqa: F401
import app.infrastructure.database.models.online_registrations  # noqa: F401

try:
    from config.config import load_config
except ModuleNotFoundError:  # pragma: no cover - fallback for limited environments
    load_config = None  # type: ignore

config = context.config

if config.config_ini_section:
    fileConfig(config.config_file_name)


def _build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    if load_config is None:
        raise RuntimeError(
            "DATABASE_URL environment variable must be set when config.load_config is unavailable"
        )

    app_config = load_config()
    db_cfg = app_config.db
    return (
        f"postgresql+psycopg://{db_cfg.user}:{db_cfg.password}"
        f"@{db_cfg.host}:{db_cfg.port}/{db_cfg.database}"
    )


def _configure_context(connection: Connection | None = None) -> None:
    config.set_main_option("sqlalchemy.url", _build_database_url())

    target_metadata = Base.metadata

    if connection is None:
        context.configure(
            url=config.get_main_option("sqlalchemy.url"),
            target_metadata=target_metadata,
            literal_binds=True,
            compare_type=True,
            compare_server_default=True,
        )
    else:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )


def run_migrations_offline() -> None:
    _configure_context()
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database_url = _build_database_url()
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _configure_context(connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
