from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.new_post import choosing_posting_method
from handlers.post_changing_common.router import post_changing_router
from handlers.post_changing_common.state import PostChanging
from keyboards import common
from model.models import Post, Channel, Message


async def entry(message_edit_method, state):
    await message_edit_method(text="Перешлите боту из канала сообщение, на которое желаете ответить постом",
                              reply_markup=common.simple_stepback_kb())
    await state.set_state(PostChanging.sending_reply_message)


@post_changing_router.message(PostChanging.sending_reply_message)
async def message_sended(message: types.Message, state: FSMContext):
    if message.forward_from_chat:
        with Session(engine) as session:
            post_id = (await state.get_data())['post_id']
            post = session.query(Post).filter_by(id=post_id).one()
            if session.query(Channel).filter_by(tg_id=message.forward_from_chat.id,
                                                bot_tg_id=bot.id).first():
                post.messages = [Message(channel_tg_id=message.forward_from_chat.id)]
            else:
                await message.answer(text="Бот не обслуживает данный канал, попробуйте еще раз")
            post.reply_channel_tg_id = message.forward_from_chat.id
            post.reply_message_tg_id = message.forward_from_message_id
            session.commit()
        state_data = await state.get_data()
        await state_data['proceed_method'](message.answer, state)
    else:
        await message.answer(text="Переслано сообщение не из канала, попробуйте еще раз")


@post_changing_router.callback_query(PostChanging.sending_reply_message, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_posting_method.entry(callback.message.answer, state)
    await callback.answer()
