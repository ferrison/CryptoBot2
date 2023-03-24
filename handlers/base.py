from datetime import date

from aiogram import Router, types
from aiogram.dispatcher.filters import BaseFilter
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import Session

from db import engine
from handlers.content_plan import choosing_setting
from handlers.new_post import sending_post
from handlers.post_changing_common import choosing_post
from handlers.tags import choosing_tag
from model.models import User

base_router = Router()


class NotIsPrivatePerson(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        with Session(engine) as session:
            manager = session.query(User).filter_by(tg_id=message.from_user.id).first()
        if manager:
            return False
        return True


@base_router.message(NotIsPrivatePerson())
async def not_authorized(message: types.Message):
    await message.answer("У вас нет прав для работы с этим ботом")


@base_router.message(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer(f"Привет, {message.from_user.full_name}!\nВесь функционал ты можешь посмотреть в меню слева")


@base_router.message(commands=['cancel'])
async def cancel_all_actions(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@base_router.message(commands=['tags'])
async def tags(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(user_id=message.from_user.id)
    await choosing_tag.entry(message.answer, state)


@base_router.message(commands=['contentplan'])
async def contentplan(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(current_date=date.today(),
                            user_id=message.from_user.id,
                            action='post_choosing',
                            proceed_entry=choosing_setting.entry)
    await choosing_post.entry(message.answer, state)


@base_router.message(commands=['newpost'])
async def new_post_data(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(user_id=message.from_user.id)
    await sending_post.entry(message.answer, state)


