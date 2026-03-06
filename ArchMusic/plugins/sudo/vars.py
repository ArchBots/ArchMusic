#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio

from pyrogram import filters

import config
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.database.memorydatabase import get_video_limit
from ArchMusic.utils.formatters import convert_bytes

VARS_COMMAND = get_command("VARS_COMMAND")


def _yn(value) -> str:
    """Return 'Yes' if value is truthy string 'True', else 'No'."""
    return "Yes" if value == str(True) else "No"


def _link(url: str, label: str) -> str:
    return f"[{label}]({url})" if url else "No"


@app.on_message(filters.command(VARS_COMMAND) & SUDOERS)
async def vars_func(client, message):
    mystic = await message.reply_text("Please wait… Getting your config")
    v_limit = await get_video_limit()
    owners = ", ".join(str(i) for i in config.OWNER_ID)

    text = f"""**MUSIC BOT CONFIG:**

**<u>Basic Vars:</u>**
`MUSIC_BOT_NAME` : **{config.MUSIC_BOT_NAME}**
`DURATION_LIMIT` : **{config.DURATION_LIMIT_MIN} min**
`SONG_DOWNLOAD_DURATION_LIMIT` : **{config.SONG_DOWNLOAD_DURATION} min**
`OWNER_ID` : **{owners}**

**<u>Custom Repo Vars:</u>**
`UPSTREAM_REPO` : **[Repo]({config.UPSTREAM_REPO})**
`UPSTREAM_BRANCH` : **{config.UPSTREAM_BRANCH}**
`GITHUB_REPO` : **{_link(config.GITHUB_REPO, "Repo")}**
`GIT_TOKEN` : **{"Yes" if config.GIT_TOKEN else "No"}**

**<u>Bot Vars:</u>**
`AUTO_LEAVING_ASSISTANT` : **{_yn(config.AUTO_LEAVING_ASSISTANT)}**
`ASSISTANT_LEAVE_TIME` : **{config.AUTO_LEAVE_ASSISTANT_TIME} seconds**
`AUTO_SUGGESTION_MODE` : **{_yn(config.AUTO_SUGGESTION_MODE)}**
`AUTO_SUGGESTION_TIME` : **{config.AUTO_SUGGESTION_TIME} seconds**
`AUTO_DOWNLOADS_CLEAR` : **{_yn(config.AUTO_DOWNLOADS_CLEAR)}**
`PRIVATE_BOT_MODE` : **{_yn(config.PRIVATE_BOT_MODE)}**
`YOUTUBE_EDIT_SLEEP` : **{config.YOUTUBE_DOWNLOAD_EDIT_SLEEP} seconds**
`TELEGRAM_EDIT_SLEEP` : **{config.TELEGRAM_DOWNLOAD_EDIT_SLEEP} seconds**
`CLEANMODE_MINS` : **{config.CLEANMODE_DELETE_MINS} mins**
`VIDEO_STREAM_LIMIT` : **{v_limit} chats**
`SERVER_PLAYLIST_LIMIT` : **{config.SERVER_PLAYLIST_LIMIT}**
`PLAYLIST_FETCH_LIMIT` : **{config.PLAYLIST_FETCH_LIMIT}**

**<u>Spotify Vars:</u>**
`SPOTIFY_CLIENT_ID` : **{"Yes" if config.SPOTIFY_CLIENT_ID else "No"}**
`SPOTIFY_CLIENT_SECRET` : **{"Yes" if config.SPOTIFY_CLIENT_SECRET else "No"}**

**<u>Playsize Vars:</u>**
`TG_AUDIO_FILESIZE_LIMIT` : **{convert_bytes(config.TG_AUDIO_FILESIZE_LIMIT)}**
`TG_VIDEO_FILESIZE_LIMIT` : **{convert_bytes(config.TG_VIDEO_FILESIZE_LIMIT)}**

**<u>URL Vars:</u>**
`SUPPORT_CHANNEL` : **{_link(config.SUPPORT_CHANNEL, "Channel")}**
`SUPPORT_GROUP` : **{_link(config.SUPPORT_GROUP, "Group")}**
`START_IMG_URL` : **{_link(config.START_IMG_URL, "Image")}**
"""
    await asyncio.sleep(1)
    await mystic.edit_text(text)
