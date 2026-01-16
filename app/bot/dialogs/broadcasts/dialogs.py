import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Row, Start, SwitchTo, Cancel, Group, Select
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.text import Const, Format


from .getters import *
from .handlers import *

from .states import BroadcastMenuSG

_MAIN_MENU_TEXT = """
<b>Разрешения на рассылку</b>
Чтобы подписаться или отписаться на рассылку, нажми на соответствующую кнопку 
"""



broadcast_menu_dialog = Dialog(
    # =============
    # MAIN
    Window(
        Format(_MAIN_MENU_TEXT),
        Format("{broadcast_subscription_status}"),
        Group(
            Select(
                Format("{item[0]}"),
                id="broadcast_selection",
                items="broadcasts",
                item_id_getter=operator.itemgetter(1),
                on_click=on_broadcast_selected,
            ),
            width=2,
        ),
        Cancel(Const("⬅️ Назад")),

        getter=[get_broadcast_subscriptions, get_broadcasts_names],
        state=BroadcastMenuSG.MAIN,
    ),


    # =============
)
