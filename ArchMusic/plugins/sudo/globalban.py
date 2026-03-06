#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from config import BANNED_USERS
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils import get_readable_time
from ArchMusic.utils.database import (
    add_banned_user,
    get_banned_count,
    get_banned_users,
    get_served_chats,
    is_banned_user,
    remove_banned_user,
)
from ArchMusic.utils.decorators.language import language

GBAN_COMMAND = get_command("GBAN_COMMAND")
UNGBAN_COMMAND = get_command("UNGBAN_COMMAND")
GBANNED_COMMAND = get_command("GBANNED_COMMAND")


async def _resolve_user(message: Message):
    """Return (user_id, mention) from reply or command argument."""
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        return u.id, u.mention
    if len(message.command) == 2:
        target = message.text.split(None, 1)[1]
        user = await app.get_users(target)
        return user.id, user.mention
    return None, None


async def _get_served_chat_ids() -> list:
    return [int(c["chat_id"]) for c in await get_served_chats()]


@app.on_message(filters.command(GBAN_COMMAND) & SUDOERS)
@language
async def gban_user(client, message: Message, _):
    user_id, mention = await _resolve_user(message)
    if user_id is None:
        return await message.reply_text(_["general_1"])
    if user_id == message.from_user.id:
        return await message.reply_text(_["gban_1"])
    if user_id == app.id:
        return await message.reply_text(_["gban_2"])
    if user_id in SUDOERS:
        return await message.reply_text(_["gban_3"])
    if await is_banned_user(user_id):
        return await message.reply_text(_["gban_4"].format(mention))

    BANNED_USERS.add(user_id)
    served_chats = await _get_served_chat_ids()
    time_expected = get_readable_time(len(served_chats))
    mystic = await message.reply_text(_["gban_5"].format(mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user_id)
            number_of_chats += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.value))
        except Exception:
            pass

    await add_banned_user(user_id)
    await message.reply_text(_["gban_6"].format(mention, number_of_chats))
    await mystic.delete()


@app.on_message(filters.command(UNGBAN_COMMAND) & SUDOERS)
@language
async def ungban_user(client, message: Message, _):
    user_id, mention = await _resolve_user(message)
    if user_id is None:
        return await message.reply_text(_["general_1"])
    if not await is_banned_user(user_id):
        return await message.reply_text(_["gban_7"].format(mention))

    BANNED_USERS.discard(user_id)
    served_chats = await _get_served_chat_ids()
    time_expected = get_readable_time(len(served_chats))
    mystic = await message.reply_text(_["gban_8"].format(mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user_id)
            number_of_chats += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.value))
        except Exception:
            pass

    await remove_banned_user(user_id)
    await message.reply_text(_["gban_9"].format(mention, number_of_chats))
    await mystic.delete()


@app.on_message(filters.command(GBANNED_COMMAND) & SUDOERS)
@language
async def gbanned_list(client, message: Message, _):
    counts = await get_banned_count()
    if counts == 0:
        return await message.reply_text(_["gban_10"])
    mystic = await message.reply_text(_["gban_11"])
    msg = "Gbanned Users:\n\n"
    count = 0
    for user_id in await get_banned_users():
        try:
            user = await app.get_users(user_id)
            display = user.mention or user.first_name
            count += 1
            msg += f"{count}➤ {display}\n"
        except Exception:
            count += 1
            msg += f"{count}➤ [Unfetched User] `{user_id}`\n"
    if count == 0:
        return await mystic.edit_text(_["gban_10"])
    await mystic.edit_text(msg)
