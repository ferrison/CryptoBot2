from typing import Literal, Iterable

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common import sending_buttons_message, sending_button_message
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from keyboards.common import url_buttons_kb
from model.models import Post, Button


class ChoosingButtonCallback(CallbackData, prefix='choosing_button'):
    action: Literal['delete_buttons', 'add_buttons', 'button_choosed']
    button_id: int = None


def get_button_settings_kb(buttons: Iterable[Button]):
    builder = InlineKeyboardBuilder()
    builder.button(text="Сброс кнопок", callback_data=ChoosingButtonCallback(action='delete_buttons'))
    builder.button(text="Добавить кнопки", callback_data=ChoosingButtonCallback(action='add_buttons'))

    for button in buttons:
        builder.button(text=f"{button.link} - {button.text}",
                       callback_data=ChoosingButtonCallback(action='button_choosed', button_id=button.id))

    builder.button(text='Назад', callback_data=common.StepbackCallback())
    builder.adjust(2, 1)
    return builder.as_markup()


async def entry(message_edit_method, state, stepback_method=None, proceed_method=None):
    if stepback_method:
        await state.update_data(stepback_method=stepback_method)
    if proceed_method:
        await state.update_data(proceed_method=proceed_method)

    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        await message_edit_method(text="Выберите, что хотите сделать с кнопками",
                                  reply_markup=get_button_settings_kb(post.buttons))
    await state.set_state(PostChanging.choosing_button_setting)


@post_changing_router.callback_query(PostChanging.choosing_button_setting,
                                     ChoosingButtonCallback.filter(F.action == 'delete_buttons'))
async def delete_buttons(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        post.buttons = []
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                await bot.edit_message_reply_markup(chat_id=msg.channel_tg_id,
                                                    message_id=msg.get_buttons_message_tg_id(),
                                                    reply_markup=url_buttons_kb(post.buttons))
        session.commit()
    await callback.message.answer(text="Кнопки  были удалены")
    await entry(callback.message.answer, state)


@post_changing_router.callback_query(PostChanging.choosing_button_setting,
                                     ChoosingButtonCallback.filter(F.action == 'add_buttons'))
async def add_buttons(callback: types.CallbackQuery, state: FSMContext):
    await sending_buttons_message.entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_button_setting,
                                     ChoosingButtonCallback.filter(F.action == 'button_choosed'))
async def button_choosed(callback: types.CallbackQuery, callback_data: ChoosingButtonCallback, state: FSMContext):
    await state.update_data(button_id=callback_data.button_id)
    await sending_button_message.entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_button_setting, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state_data['stepback_method'](callback.message.edit_text, state)
    await callback.answer()
