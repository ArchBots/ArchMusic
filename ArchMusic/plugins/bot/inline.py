#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
)
from youtubesearchpython.__future__ import VideosSearch

from config import BANNED_USERS, MUSIC_BOT_NAME
from ArchMusic import app
from ArchMusic.utils.inlinequery import answer

_INLINE_LIMIT   = 15
_CACHE_TIME_EMPTY = 10


def _build_result(item: dict) -> InlineQueryResultPhoto:
    title       = item["title"].title()
    duration    = item["duration"]
    views       = item["viewCount"]["short"]
    thumbnail   = item["thumbnails"][0]["url"].split("?")[0]
    channel     = item["channel"]["name"]
    channellink = item["channel"]["link"]
    link        = item["link"]
    published   = item["publishedTime"]

    caption = (
        f"❇️**Title:** [{title}]({link})\n\n"
        f"⏳**Duration:** {duration} Mins\n"
        f"👀**Views:** `{views}`\n"
        f"⏰**Published Time:** {published}\n"
        f"🎥**Channel Name:** {channel}\n"
        f"📎**Channel Link:** [Visit From Here]({channellink})\n\n"
        f"__Reply with /play on this searched message to stream it on voice chat.__\n\n"
        f"⚡️ **Inline Search By {MUSIC_BOT_NAME}**"
    )

    return InlineQueryResultPhoto(
        photo_url=thumbnail,
        title=title,
        thumb_url=thumbnail,
        description=f"{views} | {duration} Mins | {channel} | {published}",
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🎥 Watch on Youtube", url=link)]]
        ),
    )


@app.on_inline_query(~BANNED_USERS)
async def inline_query_handler(client, query):
    text = query.query.strip().lower()

    if not text:
        try:
            await client.answer_inline_query(
                query.id, results=answer, cache_time=_CACHE_TIME_EMPTY
            )
        except Exception:
            pass
        return

    search = VideosSearch(text, limit=_INLINE_LIMIT * 2)
    result = (await search.next()).get("result", [])

    answers = []
    for item in result[:_INLINE_LIMIT]:
        try:
            answers.append(_build_result(item))
        except (KeyError, IndexError):
            continue

    try:
        await client.answer_inline_query(query.id, results=answers)
    except Exception:
        pass
