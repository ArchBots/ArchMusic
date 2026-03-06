#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram import filters
from pyrogram.types import Message

from strings import get_command, get_string
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import get_lang, is_maintenance, maintenance_off, maintenance_on
from ArchMusic.utils.decorators.language import language

MAINTENANCE_COMMAND = get_command("MAINTENANCE_COMMAND")


@app.on_message(filters.command(MAINTENANCE_COMMAND) & SUDOERS)
async def maintenance(client, message: Message):
    try:
        lang = await get_lang(message.chat.id)
        _ = get_string(lang)
    except Exception:
        _ = get_string("en")

    usage = _["maint_1"]
    if len(message.command) != 2:
        return await message.reply_text(usage)

    state = message.text.split(None, 1)[1].strip().lower()
    # BUG FIX: original had the is_maintenance() checks inverted —
    # it reported "already enabled" when trying to enable (and mode was off).
    # is_maintenance() returns True when maintenance is ON.
    currently_on = await is_maintenance()

    if state == "enable":
        if currently_on:
            await message.reply_text("Maintenance mode is already enabled.")
        else:
            await maintenance_on()
            await message.reply_text(_["maint_2"])
    elif state == "disable":
        if not currently_on:
            await message.reply_text("Maintenance mode is already disabled.")
        else:
            await maintenance_off()
            await message.reply_text(_["maint_3"])
    else:
        await message.reply_text(usage)
