#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import (
    NoActiveGroupCall,
    NoAudioSourceFound,
    NoVideoSourceFound,
    InvalidVideoProportion,
    YtDlpError,
)
from ntgcalls import TelegramServerError
from pytgcalls.types import (
    UpdatedGroupCallParticipant,
    MediaStream,
    Update,
)
from pytgcalls.types.stream import StreamEnded

import config
from strings import get_string
from ArchMusic import LOGGER, YouTube, app
from ArchMusic.misc import db
from ArchMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_assistant,
    get_audio_bitrate,
    get_lang,
    get_loop,
    get_video_bitrate,
    group_assistant,
    is_autoend,
    music_on,
    mute_off,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from ArchMusic.utils.exceptions import AssistantErr
from ArchMusic.utils.inline.play import stream_markup, telegram_markup
from ArchMusic.utils.stream.autoclear import auto_clean
from ArchMusic.utils.thumbnails import gen_thumb

autoend = {}
counter = {}
AUTO_END_TIME = 3


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


def _build_stream(
    link: str,
    audio_quality,
    video_quality,
    video: bool = False,
    ffmpeg_params: str = "",
) -> MediaStream:
    kwargs = {}
    if ffmpeg_params:
        kwargs["additional_ffmpeg_parameters"] = ffmpeg_params

    if video:
        return MediaStream(
            link,
            audio_parameters=audio_quality,
            video_parameters=video_quality,
            **kwargs,
        )
    else:
        return MediaStream(
            link,
            audio_parameters=audio_quality,
            video_flags=MediaStream.Flags.IGNORE,
            **kwargs,
        )


