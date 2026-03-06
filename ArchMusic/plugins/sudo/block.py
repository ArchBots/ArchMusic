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

from config import BANNED_USERS
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import add_gban_user, remove_gban_user
from ArchMusic.utils.decorators.language import language

BLOCK_COMMAND = get_command("BLOCK_COMMAND")
UNBLOCK_COMMAND = get_command("UNBLOCK_COMMAND")
BLOCKED_COMMAND = get_command("BLOCKED_COMMAND")


async def _resolve_user(message: Message):
    """Return a User from reply or command argument, or None on bad input."""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) == 2:
        target = message.text.split(None, 1)[1].lstrip("@")
        return await app.get_users(target)
    return None


@app.on_message(filters.command(BLOCK_COMMAND) & SUDOERS)
@language
async def block_user(client, message: Message, _):
    user = await _resolve_user(message)
    if user is None:
        return await message.reply_text(_["general_1"])
    if user.id in BANNED_USERS:
        return await message.reply_text(_["block_1"].format(user.mention))
    await add_gban_user(user.id)
    BANNED_USERS.add(user.id)
    await message.reply_text(_["block_2"].format(user.mention))


@app.on_message(filters.command(UNBLOCK_COMMAND) & SUDOERS)
@language
async def unblock_user(client, message: Message, _):
    user = await _resolve_user(message)
    if user is None:
        return await message.reply_text(_["general_1"])
    if user.id not in BANNED_USERS:
        return await message.reply_text(_["block_3"])
    await remove_gban_user(user.id)
    BANNED_USERS.discard(user.id)
    await message.reply_text(_["block_4"])


@app.on_message(filters.command(BLOCKED_COMMAND) & SUDOERS)
@language
async def blocked_users_list(client, message: Message, _):
    if not BANNED_USERS:
        return await message.reply_text(_["block_5"])
    mystic = await message.reply_text(_["block_6"])
    msg = _["block_7"]
    count = 0
    for user_id in BANNED_USERS:
        try:
            user = await app.get_users(user_id)
            display = user.mention or user.first_name
            count += 1
            msg += f"{count}➤ {display}\n"
        except Exception:
            continue
    if count == 0:
        return await mystic.edit_text(_["block_5"])
    await mystic.edit_text(msg)
