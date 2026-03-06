#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from typing import Union

from config import autoclean, chatstats, userstats
from config.config import time_to_seconds
from ArchMusic.misc import db


def _build_entry(
    original_chat_id, file, title, duration, user, vidid, stream, duration_in_seconds
):
    return {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }


def _insert(chat_id, entry, forceplay):
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, entry)
        else:
            db[chat_id] = [entry]
    else:
        db[chat_id].append(entry)


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
):
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except Exception:
        duration_in_seconds = 0

    entry = _build_entry(
        original_chat_id, file, title, duration, user, vidid, stream, duration_in_seconds
    )
    _insert(chat_id, entry, forceplay)

    autoclean.append(file)

    stat_vidid = "telegram" if vidid == "soundcloud" else vidid
    to_append = {"vidid": stat_vidid, "title": title}
    chatstats.setdefault(chat_id, []).append(to_append)
    userstats.setdefault(user_id, []).append(to_append)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
):
    entry = _build_entry(
        original_chat_id, file, title, duration, user, vidid, stream, 0
    )
    _insert(chat_id, entry, forceplay)