class Call(PyTgCalls):
    def __init__(self):
        self._clients = []
        _names = ["one", "two", "three", "four", "five"]
        for idx, string_attr in enumerate(
            ["STRING1", "STRING2", "STRING3", "STRING4", "STRING5"], start=1
        ):
            session_string = getattr(config, string_attr, None)
            name = _names[idx - 1]
            if not session_string:
                setattr(self, f"userbot{idx}", None)
                setattr(self, name, None)
                continue

            userbot = Client(
                f"ArchMusicString{idx}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(session_string),
            )
            instance = PyTgCalls(userbot)
            setattr(self, f"userbot{idx}", userbot)
            setattr(self, name, instance)
            self._clients.append((instance, string_attr))


    @property
    def _all_clients(self):
        for name in ("one", "two", "three", "four", "five"):
            inst = getattr(self, name, None)
            if inst is not None:
                yield inst


    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    async def mute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    async def unmute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    async def volume_stream(self, chat_id: int, volume: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.change_volume_call(chat_id, volume)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_call(chat_id)
        except Exception:
            pass

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        audio_quality = await get_audio_bitrate(chat_id)
        video_quality = await get_video_bitrate(chat_id)
        stream = _build_stream(link, audio_quality, video_quality, video=bool(video))
        await assistant.play(chat_id, stream)

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        audio_quality = await get_audio_bitrate(chat_id)
        video_quality = await get_video_bitrate(chat_id)
        stream = _build_stream(
            file_path,
            audio_quality,
            video_quality,
            video=(mode == "video"),
            ffmpeg_params=f"-ss {to_seek} -to {duration}",
        )
        await assistant.play(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.play(
            config.LOG_GROUP_ID,
            MediaStream(link),
        )
        await asyncio.sleep(0.5)
        await assistant.leave_call(config.LOG_GROUP_ID)


    async def join_assistant(self, original_chat_id, chat_id):
        language = await get_lang(original_chat_id)
        _ = get_string(language)
        userbot = await get_assistant(chat_id)

        try:
            try:
                get = await app.get_chat_member(chat_id, userbot.id)
            except ChatAdminRequired:
                raise AssistantErr(_["call_1"])

            if get.status in (ChatMemberStatus.BANNED, ChatMemberStatus.LEFT):
                raise AssistantErr(
                    _["call_2"].format(userbot.username, userbot.id)
                )
        except UserNotParticipant:
            chat = await app.get_chat(chat_id)
            if chat.username:
                try:
                    await userbot.join_chat(chat.username)
                except UserAlreadyParticipant:
                    pass
                except Exception as e:
                    raise AssistantErr(_["call_3"].format(e))
            else:
                try:
                    try:
                        invitelink = chat.invite_link
                        if invitelink is None:
                            invitelink = await app.export_chat_invite_link(chat_id)
                    except Exception:
                        invitelink = await app.export_chat_invite_link(chat_id)
                except ChatAdminRequired:
                    raise AssistantErr(_["call_4"])
                except Exception as e:
                    raise AssistantErr(e)

                m = await app.send_message(original_chat_id, _["call_5"])
                if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
                await asyncio.sleep(3)
                await userbot.join_chat(invitelink)
                await asyncio.sleep(4)
                await m.edit(_["call_6"].format(userbot.name))

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        audio_quality = await get_audio_bitrate(chat_id)
        video_quality = await get_video_bitrate(chat_id)
        stream = _build_stream(link, audio_quality, video_quality, video=bool(video))

        try:
            await assistant.play(chat_id, stream)

        except NoActiveGroupCall:
            try:
                await self.join_assistant(original_chat_id, chat_id)
            except Exception as e:
                raise e
            try:
                await assistant.play(chat_id, stream)
            except Exception:
                raise AssistantErr(
                    "**No Active Voice Chat Found**\n\n"
                    "Please make sure the group's voice chat is enabled. "
                    "If already enabled, end it and start a fresh voice chat. "
                    "If the problem continues, try /restart"
                )

        except NoAudioSourceFound:
            raise AssistantErr(
                "**No Audio Source Found**\n\n"
                "The file or stream has no audio track."
            )

        except NoVideoSourceFound:
            raise AssistantErr(
                "**No Video Source Found**\n\n"
                "The file or stream has no video track."
            )

        except InvalidVideoProportion:
            raise AssistantErr(
                "**Invalid Video Proportion**\n\n"
                "The video resolution is not supported."
            )

        except YtDlpError:
            raise AssistantErr(
                "**yt-dlp Error**\n\n"
                "Failed to fetch the stream. The URL may be unavailable or geo-restricted."
            )

        except TelegramServerError:
            raise AssistantErr(
                "**Telegram Server Error**\n\n"
                "Telegram is having internal server issues. Please try again.\n\n"
                "If this keeps happening, end your voice chat and start a fresh one."
            )

        await add_active_chat(chat_id)
        await mute_off(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=AUTO_END_TIME)


    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)

            if popped:
                if config.AUTO_DOWNLOADS_CLEAR == str(True):
                    await auto_clean(popped)

            if not check:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)

        except Exception:
            try:
                await _clear_(chat_id)
                await client.leave_call(chat_id)
            except Exception:
                pass
            return

        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        audio_quality = await get_audio_bitrate(chat_id)
        video_quality = await get_video_bitrate(chat_id)
        videoid = check[0]["vidid"]
        check[0]["played"] = 0
        is_video = str(streamtype) == "video"

        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await app.send_message(original_chat_id, text=_["call_9"])

            stream = _build_stream(link, audio_quality, video_quality, video=is_video)
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_9"])

            img = await gen_thumb(videoid)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user,
                    f"https://t.me/{app.username}?start=info_{videoid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        elif "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_10"])
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=is_video,
                )
            except Exception:
                return await mystic.edit_text(
                    _["call_9"], disable_web_page_preview=True
                )

            stream = _build_stream(
                file_path, audio_quality, video_quality, video=is_video
            )
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_9"])

            img = await gen_thumb(videoid)
            button = stream_markup(_, videoid, chat_id)
            await mystic.delete()
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user,
                    f"https://t.me/{app.username}?start=info_{videoid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        elif "index_" in queued:
            stream = _build_stream(
                videoid, audio_quality, video_quality, video=is_video
            )
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_9"])

            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        else:
            stream = _build_stream(
                queued, audio_quality, video_quality, video=is_video
            )
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_9"])

            if videoid == "telegram":
                button = telegram_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=(
                        config.TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else config.TELEGRAM_VIDEO_URL
                    ),
                    caption=_["stream_3"].format(title, check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif videoid == "soundcloud":
                button = telegram_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=config.SOUNCLOUD_IMG_URL,
                    caption=_["stream_3"].format(title, check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                img = await gen_thumb(videoid)
                button = stream_markup(_, videoid, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        user,
                        f"https://t.me/{app.username}?start=info_{videoid}",
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"


    async def ping(self):
        pings = []
        for client, string_attr in self._clients:
            if getattr(config, string_attr, None):
                pings.append(await client.ping)
        if not pings:
            return "0"
        return str(round(sum(pings) / len(pings), 3))


    async def set_volume(self, chat_id: int, volume: int):
        volume = max(0, min(200, volume))
        assistant = await group_assistant(self, chat_id)
        await assistant.change_volume_call(chat_id, volume)


    async def get_stream_info(self, chat_id: int) -> dict:
        try:
            assistant = await group_assistant(self, chat_id)
            call = await assistant.get_active_call(chat_id)
            info = {
                "status": str(call.capture).split(".")[-1] if call else "IDLE",
            }
        except Exception:
            info = {"status": "IDLE"}

        check = db.get(chat_id)
        if check:
            track = check[0]
            info.update({
                "playing":    True,
                "title":      track.get("title", "Unknown"),
                "by":         track.get("by", "Unknown"),
                "duration":   track.get("dur", "N/A"),
                "streamtype": track.get("streamtype", "audio"),
            })
        else:
            info["playing"] = False
        return info


    async def get_active_call_ids(self) -> list:
        ids = []
        for client in self._all_clients:
            try:
                for call in client.calls:
                    try:
                        ids.append(call.chat_id)
                    except Exception:
                        pass
            except Exception:
                pass
        return ids

    async def active_calls(self) -> int:
        total = 0
        for client in self._all_clients:
            try:
                total += len(client.calls)
            except Exception:
                pass
        return total


    async def get_participant_count(self, chat_id: int) -> int:
        assistant = await group_assistant(self, chat_id)
        try:
            return len(await assistant.get_participants(chat_id))
        except Exception:
            return 0


    async def reconnect(self, chat_id: int):
        check = db.get(chat_id)
        if not check:
            raise AssistantErr("**Nothing in queue to reconnect.**")

        track = check[0]
        original_chat_id = track.get("chat_id", chat_id)
        link = track["file"]
        video = str(track.get("streamtype", "audio")) == "video"

        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.leave_call(chat_id)
        except Exception:
            pass

        await remove_active_chat(chat_id)
        await remove_active_video_chat(chat_id)

        await asyncio.sleep(1)
        await self.join_call(chat_id, original_chat_id, link, video=video)


    async def ping_all(self) -> dict:
        result = {}
        for client, string_attr in self._clients:
            if getattr(config, string_attr, None):
                try:
                    result[string_attr] = str(round(await client.ping, 3))
                except Exception:
                    result[string_attr] = "N/A"
        return result


    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client\n")
        for client, string_attr in self._clients:
            if getattr(config, string_attr, None):
                await client.start()
        asyncio.create_task(self._autoend_task())

    async def _autoend_task(self):
        while True:
            try:
                await asyncio.sleep(5)
                if not await is_autoend():
                    continue
                for chat_id, end_time in list(autoend.items()):
                    if not isinstance(end_time, datetime):
                        continue
                    if datetime.now() >= end_time:
                        autoend.pop(chat_id, None)
                        counter.pop(chat_id, None)
                        try:
                            await self.stop_stream(chat_id)
                        except Exception:
                            pass
            except Exception:
                pass


    async def decorators(self):

        for instance in self._all_clients:

            @instance.on_kicked()
            @instance.on_closed_voice_chat()
            @instance.on_left()
            async def stream_services_handler(_, chat_id: int):
                await self.stop_stream(chat_id)

            @instance.on_stream_end()
            async def stream_end_handler(client, update: Update):
                if not isinstance(update, StreamEnded):
                    return
                await self.change_stream(client, update.chat_id)


            @instance.on_error()
            async def stream_error_handler(client, update: Update):
                chat_id = getattr(update, "chat_id", None)
                if not chat_id:
                    return
                LOGGER(__name__).warning(
                    f"Stream error in chat {chat_id}: {update}. Attempting reconnect."
                )
                try:
                    await self.reconnect(chat_id)
                except Exception as e:
                    LOGGER(__name__).error(
                        f"Reconnect failed for {chat_id}: {e}. Stopping stream."
                    )
                    await self.stop_stream(chat_id)

            @instance.on_participants_change()
            async def participants_change_handler(client, update: Update):
                if not isinstance(update, UpdatedGroupCallParticipant):
                    return

                chat_id = update.chat_id
                users = counter.get(chat_id)

                if not users:
                    try:
                        got = len(await client.get_participants(chat_id))
                    except Exception:
                        return
                    counter[chat_id] = got
                    if got == 1:
                        autoend[chat_id] = datetime.now() + timedelta(
                            minutes=AUTO_END_TIME
                        )
                    else:
                        autoend[chat_id] = {}
                else:
                    final = (
                        users + 1
                        if update.participant.action == UpdatedGroupCallParticipant.Action.JOINED
                        else users - 1
                    )
                    counter[chat_id] = final
                    if final == 1:
                        autoend[chat_id] = datetime.now() + timedelta(
                            minutes=AUTO_END_TIME
                        )
                    else:
                        autoend[chat_id] = {}


ArchMusic = Call()
