"""Dialog definition для Ярмарки карьеры."""
import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Cancel, Group, Select, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from .getters import get_companies, get_company_detail, get_company_vacancies, get_tracks
from .handlers import on_company_selected, on_track_selected
from .states import CareerFairSG

_MAIN_TEXT = """🏪 <b>Ярмарка карьеры КБК'26</b>

Здесь собраны компании-лидеры рынка с актуальными вакансиями и стажировками.

Выбери направление:"""

career_fair_dialog = Dialog(
    # =============
    # MAIN — выбор трека
    # =============
    Window(
        Const(_MAIN_TEXT),
        Group(
            Select(
                Format("{item[0]}"),
                id="track_sel",
                items="tracks",
                item_id_getter=operator.itemgetter(1),
                on_click=on_track_selected,
            ),
            width=1,
        ),
        Cancel(Const("◀️ Назад")),
        getter=get_tracks,
        state=CareerFairSG.MAIN,
    ),

    # =============
    # COMPANY_LIST — компании в треке
    # =============
    Window(
        Format("📋 <b>{track_name}</b>\n\nВыбери компанию:"),
        Group(
            Select(
                Format("{item[0]}"),
                id="company_sel",
                items="companies",
                item_id_getter=operator.itemgetter(1),
                on_click=on_company_selected,
            ),
            width=1,
        ),
        Back(Const("◀️ Назад")),
        getter=get_companies,
        state=CareerFairSG.COMPANY_LIST,
    ),

    # =============
    # COMPANY_DETAIL — логотип + описание компании
    # Отдельное окно от вакансий, чтобы не превышать лимит подписи к фото (1024 символа)
    # =============
    Window(
        DynamicMedia("media", when="has_image"),
        Format("{company_header}"),
        SwitchTo(
            Const("📋 Вакансии"),
            id="to_vacancies",
            state=CareerFairSG.COMPANY_VACANCIES,
            when="has_vacancies",
        ),
        Back(Const("◀️ Назад")),
        getter=get_company_detail,
        state=CareerFairSG.COMPANY_DETAIL,
    ),

    # =============
    # COMPANY_VACANCIES — список вакансий со ссылками (текст, лимит 4096 символов)
    # =============
    Window(
        Format("{vacancies_text}"),
        Back(Const("◀️ Назад")),
        getter=get_company_vacancies,
        state=CareerFairSG.COMPANY_VACANCIES,
    ),
)
