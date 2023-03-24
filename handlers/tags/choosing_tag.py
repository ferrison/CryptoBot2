from typing import Literal, Iterable

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy.orm import Session

from db import engine
from handlers.tags import choosing_setting, sending_tag
from handlers.tags.router import tags_router
from handlers.tags.state import Tags
from model.models import Tag


class TagChoosingCallback(CallbackData, prefix="choosing_tag"):
    action: Literal['tag', 'add_tag']
    tag_id: int = None


def tags_kb(tags: Iterable[Tag]):
    builder = InlineKeyboardBuilder()
    for tag in tags:
        builder.button(
            text=tag.placeholder,
            callback_data=TagChoosingCallback(action="tag", tag_id=tag.id),
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕", callback_data=TagChoosingCallback(action='add_tag').pack())
    )
    return builder.as_markup()


async def entry(message_edit_method, state):
    await state.set_state(Tags.choosing_tag)
    state_data = await state.get_data()
    with Session(engine) as session:
        tags = session.query(Tag).filter_by(user_tg_id=state_data['user_id'])
    await message_edit_method(f"Редактирование тегов", reply_markup=tags_kb(tags))


@tags_router.callback_query(Tags.choosing_tag, TagChoosingCallback.filter(F.action == 'tag'))
async def tag_chosen(callback: types.CallbackQuery, callback_data: TagChoosingCallback, state: FSMContext):
    await state.update_data(tag_id=callback_data.tag_id)
    await choosing_setting.entry(callback.message.edit_text, state)


@tags_router.callback_query(Tags.choosing_tag, TagChoosingCallback.filter(F.action == 'add_tag'))
async def add_tag(callback: types.CallbackQuery, state: FSMContext):
    await sending_tag.entry(callback.message.edit_text, state)
    await callback.answer()
