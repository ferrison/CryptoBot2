from typing import Literal, Iterable

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.tags import sending_tag_value, choosing_tag, confirm_deletion
from handlers.tags.router import tags_router
from handlers.tags.state import Tags
from keyboards import common
from model.models import Tag, Channel, Bot


class TagValueSettingCallback(CallbackData, prefix="choosing_tag_value_setting"):
    action: Literal['delete', 'channel_id']
    channel_id: int = None


def tag_setting_kb(channels: Iterable[Channel]):
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.button(
            text=channel.name,
            callback_data=TagValueSettingCallback(action="channel_id", channel_id=channel.tg_id),
        )
    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(text="Удалить тег", callback_data=TagValueSettingCallback(action="delete").pack()))
    builder.row(
        InlineKeyboardButton(text="Назад", callback_data=common.StepbackCallback().pack()))

    return builder.as_markup()


async def entry(message_edit_method, state):
    await state.set_state(Tags.choosing_setting)
    state_data = await state.get_data()
    with Session(engine) as session:
        tag = session.query(Tag).filter_by(id=state_data['tag_id']).one()
        user_channels = session.query(Bot).filter_by(tg_id=bot.id).one().channels
        tag_value_by_channel = {tag_value.channel.tg_id: tag_value.value for tag_value in tag.tag_values}
        tag_print_rows = []
        for ch in user_channels:
            tag_print_rows.append(f"{ch.name} - {tag_value_by_channel.get(ch.tg_id, 'Нет значения')}")
        await message_edit_method(f"Значения:\n"+'\n'.join(tag_print_rows), reply_markup=tag_setting_kb(user_channels),
                                  parse_mode="HTML", disable_web_page_preview=True)


@tags_router.callback_query(Tags.choosing_setting, TagValueSettingCallback.filter(F.action == 'channel_id'))
async def tag_value_chosen(callback: types.CallbackQuery, callback_data: TagValueSettingCallback, state: FSMContext):
    await state.update_data(channel_id=callback_data.channel_id)
    await sending_tag_value.entry(callback.message.edit_text, state)
    await callback.answer()


@tags_router.callback_query(Tags.choosing_setting, TagValueSettingCallback.filter(F.action == 'delete'))
async def delete(callback: types.CallbackQuery, state: FSMContext):
    await confirm_deletion.entry(callback.message.edit_text, state)
    await callback.answer()


@tags_router.callback_query(Tags.choosing_setting, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_tag.entry(callback.message.edit_text, state)
    await callback.answer()
