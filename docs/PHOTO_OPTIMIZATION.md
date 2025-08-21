# Система оптимизации отправки фотографий через file_id

## Описание

Система позволяет оптимизировать отправку фотографий в Telegram боте, используя file_id вместо повторной загрузки файлов. Это существенно ускоряет отправку и снижает нагрузку на сервер.

## Принцип работы

1. **При первом запуске**: Все новые фотографии отправляются в специальный чат для получения file_id
2. **file_id сохраняются**: В JSON файл `config/photo_file_ids.json` 
3. **При отправке**: Используется file_id для мгновенной отправки
4. **Fallback**: Если file_id недоступен, отправляется файл напрямую

## Основные компоненты

### 1. PhotoFileIdManager (`app/services/photo_file_id_manager.py`)
Основной класс для управления file_id:
- `check_and_upload_new_photos()` - проверка и загрузка новых фото при старте
- `regenerate_all_file_ids()` - полная регенерация всех file_id
- `get_file_id(relative_path)` - получение file_id для конкретного файла

### 2. PhotoSender (`app/utils/photo_utils.py`)
Утилитарный класс для отправки фотографий:
- `send_photo_by_path()` - отправка одного фото
- `send_photo_group_by_paths()` - отправка медиа-группы
- `has_file_id()` - проверка наличия file_id

### 3. OptimizedStaticMedia (`app/utils/optimized_dialog_widgets.py`)
Оптимизированный виджет для aiogram-dialog

### 4. Скрипт регенерации (`regenerate_photo_file_ids.py`)
Standalone скрипт для принудительного обновления всех file_id

## Использование

### Автоматическая проверка при старте бота

Система автоматически проверяет новые фото при запуске бота и добавляет их file_id.

### Принудительная регенерация всех file_id

```bash
python regenerate_photo_file_ids.py
```

### Отправка фото в коде бота

#### Простая отправка фото:
```python
from app.utils.photo_utils import get_photo_sender

photo_sender = get_photo_sender()

# Отправка одного фото
await photo_sender.send_photo_by_path(
    bot=bot,
    chat_id=chat_id,
    relative_path="main_menu/main_menu.png",
    caption="Главное меню"
)
```

#### Отправка медиа-группы:
```python
# Отправка группы фото
paths = ["start/1.png", "start/2.png", "start/3.png"]
await photo_sender.send_photo_group_by_paths(
    bot=bot,
    chat_id=chat_id,
    relative_paths=paths
)
```

#### Использование в aiogram-dialog:
```python
from app.utils.optimized_dialog_widgets import create_optimized_static_media

Window(
    create_optimized_static_media("main_menu/main_menu.png"),
    # ... остальные виджеты
)
```

#### Оптимизированные медиа-группы:
```python
from app.bot.assets.media_groups.media_groups import compose_media_group_optimized

# Создание оптимизированной медиа-группы
paths = ["start/1.png", "start/2.png", "start/3.png"]
media_group = compose_media_group_optimized(paths, caption="Приветствие")
messages = await bot.send_media_group(chat_id, media_group.build())
```

## Конфигурация

### Настройки в коде
```python
# Целевой чат для получения file_id (ваш личный чат)
TARGET_CHAT_ID = 257026813

# Папка с изображениями
IMAGES_DIR = "app/bot/assets/images"

# Файл для хранения file_id
FILE_ID_STORAGE_PATH = "config/photo_file_ids.json"
```

### Структура JSON файла
```json
{
  "main_menu/main_menu.png": "AgACAgIAAxkBAAIC...",
  "support/support.png": "AgACAgIAAxkBAAIC...",
  "start/1.png": "AgACAgIAAxkBAAIC...",
  ...
}
```

## Файловая структура

```
app/
├── services/
│   └── photo_file_id_manager.py     # Основной менеджер file_id
├── utils/
│   ├── photo_utils.py               # Утилиты для отправки фото
│   └── optimized_dialog_widgets.py  # Оптимизированные виджеты
└── bot/assets/
    ├── images/                      # Папка с изображениями
    └── media_groups/
        └── media_groups.py          # Оптимизированные медиа-группы

config/
└── photo_file_ids.json              # Хранилище file_id

regenerate_photo_file_ids.py         # Скрипт принудительной регенерации
```

## Логирование

Система ведет подробные логи:
- ✅ Успешная отправка через file_id
- ⚠️ Fallback на отправку файлов
- ❌ Ошибки при отправке
- 🔍 Процесс проверки новых файлов

## Преимущества

1. **Скорость**: Мгновенная отправка через file_id
2. **Надежность**: Автоматический fallback на файлы
3. **Автоматизация**: Проверка новых файлов при старте
4. **Простота**: Легкая интеграция в существующий код
5. **Обратная совместимость**: Старый код продолжает работать

## Миграция существующего кода

### Замена StaticMedia:
```python
# Было:
StaticMedia(path="app/bot/assets/images/main_menu/main_menu.png")

# Стало:
create_optimized_static_media("main_menu/main_menu.png")
```

### Замена медиа-групп:
```python
# Было:
compose_media_group([str(p) for p in paths])

# Стало:
compose_media_group_optimized(relative_paths)
```

## Мониторинг

### Проверка статистики:
```python
from app.utils.photo_utils import get_photo_sender

photo_sender = get_photo_sender()
stats = photo_sender.get_stats()
print(f"Загружено file_id: {stats['total_photos']}")
```

### Проверка наличия file_id:
```python
if photo_sender.has_file_id("main_menu/main_menu.png"):
    print("file_id доступен")
```

## Безопасность

- file_id привязаны к конкретному боту
- Регулярное обновление при изменении файлов
- Graceful fallback при ошибках
- Не влияет на работу бота при отсутствии file_id
