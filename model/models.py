from sqlalchemy import Column, Integer, Boolean, ForeignKey, String, Table, Text, BigInteger, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

from db import engine

Base = declarative_base()


user_bot_table = Table(
    "user_bot",
    Base.metadata,
    Column("user_tg_id", ForeignKey("user.tg_id"), primary_key=True),
    Column("bot_tg_id", ForeignKey("bot.tg_id"), primary_key=True)
)


class Bot(Base):
    __tablename__ = "bot"

    tg_id = Column(BigInteger, primary_key=True)
    name = Column(String(256))
    users = relationship("User", secondary=user_bot_table, back_populates="bots")
    channels = relationship("Channel")


class User(Base):
    __tablename__ = "user"

    tg_id = Column(BigInteger, primary_key=True)
    bots = relationship("Bot", secondary=user_bot_table, back_populates="users")


class Message(Base):
    __tablename__ = "message"

    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    channel_tg_id = Column(BigInteger, ForeignKey("channel.tg_id"), primary_key=True)
    channel = relationship("Channel")
    message_tg_id = Column(BigInteger)
    buttons_message_tg_id = Column(BigInteger)

    def get_buttons_message_tg_id(self):
        return self.buttons_message_tg_id or self.message_tg_id


class Channel(Base):
    __tablename__ = "channel"

    tg_id = Column(BigInteger, primary_key=True)
    name = Column(String(256))
    bot_tg_id = Column(BigInteger, ForeignKey("bot.tg_id"))
    bot = relationship("Bot", back_populates="channels")


class Button(Base):
    __tablename__ = "button"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    link = Column(String(256))
    text = Column(String(256))


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    file_id = Column(String(512))
    type = Column(String(256))


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    send_attempts = Column(Integer, default=0)
    is_draft = Column(Boolean, default=True)
    is_reply = Column(Boolean)
    reply_post_id = Column(Integer, ForeignKey("post.id"))
    reply_channel_tg_id = Column(BigInteger)
    reply_message_tg_id = Column(BigInteger)
    is_posted = Column(Boolean, default=False)
    date = Column(DateTime, default=func.now())
    type = Column(String(256))
    text = Column(Text)
    file_id = Column(String(512))
    manager_tg_id = Column(BigInteger, ForeignKey("user.tg_id"))
    bot_tg_id = Column(BigInteger, ForeignKey("bot.tg_id"))

    buttons = relationship("Button", cascade="all, delete-orphan")
    medias = relationship("Media", cascade="all, delete-orphan")
    manager = relationship("User")
    reply_post = relationship("Post", remote_side=[id])
    bot = relationship("Bot")
    channels = relationship("Channel", secondary="message", viewonly=True)
    messages = relationship("Message", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    user_tg_id = Column(BigInteger, ForeignKey("user.tg_id"))
    placeholder = Column(String(256))
    tag_values = relationship("TagValue", cascade="all, delete-orphan", lazy='dynamic')


class TagValue(Base):
    __tablename__ = "tag_value"

    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tag.id"))
    channel_tg_id = Column(BigInteger, ForeignKey("channel.tg_id"))
    channel = relationship("Channel")
    value = Column(String(256))


Base.metadata.create_all(engine)
