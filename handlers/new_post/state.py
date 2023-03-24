from aiogram.dispatcher.fsm.state import StatesGroup, State


class NewPost(StatesGroup):
    choosing_posting_method = State()
    choosing_setting = State()
    sending_post = State()
