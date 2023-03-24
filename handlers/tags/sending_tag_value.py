from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from db import engine
from handlers.tags import choosing_setting
from handlers.tags.router import tags_router
from handlers.tags.state import Tags
from keyboards import common
from model.models import TagValue


async def entry(message_edit_method, state):
    await message_edit_method("Введите новое значение для тега", reply_markup=common.simple_stepback_kb())
    await state.set_state(Tags.sending_tag_value)


@tags_router.message(Tags.sending_tag_value)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        tag_value = TagValue(tag_id=state_data['tag_id'],
                             channel_tg_id=state_data['channel_id'],
                             value=message.html_text)
        session.add(tag_value)
        session.commit()
    await message.answer("Значение тега добавлено!")
    await choosing_setting.entry(message.answer, state)


@tags_router.callback_query(Tags.sending_tag_value, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_setting.entry(callback.message.edit_text, state)
    await callback.answer()
