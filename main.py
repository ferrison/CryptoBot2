import asyncio
import locale
import logging

from sqlalchemy.orm import Session

from bot import bot, dp
from db import engine
from handlers.base import base_router
from handlers.new_post.router import new_post_router
from handlers.content_plan.router import content_plan_router
from handlers.post_changing_common.router import post_changing_router
from handlers.tags.router import tags_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from model.models import Post
from poster import check_planned_posts

logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.INFO, filename='logs.log')
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

scheduler = AsyncIOScheduler()
scheduler.add_job(check_planned_posts, "interval", seconds=20)


async def delete_draft_posts():
    with Session(engine) as session:
        for post in session.query(Post).filter_by(is_draft=True).all():
            session.delete(post)
        session.commit()


async def main():
    dp.include_router(base_router)
    dp.include_router(new_post_router)
    dp.include_router(content_plan_router)
    dp.include_router(tags_router)
    dp.include_router(post_changing_router)
    dp.shutdown.register(delete_draft_posts)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
