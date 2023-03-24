from datetime import timedelta, date
from typing import Literal, Iterable

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from sqlalchemy import func
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post


class ChoosingPostCallback(CallbackData, prefix='choosing_post'):
    action: Literal['prev_year', 'next_year', 'prev_month', 'next_month', 'yesterday', 'tomorrow', 'post']
    post_id: int = None


month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
post_type = {
    "text": "Текст 📝",
    "voice": "Аудиозапись🎙",
    "photo": "Фото🖼",
    "video": "Видео 🎬",
    "video_note": "Круглое Видео 🎬",
    "animation": "Гифка 🌠",
    "mediagroup": "Медиа группа 🖼🎬🎙🌠",
}


def post_choosing_kb(current_date: date, posts: Iterable[Post], stepback):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⬅️{current_date.year-1}",
                   callback_data=ChoosingPostCallback(action="prev_year"))
    builder.button(text=f"{current_date.year}✅", callback_data=" ")
    builder.button(text=f"➡️{current_date.year+1}",
                   callback_data=ChoosingPostCallback(action="next_year"))

    prev_month = month_names[(current_date.month-2) % 12]
    current_month = month_names[current_date.month-1]
    next_month = month_names[current_date.month % 12]
    builder.button(text=f"⬅️{prev_month}",
                   callback_data=ChoosingPostCallback(action="prev_month"))
    builder.button(text=f"{current_month}✅", callback_data=" ")
    builder.button(text=f"➡️{next_month}",
                   callback_data=ChoosingPostCallback(action="next_month"))

    yesterday = current_date - timedelta(days=1)
    tomorrow = current_date + timedelta(days=1)
    builder.button(text=f"⬅️{yesterday.day}, {weekday_names[yesterday.weekday()]}",
                   callback_data=ChoosingPostCallback(action="yesterday"))
    builder.button(text=f"{current_date.day}, {weekday_names[current_date.weekday()]}✅", callback_data=" ")
    builder.button(text=f"➡️{tomorrow.day}, {weekday_names[tomorrow.weekday()]}",
                   callback_data=ChoosingPostCallback(action="tomorrow"))

    if stepback:
        builder.button(text="Назад", callback_data=common.StepbackCallback())

    for post in sorted(posts, key=lambda el: el.date):
        builder.button(
            text=f"{post.date.strftime('%H:%M')} {post_type.get(post.type, 'Неизвестный формат')}",
            callback_data=ChoosingPostCallback(action="post", post_id=post.id))
    if stepback:
        builder.adjust(3, 3, 3, 1, 2)
    else:
        builder.adjust(3, 3, 3, 2)

    return builder.as_markup()


async def entry(message_edit_method, state):
    state_data = await state.get_data()
    with Session(engine) as session:
        posts = session.query(Post).filter(func.date(Post.date) == state_data['current_date'],
                                           Post.is_draft == False,
                                           Post.bot_tg_id == bot.id,
                                           Post.manager_tg_id == state_data['user_id']).all()
    await message_edit_method("Посты:", reply_markup=post_choosing_kb(current_date=state_data.get('current_date'),
                                                                      posts=posts,
                                                                      stepback=state_data.get('stepback_entry')))
    await state.set_state(PostChanging.choosing_reply_post)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'prev_year'))
async def prev_year(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    if current_date.month == 2 and current_date.day == 29:
        new_date = current_date.replace(year=current_date.year-1, day=28)
    else:
        new_date = current_date.replace(year=current_date.year-1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'next_year'))
async def next_year(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    if current_date.month == 2 and current_date.day == 29:
        new_date = current_date.replace(year=current_date.year+1, day=28)
    else:
        new_date = current_date.replace(year=current_date.year+1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'prev_month'))
async def prev_month(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    if current_date.month == 1:
        new_date = current_date.replace(month=12, year=current_date.year-1)
    else:
        new_date = current_date.replace(month=(current_date.month - 2) % 12 + 1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'next_month'))
async def next_month(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    if current_date.month == 12:
        new_date = current_date.replace(month=1, year=current_date.year+1)
    else:
        new_date = current_date.replace(month=(current_date.month + 2) % 12 - 1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'yesterday'))
async def yesterday(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    new_date = current_date - timedelta(days=1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post,
                                     ChoosingPostCallback.filter(F.action == 'tomorrow'))
async def tomorrow(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_date = state_data.get('current_date')
    new_date = current_date + timedelta(days=1)
    await state.update_data(current_date=new_date)
    await entry(callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post, ChoosingPostCallback.filter(F.action == 'post'))
async def post_chosen(callback: types.CallbackQuery, callback_data: ChoosingPostCallback, state: FSMContext):
    state_data = await state.get_data()
    if state_data['action'] == 'reply_choosing':
        with Session(engine) as session:
            post_id = (await state.get_data())['post_id']
            post = session.query(Post).filter_by(id=post_id).one()
            post.reply_post_id = callback_data.post_id
            session.commit()
    elif state_data['action'] == 'post_choosing':
        await state.update_data(post_id=callback_data.post_id)
    await state_data['proceed_entry'](callback.message.edit_text, state)


@post_changing_router.callback_query(PostChanging.choosing_reply_post, common.StepbackCallback.filter())
async def post_chosen(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state_data['stepback_entry'](callback.message.edit_text, state)
