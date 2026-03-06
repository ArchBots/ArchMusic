#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from ArchMusic import app
from ArchMusic.core.call import ArchMusic
from ArchMusic.utils.database import get_volume, is_active_chat, save_volume
from ArchMusic.utils.decorators.admins import AdminActual
from ArchMusic.utils.decorators.language import languageCB

_VOL_MIN = 1
_VOL_MAX = 200
_VOL_STEP = 10


async def _set_and_reply(chat_id: int, vol: int, message):
    vol = max(_VOL_MIN, min(vol, _VOL_MAX))
    try:
        await ArchMusic.volume_stream(chat_id, vol)
    except Exception:
        pass
    await save_volume(chat_id, vol)
    await message.reply_text(
        f"🔊 Volume set to <b>{vol}%</b> for this chat.",
        parse_mode="html",
    )


@app.on_message(
    filters.command(["volume", "vol", "setvol"])
    & filters.group
)
@AdminActual
async def volume_command(_, message: Message, __):
    chat_id = message.chat.id
    if not await is_active_chat(chat_id):
        return await message.reply_text("❌ No active stream in this chat.")
    args = message.command[1:]
    if not args:
        current = await get_volume(chat_id)
        return await message.reply_text(
            f"🔊 Current volume: <b>{current}%</b>\n"
            f"Usage: <code>/volume 1–{_VOL_MAX}</code>",
            parse_mode="html",
        )
    try:
        vol = int(args[0])
    except ValueError:
        return await message.reply_text(
            f"❌ Please provide a number between {_VOL_MIN} and {_VOL_MAX}."
        )
    await _set_and_reply(chat_id, vol, message)


@app.on_callback_query(filters.regex(r"^ADMIN Vol([+-])\|(-?\d+)$"))
@languageCB
async def volume_callback(_, query: CallbackQuery, __):
    chat_id = int(query.data.split("|")[1])
    direction = query.data.split("Vol")[1].split("|")[0]
    if not await is_active_chat(chat_id):
        return await query.answer("❌ No active stream.", show_alert=True)
    current = await get_volume(chat_id)
    vol = current + _VOL_STEP if direction == "+" else current - _VOL_STEP
    vol = max(_VOL_MIN, min(vol, _VOL_MAX))
    try:
        await ArchMusic.volume_stream(chat_id, vol)
    except Exception:
        return await query.answer("❌ Failed to change volume.", show_alert=True)
    await save_volume(chat_id, vol)
    await query.answer(f"🔊 Volume: {vol}%", show_alert=False)
