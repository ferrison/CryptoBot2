from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common import choosing_button_setting
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Button, Post
from model.services import url_buttons_inflated_kb


async def entry(message_edit_method, state):
    await message_edit_method(text="Чтобы добавить кнопки под постом, пришлите для каждой кнопки ссылку и ее название в следующем формате:\n"
                                   "<< Ссылка - название кнопки >>\n"
                                   "К примеру, добавление 3 кнопок: \n"
                                   "https://telegram.org/ - КнопкаТелеграмм\n"
                                   "https://www.google.ru/ - Кнопка Гугл\n"
                                   "https://www.youtube.com/ - YouTube📱",
                              disable_web_page_preview=True, reply_markup=common.simple_stepback_kb())
    await state.set_state(PostChanging.sending_buttons_message)


@post_changing_router.message(PostChanging.sending_buttons_message)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        if post.type == 'mediagroup' and post.is_posted:
            await message.answer(text="Нельзя изменить кнопки у альбома опубликованного без кнопок")
            await state_data['proceed_method'](message.answer, state)
            return
        for btn_line_info in message.html_text.split("\n"):
            link_part, name_part = btn_line_info.split(" - ")
            post.buttons.append(Button(link=link_part, text=name_part))
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                await bot.edit_message_reply_markup(chat_id=msg.channel_tg_id,
                                                    message_id=msg.get_buttons_message_tg_id(),
                                                    reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session))
        session.commit()
    await message.answer(text="Кнопки были добавлены!")
    await choosing_button_setting.entry(message.answer, state)


@post_changing_router.callback_query(PostChanging.sending_buttons_message, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_button_setting.entry(callback.message.edit_text, state)
    await callback.answer()
