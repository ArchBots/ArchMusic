#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BANNED_USERS
from strings import get_command, get_string, languages_present
from ArchMusic import app
from ArchMusic.utils.database import get_lang, set_lang
from ArchMusic.utils.decorators import ActualAdminCB, language, languageCB


def _chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def lanuages_keyboard(_):
    buttons = [
        InlineKeyboardButton(
            text=languages_present[i],
            callback_data=f"languages:{i}",
        )
        for i in languages_present
    ]
    rows = [list(row) for row in _chunk(buttons, 3)]
    rows.append([
        InlineKeyboardButton(
            text=_["BACK_BUTTON"],
            callback_data="settingsback_helper",
        ),
        InlineKeyboardButton(
            text=_["CLOSE_BUTTON"],
            callback_data="close",
        ),
    ])
    return InlineKeyboardMarkup(rows)


LANGUAGE_COMMAND = get_command("LANGUAGE_COMMAND")


@app.on_message(
    filters.command(LANGUAGE_COMMAND)
    & filters.group
    & ~BANNED_USERS
)
@language
async def langs_command(client, message: Message, _):
    keyboard = lanuages_keyboard(_)
    await message.reply_text(
        _["setting_1"].format(message.chat.title, message.chat.id),
        reply_markup=keyboard,
    )


@app.on_callback_query(filters.regex("LG") & ~BANNED_USERS)
@languageCB
async def lanuagecb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    keyboard = lanuages_keyboard(_)
    return await CallbackQuery.edit_message_reply_markup(
        reply_markup=keyboard
    )


@app.on_callback_query(
    filters.regex(r"languages:(.*?)") & ~BANNED_USERS
)
@ActualAdminCB
async def language_markup(client, CallbackQuery, _):
    langauge = (CallbackQuery.data).split(":")[1]
    old = await get_lang(CallbackQuery.message.chat.id)
    if str(old) == str(langauge):
        return await CallbackQuery.answer(
            "You're already on same language", show_alert=True
        )
    try:
        _ = get_string(langauge)
        await CallbackQuery.answer(
            "Successfully changed your language.", show_alert=True
        )
    except:
        return await CallbackQuery.answer(
            "Failed to change language or Language under update.",
            show_alert=True,
        )
    await set_lang(CallbackQuery.message.chat.id, langauge)
    keyboard = lanuages_keyboard(_)
    return await CallbackQuery.edit_message_reply_markup(
        reply_markup=keyboard
    )
