#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import math
import os
import shutil
import socket
from datetime import datetime

import dotenv
import heroku3
import requests
import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from pyrogram import filters

import config
from strings import get_command
from ArchMusic import app
from ArchMusic.misc import HAPP, SUDOERS, XCB
from ArchMusic.utils.database import (
    get_active_chats,
    remove_active_chat,
    remove_active_video_chat,
)
from ArchMusic.utils.decorators.language import language
from ArchMusic.utils.pastebin import ArchMusicbin

GETLOG_COMMAND = get_command("GETLOG_COMMAND")
GETVAR_COMMAND = get_command("GETVAR_COMMAND")
DELVAR_COMMAND = get_command("DELVAR_COMMAND")
SETVAR_COMMAND = get_command("SETVAR_COMMAND")
USAGE_COMMAND = get_command("USAGE_COMMAND")
UPDATE_COMMAND = get_command("UPDATE_COMMAND")
REBOOT_COMMAND = get_command("REBOOT_COMMAND")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_RESTART_MSG = (
    f"{config.MUSIC_BOT_NAME} is restarting. "
    "Please wait 10–15 seconds before playing again."
)
_DIRS_TO_CLEAN = ("downloads", "raw_files", "cache")


def _ordinal(n: int) -> str:
    suffix = "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4]
    return f"{n}{suffix}"


async def _is_heroku() -> bool:
    return "heroku" in socket.getfqdn()


async def _notify_active_chats():
    """Send restart notice to all active chats and remove them from DB."""
    for chat_id in await get_active_chats():
        try:
            await app.send_message(chat_id, _RESTART_MSG)
            await remove_active_chat(chat_id)
            await remove_active_video_chat(chat_id)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# /getlog
# ---------------------------------------------------------------------------

@app.on_message(filters.command(GETLOG_COMMAND) & SUDOERS)
@language
async def log_(client, message, _):
    try:
        if await _is_heroku():
            if HAPP is None:
                return await message.reply_text(_["heroku_1"])
            link = await ArchMusicbin(HAPP.get_log())
            return await message.reply_text(link)
        if not os.path.exists(config.LOG_FILE_NAME):
            return await message.reply_text(_["heroku_2"])
        try:
            numb = int(message.text.split(None, 1)[1])
        except (IndexError, ValueError):
            numb = 100
        with open(config.LOG_FILE_NAME) as log:
            data = "".join(log.readlines()[-numb:])
        link = await ArchMusicbin(data)
        return await message.reply_text(link)
    except Exception as e:
        await message.reply_text(_["heroku_2"])
        raise


# ---------------------------------------------------------------------------
# /getvar
# ---------------------------------------------------------------------------

@app.on_message(filters.command(GETVAR_COMMAND) & SUDOERS)
@language
async def varget_(client, message, _):
    usage = _["heroku_3"]
    if len(message.command) != 2:
        return await message.reply_text(usage)
    key = message.text.split(None, 2)[1]
    if await _is_heroku():
        if HAPP is None:
            return await message.reply_text(_["heroku_1"])
        cfg = HAPP.config()
        if key in cfg:
            return await message.reply_text(f"**{key}:** `{cfg[key]}`")
        return await message.reply_text(_["heroku_4"])
    path = dotenv.find_dotenv()
    if not path:
        return await message.reply_text(_["heroku_5"])
    value = dotenv.get_key(path, key)
    if value is None:
        return await message.reply_text(_["heroku_4"])
    return await message.reply_text(f"**{key}:** `{value}`")


# ---------------------------------------------------------------------------
# /delvar
# ---------------------------------------------------------------------------

@app.on_message(filters.command(DELVAR_COMMAND) & SUDOERS)
@language
async def vardel_(client, message, _):
    usage = _["heroku_6"]
    if len(message.command) != 2:
        return await message.reply_text(usage)
    key = message.text.split(None, 2)[1]
    if await _is_heroku():
        if HAPP is None:
            return await message.reply_text(_["heroku_1"])
        cfg = HAPP.config()
        if key not in cfg:
            return await message.reply_text(_["heroku_4"])
        await message.reply_text(_["heroku_7"].format(key))
        del cfg[key]
        return
    path = dotenv.find_dotenv()
    if not path:
        return await message.reply_text(_["heroku_5"])
    success, _, _ = dotenv.unset_key(path, key)
    if not success:
        return await message.reply_text(_["heroku_4"])
    await message.reply_text(_["heroku_7"].format(key))
    os.system(f"kill -9 {os.getpid()} && bash start")


# ---------------------------------------------------------------------------
# /setvar
# ---------------------------------------------------------------------------

@app.on_message(filters.command(SETVAR_COMMAND) & SUDOERS)
@language
async def set_var(client, message, _):
    usage = _["heroku_8"]
    if len(message.command) < 3:
        return await message.reply_text(usage)
    parts = message.text.split(None, 2)
    key, value = parts[1].strip(), parts[2].strip()
    if await _is_heroku():
        if HAPP is None:
            return await message.reply_text(_["heroku_1"])
        cfg = HAPP.config()
        reply_key = _["heroku_9"] if key in cfg else _["heroku_10"]
        await message.reply_text(reply_key.format(key))
        cfg[key] = value
        return
    path = dotenv.find_dotenv()
    if not path:
        return await message.reply_text(_["heroku_5"])
    dotenv.set_key(path, key, value)
    reply_key = _["heroku_9"] if dotenv.get_key(path, key) else _["heroku_10"]
    await message.reply_text(reply_key.format(key))
    os.system(f"kill -9 {os.getpid()} && bash start")


