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
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from config import BANNED_USERS
from strings import get_command
from ArchMusic import YouTube, app
from ArchMusic.core.call import ArchMusic
from ArchMusic.misc import db
from ArchMusic.utils.database import get_loop
from ArchMusic.utils.decorators import AdminRightsCheck
from ArchMusic.utils.inline.play import stream_markup, telegram_markup
from ArchMusic.utils.stream.autoclear import auto_clean
from ArchMusic.utils.thumbnails import gen_thumb

SKIP_COMMAND = get_command("SKIP_COMMAND")


async def _play_next(message: Message, _, chat_id: int):
    check = db.get(chat_id)
    if not check:
        return

    queued     = check[0]["file"]
    title      = check[0]["title"].title()
    user       = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid    = check[0]["vidid"]
    status     = True if str(streamtype) == "video" else None
    db[chat_id][0]["played"] = 0

    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_11"].format(title))
        try:
            await ArchMusic.skip_stream(chat_id, link, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        img = await gen_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                user, f"https://t.me/{app.username}?start=info_{videoid}"
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    elif "vid_" in queued:
        mystic = await message.reply_text(_["call_10"], disable_web_page_preview=True)
        try:
            file_path, direct = await YouTube.download(
                videoid, mystic, videoid=True, video=status
            )
        except Exception:
            return await mystic.edit_text(_["call_9"])
        try:
            await ArchMusic.skip_stream(chat_id, file_path, video=status)
        except Exception:
            return await mystic.edit_text(_["call_9"])
        button = stream_markup(_, videoid, chat_id)
        img = await gen_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                user, f"https://t.me/{app.username}?start=info_{videoid}"
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()

    elif "index_" in queued:
        try:
            await ArchMusic.skip_stream(chat_id, videoid, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        run = await message.reply_photo(
            photo=config.STREAM_IMG_URL,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    else:
        try:
            await ArchMusic.skip_stream(chat_id, queued, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        if videoid in ("telegram", "soundcloud"):
            photo = (
                config.SOUNCLOUD_IMG_URL
                if videoid == "soundcloud"
                else (
                    config.TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else config.TELEGRAM_VIDEO_URL
                )
            )
            button = telegram_markup(_, chat_id)
            run = await message.reply_photo(
                photo=photo,
                caption=_["stream_3"].format(title, check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            button = stream_markup(_, videoid, chat_id)
            img = await gen_thumb(videoid)
            run = await message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    user, f"https://t.me/{app.username}?start=info_{videoid}"
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"


@app.on_message(
    filters.command(SKIP_COMMAND) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    check = db.get(chat_id)

    if len(message.command) >= 2:
        loop = await get_loop(chat_id)
        if loop != 0:
            return await message.reply_text(_["admin_12"])
        state = message.text.split(None, 1)[1].strip()
        if not state.isnumeric():
            return await message.reply_text(_["admin_13"])
        state = int(state)
        if not check:
            return await message.reply_text(_["queue_2"])
        count = len(check)
        if count <= 2:
            return await message.reply_text(_["admin_14"])
        max_skip = count - 1
        if not 1 <= state <= max_skip:
            return await message.reply_text(_["admin_15"].format(max_skip))
        for _ in range(state):
            popped = None
            try:
                popped = check.pop(0)
            except Exception:
                return await message.reply_text(_["admin_16"])
            if popped and config.AUTO_DOWNLOADS_CLEAR == str(True):
                await auto_clean(popped)
            if not check:
                try:
                    await message.reply_text(
                        _["admin_10"].format(message.from_user.first_name)
                    )
                    await ArchMusic.stop_stream(chat_id)
                except Exception:
                    pass
                return
    else:
        try:
            popped = check.pop(0)
            if popped and config.AUTO_DOWNLOADS_CLEAR == str(True):
                await auto_clean(popped)
            if not check:
                await message.reply_text(
                    _["admin_10"].format(message.from_user.first_name)
                )
                try:
                    return await ArchMusic.stop_stream(chat_id)
                except Exception:
                    return
        except Exception:
            try:
                await message.reply_text(
                    _["admin_10"].format(message.from_user.first_name)
                )
                return await ArchMusic.stop_stream(chat_id)
            except Exception:
                return

    await _play_next(message, _, chat_id)
