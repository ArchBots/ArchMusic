#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait
from pyrogram.raw import types

import config
from config import adminlist, chatstats, clean, userstats
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_particular_top,
    get_served_chats,
    get_served_users,
    get_user_top,
    is_cleanmode_on,
    set_queries,
    update_particular_top,
    update_user_top,
)
from ArchMusic.utils.decorators.language import language
from ArchMusic.utils.formatters import alpha_to_int

BROADCAST_COMMAND = get_command("BROADCAST_COMMAND")

_AUTO_DELETE      = config.CLEANMODE_DELETE_MINS
_AUTO_SLEEP       = 5
_SKIP_CHAT        = -1001764725348
_IS_BROADCASTING  = False
_cleanmode_group  = 15


def _parse_flags(text: str) -> dict:
    return {
        "pin":       "-pin" in text and "-pinloud" not in text,
        "pinloud":   "-pinloud" in text,
        "nobot":     "-nobot" in text,
        "assistant": "-assistant" in text,
        "user":      "-user" in text,
    }


@app.on_raw_update(group=_cleanmode_group)
async def clean_mode(client, update, users, chats):
    if _IS_BROADCASTING:
        return
    try:
        if not isinstance(update, types.UpdateReadChannelOutbox):
            return
    except Exception:
        return
    if users or chats:
        return
    chat_id    = int(f"-100{update.channel_id}")
    message_id = update.max_id
    if not await is_cleanmode_on(chat_id):
        return
    clean.setdefault(chat_id, []).append({
        "msg_id":      message_id,
        "timer_after": datetime.now() + timedelta(minutes=_AUTO_DELETE),
    })
    await set_queries(1)


@app.on_message(filters.command(BROADCAST_COMMAND) & SUDOERS)
@language
async def broadcast_message(client, message, _):
    global _IS_BROADCASTING

    if message.reply_to_message:
        src_chat = message.chat.id
        src_msg  = message.reply_to_message.id
        query    = None
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_5"])
        raw   = message.text.split(None, 1)[1]
        query = raw
        for flag in ("-pin", "-nobot", "-pinloud", "-assistant", "-user"):
            query = query.replace(flag, "")
        query = query.strip()
        if not query:
            return await message.reply_text(_["broad_6"])
        src_chat = src_msg = None

    flags = _parse_flags(message.text)
    _IS_BROADCASTING = True

    async def _send(target, client_=app):
        if src_msg:
            return await client_.forward_messages(target, src_chat, src_msg)
        return await client_.send_message(target, text=query)

    try:
        if not flags["nobot"]:
            sent = pin = 0
            for chat in await get_served_chats():
                chat_id = int(chat["chat_id"])
                if chat_id == _SKIP_CHAT:
                    continue
                try:
                    m = await _send(chat_id)
                    if flags["pin"]:
                        try:
                            await m.pin(disable_notification=True)
                            pin += 1
                        except Exception:
                            pass
                    elif flags["pinloud"]:
                        try:
                            await m.pin(disable_notification=False)
                            pin += 1
                        except Exception:
                            pass
                    sent += 1
                except FloodWait as e:
                    if int(e.value) <= 200:
                        await asyncio.sleep(e.value)
                except Exception:
                    continue
            try:
                await message.reply_text(_["broad_1"].format(sent, pin))
            except Exception:
                pass

        if flags["user"]:
            susr = 0
            for user in await get_served_users():
                user_id = int(user["user_id"])
                try:
                    await _send(user_id)
                    susr += 1
                except FloodWait as e:
                    if int(e.value) <= 200:
                        await asyncio.sleep(e.value)
                except Exception:
                    pass
            try:
                await message.reply_text(_["broad_7"].format(susr))
            except Exception:
                pass

        if flags["assistant"]:
            from ArchMusic.core.userbot import assistants
            aw   = await message.reply_text(_["broad_2"])
            text = _["broad_3"]
            for num in assistants:
                sent   = 0
                aclient = await get_client(num)
                async for dialog in aclient.get_dialogs():
                    if dialog.chat.id == _SKIP_CHAT:
                        continue
                    try:
                        await _send(dialog.chat.id, aclient)
                        sent += 1
                    except FloodWait as e:
                        if int(e.value) <= 200:
                            await asyncio.sleep(e.value)
                    except Exception:
                        continue
                text += _["broad_4"].format(num, sent)
            try:
                await aw.edit_text(text)
            except Exception:
                pass

    finally:
        _IS_BROADCASTING = False


async def _upsert_top(getter, updater, key, vidid, title):
    spot = await getter(key, vidid)
    next_spot = (spot["spot"] + 1) if spot else 1
    await updater(key, vidid, {"spot": next_spot, "title": title})


async def auto_clean():
    while not await asyncio.sleep(_AUTO_SLEEP):
        try:
            for chat_id in list(chatstats):
                for dic in list(chatstats[chat_id]):
                    chatstats[chat_id].pop(0)
                    await _upsert_top(
                        get_particular_top, update_particular_top,
                        chat_id, dic["vidid"], dic["title"]
                    )
        except Exception:
            pass

        try:
            for user_id in list(userstats):
                for dic in list(userstats[user_id]):
                    userstats[user_id].pop(0)
                    await _upsert_top(
                        get_user_top, update_user_top,
                        user_id, dic["vidid"], dic["title"]
                    )
        except Exception:
            pass

        try:
            for chat_id in list(clean):
                if chat_id == config.LOG_GROUP_ID:
                    continue
                remaining = []
                for entry in clean[chat_id]:
                    if datetime.now() > entry["timer_after"]:
                        try:
                            await app.delete_messages(chat_id, entry["msg_id"])
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                            remaining.append(entry)
                        except Exception:
                            pass
                    else:
                        remaining.append(entry)
                clean[chat_id] = remaining
        except Exception:
            pass

        try:
            for chat_id in await get_active_chats():
                if chat_id in adminlist:
                    continue
                adminlist[chat_id] = []
                try:
                    async for member in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if (
                            member.privileges
                            and member.privileges.can_manage_video_chats
                        ):
                            adminlist[chat_id].append(member.user.id)
                except Exception:
                    pass
                for token in await get_authuser_names(chat_id):
                    adminlist[chat_id].append(await alpha_to_int(token))
        except Exception:
            pass


asyncio.create_task(auto_clean())
