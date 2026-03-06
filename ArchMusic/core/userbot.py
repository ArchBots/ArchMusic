#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import sys

from pyrogram import Client
from pyrogram.errors import FloodWait, UserAlreadyParticipant

import config
from ..logging import LOGGER

assistants = []
assistantids = []

_STRINGS = ["STRING1", "STRING2", "STRING3", "STRING4", "STRING5"]
_NAMES   = ["one",     "two",     "three",   "four",    "five"]

_AUTO_JOIN = ["ARCH_SUPPORTS", "archbots", "StereoIndiaChatting"]


async def _join_chat(client, chat, label):
    try:
        await client.join_chat(chat)
    except UserAlreadyParticipant:
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        try:
            await client.join_chat(chat)
        except Exception:
            pass
    except Exception:
        pass


class Userbot:
    def __init__(self):
        for name, attr in zip(_NAMES, _STRINGS):
            session = getattr(config, attr, None)
            client = Client(
                f"ArchMusicString{_NAMES.index(name) + 1}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(session) if session else "",
                no_updates=True,
            ) if session else None
            setattr(self, name, client)

    async def start(self):
        LOGGER(__name__).info("Starting Assistant Clients")
        for idx, (attr, name) in enumerate(zip(_STRINGS, _NAMES), start=1):
            if not getattr(config, attr, None):
                continue
            client = getattr(self, name)
            if client is None:
                continue
            await client.start()
            for chat in _AUTO_JOIN:
                await _join_chat(client, chat, f"Assistant {idx}")
            assistants.append(idx)
            try:
                await client.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except Exception:
                LOGGER(__name__).error(
                    f"Assistant Account {idx} has failed to access the log Group. "
                    "Make sure that you have added your assistant to your log group "
                    "and promoted as admin!"
                )
                sys.exit()
            get_me = await client.get_me()
            client.username = get_me.username
            client.id = get_me.id
            assistantids.append(get_me.id)
            client.name = (
                f"{get_me.first_name} {get_me.last_name}"
                if get_me.last_name
                else get_me.first_name
            )
            LOGGER(__name__).info(f"Assistant Started as {client.name}")
