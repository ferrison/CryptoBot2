from typing import Literal

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.content_plan import choosing_setting, sending_media
from handlers.content_plan.router import content_plan_router
from handlers.content_plan.state import ContentPlan
from handlers.post_changing_common import choosing_posting_type, choosing_button_setting, \
    sending_post_text
from keyboards import common
from model.models import Post


class PostSettingChooseCallback(CallbackData, prefix='choosing_post_setting'):
    action: Literal['change_text', 'delete_text', 'change_media', 'change_channels', 'url_buttons']


def get_post_settings_kb(post: Post):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить описание",
        callback_data=PostSettingChooseCallback(action="change_text"),
    )
    if post.type != 'text':
        builder.button(
            text="Удалить описание",
            callback_data=PostSettingChooseCallback(action="delete_text"),
        )
    if not (post.is_posted and post.type == 'mediagroup'):
        builder.button(
            text="Изменить медиа",
            callback_data=PostSettingChooseCallback(action="change_media"),
        )
    if not post.is_posted:
        builder.button(
            text="Изменить каналы",
            callback_data=PostSettingChooseCallback(action="change_channels"),
        )
    if not (post.is_posted and post.type == 'mediagroup' and not post.buttons):
        builder.button(
            text="URL-кнопки",
            callback_data=PostSettingChooseCallback(action="url_buttons"),
        )
    builder.button(
        text="Назад",
        callback_data=common.StepbackCallback(),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


async def entry(message_edit_method, state):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        await message_edit_method(text="Информация о посте: \n"
                                       f"Статус: {'опубликован' if post.is_posted else 'не опубликован'}\n"
                                       f"Дата публикации: {post.date}\n"
                                       f"Тип поста: {'ответный' if post.is_reply else 'обычный'} \n",
                                  reply_markup=get_post_settings_kb(post))
    await state.set_state(ContentPlan.choosing_post_setting)


@content_plan_router.callback_query(ContentPlan.choosing_post_setting,
                                    PostSettingChooseCallback.filter(F.action == 'change_text'))
async def change_text(callback: types.CallbackQuery, state: FSMContext):
    await sending_post_text.entry(callback.message.edit_text, state, entry)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_post_setting,
                                    PostSettingChooseCallback.filter(F.action == 'delete_text'))
async def delete_text(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        post.text = ''
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                if post.type == 'text':
                    await bot.edit_message_text(text='',
                                                chat_id=msg.channel_tg_id,
                                                message_id=msg.message_tg_id,
                                                parse_mode="HTML",
                                                disable_web_page_preview=True)
                else:
                    await bot.edit_message_caption(caption='',
                                                   chat_id=msg.channel_tg_id,
                                                   message_id=msg.message_tg_id,
                                                   parse_mode="HTML")
        session.commit()
    await callback.message.answer("Текст удален!")
    await entry(callback.message.answer, state)


@content_plan_router.callback_query(ContentPlan.choosing_post_setting,
                                    PostSettingChooseCallback.filter(F.action == 'change_media'))
async def change_media(callback: types.CallbackQuery, state: FSMContext):
    await sending_media.entry(callback.message.edit_text, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_post_setting,
                                    PostSettingChooseCallback.filter(F.action == 'change_channels'))
async def change_channels(callback: types.CallbackQuery, state: FSMContext):
    await choosing_posting_type.entry(callback.message.edit_text, state, entry, entry)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_post_setting,
                                    PostSettingChooseCallback.filter(F.action == 'url_buttons'))
async def url_buttons(callback: types.CallbackQuery, state: FSMContext):
    await choosing_button_setting.entry(callback.message.edit_text, state, entry, entry)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_post_setting, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_setting.entry(callback.message.edit_text, state)
    await callback.answer()
