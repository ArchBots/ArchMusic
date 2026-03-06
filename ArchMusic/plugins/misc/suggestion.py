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
import random
from datetime import datetime, timedelta

import config
from config import clean
from strings import get_string
from ArchMusic import app
from ArchMusic.utils.database import (
    get_lang,
    get_private_served_chats,
    get_served_chats,
    is_suggestion,
)

_LEAVE_TIME = config.AUTO_SUGGESTION_TIME
_suggestor  = {}

_SUG_STRINGS = [
    k for k in get_string("en")
    if k.startswith("sug") and k != "sug_0"
]


def _pick_suggestion(chat_id: int) -> str:
    previous = _suggestor.get(chat_id)
    choice   = random.choice(_SUG_STRINGS)
    if previous and len(_SUG_STRINGS) > 1:
        while choice.split("_")[1] == previous:
            choice = random.choice(_SUG_STRINGS)
    _suggestor[chat_id] = choice.split("_")[1]
    return choice


async def dont_do_this():
    if config.AUTO_SUGGESTION_MODE != str(True):
        return
    while not await asyncio.sleep(_LEAVE_TIME):
        try:
            getter = (
                get_private_served_chats
                if config.PRIVATE_BOT_MODE == str(True)
                else get_served_chats
            )
            schats = await getter()
            chats  = [int(c["chat_id"]) for c in schats]
            random.shuffle(chats)

            limit   = max(1, len(chats) // 10) if len(chats) >= 100 else len(chats)
            send_to = 0

            for chat_id in chats:
                if send_to >= limit:
                    break
                if chat_id == config.LOG_GROUP_ID:
                    continue
                if not await is_suggestion(chat_id):
                    continue

                try:
                    _ = get_string(await get_lang(chat_id))
                except Exception:
                    _ = get_string("en")

                string = _pick_suggestion(chat_id)
                try:
                    sent = await app.send_message(chat_id, _["sug_0"] + _[string])
                    clean.setdefault(chat_id, []).append({
                        "msg_id":      sent.id,
                        "timer_after": datetime.now() + timedelta(
                            minutes=config.CLEANMODE_DELETE_MINS
                        ),
                    })
                    send_to += 1
                except Exception:
                    pass
        except Exception:
            pass


asyncio.create_task(dont_do_this())
