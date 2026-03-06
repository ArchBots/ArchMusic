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

import config
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import (
    add_private_chat,
    get_private_served_chats,
    is_served_private_chat,
    remove_private_chat,
)
from ArchMusic.utils.decorators.language import language

AUTHORIZE_COMMAND = get_command("AUTHORIZE_COMMAND")
UNAUTHORIZE_COMMAND = get_command("UNAUTHORIZE_COMMAND")
AUTHORIZED_COMMAND = get_command("AUTHORIZED_COMMAND")

_PRIVATE_MODE = config.PRIVATE_BOT_MODE == str(True)


def _parse_chat_id(message: Message):
    """Return int chat_id from command arg, or raise ValueError."""
    return int(message.text.strip().split()[1])


@app.on_message(filters.command(AUTHORIZE_COMMAND) & SUDOERS)
@language
async def authorize(client, message: Message, _):
    if not _PRIVATE_MODE:
        return await message.reply_text(_["pbot_12"])
    if len(message.command) != 2:
        return await message.reply_text(_["pbot_1"])
    try:
        chat_id = _parse_chat_id(message)
    except (ValueError, IndexError):
        return await message.reply_text(_["pbot_7"])
    if await is_served_private_chat(chat_id):
        return await message.reply_text(_["pbot_5"])
    await add_private_chat(chat_id)
    await message.reply_text(_["pbot_3"])


@app.on_message(filters.command(UNAUTHORIZE_COMMAND) & SUDOERS)
@language
async def unauthorize(client, message: Message, _):
    if not _PRIVATE_MODE:
        return await message.reply_text(_["pbot_12"])
    if len(message.command) != 2:
        return await message.reply_text(_["pbot_2"])
    try:
        chat_id = _parse_chat_id(message)
    except (ValueError, IndexError):
        return await message.reply_text(_["pbot_7"])
    if not await is_served_private_chat(chat_id):
        return await message.reply_text(_["pbot_6"])
    await remove_private_chat(chat_id)
    await message.reply_text(_["pbot_4"])


@app.on_message(filters.command(AUTHORIZED_COMMAND) & SUDOERS)
@language
async def authorized(client, message: Message, _):
    if not _PRIVATE_MODE:
        return await message.reply_text(_["pbot_12"])
    m = await message.reply_text(_["pbot_8"])
    chats = await get_private_served_chats()
    served_ids = [int(c["chat_id"]) for c in chats]
    if not served_ids:
        return await m.edit(_["pbot_11"])

    known_text = _["pbot_9"]
    unknown_text = _["pbot_13"]
    known_count = 0
    unknown_count = 0
    for chat_id in served_ids:
        try:
            title = (await app.get_chat(chat_id)).title
            known_count += 1
            known_text += f"{known_count}:- {title[:15]} [{chat_id}]\n"
        except Exception:
            unknown_count += 1
            unknown_text += f"{unknown_count}:- {_['pbot_10']} [{chat_id}]\n"

    if known_count == 0 and unknown_count == 0:
        return await m.edit(_["pbot_11"])
    result = known_text if known_count else ""
    if unknown_count:
        result = f"{result} {unknown_text}".strip()
    await m.edit(result)
