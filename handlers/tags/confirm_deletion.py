from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from db import engine
from handlers.tags import choosing_setting, choosing_tag
from handlers.tags.router import tags_router
from handlers.tags.state import Tags
from keyboards import common
from model.models import Tag


def confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=common.NextCallback(),
    )
    builder.button(
        text="Назад",
        callback_data=common.StepbackCallback(),
    )

    return builder.as_markup()


async def entry(message_edit_method, state):
    await message_edit_method(text="Вы уверены, что хотите удалить тег?", reply_markup=confirm_kb())
    await state.set_state(Tags.confirm_deletion)


@tags_router.callback_query(Tags.confirm_deletion, common.NextCallback.filter())
async def proceed(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        tag = session.query(Tag).filter_by(id=state_data['tag_id']).one()
        session.delete(tag)
        session.commit()
    await callback.message.answer("Тег успешно удален")
    await choosing_tag.entry(callback.message.answer, state)


@tags_router.callback_query(Tags.confirm_deletion, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_setting.entry(callback.message.edit_text, state)
    await callback.answer()
