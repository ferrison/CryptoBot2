from datetime import date

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext

from handlers.post_changing_common import choosing_posting_type, sending_reply_message, choosing_post, \
    choosing_channels
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common

reply_type_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="Да", callback_data="yes"),
     types.InlineKeyboardButton(text="Нет", callback_data="no")],
    [common.backBtn]
])


async def entry(message_edit_method, state):
    await message_edit_method(text="Сообщение, на которое необходимо ответить, было создано с помощью бота?",
                              reply_markup=reply_type_kb)
    await state.set_state(PostChanging.choosing_reply_type)


@post_changing_router.callback_query(PostChanging.choosing_reply_type, Text(text='yes'))
async def yes(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_date=date.today(),
                            action='reply_choosing',
                            stepback_entry=entry,
                            proceed_entry=choosing_channels.entry)
    await choosing_post.entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_reply_type, Text(text='no'))
async def no(callback: types.CallbackQuery, state: FSMContext):
    await sending_reply_message.entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_reply_type, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_posting_type.entry(callback.message.edit_text, state)
    await callback.answer()
