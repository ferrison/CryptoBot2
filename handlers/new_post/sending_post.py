from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import ContentType
from aiogram_media_group import media_group_handler
from magic_filter import F
from sqlalchemy.orm import Session

from bot import bot
from db import engine
from handlers.new_post import choosing_setting
from handlers.post_changing_common import choosing_posting_type
from handlers.new_post.router import new_post_router
from handlers.new_post.state import NewPost
from model.models import Post, Media


async def entry(message_edit_method, state):
    await message_edit_method("Пришлите пост, который хотите опубликовать в канал")
    await state.set_state(NewPost.sending_post)


@new_post_router.message(NewPost.sending_post, F.media_group_id, content_types=ContentType.ANY)
@media_group_handler
async def album_sended(messages: list[types.Message], state: FSMContext):
    with Session(engine) as session:
        post = Post(manager_tg_id=messages[0].from_user.id,
                    type="mediagroup",
                    text=messages[0].html_text,
                    bot_tg_id=bot.id)
        for msg in messages:
            if msg.content_type == 'photo':
                post.medias.append(Media(file_id=msg.photo[-1].file_id, type='photo'))
            else:
                post.medias.append(Media(file_id=getattr(msg, msg.content_type).file_id, type=msg.content_type))
        session.add(post)
        session.commit()

        await state.update_data(post_id=post.id)

    await choosing_posting_type.entry(messages[0].answer, state, entry, choosing_setting.entry)


@new_post_router.message(NewPost.sending_post)
async def message_sended(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        file_id = None
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    else:
        file_id = getattr(message, message.content_type).file_id

    with Session(engine) as session:
        post = Post(manager_tg_id=message.from_user.id,
                    type=message.content_type,
                    text=message.html_text,
                    file_id=file_id,
                    bot_tg_id=bot.id)
        session.add(post)
        session.commit()

        await state.update_data(post_id=post.id)

    await choosing_posting_type.entry(message.answer, state, entry, choosing_setting.entry)
