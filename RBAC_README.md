# Система ролей для CBC Crew Selection Bot

## Описание

Реализована полнофункциональная система контроля доступа на основе ролей (RBAC) для телеграм-бота CBC Crew Selection Bot.

## Роли в системе

- **ADMIN** - Администраторы (полный доступ, управление ролями)
- **STAFF** - Сотрудники (работа с заявками, модерация)
- **VOLUNTEER** - Волонтёры (помощь пользователям, поддержка)
- **GUEST** - Гости (подача заявок, базовый функционал)
- **BANNED** - Заблокированные пользователи

## Архитектура

### Компоненты системы

1. **Enum ролей** (`app/enums/roles.py`)
2. **Миграции БД** (`migrations/015_add_roles_system.sql`)
3. **Модели данных** (`app/infrastructure/database/models/users.py`)
4. **Методы БД** (`app/infrastructure/database/database/users.py`)
5. **Middleware** (`app/bot/middlewares/rbac.py`)
6. **Фильтры** (`app/bot/filters/rbac.py`)
7. **Роутеры** (`app/bot/routers/`)
8. **Валидаторы диалогов** (`app/bot/dialogs/access.py`)
9. **Система аудита** (`app/utils/audit.py`)

### Поток данных

```
Telegram Event → UserCtxMiddleware → Router Filters → Handler → Dialog Validator
      ↓                 ↓                   ↓            ↓           ↓
  get_event_user    load_user_roles    HasRole    check_roles   RolesValidator
      ↓                 ↓                   ↓            ↓           ↓
   Redis Cache      set roles in       Filter by    Process      Allow/Deny
                     context           role access   request      dialog access
```

## Внедрение

### 1. Выполнение миграций

```bash
# Примените миграцию для добавления системы ролей
python run_applications_migrations.py
```

### 2. Настройка администраторов

В `.env` файле укажите ID первых администраторов:
```env
ADMIN_IDS=123456789,987654321
```

Выполните скрипт установки:
```bash
python scripts/setup_initial_admins.py setup
```

Проверьте результат:
```bash
python scripts/setup_initial_admins.py show
```

### 3. Запуск бота

Система ролей автоматически активируется при запуске:
```bash
python main.py
```

## Использование

### Командное управление ролями (для админов)

```bash
# Информация о себе
/whoami

# Выдача роли (ответ на сообщение пользователя)
/grant staff

# Выдача роли по ID
/grant volunteer 123456789

# Отзыв роли
/revoke staff 123456789

# Административная панель
/admin_panel
```

### Программное управление ролями

```python
# В обработчиках
async def some_handler(message: Message, db=None, current_user=None, roles: set[str] = None):
    # Проверка роли
    if "admin" in roles:
        await message.answer("Вы администратор!")
    
    # Работа с БД
    await db.users.add_user_role(user_id=123, role="staff")
    await db.users.remove_user_role(user_id=123, role="guest")
```

### Фильтрация роутеров

```python
from app.bot.filters.rbac import HasRole
from app.enums.roles import Role

router = Router(name="admin")
router.message.filter(HasRole(Role.ADMIN))
router.callback_query.filter(HasRole(Role.ADMIN))

@router.message(HasRole(Role.STAFF, Role.ADMIN))
async def staff_function(message: Message):
    await message.answer("Доступно только сотрудникам и админам")
```

### Ограничение диалогов

```python
from app.bot.dialogs.access import StaffValidator

# При запуске диалога
await dialog_manager.start(
    AdminStates.PANEL,
    access_settings=AccessSettings(
        custom={"validator": StaffValidator()}
    )
)
```

## Функции безопасности

### Защита от флуда

- Автоматическое отслеживание попыток несанкционированного доступа
- Временная блокировка при превышении лимитов (5 попыток за 60 сек)
- Алерты для администраторов

### Кэширование

- Роли пользователей кэшируются в Redis (TTL: 120 сек)
- Автоматическая инвалидация кэша при изменении ролей
- Graceful degradation при недоступности Redis

