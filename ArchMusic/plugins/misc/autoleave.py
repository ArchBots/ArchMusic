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
from datetime import datetime

import config
from pyrogram.enums import ChatType

from ArchMusic import app
from ArchMusic.core.call import ArchMusic, autoend
from ArchMusic.utils.database import get_client, is_active_chat, is_autoend

_LEAVE_MAX      = 20
_AUTOEND_POLL   = 5
_PROTECTED_IDS  = {
    config.LOG_GROUP_ID,
    -1001952511944,   # support group
    -1001996363416,   # channel
}
_GROUP_TYPES    = {ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL}
_INACTIVITY_MSG = (
    "Bot has left voice chat due to inactivity to avoid overload on servers. "
    "No-one was listening to the bot on voice chat."
)


async def auto_leave():
    if config.AUTO_LEAVING_ASSISTANT != str(True):
        return
    while not await asyncio.sleep(config.AUTO_LEAVE_ASSISTANT_TIME):
        from ArchMusic.core.userbot import assistants
        for num in assistants:
            client = await get_client(num)
            left = 0
            try:
                async for dialog in client.iter_dialogs():
                    if dialog.chat.type not in _GROUP_TYPES:
                        continue
                    if left >= _LEAVE_MAX:
                        break
                    chat_id = dialog.chat.id
                    if chat_id in _PROTECTED_IDS:
                        continue
                    if not await is_active_chat(chat_id):
                        try:
                            await client.leave_chat(chat_id)
                            left += 1
                        except Exception:
                            continue
            except Exception:
                pass


async def auto_end():
    while not await asyncio.sleep(_AUTOEND_POLL):
        if not await is_autoend():
            continue
        for chat_id in list(autoend):
            timer = autoend.get(chat_id)
            if not timer:
                continue
            if datetime.now() <= timer:
                continue
            autoend[chat_id] = {}
            if not await is_active_chat(chat_id):
                continue
            try:
                await ArchMusic.stop_stream(chat_id)
            except Exception:
                continue
            try:
                await app.send_message(chat_id, _INACTIVITY_MSG)
            except Exception:
                continue


asyncio.create_task(auto_leave())
asyncio.create_task(auto_end())
