import logging
import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from environs import Env

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    user: str
    password: str
    database: str
    host: str
    port: int = 5432

@dataclass
class RedisConfig:
    password: str
    host: str = "0.0.0.0"
    port: str = 6379

@dataclass
class TgBot:
    token: str

@dataclass
class GoogleConfig:
    credentials_path: str
    spreadsheet_id: str
    drive_folder_id: Optional[str] = None  # Теперь опциональный
    spreadsheet_name: str = "Заявки КБК26"  # Название таблицы по умолчанию
    drive_folder_name: str = "Резюме_КБК26"  # Название папки по умолчанию
    enable_drive: bool = False  # Включить/выключить Google Drive

@dataclass
class SelectionConfig:
    stages: Dict[str, Any]
    departments: Dict[str, Any]
    how_found_options: list[str]
    support_contacts: Dict[str, str]

@dataclass
class SQLAlchemyEngineConfig:
    db_pool_size: int
    db_pool_max_overflow: int
    db_pool_timeout: float
    db_statement_timeout_ms: int
    db_connect_timeout: int
    db_echo_sql: bool

@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    redis: RedisConfig
    selection: SelectionConfig
    google: Optional[GoogleConfig] = None
    admin_ids: list[int] = field(default_factory=list)
    sqlalchemy_eng: SQLAlchemyEngineConfig


_CONFIG_CACHE: Optional[Config] = None


def _build_config(path: str | None = None) -> Config:
    # Загружаем JSON конфигурацию
    config_path = os.path.join(os.path.dirname(__file__), "selection_config.json")
    with open(config_path, "r", encoding="utf-8") as file:
        json_config = json.load(file)

    # Загружаем departments.json с под-отделами
    departments_path = os.path.join(os.path.dirname(__file__), "departments.json")
    with open(departments_path, "r", encoding="utf-8") as file:
        departments_config = json.load(file)

    # Загружаем переменные окружения для секретных данных
    env = Env()
    if path:
        env.read_env(path)
    else:
        env.read_env()

    tg_bot = TgBot(token=env.str("BOT_TOKEN"))
    db_config = DatabaseConfig(
        user=env.str("DB_USER"),
        password=env.str("DB_PASS"),
        database=env.str("DB_NAME"),
        host=env.str("DB_HOST"),
        port=env.int("DB_PORT", 5432),
    )

    redis = RedisConfig(
        host=env.str("REDIS_HOST"),
        port=env.int("REDIS_PORT", 6379),
        password=env.str("REDIS_PASSWORD"),
    )

    # Настройки Google (опциональные)
    google_config = None
    credentials_path = env.str("GOOGLE_CREDENTIALS_PATH", None)
    spreadsheet_id = env.str("GOOGLE_SPREADSHEET_ID", None)
    drive_folder_id = env.str("GOOGLE_DRIVE_FOLDER_ID", None)
    enable_drive = env.bool("GOOGLE_ENABLE_DRIVE", False)

    logger.info(
        "Google credentials check: credentials_path=%s, spreadsheet_id=%s",
        credentials_path,
        spreadsheet_id,
    )
    logger.info(
        "Google Drive settings: drive_folder_id=%s, enable_drive=%s",
        drive_folder_id,
        enable_drive,
    )

    if credentials_path and spreadsheet_id:
        google_config = GoogleConfig(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id,
            drive_folder_id=drive_folder_id,
            enable_drive=enable_drive,
        )
        logger.info("Google config создан: %s", google_config)
        logger.info("Google Drive %s", "включен" if enable_drive else "отключен")
    else:
        logger.warning("Некоторые переменные Google не заданы, Google сервисы отключены")

    selection_config = SelectionConfig(
        stages=json_config["selection_stages"],
        departments=departments_config["departments"],
        how_found_options=json_config["how_found_options"],
        support_contacts=json_config["support_contacts"],
    )

    admin_ids_str = env.str("ADMIN_IDS", "")
    admin_ids: list[int] = []
    if admin_ids_str:
        try:
            admin_ids = [int(value.strip()) for value in admin_ids_str.split(",") if value.strip()]
        except ValueError:
            logger.warning("Некорректный формат ADMIN_IDS: %s", admin_ids_str)

    sqlalchemy_eng=SQLAlchemyEngineConfig(
        db_pool_size=env.int("DB_POOL_SIZE", 5),
        db_pool_max_overflow=env.int("DB_POOL_MAX_OVERFLOW", 10),
        db_pool_timeout=env.float("DB_POOL_TIMEOUT", 30.0),
        db_statement_timeout_ms=env.int("DB_STATEMENT_TIMEOUT_MS", 30_000),
        db_connect_timeout=env.int("DB_CONNECT_TIMEOUT", 10),
        db_echo_sql=env.bool("DB_ECHO_SQL", False)
    )

    return Config(
        tg_bot=tg_bot,
        db=db_config,
        redis=redis,
        selection=selection_config,
        google=google_config,
        admin_ids=admin_ids,
        sqlalchemy_eng=sqlalchemy_eng
    )


def load_config(path: str | None = None, *, force_reload: bool = False) -> Config:
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None and not force_reload:
        return _CONFIG_CACHE

    config = _build_config(path)
    _CONFIG_CACHE = config
    return config