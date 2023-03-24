from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import ContentType
from aiogram_media_group import media_group_handler
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.content_plan import choosing_post_setting
from handlers.content_plan.router import content_plan_router
from handlers.content_plan.state import ContentPlan
from keyboards import common
from model.models import Post, Media
from model.services import url_buttons_inflated_kb


async def entry(message_edit_method, state):
    await message_edit_method(text="Теперь пришлите медиафайл", reply_markup=common.simple_stepback_kb())
    await state.set_state(ContentPlan.sending_media)


@content_plan_router.message(ContentPlan.sending_media, F.media_group_id, content_types=ContentType.ANY)
@media_group_handler
async def album_sended(messages: list[types.Message], state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        if post.is_posted:
            await messages[0].answer("Нельзя изменить медиа на альбом у опубликованного поста")
            await choosing_post_setting.entry(messages[0].answer, state)
            return
        post.type = 'mediagroup'
        post.file_id = None
        post.medias = []
        for msg in messages:
            if msg.content_type == 'photo':
                post.medias.append(Media(file_id=msg.photo[-1].file_id, type='photo'))
            else:
                post.medias.append(Media(file_id=getattr(msg, msg.content_type).file_id, type=msg.content_type))
        session.commit()


@content_plan_router.message(ContentPlan.sending_media)
async def message_sended(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    with Session(engine) as session:
        post = session.query(Post).filter_by(id=state_data['post_id']).one()
        if post.type == 'mediagroup' and post.is_posted:
            await message.answer("Нельзя изменить медиа на альбом у опубликованного поста")
            await choosing_post_setting.entry(message.answer, state)
            return
        if post.type == 'text' and post.is_posted:
            await message.answer("Нельзя изменить медиа у опубликованного текстового поста")
            await choosing_post_setting.entry(message.answer, state)
            return
        if post.is_posted and message.content_type in ('voice', 'video_note'):
            await message.answer("Нельзя изменить медиа у опубликованного поста на голосовое или видеосообщение")
            await choosing_post_setting.entry(message.answer, state)
            return
        if post.is_posted and post.type in ('voice', 'video_note'):
            await message.answer("Нельзя изменить медиа у опубликованного голосового или видеосообщения")
            await choosing_post_setting.entry(message.answer, state)
            return

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = getattr(message, message.content_type).file_id
        post.type = message.content_type
        post.file_id = file_id
        post.medias = []
        if post.is_posted:
            for msg in (m for m in post.messages if m.message_tg_id):
                await bot.edit_message_media(media=types.InputMedia(type=post.type, media=post.file_id),
                                             chat_id=msg.channel.tg_id,
                                             message_id=msg.message_tg_id,
                                             reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session))
        session.commit()
    await message.answer("Уcпешно изменен медиафайл!")
    await choosing_post_setting.entry(message.answer, state)


@content_plan_router.callback_query(ContentPlan.sending_media, common.StepbackCallback.filter())
async def stepback(callback: types.CallbackQuery, state: FSMContext):
    await choosing_post_setting.entry(callback.message.edit_text, state)
    await callback.answer()
