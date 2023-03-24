from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post
from model.services import get_inflated_text, url_buttons_inflated_kb


async def entry(message_edit_method, state, stepback_method):
    if stepback_method:
        await state.update_data(stepback_method=stepback_method)
    await message_edit_method(text="Пришлите новое описание", reply_markup=common.simple_stepback_kb())
    await state.set_state(PostChanging.sending_post_text)


@post_changing_router.message(PostChanging.sending_post_text)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        post.text = message.html_text
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                if post.type == 'text':
                    await bot.edit_message_text(text=get_inflated_text(post.text, post.manager_tg_id, msg.channel, session),
                                                reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                chat_id=msg.channel_tg_id,
                                                message_id=msg.message_tg_id,
                                                parse_mode="HTML",
                                                disable_web_page_preview=True)
                else:
                    await bot.edit_message_caption(caption=get_inflated_text(post.text, post.manager_tg_id, msg.channel, session),
                                                   reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                   chat_id=msg.channel_tg_id,
                                                   message_id=msg.message_tg_id,
                                                   parse_mode="HTML")
        session.commit()
    await message.answer("Описание было изменено!")
    state_data = await state.get_data()
    await state_data['stepback_method'](message.answer, state)


@post_changing_router.callback_query(PostChanging.sending_post_text, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state_data['stepback_method'](callback.message.answer, state)
    await callback.answer()
