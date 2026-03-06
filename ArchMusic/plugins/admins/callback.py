#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import random

from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from config import (
    AUTO_DOWNLOADS_CLEAR,
    BANNED_USERS,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
)

from ArchMusic import YouTube, app
from ArchMusic.core.call import ArchMusic
from ArchMusic.misc import SUDOERS, db
from ArchMusic.utils.database import (
    get_volume,
    is_active_chat,
    is_music_playing,
    is_muted,
    is_nonadmin_chat,
    music_off,
    music_on,
    mute_off,
    mute_on,
    save_volume,
    set_loop,
)
from ArchMusic.utils.decorators.language import languageCB
from ArchMusic.utils.formatters import seconds_to_min
from ArchMusic.utils.inline.play import (
    panel_markup_1,
    panel_markup_2,
    panel_markup_3,
    stream_markup,
    telegram_markup,
)
from ArchMusic.utils.stream.autoclear import auto_clean
from ArchMusic.utils.thumbnails import gen_thumb

wrong = {}

_VOL_STEP = 10
_VOL_MIN  = 1
_VOL_MAX  = 200

_SEEK_MAP = {
    "1": -10,
    "2": +10,
    "3": -30,
    "4": +30,
    "5": -60,
    "6": +60,
}


async def _check_admin(query: CallbackQuery, _) -> bool:
    if query.from_user.id in SUDOERS:
        return True
    is_non_admin = await is_nonadmin_chat(query.message.chat.id)
    if is_non_admin:
        return True
    admins = adminlist.get(query.message.chat.id)
    if not admins or query.from_user.id not in admins:
        await query.answer(_["admin_19"], show_alert=True)
        return False
    return True


