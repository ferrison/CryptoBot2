from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from db import engine
from handlers.content_plan import choosing_setting
from handlers.post_changing_common import sending_posting_date, choosing_post
from handlers.new_post.router import new_post_router
from handlers.new_post.state import NewPost
from keyboards import common
from model.models import Post
from model.services import send_post


posting_method_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="Опубликовать 🔥", callback_data="now"),
     types.InlineKeyboardButton(text="Отложить ⏰", callback_data="delayed")],
    [common.backBtn]
])


async def entry(message_edit_method, state):
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        channels = post.channels
    await message_edit_method(text=f"Пост готов к публикации в следующие каналы: {', '.join(ch.name for ch in channels)}. \n"
                                   f"Опубликуем сейчас или запланируем на потом?",
                              reply_markup=posting_method_kb)
    await state.set_state(NewPost.choosing_posting_method)


@new_post_router.callback_query(NewPost.choosing_posting_method, Text(text='now'))
async def now(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        if post.is_reply and post.reply_post_id and not post.reply_post.is_posted:
            await callback.message.answer("Нельзя опубликовать ответный пост раньше отвечаемого")
            await entry(callback.message.answer, state)
            await callback.answer()
            return
        post.is_draft = False
        post_links = await send_post(post, session)
        if all(m.message_tg_id for m in post.messages):
            post.is_posted = True
        session.commit()
        await callback.message.edit_text(text=f'Пост был успешно опубликован'
                                              f'в следующих каналах: {", ".join(post_links)}',
                                         parse_mode="HTML")
    await callback.answer()
    state_data = await state.get_data()
    if state_data.get('back_to_contentplan'):
        await state.update_data(action='post_choosing',
                                proceed_entry=choosing_setting.entry,
                                stepback_entry=None)
        await choosing_post.entry(callback.message.answer, state)
    else:
        await state.clear()


@new_post_router.callback_query(NewPost.choosing_posting_method, Text(text='delayed'))
async def delayed(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(stepback_entry=entry, terminate=True)
    await sending_posting_date.entry(callback.message.edit_text, state)
    await callback.answer()


@new_post_router.callback_query(NewPost.choosing_posting_method, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_setting.entry(callback.message.edit_text, state)
    await callback.answer()

