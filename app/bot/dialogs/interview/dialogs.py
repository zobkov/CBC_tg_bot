"""
Interview scheduling dialog
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button, Group, Select, ScrollingGroup, 
    Row, Column, Back, Cancel, Start
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from magic_filter import F

from app.bot.states.interview import InterviewSG
from app.bot.states.main_menu import MainMenuSG
from .getters import (
    get_user_approved_department,
    get_available_dates, 
    get_available_timeslots,
    get_current_booking,
    get_selected_timeslot_info,
    get_reschedule_timeslots,
    get_reschedule_timeslot_info
)
from .handlers import (
    on_date_selected,
    on_timeslot_selected,
    on_confirm_booking,
    on_cancel_booking,
    on_back_to_dates,
    on_reschedule_request,
    on_reschedule_date_selected,
    on_reschedule_timeslot_selected,
    on_confirm_reschedule,
    on_cancel_reschedule,
    on_cancel_interview_request,
    on_confirm_cancel_interview,
    on_cancel_interview_cancellation
)


interview_dialog = Dialog(
    # Main interview menu
    Window(
        Multi(
            Const("🎯 <b>Запись на интервью</b>\n"),
            Format("Вы прошли во второй этап отбора на позицию в отделе {approved_department}!\n", when="has_approval"),
            Const("❌ К сожалению, вы не прошли во второй этап отбора.", when=~F["has_approval"]),
            Const("Тетерь необходимо записаться на интервью с менеджером вашего отдела.\n", when="has_approval"),
            Format("📅 <b>Ваша текущая запись:</b> {booking_date} в {booking_time}", 
                   when=F["has_booking"] & F["has_approval"]),
            sep="\n"
        ),
        Group(
            Start(
                Const("📅 Записаться на интервью"),
                id="schedule_interview",
                state=InterviewSG.date_selection,
                when=~F["has_booking"] & F["has_approval"]
            ),
            Button(
                Const("📝 Перенести интервью"),
                id="reschedule_interview",
                on_click=on_reschedule_request,
                when=F["has_booking"] & F["has_approval"]
            ),
            Button(
                Const("❌ Отменить интервью"),
                id="cancel_interview",
                on_click=on_cancel_interview_request,
                when=F["has_booking"] & F["has_approval"]
            ),
            Start(
                Const("🏠 Главное меню"),
                id="main_menu",
                state=MainMenuSG.main_menu
            ),
            width=1
        ),
        state=InterviewSG.main_menu,
        getter=[get_user_approved_department, get_current_booking],
    ),
    
    # Date selection
    Window(
        Multi(
            Const("📅 <b>Выберите день для интервью</b>\n"),
            Const("Доступные дни:"),
            sep="\n"
        ),
        Group(
            Select(
                Format("{item[display]}"),
                id="date_select",
                item_id_getter=lambda item: item["value"],
                items="dates",
                on_click=on_date_selected
            ),
            width=1
        ),
        Back(Const("🔙 Назад")),
        state=InterviewSG.date_selection,
        getter=get_available_dates,
    ),
    
    # Time slot selection
    Window(
        Multi(
            Format("🕐 <b>Выберите время для интервью</b>\n"),
            Format("📅 День: {selected_date_display}\n"),
            Format("Доступно временных слотов: {total_slots}"),
            sep="\n"
        ),
        ScrollingGroup(
            Select(
                Format("{item[display]}"),
                id="timeslot_select",
                item_id_getter=lambda item: item["value"],
                items="timeslots",
                on_click=on_timeslot_selected
            ),
            id="timeslots_scroll",
            width=2,
            height=6
        ),
        Row(
            Button(
                Const("🔙 Другой день"),
                id="back_to_dates",
                on_click=on_back_to_dates
            ),
            Back(Const("🏠 Главное меню"))
        ),
        state=InterviewSG.time_selection,
        getter=get_available_timeslots,
    ),
    
    # Booking confirmation
    Window(
        Multi(
            Const("✅ <b>Подтверждение записи</b>\n"),
            Format("📅 Дата: {timeslot_info[date]}"),
            Format("🕐 Время: {timeslot_info[time]}\n"),
            Const("Подтвердите запись на интервью:"),
            sep="\n"
        ),
        Row(
            Button(
                Const("✅ Подтвердить"),
                id="confirm_booking",
                on_click=on_confirm_booking
            ),
            Button(
                Const("❌ Отменить"),
                id="cancel_booking",
                on_click=on_cancel_booking
            )
        ),
        state=InterviewSG.confirmation,
        getter=get_selected_timeslot_info,
    ),
    
    # Success state
    Window(
        Multi(
            Const("🎉 <b>Запись успешно создана!</b>\n"),
            Const("Ваш интервью назначен. "),
            Const("Менеджер отдела получил уведомление и свяжется с вами "),
            Const("для уточнения деталей.\n"),
            Const("Удачи на интервью! 🍀"),
            sep=""
        ),
        Start(
            Const("🏠 Главное меню"),
            id="main_menu",
            state=MainMenuSG.main_menu
        ),
        state=InterviewSG.success,
    ),
    
    # Reschedule date selection
    Window(
        Multi(
            Const("📅 <b>Перенести интервью</b>\n"),
            Const("Выберите новый день:"),
            sep="\n"
        ),
        Group(
            Select(
                Format("{item[display]}"),
                id="reschedule_date_select",
                item_id_getter=lambda item: item["value"],
                items="dates",
                on_click=on_reschedule_date_selected
            ),
            width=1
        ),
        Back(Const("🔙 Назад")),
        state=InterviewSG.reschedule_date_selection,
        getter=get_available_dates,
    ),
    
    # Reschedule time selection
    Window(
        Multi(
            Format("🕐 <b>Выберите новое время</b>\n"),
            Format("📅 День: {selected_date_display}\n"),
            Format("Доступно временных слотов: {total_slots}"),
            sep="\n"
        ),
        ScrollingGroup(
            Select(
                Format("{item[display]}"),
                id="reschedule_timeslot_select",
                item_id_getter=lambda item: item["value"],
                items="timeslots",
                on_click=on_reschedule_timeslot_selected
            ),
            id="reschedule_timeslots_scroll",
            width=2,
            height=6
        ),
        Row(
            Button(
                Const("🔙 Другой день"),
                id="back_to_reschedule_dates",
                on_click=lambda c, b, m: m.switch_to(InterviewSG.reschedule_date_selection)
            ),
            Button(
                Const("❌ Отменить"),
                id="cancel_reschedule",
                on_click=on_cancel_reschedule
            )
        ),
        state=InterviewSG.reschedule_time_selection,
        getter=get_reschedule_timeslots,
    ),
    
    # Reschedule confirmation
    Window(
        Multi(
            Const("✅ <b>Подтверждение переноса</b>\n"),
            Format("📅 Новая дата: {timeslot_info[date]}"),
            Format("🕐 Новое время: {timeslot_info[time]}\n"),
            Const("Подтвердите перенос интервью:"),
            sep="\n"
        ),
        Row(
            Button(
                Const("✅ Подтвердить"),
                id="confirm_reschedule", 
                on_click=on_confirm_reschedule
            ),
            Button(
                Const("❌ Отменить"),
                id="cancel_reschedule_final",
                on_click=on_cancel_reschedule
            )
        ),
        state=InterviewSG.reschedule_confirmation,
        getter=get_reschedule_timeslot_info,
    ),
    
    # Cancel interview confirmation
    Window(
        Multi(
            Const("❌ <b>Подтверждение отмены</b>\n"),
            Format("📅 Текущая запись: {booking_date} в {booking_time}\n"),
            Const("⚠️ Вы уверены, что хотите отменить запись на интервью?\n"),
            Const("После отмены вы сможете записаться на новое время."),
            sep="\n"
        ),
        Row(
            Button(
                Const("❌ Да, отменить"),
                id="confirm_cancel_interview", 
                on_click=on_confirm_cancel_interview
            ),
            Button(
                Const("↩️ Назад"),
                id="cancel_interview_cancellation",
                on_click=on_cancel_interview_cancellation
            )
        ),
        state=InterviewSG.cancel_confirmation,
        getter=get_current_booking,
    )
)