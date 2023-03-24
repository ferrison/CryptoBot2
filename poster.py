import traceback
from datetime import datetime

from sqlalchemy.orm import Session

from bot import bot
from db import engine
from model.models import Post
from model.services import send_post


async def check_planned_posts():
    with Session(engine) as session:
        posts_to_publish = session.query(Post).filter(Post.date <= datetime.now(),
                                                      Post.is_posted == False,
                                                      Post.is_draft == False,
                                                      Post.bot_tg_id == bot.id,
                                                      Post.send_attempts < 30).order_by(Post.date).all()

        for post in posts_to_publish:
            try:
                await send_post(post, session)
                if all(m.message_tg_id for m in post.messages):
                    post.is_posted = True
            except Exception:
                traceback.print_exc()
            post.send_attempts += 1

        session.commit()