async def _now_playing_photo(query, chat_id, check, _, txt):
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
            return await query.message.reply_text(_["admin_11"].format(title))
        try:
            await ArchMusic.skip_stream(chat_id, link, video=status)
        except Exception:
            return await query.message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        img    = await gen_thumb(videoid)
        run = await query.message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                user, f"https://t.me/{app.username}?start=info_{videoid}"
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
        await query.edit_message_text(txt)

    elif "vid_" in queued:
        mystic = await query.message.reply_text(
            _["call_10"], disable_web_page_preview=True
        )
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
        img    = await gen_thumb(videoid)
        run = await query.message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                user, f"https://t.me/{app.username}?start=info_{videoid}"
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await query.edit_message_text(txt)
        await mystic.delete()

    elif "index_" in queued:
        try:
            await ArchMusic.skip_stream(chat_id, videoid, video=status)
        except Exception:
            return await query.message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        run = await query.message.reply_photo(
            photo=STREAM_IMG_URL,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
        await query.edit_message_text(txt)

    else:
        try:
            await ArchMusic.skip_stream(chat_id, queued, video=status)
        except Exception:
            return await query.message.reply_text(_["call_9"])
        if videoid in ("telegram", "soundcloud"):
            photo  = SOUNCLOUD_IMG_URL if videoid == "soundcloud" else (
                TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else TELEGRAM_VIDEO_URL
            )
            button = telegram_markup(_, chat_id)
            run = await query.message.reply_photo(
                photo=photo,
                caption=_["stream_3"].format(title, check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            button = stream_markup(_, videoid, chat_id)
            img    = await gen_thumb(videoid)
            run = await query.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    user, f"https://t.me/{app.username}?start=info_{videoid}"
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
        await query.edit_message_text(txt)


@app.on_callback_query(filters.regex("PanelMarkup") & ~BANNED_USERS)
@languageCB
async def markup_panel(client, query: CallbackQuery, _):
    await query.answer()
    _, videoid, chat_id = query.data.strip().split(None, 1)[1], *query.data.strip().split(None, 1)[1].split("|")
    videoid, chat_raw = query.data.strip().split(None, 1)[1].split("|")
    chat_id = query.message.chat.id
    buttons = panel_markup_1(_, videoid, chat_id)
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        return
    wrong.setdefault(chat_id, {})[query.message.id] = False


@app.on_callback_query(filters.regex("MainMarkup") & ~BANNED_USERS)
@languageCB
async def main_markup_back(client, query: CallbackQuery, _):
    await query.answer()
    videoid, chat_raw = query.data.strip().split(None, 1)[1].split("|")
    chat_id = query.message.chat.id
    buttons = telegram_markup(_, chat_id) if videoid == str(None) else stream_markup(_, videoid, chat_id)
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        return
    wrong.setdefault(chat_id, {})[query.message.id] = True


@app.on_callback_query(filters.regex("Pages") & ~BANNED_USERS)
@languageCB
async def pages_nav(client, query: CallbackQuery, _):
    await query.answer()
    state, pages, videoid, chat = query.data.strip().split(None, 1)[1].split("|")
    chat_id = int(chat)
    pages   = int(pages)

    page_fwd = {0: panel_markup_2, 1: panel_markup_3, 2: panel_markup_1}
    page_bck = {0: panel_markup_3, 1: panel_markup_1, 2: panel_markup_2}

    fn = page_fwd[pages] if state == "Forw" else page_bck[pages]
    buttons = fn(_, videoid, chat_id)
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        return


@app.on_callback_query(filters.regex(r"^ADMIN ") & ~BANNED_USERS)
@languageCB
async def admin_callback(client, query: CallbackQuery, _):
    callback_request = query.data.strip().split(None, 1)[1]
    command, chat    = callback_request.split("|")
    chat_id          = int(chat)
    mention          = query.from_user.mention

    if not await is_active_chat(chat_id):
        return await query.answer(_["general_6"], show_alert=True)

    if not await _check_admin(query, _):
        return

    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await query.answer(_["admin_1"], show_alert=True)
        await query.answer()
        await music_off(chat_id)
        await ArchMusic.pause_stream(chat_id)
        await query.message.reply_text(_["admin_2"].format(mention))

    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await query.answer(_["admin_3"], show_alert=True)
        await query.answer()
        await music_on(chat_id)
        await ArchMusic.resume_stream(chat_id)
        await query.message.reply_text(_["admin_4"].format(mention))

    elif command in ("Stop", "End"):
        await query.answer()
        await ArchMusic.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await query.message.reply_text(_["admin_9"].format(mention))

    elif command == "Mute":
        if await is_muted(chat_id):
            return await query.answer(_["admin_5"], show_alert=True)
        await query.answer()
        await mute_on(chat_id)
        await ArchMusic.mute_stream(chat_id)
        await query.message.reply_text(_["admin_6"].format(mention))

    elif command == "Unmute":
        if not await is_muted(chat_id):
            return await query.answer(_["admin_7"], show_alert=True)
        await query.answer()
        await mute_off(chat_id)
        await ArchMusic.unmute_stream(chat_id)
        await query.message.reply_text(_["admin_8"].format(mention))

    elif command == "Loop":
        await query.answer()
        await set_loop(chat_id, 3)
        await query.message.reply_text(_["admin_25"].format(mention, 3))

    elif command == "Shuffle":
        check = db.get(chat_id)
        if not check:
            return await query.answer(_["admin_21"], show_alert=True)
        try:
            popped = check.pop(0)
        except Exception:
            return await query.answer(_["admin_22"], show_alert=True)
        check = db.get(chat_id)
        if not check:
            check.insert(0, popped)
            return await query.answer(_["admin_22"], show_alert=True)
        await query.answer()
        random.shuffle(check)
        check.insert(0, popped)
        await query.message.reply_text(_["admin_23"].format(mention))

    elif command == "Skip":
        check = db.get(chat_id)
        txt   = f"⏭ Skipped by {mention}"
        popped = None
        try:
            popped = check.pop(0)
            if popped and AUTO_DOWNLOADS_CLEAR == str(True):
                await auto_clean(popped)
            if not check:
                await query.edit_message_text(txt)
                await query.message.reply_text(_["admin_10"].format(mention))
                try:
                    return await ArchMusic.stop_stream(chat_id)
                except Exception:
                    return
        except Exception:
            try:
                await query.edit_message_text(txt)
                await query.message.reply_text(_["admin_10"].format(mention))
                return await ArchMusic.stop_stream(chat_id)
            except Exception:
                return
        await query.answer()
        await _now_playing_photo(query, chat_id, check, _, txt)

    elif command == "Back":
        check = db.get(chat_id)
        if not check or len(check) < 2:
            return await query.answer("❌ No previous track in queue.", show_alert=True)
        await query.answer()
        check.insert(0, check.pop(-1))
        txt = f"⏮ Previous track by {mention}"
        await _now_playing_photo(query, chat_id, check, _, txt)

    elif command == "Queue":
        check = db.get(chat_id)
        if not check:
            return await query.answer(_["queue_2"], show_alert=True)
        await query.answer()
        lines = [f"**Queue for this chat:**\n"]
        for i, item in enumerate(check):
            lines.append(f"{i + 1}. {item['title'][:40]} — {item['dur']} [{item['by']}]")
            if i >= 9:
                lines.append(f"...and {len(check) - 10} more")
                break
        await query.message.reply_text("\n".join(lines))

    elif command == "Clear":
        check = db.get(chat_id)
        if not check or len(check) <= 1:
            return await query.answer("❌ Queue is already empty.", show_alert=True)
        await query.answer()
        current = check[0]
        db[chat_id] = [current]
        await query.message.reply_text(
            f"🗑 Queue cleared by {mention}. Current track kept."
        )

    elif command == "Vol-":
        current = await get_volume(chat_id)
        vol = max(_VOL_MIN, current - _VOL_STEP)
        try:
            await ArchMusic.volume_stream(chat_id, vol)
        except Exception:
            return await query.answer("❌ Failed to change volume.", show_alert=True)
        await save_volume(chat_id, vol)
        await query.answer(f"🔉 Volume: {vol}%", show_alert=False)

    elif command == "Vol+":
        current = await get_volume(chat_id)
        vol = min(_VOL_MAX, current + _VOL_STEP)
        try:
            await ArchMusic.volume_stream(chat_id, vol)
        except Exception:
            return await query.answer("❌ Failed to change volume.", show_alert=True)
        await save_volume(chat_id, vol)
        await query.answer(f"🔊 Volume: {vol}%", show_alert=False)

    elif command in _SEEK_MAP:
        playing = db.get(chat_id)
        if not playing:
            return await query.answer(_["queue_2"], show_alert=True)
        duration_seconds = int(playing[0]["seconds"])
        if duration_seconds == 0:
            return await query.answer(_["admin_30"], show_alert=True)
        file_path = playing[0]["file"]
        if "index_" in file_path or "live_" in file_path:
            return await query.answer(_["admin_30"], show_alert=True)
        duration_played = int(playing[0]["played"])
        duration        = playing[0]["dur"]
        delta           = _SEEK_MAP[command]
        to_seek         = duration_played + delta + 1
        if to_seek <= 10:
            bet = seconds_to_min(duration_played)
            return await query.answer(
                f"Cannot seek — already at start.\n\nPlayed: {bet} / {duration}",
                show_alert=True,
            )
        if (duration_seconds - to_seek) <= 10:
            bet = seconds_to_min(duration_played)
            return await query.answer(
                f"Cannot seek — too close to end.\n\nPlayed: {bet} / {duration}",
                show_alert=True,
            )
        await query.answer()
        mystic = await query.message.reply_text(_["admin_32"])
        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await mystic.edit_text(_["admin_30"])
        try:
            await ArchMusic.seek_stream(
                chat_id,
                file_path,
                seconds_to_min(to_seek),
                duration,
                playing[0]["streamtype"],
            )
        except Exception:
            return await mystic.edit_text(_["admin_34"])
        db[chat_id][0]["played"] += delta
        string = _["admin_33"].format(seconds_to_min(to_seek))
        await mystic.edit_text(f"{string}\n\nChanges done by: {mention}")
