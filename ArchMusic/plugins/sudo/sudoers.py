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

from config import BANNED_USERS, MONGO_DB_URI, OWNER_ID
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import add_sudo, remove_sudo
from ArchMusic.utils.decorators.language import language

ADDSUDO_COMMAND = get_command("ADDSUDO_COMMAND")
DELSUDO_COMMAND = get_command("DELSUDO_COMMAND")
SUDOUSERS_COMMAND = get_command("SUDOUSERS_COMMAND")

_NO_MONGO_MSG = (
    "**Due to privacy reasons, sudo users cannot be managed "
    "without a personal database.\n\n"
    "Please set MONGO_DB_URI in your vars to use this feature.**"
)


async def _resolve_user(message: Message):
    """Return a User from reply or command argument, or None."""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) == 2:
        target = message.text.split(None, 1)[1].lstrip("@")
        return await app.get_users(target)
    return None


@app.on_message(filters.command(ADDSUDO_COMMAND) & filters.user(OWNER_ID))
@language
async def add_sudo_user(client, message: Message, _):
    if MONGO_DB_URI is None:
        return await message.reply_text(_NO_MONGO_MSG)
    user = await _resolve_user(message)
    if user is None:
        return await message.reply_text(_["general_1"])
    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention))
    if await add_sudo(user.id):
        SUDOERS.add(user.id)
        await message.reply_text(_["sudo_2"].format(user.mention))
    else:
        await message.reply_text("Failed to add sudo user.")


@app.on_message(filters.command(DELSUDO_COMMAND) & filters.user(OWNER_ID))
@language
async def del_sudo_user(client, message: Message, _):
    if MONGO_DB_URI is None:
        return await message.reply_text(_NO_MONGO_MSG)
    user = await _resolve_user(message)
    if user is None:
        return await message.reply_text(_["general_1"])
    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"])
    if await remove_sudo(user.id):
        SUDOERS.discard(user.id)
        await message.reply_text(_["sudo_4"])
    else:
        await message.reply_text("Something went wrong.")


@app.on_message(filters.command(SUDOUSERS_COMMAND) & ~BANNED_USERS)
@language
async def sudoers_list(client, message: Message, _):
    text = _["sudo_5"]
    count = 0
    # Owners first
    for user_id in OWNER_ID:
        try:
            user = await app.get_users(user_id)
            display = user.mention or user.first_name
            count += 1
            text += f"{count}➤ {display}\n"
        except Exception:
            continue
    # Additional sudo users (not owners)
    added_header = False
    for user_id in SUDOERS:
        if user_id in OWNER_ID:
            continue
        try:
            user = await app.get_users(user_id)
            display = user.mention or user.first_name
            if not added_header:
                text += _["sudo_6"]
                added_header = True
            count += 1
            text += f"{count}➤ {display}\n"
        except Exception:
            continue
    if count == 0:
        await message.reply_text(_["sudo_7"])
    else:
        await message.reply_text(text)
