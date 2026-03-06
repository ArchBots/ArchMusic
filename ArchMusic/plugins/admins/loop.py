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
from pyrogram.types import Message

from config import BANNED_USERS
from strings import get_command
from ArchMusic import app
from ArchMusic.utils.database.memorydatabase import get_loop, set_loop
from ArchMusic.utils.decorators import AdminRightsCheck

LOOP_COMMAND = get_command("LOOP_COMMAND")

_LOOP_MAX = 10


@app.on_message(
    filters.command(LOOP_COMMAND) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def loop_com(cli, message: Message, _, chat_id):
    if len(message.command) != 2:
        return await message.reply_text(_["admin_24"])
    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await set_loop(chat_id, _LOOP_MAX)
        return await message.reply_text(
            _["admin_25"].format(message.from_user.first_name, _LOOP_MAX)
        )
    if state == "disable":
        await set_loop(chat_id, 0)
        return await message.reply_text(_["admin_27"])
    if state.isnumeric():
        n = int(state)
        if not 1 <= n <= _LOOP_MAX:
            return await message.reply_text(_["admin_26"])
        current = await get_loop(chat_id)
        total = min(current + n if current != 0 else n, _LOOP_MAX)
        await set_loop(chat_id, total)
        return await message.reply_text(
            _["admin_25"].format(message.from_user.first_name, total)
        )
    await message.reply_text(_["admin_24"])
