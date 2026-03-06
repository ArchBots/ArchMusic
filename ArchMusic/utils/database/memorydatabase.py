#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import config
from config import PRIVATE_BOT_MODE
from pytgcalls.types import AudioQuality, VideoQuality

from ArchMusic.core.mongo import mongodb

channeldb  = mongodb.cplaymode
commanddb  = mongodb.commands
cleandb    = mongodb.cleanmode
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
langdb     = mongodb.language
authdb     = mongodb.adminauth
videodb    = mongodb.ArchMusicvideocalls
onoffdb    = mongodb.onoffper
suggdb     = mongodb.suggestion
autoenddb  = mongodb.autoend
volumedb   = mongodb.volume

loop           = {}
playtype       = {}
playmode       = {}
channelconnect = {}
langm          = {}
pause          = {}
mute           = {}
audio          = {}
video          = {}
active         = []
activevideo    = []
command        = []
cleanmode      = []
nonadmin       = {}
vlimit         = []
maintenance    = []
suggestion     = {}
autoend        = {}
volume         = {}


async def is_autoend() -> bool:
    chat_id = 123
    mode = autoend.get(chat_id)
    if mode is not None:
        return mode
    user = await autoenddb.find_one({"chat_id": chat_id})
    if not user:
        autoend[chat_id] = False
        return False
    autoend[chat_id] = True
    return True


async def autoend_on():
    chat_id = 123
    autoend[chat_id] = True
    user = await autoenddb.find_one({"chat_id": chat_id})
    if not user:
        return await autoenddb.insert_one({"chat_id": chat_id})


async def autoend_off():
    chat_id = 123
    autoend[chat_id] = False
    user = await autoenddb.find_one({"chat_id": chat_id})
    if user:
        return await autoenddb.delete_one({"chat_id": chat_id})


async def is_suggestion(chat_id: int) -> bool:
    mode = suggestion.get(chat_id)
    if mode is not None:
        return mode
    user = await suggdb.find_one({"chat_id": chat_id})
    if not user:
        suggestion[chat_id] = True
        return True
    suggestion[chat_id] = False
    return False


async def suggestion_on(chat_id: int):
    suggestion[chat_id] = True
    user = await suggdb.find_one({"chat_id": chat_id})
    if user:
        return await suggdb.delete_one({"chat_id": chat_id})


async def suggestion_off(chat_id: int):
    suggestion[chat_id] = False
    user = await suggdb.find_one({"chat_id": chat_id})
    if not user:
        return await suggdb.insert_one({"chat_id": chat_id})


async def get_loop(chat_id: int) -> int:
    return loop.get(chat_id, 0)


async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode


async def get_cmode(chat_id: int):
    mode = channelconnect.get(chat_id)
    if mode is not None:
        return mode
    rec = await channeldb.find_one({"chat_id": chat_id})
    if not rec:
        return None
    channelconnect[chat_id] = rec["mode"]
    return rec["mode"]


async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode
    await channeldb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playtype(chat_id: int) -> str:
    mode = playtype.get(chat_id)
    if mode is not None:
        return mode
    rec = await playtypedb.find_one({"chat_id": chat_id})
    if not rec:
        playtype[chat_id] = "Everyone"
        return "Everyone"
    playtype[chat_id] = rec["mode"]
    return rec["mode"]


async def set_playtype(chat_id: int, mode: str):
    playtype[chat_id] = mode
    await playtypedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playmode(chat_id: int) -> str:
    mode = playmode.get(chat_id)
    if mode is not None:
        return mode
    rec = await playmodedb.find_one({"chat_id": chat_id})
    if not rec:
        playmode[chat_id] = "Direct"
        return "Direct"
    playmode[chat_id] = rec["mode"]
    return rec["mode"]


async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode
    await playmodedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_lang(chat_id: int) -> str:
    mode = langm.get(chat_id)
    if mode is not None:
        return mode
    lang = await langdb.find_one({"chat_id": chat_id})
    if not lang:
        langm[chat_id] = "en"
        return "en"
    langm[chat_id] = lang["lang"]
    return lang["lang"]


async def set_lang(chat_id: int, lang: str):
    langm[chat_id] = lang
    await langdb.update_one(
        {"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True
    )


async def is_muted(chat_id: int) -> bool:
    return mute.get(chat_id, False)


async def mute_on(chat_id: int):
    mute[chat_id] = True


async def mute_off(chat_id: int):
    mute[chat_id] = False


async def is_music_playing(chat_id: int) -> bool:
    return pause.get(chat_id, False)


async def music_on(chat_id: int):
    pause[chat_id] = True


async def music_off(chat_id: int):
    pause[chat_id] = False


async def get_active_chats() -> list:
    return active


async def is_active_chat(chat_id: int) -> bool:
    return chat_id in active


async def add_active_chat(chat_id: int):
    if chat_id not in active:
        active.append(chat_id)


async def remove_active_chat(chat_id: int):
    if chat_id in active:
        active.remove(chat_id)


async def get_active_video_chats() -> list:
    return activevideo


async def is_active_video_chat(chat_id: int) -> bool:
    return chat_id in activevideo


async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo:
        activevideo.append(chat_id)


async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo:
        activevideo.remove(chat_id)


async def is_commanddelete_on(chat_id: int) -> bool:
    return chat_id not in command


async def commanddelete_off(chat_id: int):
    if chat_id not in command:
        command.append(chat_id)


async def commanddelete_on(chat_id: int):
    try:
        command.remove(chat_id)
    except ValueError:
        pass


async def is_cleanmode_on(chat_id: int) -> bool:
    return chat_id not in cleanmode


async def cleanmode_off(chat_id: int):
    if chat_id not in cleanmode:
        cleanmode.append(chat_id)


async def cleanmode_on(chat_id: int):
    try:
        cleanmode.remove(chat_id)
    except ValueError:
        pass


async def check_nonadmin_chat(chat_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id})
    return bool(user)


