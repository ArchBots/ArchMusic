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

from pyrogram.types import InlineKeyboardMarkup

from strings import get_string
from ArchMusic.misc import db
from ArchMusic.utils.database import get_active_chats, get_lang, is_music_playing
from ArchMusic.utils.formatters import seconds_to_min
from ArchMusic.utils.inline import stream_markup_timer, telegram_markup_timer

from ..admins.callback import wrong

_TIMER_POLL  = 1
_MARKUP_POLL = 4
_LIVE_TYPES  = ("index_", "live_")


async def timer():
    while not await asyncio.sleep(_TIMER_POLL):
        for chat_id in await get_active_chats():
            if not await is_music_playing(chat_id):
                continue
            playing = db.get(chat_id)
            if not playing:
                continue
            file_path = playing[0]["file"]
            if any(t in file_path for t in _LIVE_TYPES):
                continue
            if int(playing[0]["seconds"]) == 0:
                continue
            db[chat_id][0]["played"] += 1


async def markup_timer():
    while not await asyncio.sleep(_MARKUP_POLL):
        for chat_id in await get_active_chats():
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                if int(playing[0]["seconds"]) == 0:
                    continue

                mystic = playing[0].get("mystic")
                markup = playing[0].get("markup")
                if not mystic or not markup:
                    continue

                if wrong.get(chat_id, {}).get(mystic.id) is False:
                    continue

                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except Exception:
                    _ = get_string("en")

                played = seconds_to_min(playing[0]["played"])
                dur    = playing[0]["dur"]
                vidid  = playing[0]["vidid"]

                buttons = (
                    stream_markup_timer(_, vidid, chat_id, played, dur)
                    if markup == "stream"
                    else telegram_markup_timer(_, chat_id, played, dur)
                )
                await mystic.edit_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except Exception:
                continue


asyncio.create_task(timer())
asyncio.create_task(markup_timer())
