# Scripts Directory

Этот каталог содержит вспомогательные скрипты для управления ботом CBC Crew Selection Bot.

## Структура папок

### `broadcasts/`
Содержит скрипты для рассылки сообщений пользователям и связанные CSV файлы с данными:

**Скрипты рассылки:**
- `add_task_status_broadcast.py` - Добавление рассылки о статусе задач
- `send_broadcast_to_accepted.py` - Рассылка принятым кандидатам
- `send_broadcast_to_all.py` - Рассылка всем пользователям
- `send_final_task_reminder.py` - Напоминание о финальных задачах
- `send_interview_reminder.py` - Напоминание о собеседованиях
- `send_stage3_broadcast.py` - Рассылка для 3-го этапа
- `send_task_status_broadcast.py` - Рассылка статуса задач

**CSV файлы:**
- Различные файлы с данными для рассылок и анализа

### `utils/`
Содержит служебные скрипты для администрирования и обслуживания системы:

**Управление данными:**
- `analyze_interview_bookings.py` - Анализ записей на собеседования
- `check_config_state.py` - Проверка состояния конфигурации
- `compare_evaluated_applications.py` - Сравнение оцененных заявок
- `export_applications.py` - Экспорт заявок
- `final_analysis_report.py` - Финальный отчет анализа

**Системное администрирование:**
- `clear_caches.py` - Очистка кешей
- `generate_position_file_mapping.py` - Генерация маппинга позиций к файлам
- `manual_google_sync.py` - Ручная синхронизация с Google
- `regenerate_photo_file_ids.py` - Регенерация ID файлов фото
- `regenerate_task_file_ids.py` - Регенерация ID файлов задач
- `run_applications_migrations.py` - Запуск миграций БД
- `setup_google_sheets.py` - Настройка Google Sheets

**Управление данными пользователей:**
- `manage_timeslots.py` - Управление временными слотами
- `populate_evaluated_applications.py` - Заполнение оцененных заявок
- `populate_interview_timeslots.py` - Заполнение временных слотов собеседований
- `update_approved_status.py` - Обновление статуса одобрения
- `update_interview_timeslots.py` - Обновление временных слотов собеседований

## Использование

Все скрипты должны запускаться из корневой директории проекта:

```bash
# Пример использования утилит
python scripts/utils/check_config_state.py

# Пример использования рассылок
python scripts/broadcasts/send_broadcast_to_all.py
```

**Важно:** Перед запуском любых скриптов убедитесь, что:
1. Активировано виртуальное окружение
2. Настроены переменные окружения (файл `.env`)
3. Доступна база данных и Redis