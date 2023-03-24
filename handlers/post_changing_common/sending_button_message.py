from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common import choosing_button_setting
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post, Button
from model.services import url_buttons_inflated_kb


async def entry(message_edit_method, state):
    with Session(engine) as session:
        button_id = (await state.get_data())['button_id']
        button = session.query(Button).filter_by(id=button_id).one()
        await message_edit_method(text="Чтобы изменить кнопку, пришлите ее ссылку и название в следующем формате:\n"
                                       "<< Ссылка - название кнопки >>\n"
                                       "Пример: \n"
                                       f"{button.link} - {button.text}",
                                  disable_web_page_preview=True, reply_markup=common.simple_stepback_kb())
    await state.set_state(PostChanging.sending_button_message)


@post_changing_router.message(PostChanging.sending_button_message)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        button_id = state_data['button_id']
        post_id = state_data['post_id']
        button = session.query(Button).filter_by(id=button_id).one()
        post = session.query(Post).filter_by(id=post_id).one()
        if post.type == 'mediagroup' and post.is_posted:
            await message.answer(text="Нельзя изменить кнопки у альбома опубликованного без кнопок")
            await state_data['proceed_method'](message.answer, state)
            return
        link_part, name_part = message.html_text.split(" - ")
        button.link = link_part
        button.text = name_part
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                await bot.edit_message_reply_markup(chat_id=msg.channel_tg_id,
                                                    message_id=msg.get_buttons_message_tg_id(),
                                                    reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session))
        session.commit()
    await message.answer(text="Кнопка изменена")
    await choosing_button_setting.entry(message.answer, state)


@post_changing_router.callback_query(PostChanging.sending_button_message, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_button_setting.entry(callback.message.edit_text, state)
    await callback.answer()
