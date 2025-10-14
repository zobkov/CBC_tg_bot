# 🛡️ Система управления ролями (RBAC) для CBC Crew Selection Bot

## 📋 Обзор

Комплексная система управления доступом на основе ролей (Role-Based Access Control) для Telegram-бота отбора команды КБК, построенная на aiogram 3.x + aiogram-dialog 2.x.

## 🏗️ Архитектура системы

### 🎭 Роли и иерархия

```
ADMIN (5)      - Полное управление системой
    ↓
STAFF (4)      - Управление участниками и процессами  
    ↓
VOLUNTEER (3)  - Помощь участникам и модерация
    ↓
GUEST (2)      - Базовое взаимодействие с системой
    ↓
BANNED (1)     - Заблокированные пользователи
```

### 📁 Структура файлов

```
app/
├── enums/
│   └── roles.py                    # Определение ролей и иерархии
├── bot/
│   ├── filters/
│   │   └── rbac.py                 # Фильтры доступа по ролям
│   ├── middlewares/
│   │   ├── rbac.py                 # Middleware загрузки ролей
│   │   └── role_validator.py       # Валидация ролей для диалогов
│   ├── routers/
│   │   ├── public.py               # Публичные команды (/start, /help, /whoami)
│   │   ├── guest.py                # Команды для гостей
│   │   ├── volunteer.py            # Команды для волонтёров
│   │   ├── staff.py                # Команды для сотрудников
│   │   └── admin.py                # Административные команды
│   └── dialogs/
│       ├── legacy/                 # Существующие диалоги (временно)
│       ├── guest/                  # Диалоги для гостей
│       ├── volunteer/              # Диалоги для волонтёров
│       └── staff/                  # Диалоги для сотрудников
├── utils/
│   └── audit.py                    # Система аудита изменений ролей
└── infrastructure/
    └── database/
        └── models.py               # Модели данных и контекст
```

### 🛠️ Миграции базы данных

- **015_add_roles_system.sql** - Добавляет поддержку ролей в БД:
  - JSONB поле `roles` в таблице `users`
  - Таблица `user_roles` для аудита изменений
  - Trigger для синхронизации изменений

## 🚀 Основные компоненты

### 1. 🎭 Enum ролей (`app/enums/roles.py`)

```python
from app.enums.roles import Role

# Проверка иерархии
Role.ADMIN.has_privilege_over(Role.STAFF)     # True
Role.VOLUNTEER.has_privilege_over(Role.ADMIN) # False

# Получение всех ролей пользователя (включая вложенные)
Role.STAFF.get_effective_roles()  # [STAFF, VOLUNTEER, GUEST]
```

### 2. 🛡️ Middleware и фильтры

```python
# Фильтр проверки роли
@router.message(HasRole(Role.STAFF))
async def staff_command(message: Message):
    await message.answer("Команда доступна только сотрудникам")

# Фильтр минимальной роли (включает высшие роли)
@router.message(HasMinRole(Role.VOLUNTEER))
async def volunteer_or_higher_command(message: Message):
    await message.answer("Доступно волонтёрам и выше")
```

### 3. 📋 Команды управления

```bash
# Публичные команды (доступны всем)
/start                    # Запуск бота
/help                     # Справка
/whoami                   # Информация о пользователе и ролях

# Административные команды
/grant <role> [user_id]   # Выдача роли
/revoke <role> [user_id]  # Отзыв роли
/system_stats             # Статистика системы
/cache_clear              # Очистка кеша ролей
```

### 4. 🗣️ Диалоги по ролям

- **Гостевые диалоги** - Подача заявок, поддержка
- **Волонтёрские диалоги** - Помощь участникам, модерация
- **Сотрудничество диалоги** - Управление процессами, аналитика

## ⚙️ Настройка и использование

### 1. Применение миграций

```bash
python run_applications_migrations.py
```

### 2. Настройка в bot.py

