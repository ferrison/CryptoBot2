from aiogram.dispatcher.fsm.state import StatesGroup, State


class PostChanging(StatesGroup):
    sending_posting_date = State()
    sending_reply_message = State()
    sending_post_text = State()
    sending_button_message = State()
    sending_buttons_message = State()
    choosing_reply_type = State()
    choosing_reply_post = State()
    choosing_posting_type = State()
    choosing_channels = State()
    choosing_button_setting = State()