### Аудит

- Подробное логирование всех действий с ролями
- Отслеживание попыток несанкционированного доступа
- История назначения/отзыва ролей в БД

## Структура файлов

```
app/
├── enums/
│   └── roles.py                    # Enum ролей
├── bot/
│   ├── filters/
│   │   └── rbac.py                # Фильтры для ролей
│   ├── middlewares/
│   │   └── rbac.py                # Middleware пользователей и ролей
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── public.py              # Публичные команды
│   │   ├── guest.py               # Роутер для гостей
│   │   ├── volunteer.py           # Роутер для волонтёров
│   │   ├── staff.py               # Роутер для сотрудников
│   │   └── admin.py               # Роутер для админов
│   └── dialogs/
│       └── access.py              # Валидаторы доступа к диалогам
├── infrastructure/database/
│   ├── models/
│   │   └── users.py               # Модель пользователя с ролями
│   └── database/
│       └── users.py               # Методы работы с ролями в БД
└── utils/
    ├── telegram.py                # Утилиты для работы с Telegram
    └── audit.py                   # Система аудита

migrations/
└── 015_add_roles_system.sql       # Миграция для системы ролей

scripts/
└── setup_initial_admins.py        # Скрипт установки первых админов
```

## Конфигурация

### Переменные окружения

```env
# Список ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# Существующие переменные для Redis и БД
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

DB_APPLICATIONS_HOST=localhost
DB_APPLICATIONS_PORT=5432
DB_APPLICATIONS_NAME=cbc_applications
DB_APPLICATIONS_USER=cbc_user
DB_APPLICATIONS_PASS=your_password
```

### Настройки аудита

В коде можно настроить:
- Лимиты попыток доступа (`forbidden_limit`)
- Окно времени для отслеживания (`window_seconds`)
- Время блокировки (`ban_duration`)
- ID чата для алертов (`alert_chat_id`)

## Миграция с существующей системы

1. **Резервное копирование БД**
2. **Применение миграций** (добавляет новые поля и таблицы)
3. **Установка админов** через скрипт
4. **Постепенный перевод функций** на новую систему ролей
5. **Тестирование** всех критических путей

## Мониторинг и отладка

### Логи

Система ведет подробные логи:
- `rbac.audit` - аудит доступа
- Основные логи бота - действия с ролями

### Диагностика

```bash
# Проверка ролей пользователя
/whoami

# Для админов - системная статистика
/system_stats

# Очистка кэша (админы)
/cache_clear
```

## Развитие системы

### Запланированные улучшения

1. **Permissions** - детализированная система прав
2. **Временные роли** - роли с истечением срока
3. **Роли групп** - массовое управление
4. **Web-интерфейс** - управление через веб
5. **Интеграция с внешними системами** - LDAP, OAuth

### Точки расширения

- `app/enums/roles.py` - добавление новых ролей
- `app/bot/filters/rbac.py` - новые типы фильтров
- `app/utils/audit.py` - расширение аудита
- БД схема поддерживает дополнительные поля

## Troubleshooting

### Частые проблемы

1. **Пользователь не может получить доступ**
   - Проверьте роли: `/whoami`
   - Проверьте кэш Redis
   - Проверьте логи на ошибки БД

2. **Роли не применяются**
   - Перезапустите бота для применения middleware
   - Очистите кэш: `/cache_clear`
   - Проверьте порядок middleware в bot.py

3. **Миграция не применилась**
   - Проверьте права пользователя БД
   - Убедитесь что БД совместима с PostgreSQL JSON
   - Проверьте логи миграций

### Команды диагностики

```bash
# Проверка состояния БД
python -c "
import asyncio
from scripts.setup_initial_admins import show_current_admins
asyncio.run(show_current_admins())
"

# Проверка Redis
redis-cli ping

# Просмотр логов
tail -f app/logs/bot.log | grep -i rbac
```