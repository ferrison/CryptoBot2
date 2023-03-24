from aiogram.dispatcher.fsm.state import StatesGroup, State


class ContentPlan(StatesGroup):
    watching_post = State()
    choosing_post = State()
    choosing_post_setting = State()
    choosing_setting = State()
    confirm_deletion = State()
    sending_media = State()
    sending_posting_date = State()
    sending_post_text = State()
