from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from db import engine
from handlers.tags import choosing_tag
from handlers.tags.router import tags_router
from handlers.tags.state import Tags
from keyboards import common
from model.models import Tag


async def entry(message_edit_method, state):
    await message_edit_method("Введите название нового тега (без знаков %)", reply_markup=common.simple_stepback_kb())
    await state.set_state(Tags.sending_tag)


@tags_router.message(Tags.sending_tag)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        if tag := session.query(Tag).filter_by(user_tg_id=state_data['user_id'], placeholder=message.html_text.lower()).first():
            await message.answer(f"У вас уже есть тег %{tag.placeholder}%. Добавление невозможно")
            await entry(message.answer, state)
        else:
            tag = Tag(user_tg_id=state_data['user_id'], placeholder=message.html_text.lower())
            session.add(tag)
            session.commit()
            await message.answer("Тег добавлен")
            await choosing_tag.entry(message.answer, state)


@tags_router.callback_query(Tags.sending_tag, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_tag.entry(callback.message.answer, state)
    await callback.answer()
