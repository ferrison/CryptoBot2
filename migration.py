import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import config
from db import engine
from model.models import User, Bot, Channel, Tag, TagValue, Post, Button, Message, Media

with Session(create_engine(f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/crypto_bot")) as new_session,\
        Session(create_engine(f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/content_bots")) as old_session:
    content_managers = old_session.execute("SELECT * FROM content_managers;").all()
    for manager in content_managers:
        user = User(tg_id=manager["tgid"])

        bots = json.loads(manager["bots"])
        for bot_id in bots:
            bot = new_session.query(Bot).filter_by(tg_id=bot_id).one_or_none()
            if not bot:
                bot = Bot(tg_id=bot_id, name=bots[bot_id]["name"])
            user.bots.append(bot)
        new_session.add(user)

    channels = old_session.execute("SELECT * FROM channels;").all()
    for channel in channels:
        channel = Channel(tg_id=channel["tgid"], name=channel["name"], bot_tg_id=channel["id_bot_inner"])
        new_session.add(channel)

    tags = old_session.execute("SELECT * FROM tags;").all()
    for tag in tags:
        tag = Tag(id=tag["id"], placeholder=tag["placeholder"].lower(), user_tg_id=tag["manager_user_id"])
        new_session.add(tag)

    tag_values = old_session.execute("SELECT * FROM tags_values;").all()
    for tag_value in tag_values:
        tag_value = TagValue(tag_id=tag_value["tag_id"], channel_tg_id=tag_value["channel_id"], value=tag_value["value"])
        new_session.add(tag_value)

    planned_posts = old_session.execute("SELECT * FROM planned_posts;").all()
    for planned_post in planned_posts:
        data = json.loads(planned_post["data_post"])
        post = Post(id=planned_post["id"],
                    is_draft=False,
                    is_reply=data["isreply"],
                    reply_channel_tg_id=data.get("forward_from_chat"),
                    reply_message_tg_id=data.get("forward_from_message_id"),
                    is_posted=planned_post["is_published"],
                    date=planned_post["date_planned"],
                    type=data["post_type"],
                    text=data["post_text"],
                    file_id=data["file_id"],
                    manager_tg_id=data["manager_id"],
                    bot_tg_id=planned_post["planned_from"])

        for button in data["btn_data"]:
            button = Button(text=button["text"], link=button["link"])
            post.buttons.append(button)

        for media_data in data["media_data"]:
            media = Media(file_id=media_data["media"], type=media_data["type"])
            post.medias.append(media)

        for ch in data["needed_channels"]:
            message = Message(channel_tg_id=ch)
            post.messages.append(message)

        new_session.add(post)

    new_session.commit()

