from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.content_plan import choosing_setting
from handlers.content_plan.router import content_plan_router
from handlers.content_plan.state import ContentPlan
from keyboards import common
from keyboards.common import url_buttons_kb
from model.models import Post


async def entry(message, state):
    state_data = await state.get_data()
    await message.edit_reply_markup(reply_markup=common.simple_stepback_kb())
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        if post.type == 'text':
            msg = await message.answer(text=post.text, reply_markup=url_buttons_kb(post.buttons),
                                       disable_notification=True, parse_mode="HTML")
        elif post.type == 'video_note':
            msg = await message.answer_video_note(video_note=post.file_id, reply_markup=url_buttons_kb(post.buttons),
                                                  disable_notification=True)
        elif post.type == 'mediagroup':
            msg = await message.answer_media_group(media=[types.InputMedia(type=post.medias[0].type,
                                                                           media=post.medias[0].file_id,
                                                                           caption=post.text,
                                                                           parse_mode="HTML")]
                                                         + [types.InputMedia(type=m.type, media=m.file_id) for m in
                                                            post.medias[1:]],
                                                   disable_notification=True)
            if post.buttons:
                buttons_msg = await message.answer(text='Кнопки',
                                                   parse_mode='HTML',
                                                   reply_markup=url_buttons_kb(post.buttons),
                                                   disable_notification=True)
                await state.update_data(buttons_msg_id=buttons_msg.message_id)
        else:
            msg = await getattr(message, f"answer_{post.type}")(caption=post.text,
                                                                reply_markup=url_buttons_kb(post.buttons),
                                                                disable_notification=True,
                                                                parse_mode='HTML',
                                                                **{post.type: post.file_id})
    await state.update_data(chat_id=message.chat.id, msg=msg)
    await state.set_state(ContentPlan.watching_post)


@content_plan_router.callback_query(ContentPlan.watching_post, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    if isinstance(state_data['msg'], list):
        for msg in state_data['msg']:
            await bot.delete_message(chat_id=state_data['chat_id'], message_id=msg.message_id)
    else:
        await bot.delete_message(chat_id=state_data['chat_id'], message_id=state_data['msg'].message_id)
    if state_data.get('buttons_msg_id'):
        await bot.delete_message(chat_id=state_data['chat_id'], message_id=state_data['buttons_msg_id'])
    await choosing_setting.entry(callback.message.edit_text, state)