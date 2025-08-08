# 🚨 Google Drive: Решение проблемы с Service Account

## ❌ **Проблема**
```
Service Accounts do not have storage quota. 
Leverage shared drives or use OAuth delegation instead.
```

## 💡 **Решения**

### 🥇 **Решение 1: Использовать Google Shared Drive (Рекомендуется)**

1. **Создайте Shared Drive:**
   - Перейдите в Google Drive
   - Нажмите "Создать" → "Общий диск" 
   - Назовите его "КБК Резюме"

2. **Добавьте Service Account в Shared Drive:**
   - Откройте созданный Shared Drive
   - Нажмите "Управление участниками"
   - Добавьте email вашего Service Account из `google_credentials.json`
   - Дайте права "Редактор" или "Администратор"

3. **Создайте папку в Shared Drive:**
   - В Shared Drive создайте папку "Резюме_КБК26"
   - Скопируйте ID папки из URL (часть после `/folders/`)

4. **Обновите конфигурацию:**
   ```bash
   # В .env файле обновите GOOGLE_DRIVE_FOLDER_ID
   GOOGLE_DRIVE_FOLDER_ID=новый_id_папки_из_shared_drive
   ```

### 🥈 **Решение 2: OAuth 2.0 (Для разработки)**

1. **Создайте OAuth 2.0 credentials:**
   - Google Cloud Console → APIs & Services → Credentials
   - Создайте "OAuth 2.0 Client ID"
   - Тип приложения: "Desktop application"

2. **Обновите код** для использования OAuth вместо Service Account

### 🥉 **Решение 3: Временное отключение Google Drive**

```bash
# В .env файле закомментируйте:
# GOOGLE_DRIVE_FOLDER_ID=1eBZayV7F3jdToW-6hCeLPYYW-k0eUCih
```

Бот будет работать, сохраняя файлы только локально.

## ✅ **Проверка решения**

После настройки Shared Drive бот должен успешно загружать файлы:
```
✅ Файл успешно загружен в Google Drive: https://drive.google.com/file/d/...
```

## 🔧 **Дополнительная информация**

- Service Account не имеют собственного Google Drive
- Shared Drive принадлежат организации, а не пользователю
- OAuth позволяет использовать личный Google Drive пользователя

## 📞 **Поддержка**

Если проблема не решается:
1. Проверьте права Service Account в Shared Drive
2. Убедитесь, что Google Drive API включен
3. Проверьте правильность ID папки
