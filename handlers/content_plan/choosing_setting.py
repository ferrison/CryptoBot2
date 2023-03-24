from typing import Literal

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.content_plan import confirm_deletion, choosing_post_setting, \
    watching_post
from handlers.content_plan.router import content_plan_router
from handlers.content_plan.state import ContentPlan
from handlers.new_post import choosing_setting
from handlers.post_changing_common import choosing_posting_type, sending_posting_date, choosing_post
from keyboards import common
from model.models import Post, Message, Button, Media


class SettingChooseCallback(CallbackData, prefix='choosing_setting'):
    action: Literal['change_date', 'change_post', 'delete', 'show', 'show_links', 'copy']


def get_settings_kb(post: Post):
    builder = InlineKeyboardBuilder()
    if not post.is_posted:
        builder.button(
            text="Изменить дату публикации поста",
            callback_data=SettingChooseCallback(action="change_date"),
        )
    builder.button(
        text="Удалить пост",
        callback_data=SettingChooseCallback(action="delete"),
    )
    builder.button(
        text="Изменить содержимое поста",
        callback_data=SettingChooseCallback(action="change_post"),
    )
    builder.button(
        text="Показать пост",
        callback_data=SettingChooseCallback(action="show"),
    )
    if post.is_posted:
        builder.button(
            text="Показать ссылки на посты",
            callback_data=SettingChooseCallback(action="show_links"),
        )
    builder.button(
        text="Копировать пост",
        callback_data=SettingChooseCallback(action="copy"),
    )

    builder.button(
        text="Назад",
        callback_data=common.StepbackCallback(),
    )
    builder.adjust(1)
    return builder.as_markup()


async def entry(message_edit_method, state):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        await message_edit_method(text="Информация о посте: \n"
                                       f"Статус: {'опубликован' if post.is_posted else 'не опубликован'}\n"
                                       f"Дата публикации: {post.date}\n"
                                       f"Тип поста: {'ответный' if post.is_reply else 'обычный'} \n",
                                  reply_markup=get_settings_kb(post))
    await state.set_state(ContentPlan.choosing_setting)


@content_plan_router.callback_query(ContentPlan.choosing_setting,
                                    SettingChooseCallback.filter(F.action == 'change_date'))
async def change_date(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(stepback_entry=entry, terminate=False)
    await sending_posting_date.entry(callback.message.edit_text, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_setting,
                                    SettingChooseCallback.filter(F.action == 'change_post'))
async def change_post(callback: types.CallbackQuery, state: FSMContext):
    await choosing_post_setting.entry(callback.message.edit_text, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_setting, SettingChooseCallback.filter(F.action == 'delete'))
async def delete(callback: types.CallbackQuery, state: FSMContext):
    await confirm_deletion.entry(callback.message.edit_text, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_setting,
                                    SettingChooseCallback.filter(F.action == 'show_links'))
async def show_links(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        links = []
        for msg in post.messages:
            chat = await bot.get_chat(msg.channel_tg_id)
            links.append(f'<a href="https://t.me/c/{chat.shifted_id}/{msg.message_tg_id}">{msg.channel.name}</a>')
    await callback.message.answer(text='Ссылки:\n' +
                                       ', '.join(links), parse_mode="HTML")
    await entry(callback.message.answer, state)


@content_plan_router.callback_query(ContentPlan.choosing_setting, SettingChooseCallback.filter(F.action == 'show'))
async def show_post(callback: types.CallbackQuery, state: FSMContext):
    await watching_post.entry(callback.message, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.choosing_setting, SettingChooseCallback.filter(F.action == 'copy'))
async def copy(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        new_post = Post(manager_tg_id=post.manager_tg_id,
                        type=post.type,
                        text=post.text,
                        bot_tg_id=bot.id)
        if post.type == 'mediagroup':
            new_post.medias = [Media(file_id=m.file_id, type=m.type) for m in post.medias]
        else:
            new_post.file_id = post.file_id
        new_post.messages = [Message(channel_tg_id=msg.channel_tg_id) for msg in post.messages]
        new_post.buttons = [Button(link=btn.link, text=btn.text) for btn in post.buttons]
        session.add(new_post)
        session.commit()
        await state.update_data(post_id=new_post.id)
    await choosing_posting_type.entry(callback.message.edit_text, state, entry, choosing_setting.entry)


@content_plan_router.callback_query(ContentPlan.choosing_setting, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action='post_choosing', proceed_entry=entry)
    await choosing_post.entry(callback.message.edit_text, state)
    await callback.answer()
