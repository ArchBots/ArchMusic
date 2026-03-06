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
from ArchMusic.utils.database import blacklist_chat, blacklisted_chats, whitelist_chat
from ArchMusic.utils.decorators.language import language

BLACKLISTCHAT_COMMAND = get_command("BLACKLISTCHAT_COMMAND")
WHITELISTCHAT_COMMAND = get_command("WHITELISTCHAT_COMMAND")
BLACKLISTEDCHAT_COMMAND = get_command("BLACKLISTEDCHAT_COMMAND")


@app.on_message(filters.command(BLACKLISTCHAT_COMMAND) & SUDOERS)
@language
async def blacklist_chat_func(client, message: Message, _):
    if len(message.command) != 2:
        return await message.reply_text(_["black_1"])
    try:
        chat_id = int(message.text.strip().split()[1])
    except ValueError:
        return await message.reply_text(_["black_1"])
    if chat_id in await blacklisted_chats():
        return await message.reply_text(_["black_2"])
    if await blacklist_chat(chat_id):
        await message.reply_text(_["black_3"])
    else:
        await message.reply_text("Something went wrong.")
    try:
        await app.leave_chat(chat_id)
    except Exception:
        pass


@app.on_message(filters.command(WHITELISTCHAT_COMMAND) & SUDOERS)
@language
async def whitelist_chat_func(client, message: Message, _):
    if len(message.command) != 2:
        return await message.reply_text(_["black_4"])
    try:
        chat_id = int(message.text.strip().split()[1])
    except ValueError:
        return await message.reply_text(_["black_4"])
    if chat_id not in await blacklisted_chats():
        return await message.reply_text(_["black_5"])
    if await whitelist_chat(chat_id):
        return await message.reply_text(_["black_6"])
    await message.reply_text("Something went wrong.")


@app.on_message(filters.command(BLACKLISTEDCHAT_COMMAND) & ~BANNED_USERS)
@language
async def all_blacklisted_chats(client, message: Message, _):
    chats = await blacklisted_chats()
    if not chats:
        return await message.reply_text(_["black_8"])
    text = _["black_7"]
    for count, chat_id in enumerate(chats, 1):
        try:
            title = (await app.get_chat(chat_id)).title
        except Exception:
            title = "Private"
        text += f"**{count}. {title}** [`{chat_id}`]\n"
    await message.reply_text(text)
