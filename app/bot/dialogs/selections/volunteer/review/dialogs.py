"""Aiogram Dialog definition for the volunteer review menu."""

import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Select
from aiogram_dialog.widgets.text import Const, Format

from .getters import (
    get_app_detail_data,
    get_page_data,
    get_page_select_data,
    get_video_data,
)
from .handlers import (
    on_app_selected,
    on_back_to_page,
    on_back_to_pages,
    on_detail_next,
    on_detail_prev,
    on_next_page,
    on_page_selected,
    on_prev_page,
    on_sync_to_sheets,
    on_to_videos,
    on_toggle_reviewed,
    on_video_back,
)
from .states import VolReviewSG

volunteer_review_dialog = Dialog(

    # ── PAGE SELECT ──────────────────────────────────────────────────────────
    Window(
        Format("📋 <b>Просмотр заявок (всего: {total})</b>\n\nВыбери страницу:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="rev_page_sel",
                items="pages",
                item_id_getter=operator.itemgetter(0),
                on_click=on_page_selected,
            ),
        ),
        Button(
            Const("🔄 Синхр. с Google Sheets"),
            id="rev_sync_sheets",
            on_click=on_sync_to_sheets,
        ),
        getter=get_page_select_data,
        state=VolReviewSG.PAGE_SELECT,
    ),

    # ── PAGE ──────────────────────────────────────────────────────────────────
    Window(
        Format("📄 <b>{page_label}</b>\n\nВыбери участника:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="rev_app_sel",
                items="apps",
                item_id_getter=operator.itemgetter(0),
                on_click=on_app_selected,
            ),
        ),
        Row(
            Button(
                Const("◀️ Пред."),
                id="rev_prev",
                on_click=on_prev_page,
                when="has_prev",
            ),
            Button(
                Const("След. ▶️"),
                id="rev_next",
                on_click=on_next_page,
                when="has_next",
            ),
        ),
        Button(Const("⬅️ К страницам"), id="rev_to_pages", on_click=on_back_to_pages),
        getter=get_page_data,
        state=VolReviewSG.PAGE,
    ),

    # ── APP DETAIL ────────────────────────────────────────────────────────────
    Window(
        Format("{detail_text}"),
        Row(
            Button(Const("⬅️ К списку"), id="rev_detail_back", on_click=on_back_to_page),
            Button(
                Const("🎥 Видео ▶️"),
                id="rev_detail_video",
                on_click=on_to_videos,
                when="has_videos",
            ),
        ),
        Row(
            Button(
                Const("◀️ Назад"),
                id="rev_detail_pg_prev",
                on_click=on_detail_prev,
                when="has_detail_prev",
            ),
            Button(
                Const("Далее ▶️"),
                id="rev_detail_pg_next",
                on_click=on_detail_next,
                when="has_detail_next",
            ),
        ),
        Row(
            Button(
                Const("❌ Просмотрено"),
                id="rev_mark_reviewed",
                on_click=on_toggle_reviewed,
                when="not_is_reviewed",
            ),
            Button(
                Const("✅ Просмотрено"),
                id="rev_mark_not_reviewed",
                on_click=on_toggle_reviewed,
                when="is_reviewed",
            ),
        ),
        getter=get_app_detail_data,
        state=VolReviewSG.APP_DETAIL,
    ),

    # ── VIDEO ─────────────────────────────────────────────────────────────────
    Window(
        Format("{video_header}"),
        Button(Const("⬅️ Назад"), id="rev_video_back", on_click=on_video_back),
        getter=get_video_data,
        state=VolReviewSG.VIDEO,
    ),
)
