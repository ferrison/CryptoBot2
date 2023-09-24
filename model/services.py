import traceback

from aiogram import types
import re

from bot import bot
from keyboards.common import url_buttons_kb
from model.models import Post, Tag, Channel, Button, Message


def get_inflated_text(text: str, user_id: int, channel: Channel, session):
    placeholders = re.findall("%(.[ЁёА-я-A-Za-z-0-9-_]*?)%", text)
    for placeholder in placeholders:
        text = text.replace(f"%{placeholder}%", f"%{placeholder.lower()}%")
    tags = session.query(Tag).filter(Tag.placeholder.in_({p.lower() for p in placeholders}), Tag.user_tg_id == user_id).all()

    for tag in tags:
        text = text.replace(f"%{tag.placeholder}%", getattr(tag.tag_values.filter_by(channel_tg_id=channel.tg_id).first(), 'value', ''))

    return text


def url_buttons_inflated_kb(buttons: list[Button], user_id, channel, session):
    return url_buttons_kb([Button(text=get_inflated_text(btn.text, user_id, channel, session),
                                  link=get_inflated_text(btn.link, user_id, channel, session)) for btn in buttons])


async def send_post(post: Post, session):
    post_links = []
    for msg in (m for m in post.messages if not m.message_tg_id):
        try:
            buttons_sended_msg = None
            if post.is_reply and post.reply_post_id:
                reply_msg_id = session.query(Message).filter_by(post_id=post.reply_post_id, channel_tg_id=msg.channel_tg_id).one().message_tg_id
            else:
                reply_msg_id = None
            if post.type == 'text':
                sended_msg = await bot.send_message(chat_id=msg.channel.tg_id,
                                                    reply_to_message_id=post.reply_message_tg_id or reply_msg_id,
                                                    text=get_inflated_text(post.text, post.manager_tg_id, msg.channel, session),
                                                    reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                    parse_mode="HTML",
                                                    disable_web_page_preview=True)
            elif post.type == 'video_note':
                sended_msg = await bot.send_video_note(chat_id=msg.channel.tg_id,
                                                       reply_to_message_id=post.reply_message_tg_id or reply_msg_id,
                                                       reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                       disable_notification=True,
                                                       video_note=post.file_id)
            elif post.type == 'mediagroup':
                sended_msg = (await bot.send_media_group(chat_id=msg.channel.tg_id,
                                                         reply_to_message_id=post.reply_message_tg_id or reply_msg_id,
                                                         media=[types.InputMedia(type=post.medias[0].type,
                                                                                 media=post.medias[0].file_id,
                                                                                 caption=get_inflated_text(post.text, post.manager_tg_id, msg.channel, session),
                                                                                 parse_mode="HTML")]
                                                                + [types.InputMedia(type=m.type, media=m.file_id) for m in
                                                                  post.medias[1:]],
                                                         disable_notification=True))[0]
                if post.buttons:
                    buttons_sended_msg = await bot.send_message(chat_id=msg.channel.tg_id,
                                                                reply_to_message_id=post.reply_message_tg_id or reply_msg_id,
                                                                text='Кнопки',
                                                                parse_mode='HTML',
                                                                reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                                disable_notification=True)
            else:
                sended_msg = await getattr(bot, f"send_{post.type}")(chat_id=msg.channel.tg_id,
                                                                     reply_to_message_id=post.reply_message_tg_id or reply_msg_id,
                                                                     caption=get_inflated_text(post.text, post.manager_tg_id, msg.channel, session),
                                                                     reply_markup=url_buttons_inflated_kb(post.buttons, post.manager_tg_id, msg.channel, session),
                                                                     parse_mode="HTML",
                                                                     disable_notification=True,
                                                                     **{post.type: post.file_id})
            msg.message_tg_id = sended_msg.message_id
            if buttons_sended_msg:
                msg.buttons_message_tg_id = buttons_sended_msg.message_id
            post_links.append(f'<a href="{sended_msg.get_url()}">{msg.channel.name}</a>')
        except Exception:
            traceback.print_exc()

    return post_links