# ---------------------------------------------------------------------------
# /usage
# ---------------------------------------------------------------------------

@app.on_message(filters.command(USAGE_COMMAND) & SUDOERS)
@language
async def usage_dynos(client, message, _):
    # Credits: CatUserbot
    if not await _is_heroku():
        return await message.reply_text(_["heroku_11"])
    if HAPP is None:
        return await message.reply_text(_["heroku_1"])
    dyno = await message.reply_text(_["heroku_12"])
    Heroku = heroku3.from_key(config.HEROKU_API_KEY)
    account_id = Heroku.account().id
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/80.0.3987.149 Mobile Safari/537.36"
        ),
        "Authorization": f"Bearer {config.HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3.account-quotas",
    }
    r = requests.get(
        f"https://api.heroku.com/accounts/{account_id}/actions/get-quota",
        headers=headers,
    )
    if r.status_code != 200:
        return await dyno.edit("Unable to fetch dyno usage.")
    result = r.json()
    quota = result["account_quota"]
    quota_used = result["quota_used"]
    remaining = quota - quota_used
    percentage = math.floor(remaining / quota * 100)
    hours = math.floor(remaining / 3600)
    minutes = math.floor((remaining % 3600) / 60)
    apps = result.get("apps", [])
    app_used = apps[0]["quota_used"] if apps else 0
    app_pct = math.floor(app_used * 100 / quota) if apps else 0
    app_h = math.floor(app_used / 3600)
    app_m = math.floor((app_used % 3600) / 60)
    await asyncio.sleep(1.5)
    text = (
        "**DYNO USAGE**\n\n"
        f"<u>App Usage:</u>\n"
        f"Total Used: `{app_h}`**h** `{app_m}`**m** [`{app_pct}`**%**]\n\n"
        f"<u>Remaining Quota:</u>\n"
        f"Total Left: `{hours}`**h** `{minutes}`**m** [`{percentage}`**%**]"
    )
    await dyno.edit(text)


# ---------------------------------------------------------------------------
# /update
# ---------------------------------------------------------------------------

@app.on_message(filters.command(UPDATE_COMMAND) & SUDOERS)
@language
async def update_(client, message, _):
    if await _is_heroku() and HAPP is None:
        return await message.reply_text(_["heroku_1"])
    response = await message.reply_text(_["heroku_13"])
    try:
        repo = Repo()
    except GitCommandError:
        return await response.edit(_["heroku_14"])
    except InvalidGitRepositoryError:
        return await response.edit(_["heroku_15"])

    os.system(f"git fetch origin {config.UPSTREAM_BRANCH} &> /dev/null")
    await asyncio.sleep(7)

    commits = list(repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}"))
    if not commits:
        return await response.edit("Bot is up-to-date!")

    REPO_ = repo.remotes.origin.url.split(".git")[0]
    updates = ""
    for info in commits:
        day = _ordinal(int(datetime.fromtimestamp(info.committed_date).strftime("%d")))
        date_str = datetime.fromtimestamp(info.committed_date).strftime(f"{day} %b, %Y")
        updates += (
            f"<b>➣ #{info.count()}: [{info.summary}]({REPO_}/commit/{info})"
            f" by → {info.author}</b>\n"
            f"\t\t<b>➥ Committed on:</b> {date_str}\n\n"
        )

    header = "<b>A new update is available!</b>\n\n➣ Pushing Updates Now\n\n<u>Updates:</u>\n\n"
    full_text = header + updates
    if len(full_text) > 4096:
        url = await ArchMusicbin(updates)
        nrs = await response.edit(
            f"<b>A new update is available!</b>\n\n"
            f"➣ Pushing Updates Now\n\n"
            f"[Click Here to view updates]({url})"
        )
    else:
        nrs = await response.edit(full_text, disable_web_page_preview=True)

    os.system("git stash &> /dev/null && git pull")

    await _notify_active_chats()
    if await _is_heroku():
        try:
            await response.edit(
                f"{nrs.text}\n\nUpdated on Heroku! Wait 2–3 mins for the bot to restart."
            )
            os.system(
                f"{XCB[5]} {XCB[7]} {XCB[9]}{XCB[4]}{XCB[0]*2}{XCB[6]}{XCB[4]}"
                f"{XCB[8]}{XCB[1]}{XCB[5]}{XCB[2]}{XCB[6]}{XCB[2]}{XCB[3]}"
                f"{XCB[0]}{XCB[10]}{XCB[2]}{XCB[5]} {XCB[11]}{XCB[4]}{XCB[12]}"
            )
        except Exception as err:
            await response.edit(
                f"{nrs.text}\n\nReboot failed. Check logs for details."
            )
            await app.send_message(
                config.LOG_GROUP_ID,
                f"#UPDATER exception: <code>{err}</code>",
            )
    else:
        await response.edit(
            f"{nrs.text}\n\nUpdated successfully! Wait 1–2 mins for the bot to reboot."
        )
        os.system("pip3 install -r requirements.txt")
        os.system(f"kill -9 {os.getpid()} && bash start")
        exit()


# ---------------------------------------------------------------------------
# /reboot
# ---------------------------------------------------------------------------

@app.on_message(filters.command(REBOOT_COMMAND) & SUDOERS)
async def restart_(_, message):
    response = await message.reply_text("Restarting…")
    await _notify_active_chats()
    for d in _DIRS_TO_CLEAN:
        try:
            shutil.rmtree(d)
        except Exception:
            pass
    await response.edit(
        "Reboot initiated. Wait 1–2 minutes for the bot to restart."
    )
    os.system(f"kill -9 {os.getpid()} && bash start")
