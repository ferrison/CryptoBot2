from aiogram.dispatcher.fsm.state import StatesGroup, State


class Tags(StatesGroup):
    sending_tag = State()
    sending_tag_value = State()
    confirm_deletion = State()
    choosing_setting = State()
    choosing_tag = State()
