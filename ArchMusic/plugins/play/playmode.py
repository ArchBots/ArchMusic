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
from pyrogram.types import InlineKeyboardMarkup, Message

from config import BANNED_USERS
from strings import get_command
from ArchMusic import app
from ArchMusic.utils.database import get_playmode, get_playtype, is_nonadmin_chat
from ArchMusic.utils.decorators import language
from ArchMusic.utils.inline.settings import playmode_users_markup

PLAYMODE_COMMAND = get_command("PLAYMODE_COMMAND")


@app.on_message(
    filters.command(PLAYMODE_COMMAND) & filters.group & ~BANNED_USERS
)
@language
async def playmode_(client, message: Message, _):
    chat_id = message.chat.id

    playmode     = await get_playmode(chat_id)
    is_non_admin = await is_nonadmin_chat(chat_id)
    playty       = await get_playtype(chat_id)

    Direct   = playmode == "Direct"
    Group    = not is_non_admin
    Playtype = playty != "Everyone"

    buttons = playmode_users_markup(_, Direct, Group, Playtype)
    await message.reply_text(
        _["playmode_1"].format(message.chat.title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
