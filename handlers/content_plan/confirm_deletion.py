from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.content_plan import choosing_setting
from handlers.content_plan.router import content_plan_router
from handlers.content_plan.state import ContentPlan
from handlers.post_changing_common import choosing_post
from keyboards import common
from model.models import Post

confirm_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="Да", callback_data=common.NextCallback().pack()),
     types.InlineKeyboardButton(text="Нет", callback_data=common.StepbackCallback().pack())]
])


async def entry(message_edit_method, state):
    await message_edit_method(text="Вы уверены что хотите удалить данный  пост из 'запланированных'? "
                              "Опубликованные посты также будут удалены из каналов",
                              reply_markup=confirm_kb)
    await state.set_state(ContentPlan.confirm_deletion)


@content_plan_router.callback_query(ContentPlan.confirm_deletion, common.NextCallback.filter())
async def yes(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        try:
            post = session.query(Post).filter_by(id=state_data['post_id']).one()
        except NoResultFound:
            await callback.message.answer('Пост уже опубликован')
            await choosing_setting.entry(callback.message.answer, state)
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                await bot.delete_message(chat_id=msg.channel.tg_id, message_id=msg.message_tg_id)
        session.delete(post)
        session.commit()
    await state.update_data(action='post_choosing', proceed_entry=choosing_setting.entry)
    await choosing_post.entry(callback.message.edit_text, state)
    await callback.answer()


@content_plan_router.callback_query(ContentPlan.confirm_deletion, common.StepbackCallback.filter())
async def no(callback: types.CallbackQuery, state: FSMContext):
    await choosing_setting.entry(callback.message.edit_text, state)
    await callback.answer()