```python
# Middleware загружается автоматически
dp.update.middleware(UserCtxMiddleware())  # Загрузка контекста пользователя
dp.message.middleware(RoleValidatorMiddleware())  # Валидация ролей

# Роутеры подключаются в порядке приоритета
dp.include_routers(
    public_router,     # Публичные команды
    admin_router,      # Административные функции  
    staff_router,      # Сотрудники
    volunteer_router,  # Волонтёры
    guest_router,      # Гости
)
```

### 3. Кеширование ролей

Роли кешируются в Redis на 120 секунд для оптимизации производительности.

```python
# Автоматическая очистка кеша при изменении ролей
await clear_user_role_cache(user_id)

# Принудительная очистка всего кеша (команда /cache_clear)
```

## 🔧 Система аудита

Все изменения ролей логируются в таблицу `user_roles`:

```sql
SELECT 
    user_id,
    role_name, 
    action,        -- 'granted' или 'revoked'
    changed_by,    -- ID администратора
    created_at
FROM user_roles 
WHERE user_id = 123456789
ORDER BY created_at DESC;
```

## 🧪 Тестирование

Запустите тест системы:

```bash
python3 test_rbac_system.py
```

Тест проверяет:
- ✅ Корректность enum ролей
- ✅ Иерархию и привилегии
- ✅ Импорт фильтров и middleware
- ✅ Работоспособность роутеров
- ✅ Загрузку диалогов

## 📋 Использование в коде

### Проверка ролей в хендлерах

```python
from app.bot.filters.rbac import HasRole, HasMinRole

@router.message(HasRole(Role.ADMIN))
async def admin_only(message: Message, user_ctx: UserContext):
    await message.answer(f"Привет, администратор {user_ctx.role}!")

@router.message(HasMinRole(Role.VOLUNTEER))  
async def volunteer_or_higher(message: Message, user_ctx: UserContext):
    if user_ctx.role == Role.STAFF:
        await message.answer("Добро пожаловать, сотрудник!")
    else:
        await message.answer("Привет, волонтёр!")
```

### Валидация ролей в диалогах

```python
from app.bot.middlewares.role_validator import RoleValidator

# В диалоге
Dialog(
    Window(
        Const("Панель управления"),
        state=AdminSG.MAIN,
    ),
    # Автоматическая проверка роли ADMIN для всех окон диалога
)
```

### Управление ролями

```python
from app.utils.audit import grant_role, revoke_role

# Выдача роли
await grant_role(
    user_id=123456789,
    role=Role.VOLUNTEER,
    changed_by=admin_user_id,
    db_pool=db_pool,
    redis_client=redis
)

# Отзыв роли
await revoke_role(
    user_id=123456789, 
    role=Role.VOLUNTEER,
    changed_by=admin_user_id,
    db_pool=db_pool,
    redis_client=redis
)
```

## 🔒 Безопасность

1. **Middleware блокировки BANNED пользователей** - заблокированные пользователи не могут использовать бота
2. **Кеширование с TTL** - роли кешируются на 120 секунд, автоматически очищаются при изменениях
3. **Аудит изменений** - все изменения ролей логируются с указанием автора
4. **Иерархическая проверка** - высшие роли автоматически включают права нижних

## 🔄 Интеграция с Command фильтрами

Система использует современные Command фильтры aiogram вместо устаревших F.text паттернов:

```python
# Старый способ (убран)
@router.message(F.text == "/command")

# Новый способ  
@router.message(Command("command"))
async def cmd_handler(message: Message, command: CommandObject):
    args = command.args  # Аргументы команды
```

## 📈 Производительность

- **Redis кеширование** - роли кешируются для быстрого доступа
- **Эффективные SQL запросы** - использование JSONB для хранения ролей
- **Lazy loading** - роли загружаются только при необходимости
- **Batch операции** - массовые изменения ролей оптимизированы

## 🎯 Roadmap

- [ ] Web-интерфейс для управления ролями
- [ ] Временные роли с автоматическим истечением  
- [ ] Детальные разрешения внутри ролей
- [ ] Интеграция с внешними системами аутентификации
- [ ] Метрики и аналитика использования ролей

---

🚀 **Система RBAC готова к продакшну!** Все компоненты протестированы и интегрированы.