# Исправление передачи данных между диалогами

## Проблема
При переходе из диалога выбора вакансий к диалогу подтверждения заявки данные о приоритетах пропадали. 

Логи показывали:
```
DEBUG: dialog_data before processing = {'selected_department': 'program', 'priority_1_department': 'creative', 'priority_1_position': '1', ...}
DEBUG: get_form_summary - dialog_data keys = []
DEBUG: get_form_summary - final priorities_summary = '❌ Вакансии не выбраны'
```

## Причина
При использовании `StartMode.RESET_STACK` данные передаются через параметр `data`, но становятся доступными как `dialog_manager.start_data`, а не как `dialog_manager.dialog_data`.

## Решение

### 1. В handlers.py (уже было исправлено)
```python
# Передаем ВСЕ данные в новый диалог явно
all_data = dict(dialog_manager.dialog_data)
await dialog_manager.start(FirstStageSG.confirmation, mode=StartMode.RESET_STACK, data=all_data)
```

### 2. В first_stage/getters.py
Изменили функцию `get_form_summary()` для корректного получения данных:

```python
async def get_form_summary(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    dialog_data = dialog_manager.dialog_data
    
    # Получаем данные переданные через start_data (например, от диалога выбора вакансий)
    start_data = dialog_manager.start_data or {}
    
    # Объединяем данные: приоритет у dialog_data, но start_data может дополнить
    combined_data = {**start_data, **dialog_data}
    
    # Используем combined_data вместо dialog_data для получения всех данных
    for i in range(1, 4):
        dept_key = combined_data.get(f"priority_{i}_department")
        pos_index = combined_data.get(f"priority_{i}_position")
        # ...
```

## Ключевые изменения
1. **start_data vs dialog_data**: При `StartMode.RESET_STACK` данные передаются через `start_data`
2. **combined_data**: Объединяем `start_data` и `dialog_data` для получения полной картины
3. **Отладка**: Добавили логирование ключей всех источников данных

## Результат
Теперь приоритеты корректно отображаются на экране подтверждения заявки.
