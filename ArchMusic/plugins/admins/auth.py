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

from config import BANNED_USERS, adminlist
from strings import get_command
from ArchMusic import app
from ArchMusic.utils.database import (
    delete_authuser,
    get_authuser,
    get_authuser_names,
    save_authuser,
)
from ArchMusic.utils.decorators import AdminActual, language
from ArchMusic.utils.formatters import int_to_alpha

AUTH_COMMAND      = get_command("AUTH_COMMAND")
UNAUTH_COMMAND    = get_command("UNAUTH_COMMAND")
AUTHUSERS_COMMAND = get_command("AUTHUSERS_COMMAND")

_AUTH_LIMIT = 20


def _update_adminlist(chat_id: int, user_id: int, add: bool):
    lst = adminlist.get(chat_id)
    if not lst:
        return
    if add and user_id not in lst:
        lst.append(user_id)
    elif not add and user_id in lst:
        lst.remove(user_id)


async def _resolve_user(message: Message):
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        return u.id, u.first_name
    if len(message.command) != 2:
        return None, None
    username = message.text.split(None, 1)[1].lstrip("@")
    user = await app.get_users(username)
    return user.id, user.first_name


@app.on_message(
    filters.command(AUTH_COMMAND) & filters.group & ~BANNED_USERS
)
@AdminActual
async def auth(client, message: Message, _):
    user_id, user_name = await _resolve_user(message)
    if user_id is None:
        return await message.reply_text(_["general_1"])
    existing = await get_authuser_names(message.chat.id)
    if len(existing) >= _AUTH_LIMIT:
        return await message.reply_text(_["auth_1"])
    token = await int_to_alpha(user_id)
    if token in existing:
        return await message.reply_text(_["auth_3"])
    assis = {
        "auth_user_id": user_id,
        "auth_name": user_name,
        "admin_id": message.from_user.id,
        "admin_name": message.from_user.first_name,
    }
    _update_adminlist(message.chat.id, user_id, add=True)
    await save_authuser(message.chat.id, token, assis)
    await message.reply_text(_["auth_2"])


@app.on_message(
    filters.command(UNAUTH_COMMAND) & filters.group & ~BANNED_USERS
)
@AdminActual
async def unauthusers(client, message: Message, _):
    user_id, _ = await _resolve_user(message)
    if user_id is None:
        return await message.reply_text(_["general_1"])
    token   = await int_to_alpha(user_id)
    deleted = await delete_authuser(message.chat.id, token)
    _update_adminlist(message.chat.id, user_id, add=False)
    if deleted:
        await message.reply_text(_["auth_4"])
    else:
        await message.reply_text(_["auth_5"])


@app.on_message(
    filters.command(AUTHUSERS_COMMAND) & filters.group & ~BANNED_USERS
)
@language
async def authusers(client, message: Message, _):
    names = await get_authuser_names(message.chat.id)
    if not names:
        return await message.reply_text(_["setting_5"])
    mystic = await message.reply_text(_["auth_6"])
    text   = _["auth_7"]
    j      = 0
    for token in names:
        rec = await get_authuser(message.chat.id, token)
        user_id    = rec["auth_user_id"]
        admin_id   = rec["admin_id"]
        admin_name = rec["admin_name"]
        try:
            user = await app.get_users(user_id)
            j   += 1
        except Exception:
            continue
        text += f"{j}➤ {user.first_name}[`{user_id}`]\n"
        text += f"   {_['auth_8']} {admin_name}[`{admin_id}`]\n\n"
    await mystic.delete()
    await message.reply_text(text)