async def is_nonadmin_chat(chat_id: int) -> bool:
    mode = nonadmin.get(chat_id)
    if mode is not None:
        return mode
    user = await authdb.find_one({"chat_id": chat_id})
    if not user:
        nonadmin[chat_id] = False
        return False
    nonadmin[chat_id] = True
    return True


async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True
    if await check_nonadmin_chat(chat_id):
        return
    return await authdb.insert_one({"chat_id": chat_id})


async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False
    if not await check_nonadmin_chat(chat_id):
        return
    return await authdb.delete_one({"chat_id": chat_id})


async def is_video_allowed(chat_idd) -> bool:
    chat_id = 123456
    if not vlimit:
        dblimit = await videodb.find_one({"chat_id": chat_id})
        limit = dblimit["limit"] if dblimit else config.VIDEO_STREAM_LIMIT
        vlimit.clear()
        vlimit.append(limit)
    else:
        limit = vlimit[0]
    if limit == 0:
        return False
    count = len(await get_active_video_chats())
    if count == limit:
        return await is_active_video_chat(chat_idd)
    return True


async def get_video_limit():
    chat_id = 123456
    if not vlimit:
        dblimit = await videodb.find_one({"chat_id": chat_id})
        return dblimit["limit"] if dblimit else config.VIDEO_STREAM_LIMIT
    return vlimit[0]


async def set_video_limit(limt: int):
    chat_id = 123456
    vlimit.clear()
    vlimit.append(limt)
    return await videodb.update_one(
        {"chat_id": chat_id}, {"$set": {"limit": limt}}, upsert=True
    )


async def is_on_off(on_off: int) -> bool:
    onoff = await onoffdb.find_one({"on_off": on_off})
    return bool(onoff)


async def add_on(on_off: int):
    if await is_on_off(on_off):
        return
    return await onoffdb.insert_one({"on_off": on_off})


async def add_off(on_off: int):
    if not await is_on_off(on_off):
        return
    return await onoffdb.delete_one({"on_off": on_off})


async def is_maintenance() -> bool:
    if not maintenance:
        get = await onoffdb.find_one({"on_off": 1})
        if not get:
            maintenance.clear()
            maintenance.append(2)
            return True
        maintenance.clear()
        maintenance.append(1)
        return False
    return 1 not in maintenance


async def maintenance_off():
    maintenance.clear()
    maintenance.append(2)
    if await is_on_off(1):
        return await onoffdb.delete_one({"on_off": 1})


async def maintenance_on():
    maintenance.clear()
    maintenance.append(1)
    if not await is_on_off(1):
        return await onoffdb.insert_one({"on_off": 1})


async def save_audio_bitrate(chat_id: int, bitrate: str):
    audio[chat_id] = bitrate


async def save_video_bitrate(chat_id: int, bitrate: str):
    video[chat_id] = bitrate


async def get_aud_bit_name(chat_id: int) -> str:
    return audio.get(chat_id, "High")


async def get_vid_bit_name(chat_id: int) -> str:
    mode = video.get(chat_id)
    if not mode:
        return "High" if PRIVATE_BOT_MODE == str(True) else "Medium"
    return mode


async def get_audio_bitrate(chat_id: int) -> AudioQuality:
    mode = audio.get(chat_id)
    if not mode:
        return AudioQuality.MEDIUM
    return {
        "High":   AudioQuality.HIGH,
        "Medium": AudioQuality.MEDIUM,
        "Low":    AudioQuality.LOW,
    }.get(mode, AudioQuality.MEDIUM)


async def get_video_bitrate(chat_id: int) -> VideoQuality:
    mode = video.get(chat_id)
    if not mode:
        return VideoQuality.FHD_1080p if PRIVATE_BOT_MODE == str(True) else VideoQuality.HD_720p
    return {
        "High":   VideoQuality.FHD_1080p,
        "Medium": VideoQuality.HD_720p,
        "Low":    VideoQuality.SD_480p,
    }.get(mode, VideoQuality.HD_720p)


async def get_volume(chat_id: int) -> int:
    vol = volume.get(chat_id)
    if vol is not None:
        return int(vol)
    rec = await volumedb.find_one({"chat_id": chat_id})
    if not rec:
        volume[chat_id] = 100
        return 100
    volume[chat_id] = int(rec.get("volume", 100))
    return volume[chat_id]


async def save_volume(chat_id: int, vol: int):
    vol = max(1, min(int(vol), 200))
    volume[chat_id] = vol
    return await volumedb.update_one(
        {"chat_id": chat_id}, {"$set": {"volume": vol}}, upsert=True
    )


async def set_volume(chat_id: int, vol: int):
    return await save_volume(chat_id, vol)


async def remove_volume(chat_id: int):
    volume.pop(chat_id, None)
    return await volumedb.delete_one({"chat_id": chat_id})
