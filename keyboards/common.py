import re

from aiogram import types
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from model.models import Button


class StepbackCallback(CallbackData, prefix='stepback'):
    pass


class NextCallback(CallbackData, prefix='next'):
    pass


nextBtn = types.InlineKeyboardButton(text="Далее", callback_data=NextCallback().pack())
backBtn = types.InlineKeyboardButton(text="Назад", callback_data=StepbackCallback().pack())


def simple_stepback_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data=StepbackCallback())
    return builder.as_markup()


def url_buttons_kb(buttons: list[Button]):
    builder = InlineKeyboardBuilder()
    for btn in buttons:
        placeholders = re.findall("%(.[ЁёА-я-A-Za-z-0-9-_]*?)%", btn.link)
        builder.button(
            text=btn.text,
            url="http://www.example.com/" if placeholders else btn.link
        )
    builder.adjust(1)
    return builder.as_markup()
