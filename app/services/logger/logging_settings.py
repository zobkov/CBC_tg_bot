import json
import sys
from datetime import datetime
import os
from pathlib import Path
from typing import Dict

from app.utils.logging_utils import (
    SQLALCHEMY_DEBUG_LEVEL,
    AIOGRAM_DEBUG_LEVEL,
    AIOGRAM_DIALOG_DEBUG_LEVEL,
)

# Указываем папку для логов
LOG_DIR = os.path.join(os.path.dirname(__file__), '../../logs')
os.makedirs(LOG_DIR, exist_ok=True)  # Создаем папку, если она не существует

BASE_DIR = Path(__file__).resolve().parents[3]
LOGGING_LEVELS_FILE = BASE_DIR / "config/logging_levels.json"

DEFAULT_LEVEL_MATRIX: Dict[str, Dict[str, bool]] = {
    "console": {
        "SQLALCHEMY#DEBUG": True,
        "AIOGRAM#DEBUG": True,
        "AIOGRAM_DIALOG#DEBUG": True,
        "DEBUG": True,
        "INFO": True,
        "WARNING": True,
        "ERROR": True,
        "CRITICAL": True,
    },
    "file": {
        "SQLALCHEMY#DEBUG": True,
        "AIOGRAM#DEBUG": True,
        "AIOGRAM_DIALOG#DEBUG": True,
        "DEBUG": True,
        "INFO": True,
        "WARNING": True,
        "ERROR": True,
        "CRITICAL": True,
    },
}


def _load_handler_level_matrix() -> Dict[str, Dict[str, bool]]:
    if not LOGGING_LEVELS_FILE.exists():
        return DEFAULT_LEVEL_MATRIX

    try:
        with LOGGING_LEVELS_FILE.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:  # pragma: no cover - fallback for invalid user config
        return DEFAULT_LEVEL_MATRIX

    handlers_section = payload.get("handlers", {})
    matrix: Dict[str, Dict[str, bool]] = {}

    for handler_key, handler_config in handlers_section.items():
        levels_config = handler_config.get("levels", {}) if isinstance(handler_config, dict) else {}
        matrix[handler_key] = {
            str(level_name).upper(): bool(is_enabled)
            for level_name, is_enabled in levels_config.items()
        }

    # Merge with defaults to guarantee presence of known levels
    merged = {}
    for handler in DEFAULT_LEVEL_MATRIX:
        merged_levels = DEFAULT_LEVEL_MATRIX[handler].copy()
        merged_levels.update(matrix.get(handler, {}))
        merged[handler] = merged_levels

    return merged


HANDLER_LEVEL_MATRIX = _load_handler_level_matrix()


logging_config = {
    'version': 1,
    'disable_existing_loggers': False,  # Allow existing loggers to propagate
    'formatters': {
        'formatter_2': {
            'format': '#%(levelname)-8s [%(asctime)s] - %(filename)s:'
                      '%(lineno)d - %(name)s:%(funcName)s - %(message)s'
        }
    },
    'filters': {
        'custom_domain_level': {
            '()': 'app.utils.logging_utils.LoggerLevelOverrideFilter',
            'overrides': {
                'app.infrastructure.database.sqlalchemy_core': SQLALCHEMY_DEBUG_LEVEL,
                'sqlalchemy.engine': SQLALCHEMY_DEBUG_LEVEL,
                'aiogram': AIOGRAM_DEBUG_LEVEL,
                'aiogram_dialog': AIOGRAM_DIALOG_DEBUG_LEVEL,
            }
        },
        'stdout_level_filter': {
            '()': 'app.utils.logging_utils.HandlerLevelToggleFilter',
            'levels': HANDLER_LEVEL_MATRIX.get('console', {})
        },
        'file_level_filter': {
            '()': 'app.utils.logging_utils.HandlerLevelToggleFilter',
            'levels': HANDLER_LEVEL_MATRIX.get('file', {})
        }
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter_2',
            'stream': sys.stdout,
            'filters': ['custom_domain_level', 'stdout_level_filter']
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'formatter_2',
            'filename': os.path.join(LOG_DIR, f'Log {datetime.now().strftime("%d.%m.%Y")}.log'),
            'mode': 'a',  # Append mode
            'encoding': 'utf-8',  # Добавляем поддержку Unicode
            'filters': ['custom_domain_level', 'file_level_filter']
        }
    },
    'root': {
        'handlers': ['stdout', 'file'],
        'level': 'DEBUG'
    },
    'loggers': {
        'aiogram': {
            'handlers': ['stdout', 'file'],
            'level': 'INFO',  # Keep default level for general aiogram logs
            'propagate': False
        },
        'aiogram.event': {
            'handlers': ['stdout', 'file'],
            'level': 'DEBUG',  # Set only event handling logs to DEBUG
            'propagate': False
        },
        'aiogram_dialog': {
            'handlers': ['stdout', 'file'],
            'level': AIOGRAM_DIALOG_DEBUG_LEVEL,
            'propagate': False
        },
        'app.infrastructure.database.sqlalchemy_core': {
            'handlers': ['stdout', 'file'],
            'level': SQLALCHEMY_DEBUG_LEVEL,
            'propagate': False
        }
    }
}