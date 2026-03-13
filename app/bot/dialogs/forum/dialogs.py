"""Forum section dialog — all windows and the Dialog object."""
from __future__ import annotations

import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Cancel,
    Group,
    Row,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.forum.getters import (
    get_change_track,
    get_forum_main,
    get_tracks_info,
)
from app.bot.dialogs.forum.handlers import on_track_selected
from app.bot.dialogs.forum.states import ForumSG
from app.bot.dialogs.grants.states import GrantsSG
from app.bot.dialogs.settings.states import SettingsSG

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
_MAIN_TEXT = (
    "<b>Всероссийский студенческий форум «Китай Бизнес Культура» (КБК)</b> — ежегодная "
    "федеральная очная и онлайн-площадка, объединяющая студентов и молодых специалистов "
    "для нетворкинга, карьерного развития и практического изучения взаимодействия России "
    "и Китая через образовательные, культурные и бизнес-инициативы.\n\n"
    "<b>Твой трек</b>  — {user_track}\n"
    "<b>Твой куратор</b> — {track_curator}"
)

# ---------------------------------------------------------------------------
# TRACKS INFO
# ---------------------------------------------------------------------------
_TRACKS_INFO_TEXT = "<b>Треки КБК'26</b>\n\n{tracks_info}"

# ---------------------------------------------------------------------------
# CHANGE TRACK
# ---------------------------------------------------------------------------
_CHANGE_TRACK_TEXT = (
    "<b>Сменить трек</b>\n\n"
    "Твой трек: {user_track}\n\n"
    "<b>ВНИМАНИЕ!</b>\n"
    "Количество мест на треке ограничено. Если ты поменяешь свой трек, то мы не гарантируем "
    "возможность смены на изначальный трек."
)

# ---------------------------------------------------------------------------
# WAY
# ---------------------------------------------------------------------------
_WAY_TEXT = (
    "<b>📍 Как добраться до кампуса ВШМ СПбГУ</b>\n\n"
    "Адрес: Петергоф, Санкт-Петербургское ш., 109\n\n"
    "🚆 <b>Электричка</b>\n"
    "Станция «Михайловская дача» → 15 минут пешком\n\n"
    "🚇 <b>Метро + автобус</b>\n"
    "Ст. м. «Автово» → автобус до остановки «Гофмейстерская» → 5 минут пешком\n\n"
    "🚗 <b>На машине</b>\n"
    "Два пути:\n"
    "— бесплатно (возможны пробки)\n"
    "— по ЗСД (быстро, но платно — около 500₽)\n"
    "На территории кампуса имеется парковка – необходимо передать номер машины при регистрации "
    "на форум. Также машину можно припарковать на ул. Гофмейстерская."
)


# ===========================================================================
# Dialog
# ===========================================================================
forum_dialog = Dialog(
    # -----------------------------------------------------------------------
    # 1. MAIN
    # -----------------------------------------------------------------------
    Window(
        Format(_MAIN_TEXT),
        Row(
            SwitchTo(
                Const("↗️ Информация о треках"),
                id="tracks_info_btn",
                state=ForumSG.tracks_info,
            ),
        ),
        Row(
            SwitchTo(
                Const("🔄 Сменить трек"),
                id="change_track_btn",
                state=ForumSG.change_track,
            ),
        ),
        Row(
            Start(
                Const("🏆 Грантовый конкурс"),
                id="grants_btn",
                state=GrantsSG.MAIN_GENERAL,
            ),
        ),
        Row(
            SwitchTo(
                Const("📍 Как добраться"),
                id="way_btn",
                state=ForumSG.way,
            ),
        ),
        Row(
            Start(
                Const("⚙️ Помощь и настройки"),
                id="settings_btn",
                state=SettingsSG.MAIN,
            ),
            Cancel(Const("⬅️ В главное меню")),
        ),
        state=ForumSG.MAIN,
        getter=get_forum_main,
    ),

    # -----------------------------------------------------------------------
    # 2. TRACKS INFO
    # -----------------------------------------------------------------------
    Window(
        Format(_TRACKS_INFO_TEXT),
        Row(
            SwitchTo(
                Const("🔄 Сменить трек"),
                id="change_track_from_info",
                state=ForumSG.change_track,
            ),
        ),
        Row(
            SwitchTo(
                Const("⬅️ В главное меню"),
                id="back_from_tracks_info",
                state=ForumSG.MAIN,
            ),
        ),
        state=ForumSG.tracks_info,
        getter=get_tracks_info,
    ),

    # -----------------------------------------------------------------------
    # 3. CHANGE TRACK
    # -----------------------------------------------------------------------
    Window(
        Format(_CHANGE_TRACK_TEXT),
        Row(
            SwitchTo(
                Const("↗️ Информация о треках"),
                id="tracks_info_from_change",
                state=ForumSG.tracks_info,
            ),
        ),
        Group(
            Select(
                Format("{item[0]}"),
                id="track_select",
                item_id_getter=operator.itemgetter(1),
                items="tracks",
                on_click=on_track_selected,
            ),
            width=2,
        ),
        Row(
            SwitchTo(
                Const("⬅️ В главное меню"),
                id="back_from_change_track",
                state=ForumSG.MAIN,
            ),
        ),
        state=ForumSG.change_track,
        getter=get_change_track,
    ),

    # -----------------------------------------------------------------------
    # 4. WAY
    # -----------------------------------------------------------------------
    Window(
        Const(_WAY_TEXT),
        Row(
            SwitchTo(
                Const("⬅️ В главное меню"),
                id="back_from_way",
                state=ForumSG.MAIN,
            ),
        ),
        state=ForumSG.way,
    ),
)
