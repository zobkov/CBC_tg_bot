from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
import logging

from aiogram_dialog import DialogManager, StartMode

from app.bot.states.start import StartSG
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.first_stage import FirstStageSG
from app.bot.states.job_selection import JobSelectionSG

from app.bot.assets.media_groups.media_groups import build_start_media_group
from app.services.google_sync_service import setup_google_sync_service

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def process_command_start(message: Message, dialog_manager: DialogManager):
    media_group = build_start_media_group()
    await message.bot.send_media_group(chat_id=message.chat.id, media=media_group)
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)

@router.message(Command(commands=['menu']))
async def process_command_menu(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=MainMenuSG.main_menu, mode=StartMode.RESET_STACK)

@router.message(Command(commands=['test']))
async def process_command_test(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=JobSelectionSG.select_department, mode=StartMode.RESET_STACK)

@router.message(Command(commands=['sync_to_google']))
async def process_sync_to_google_command(message: Message, **middleware_data):
    """Хендлер команды /sync_to_google для синхронизации одобренных заявок с Google Sheets"""
    ADMIN_IDS = [257026813, 1905792261]
    # Получаем конфигурацию из middleware_data или загружаем заново
    config = middleware_data.get("config")
    if not config:
        from config.config import load_config
        config = load_config()
    
    # Проверяем права доступа (только для админов)
    if  message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        # Отправляем сообщение о начале синхронизации
        status_msg = await message.answer("🔄 Начинаем синхронизацию одобренных заявок с Google Sheets...")
        
        if not config.google:
            await status_msg.edit_text("❌ Google Sheets не настроен в конфигурации")
            return
        
        # Получаем пул соединений базы данных через middleware_data
        dispatcher = middleware_data.get("_dispatcher") or middleware_data.get("dispatcher")
        db_pool = None
        
        if dispatcher:
            db_pool = dispatcher.get("db_applications")
        
        if not db_pool:
            await status_msg.edit_text("❌ Не удалось получить соединение с базой данных")
            return
        
        # Настраиваем сервис синхронизации
        sync_service = await setup_google_sync_service(
            config.google.credentials_path,
            config.google.spreadsheet_id
        )
        
        if not sync_service:
            await status_msg.edit_text("❌ Ошибка настройки сервиса синхронизации")
            return
        
        # Выполняем синхронизацию
        await status_msg.edit_text("📊 Получаем данные одобренных заявок...")
        
        sync_stats = await sync_service.sync_approved_applications(db_pool)
        
        if not sync_stats:
            await status_msg.edit_text("⚠️ Нет данных для синхронизации или произошла ошибка")
            return
        
        # Формируем отчет о синхронизации
        report_lines = ["✅ Синхронизация завершена успешно!\n"]
        report_lines.append("📊 Статистика изменений по отделам:")
        
        total_changes = 0
        for sheet_name, count in sync_stats.items():
            if count > 0:
                report_lines.append(f"• {sheet_name}: {count} изменений")
            else:
                report_lines.append(f"• {sheet_name}: без изменений")
            total_changes += count
        
        if total_changes > 0:
            report_lines.append(f"\n📈 Общее количество изменений: {total_changes}")
        else:
            report_lines.append(f"\n📈 Все данные актуальны, изменений не требуется")
        
        report_lines.append(f"🔗 Ссылка на таблицу: https://docs.google.com/spreadsheets/d/{config.google.spreadsheet_id}")
        
        await status_msg.edit_text("\n".join(report_lines))
        
        logger.info(f"Синхронизация выполнена администратором {message.from_user.id} (@{message.from_user.username})")
        
    except Exception as e:
        logger.error(f"Ошибка выполнения команды sync_to_google: {e}")
        await message.answer(f"❌ Ошибка синхронизации: {str(e)}")