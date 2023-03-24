from typing import Literal

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common import choosing_posting_type
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Channel, Post, Message


class ChannelsChooseCallback(CallbackData, prefix='channels_choose'):
    action: Literal['channel_picked', 'all_channels']
    id: int = None


def get_channels_kb(channels: list[Channel], selected_channel_ids: set):
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.button(
            text=channel.name + ("✅" if channel.tg_id in selected_channel_ids else ""),
            callback_data=ChannelsChooseCallback(action='channel_picked', id=channel.tg_id)
        )
    builder.adjust(2)

    builder.row(
        types.InlineKeyboardButton(
            text="Выбрать все✅" if selected_channel_ids == {ch.tg_id for ch in channels} else "Выбрать все",
            callback_data=ChannelsChooseCallback(action='all_channels').pack()
        )
    )

    if selected_channel_ids:
        builder.row(common.nextBtn)

    builder.row(common.backBtn)

    return builder.as_markup()


async def entry(message_edit_method, state):
    state_data = await state.get_data()
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        if "selected_channel_ids" not in state_data:
            await state.update_data(selected_channel_ids={ch.tg_id for ch in post.channels})
            state_data = await state.get_data()
        selected_channels = state_data["selected_channel_ids"]
        if post.reply_post_id:
            reply_post = session.query(Post).filter_by(id=post.reply_post_id).one()
            channels = reply_post.channels
        else:
            channels = session.query(Channel).filter_by(bot_tg_id=bot.id).all()
    await message_edit_method(text="Теперь выберите канал", reply_markup=get_channels_kb(channels, selected_channels))
    await state.set_state(PostChanging.choosing_channels)


@post_changing_router.callback_query(PostChanging.choosing_channels,
                                     ChannelsChooseCallback.filter(F.action == 'channel_picked'))
async def channel_picked(callback: types.CallbackQuery, callback_data: ChannelsChooseCallback, state: FSMContext):
    post_data = await state.get_data()
    selected_channel_ids = post_data["selected_channel_ids"]
    if callback_data.id in selected_channel_ids:
        selected_channel_ids.remove(callback_data.id)
    else:
        selected_channel_ids.add(callback_data.id)
    await state.update_data(selected_channel_ids=selected_channel_ids)
    await entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_channels,
                                     ChannelsChooseCallback.filter(F.action == 'all_channels'))
async def all_channels(callback: types.CallbackQuery, state: FSMContext):
    post_data = await state.get_data()
    selected_channel_ids = post_data["selected_channel_ids"]
    with Session(engine) as session:
        channels = session.query(Channel).filter_by(bot_tg_id=bot.id).all()
    channel_ids = set(ch.tg_id for ch in channels)
    if selected_channel_ids == channel_ids:
        await state.update_data(selected_channel_ids=set())
    else:
        await state.update_data(selected_channel_ids=channel_ids)
    await entry(callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_channels, common.NextCallback.filter())
async def proceed(callback: types.CallbackQuery, state: FSMContext):
    post_data = await state.get_data()
    selected_channel_ids = post_data["selected_channel_ids"]
    with Session(engine) as session:
        post_id = (await state.get_data())['post_id']
        post = session.query(Post).filter_by(id=post_id).one()
        post.messages = [Message(channel_tg_id=ch) for ch in selected_channel_ids]
        session.commit()
    state_data = await state.get_data()
    await state_data['proceed_method'](callback.message.edit_text, state)
    await callback.answer()


@post_changing_router.callback_query(PostChanging.choosing_channels, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_posting_type.entry(callback.message.edit_text, state)
    await callback.answer()
