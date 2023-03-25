from datetime import datetime

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from db import engine
from handlers.content_plan import choosing_setting
from handlers.post_changing_common import choosing_post
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post

DATETIME_FORMAT = '%Y-%m-%d %H:%M'


async def entry(message_edit_method, state):
    await message_edit_method("Введите дату в следующем формате: год-месяц-день часы:минуты \n"
                              f"Пример: <code>{datetime.now().strftime(DATETIME_FORMAT)}</code>",
                              parse_mode="HTML",
                              reply_markup=common.simple_stepback_kb())
    await state.set_state(PostChanging.sending_posting_date)


@post_changing_router.message(PostChanging.sending_posting_date)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    stepback = state_data['stepback_entry']
    try:
        with Session(engine) as session:
            post_id = state_data['post_id']
            post = session.query(Post).filter_by(id=post_id).one()
            if post.is_posted:
                await message.answer('Нельзя менять дату публикации опубликованного поста')
                await stepback(message.answer, state)
                return
            if post.is_reply and post.reply_post_id and post.date <= post.reply_post.date:
                await message.answer("Ответный пост не может быть опубликован раньше отвечаемого поста. Попробуйте еще раз")
                return

            post.date = datetime.strptime(message.text, DATETIME_FORMAT)
            post.is_draft = False
            session.commit()
        state_data = await state.get_data()

        if state_data['terminate']:
            await message.answer("Пост запланирован!")
            if state_data.get('back_to_contentplan'):
                await state.update_data(action='post_choosing',
                                        proceed_entry=choosing_setting.entry,
                                        stepback_entry=None)
                await choosing_post.entry(message.answer, state)
                return
            await state.clear()
            return
        else:
            await message.answer("Дата публикации поста успешно изменена!")
            await stepback(message.answer, state)
    except ValueError:
        await message.answer('Некорректный формат даты и времени! Попробуйте еще раз')


@post_changing_router.callback_query(PostChanging.sending_posting_date, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state_data['stepback_entry'](callback.message.answer, state)
    await callback.answer()
