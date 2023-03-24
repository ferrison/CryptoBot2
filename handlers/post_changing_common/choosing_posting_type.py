from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from db import engine
from handlers.post_changing_common import choosing_reply_type, choosing_channels
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post

post_type_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="Выбрать каналы", callback_data="select_channels"),
     types.InlineKeyboardButton(text="Ответный пост", callback_data="reply")],
    [common.backBtn]
])


async def entry(message_edit_method, state, stepback_method=None, proceed_method=None):
    if stepback_method:
        await state.update_data(stepback_method=stepback_method)
    if proceed_method:
        await state.update_data(proceed_method=proceed_method)
    await message_edit_method("Теперь выберите метод публикации", reply_markup=post_type_kb)
    await state.set_state(PostChanging.choosing_posting_type)


@post_changing_router.callback_query(PostChanging.choosing_posting_type, Text(text='reply'))
async def reply(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        post.is_reply = True
        session.commit()
    await choosing_reply_type.entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_posting_type, Text(text='select_channels'))
async def select_channels(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        post.is_reply = False
        session.commit()
    await choosing_channels.entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_posting_type, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await state_data['stepback_method'](callback.message.answer, state)
    await callback.answer()
