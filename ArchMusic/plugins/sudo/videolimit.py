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

from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import set_video_limit
from ArchMusic.utils.decorators.language import language

VIDEOLIMIT_COMMAND = get_command("VIDEOLIMIT_COMMAND")


@app.on_message(filters.command(VIDEOLIMIT_COMMAND) & SUDOERS)
@language
async def set_video_limit_cmd(client, message: Message, _):
    if len(message.command) != 2:
        return await message.reply_text(_["vid_1"])
    state = message.text.split(None, 1)[1].strip()
    if state.lower() == "disable":
        await set_video_limit(0)
        return await message.reply_text(_["vid_4"])
    if not state.isnumeric():
        return await message.reply_text(_["vid_2"])
    limit = int(state)
    await set_video_limit(limit)
    if limit == 0:
        return await message.reply_text(_["vid_4"])
    await message.reply_text(_["vid_3"].format(limit))
