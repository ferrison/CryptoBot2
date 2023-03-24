from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext

from handlers.new_post import choosing_posting_method
from handlers.new_post.router import new_post_router
from handlers.new_post.state import NewPost
from handlers.post_changing_common import choosing_channels, choosing_button_setting, sending_post_text
from keyboards import common

settings_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="Изменить описание", callback_data="change_text")],
    [types.InlineKeyboardButton(text="URL-кнопки", callback_data="url_buttons")],
    [common.nextBtn],
    [common.backBtn]
])


async def entry(message_edit_method, state):
    await message_edit_method(text="Дополнительные настройки", reply_markup=settings_kb)
    await state.set_state(NewPost.choosing_setting)


@new_post_router.callback_query(NewPost.choosing_setting, Text(text="change_text"))
async def change_text(callback: types.CallbackQuery, state: FSMContext):
    await sending_post_text.entry(callback.message.edit_text, state, entry)
    await callback.answer()


@new_post_router.chosen_inline_result
@new_post_router.callback_query(NewPost.choosing_setting, Text(text="url_buttons"))
async def url_buttons(callback: types.CallbackQuery, state: FSMContext):
    await choosing_button_setting.entry(callback.message.edit_text, state, entry, entry)
    await callback.answer()


@new_post_router.callback_query(NewPost.choosing_setting, common.NextCallback.filter())
async def proceed(callback: types.CallbackQuery, state: FSMContext):
    await choosing_posting_method.entry(callback.message.edit_text, state)
    await callback.answer()


@new_post_router.callback_query(NewPost.choosing_setting, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_channels.entry(callback.message.edit_text, state)
    await callback.answer()
