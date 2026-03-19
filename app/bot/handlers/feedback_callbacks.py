"""
Callback handlers for feedback system and main menu navigation
"""
from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.main.states import MainMenuSG
from app.bot.dialogs.selections.creative.states import CreativeSelectionSG
from app.bot.dialogs.selections.creative.part_2.states import CreativeSelectionPart2SG

from app.bot.dialogs.selections.volunteer.states import VolunteerSelectionSG
from app.bot.dialogs.selections.volunteer.part_2.states import VolSelPart2SG

# Users who receive photographer/translator confirmation notifications
_VOL_NOTIFY_ADMIN_IDS = [257026813]

feedback_callbacks_router = Router()



@feedback_callbacks_router.callback_query(F.data == "go_to_main_menu")
async def go_to_main_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle main menu navigation from inline button"""
    await callback.answer()
    
    # Start main menu dialog
    await dialog_manager.start(
        MainMenuSG.main_menu,
        mode=StartMode.RESET_STACK
    )



@feedback_callbacks_router.callback_query(F.data == "start_staff_menu")
async def start_staff_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle staff menu start from inline button (for approved users)"""
    await callback.answer()
    
    # Redirect to main menu (staff system removed)
    await dialog_manager.start(
        MainMenuSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_guest_menu")
async def start_guest_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle guest menu start from inline button (for declined users)"""
    await callback.answer()
    
    # Start guest menu dialog
    await dialog_manager.start(
        MainMenuSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_creative_selection")
async def start_creative_selection(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle creative selection (casting) start from inline button"""
    await callback.answer()
    
    # Start creative selection dialog
    await dialog_manager.start(
        CreativeSelectionSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_creative_selection_part2")
async def start_creative_selection_part2(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle creative selection part 2 start from broadcast inline button"""
    await callback.answer()
    await dialog_manager.start(
        state=CreativeSelectionPart2SG.question_1,
        mode=StartMode.RESET_STACK
    )

@feedback_callbacks_router.callback_query(F.data == "start_volunteer_selection_part1")
async def start_volunteer_selection_part1(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle volunteer selection part 1 start from broadcast inline button"""
    await callback.answer()
    await dialog_manager.start(
        state=VolunteerSelectionSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_volunteer_selection_part2")
async def start_volunteer_selection_part2(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle volunteer selection part 2 start from broadcast inline button"""
    await callback.answer()
    await dialog_manager.start(
        state=VolSelPart2SG.MAIN,
        mode=StartMode.RESET_STACK
    )


async def _notify_admins(bot: Bot, role: str, confirmed: bool, user: CallbackQuery) -> None:
    """Send confirmation result to admin users."""
    user_obj = user.from_user
    name = user_obj.full_name
    username = f"@{user_obj.username}" if user_obj.username else "нет username"
    answer = "✅ Подтвердил(а)" if confirmed else "❌ Отказал(а)"
    text = (
        f"<b>Ответ на приглашение [{role}]</b>\n\n"
        f"{answer}\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"ID: <code>{user_obj.id}</code>"
    )
    for admin_id in _VOL_NOTIFY_ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception:
            pass


@feedback_callbacks_router.callback_query(F.data == "vol_photo_confirm_yes")
async def vol_photo_confirm_yes(callback: CallbackQuery, bot: Bot):
    """Photographer confirmed participation."""
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Спасибо! Очень рады, что ты решил(а) присоединиться к нашей команде! "
        "Скорее записывай КБК в свой календарь и внимательно следи за чатом в боте. "
        "Мы свяжемся с тобой по завершении общего отбора."
    )
    await _notify_admins(bot, "Фотограф/Видеограф", confirmed=True, user=callback)


@feedback_callbacks_router.callback_query(F.data == "vol_photo_confirm_no")
async def vol_photo_confirm_no(callback: CallbackQuery, bot: Bot):
    """Photographer declined participation."""
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Спасибо за ответ! Очень жаль, надеемся увидеться с тобой в следующий раз! Успехов!"
    )
    await _notify_admins(bot, "Фотограф/Видеограф", confirmed=False, user=callback)


@feedback_callbacks_router.callback_query(F.data == "vol_trans_confirm_yes")
async def vol_trans_confirm_yes(callback: CallbackQuery, bot: Bot):
    """Translator confirmed participation."""
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Спасибо! Очень рады, что ты решил(а) присоединиться к нашей команде! "
        "Скорее записывай КБК в свой календарь и внимательно следи за чатом в боте. "
        "Мы свяжемся с тобой по завершении общего отбора."
    )
    await _notify_admins(bot, "Переводчик", confirmed=True, user=callback)


@feedback_callbacks_router.callback_query(F.data == "vol_trans_confirm_no")
async def vol_trans_confirm_no(callback: CallbackQuery, bot: Bot):
    """Translator declined participation."""
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Спасибо за ответ! Очень жаль, надеемся увидеться с тобой в следующий раз! Успехов!"
    )
    await _notify_admins(bot, "Переводчик", confirmed=False, user=callback)
