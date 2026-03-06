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

from pyrogram.types import InlineKeyboardButton

selection = [
    "░▒░▒▓▒░▒░",
    "▒░▓▒░▒▓░▒",
    "▓░▒▓░▒░▓░",
    "░▓▒░▒▓▒░▓",
    "▒▓░▒▓░▒▓░",
    "░░▒▓▓▒░░▒",
    "▒░░▓▒▓░░▒",
    "▓▒░▒░▒░▒▓",
    "░▒▓░▓▒░▒░",
    "▒░▒▓░▒▓▒░",
    "▁▂▃▅▇▅▃▂▁",
    "▂▃▅▇▅▃▂▁▂",
    "▃▅▇▅▃▂▁▂▃",
]


def time_to_sec(time: str) -> int:
    try:
        parts = time.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except (ValueError, AttributeError):
        return 0


def _build_progress_bar(played: str, dur: str) -> str:
    played_sec = time_to_sec(played)
    total_sec = time_to_sec(dur)
    if total_sec == 0:
        return f"{played} ══════════ {dur}"
    ratio = min(played_sec / total_sec, 1.0)
    pos = max(0, min(int(ratio * 10), 9))
    bar = "─" * pos + "●" + "─" * (9 - pos)
    return f"{played} {bar} {dur}"


def _nav_row(page: int, videoid, chat_id):
    return [
        InlineKeyboardButton(text="◀️", callback_data=f"Pages Back|{page}|{videoid}|{chat_id}"),
        InlineKeyboardButton(text="🔙 Back", callback_data=f"MainMarkup {videoid}|{chat_id}"),
        InlineKeyboardButton(text="▶️", callback_data=f"Pages Forw|{page}|{videoid}|{chat_id}"),
    ]


def stream_markup_timer(_, videoid, chat_id, played, dur):
    progress = _build_progress_bar(played, dur)
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎵 {progress}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="⏮ Prev",    callback_data=f"ADMIN Back|{chat_id}"),
            InlineKeyboardButton(text="⏸ Pause",   callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️ Resume",  callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏭ Skip",    callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="🔉 Vol-",   callback_data=f"ADMIN Vol-|{chat_id}"),
            InlineKeyboardButton(text="➕ Queue",   callback_data=f"add_playlist {videoid}"),
            InlineKeyboardButton(text="⏹ Stop",    callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text="🔊 Vol+",   callback_data=f"ADMIN Vol+|{chat_id}"),
        ],
    ]
    return buttons


def telegram_markup_timer(_, videoid, chat_id, played, dur):
    bar = random.choice(selection)
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎶 {played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="⏮ Prev",    callback_data=f"ADMIN Back|{chat_id}"),
            InlineKeyboardButton(text="⏸ Pause",   callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️ Resume",  callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏭ Skip",    callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="🔉 Vol-",   callback_data=f"ADMIN Vol-|{chat_id}"),
            InlineKeyboardButton(text="➕ Queue",   callback_data=f"add_playlist {videoid}"),
            InlineKeyboardButton(text="⏹ Stop",    callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text="🔊 Vol+",   callback_data=f"ADMIN Vol+|{chat_id}"),
        ],
    ]
    return buttons


def stream_markup(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["PL_B_2"],
                callback_data=f"add_playlist {videoid}",
            ),
            InlineKeyboardButton(
                text=_["PL_B_3"],
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"],
                callback_data="close",
            )
        ],
    ]
    return buttons


def telegram_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["PL_B_3"],
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    return buttons


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"ArchMusicPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"ArchMusicPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = query[:20]
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons


def panel_markup_1(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="⏮ Prev",    callback_data=f"ADMIN Back|{chat_id}"),
            InlineKeyboardButton(text="⏸ Pause",   callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️ Resume",  callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏭ Skip",    callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏹ Stop",    callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text="🔁 Loop",    callback_data=f"ADMIN Loop|{chat_id}"),
            InlineKeyboardButton(text="🔀 Shuffle", callback_data=f"ADMIN Shuffle|{chat_id}"),
        ],
        _nav_row(0, videoid, chat_id),
    ]
    return buttons


def panel_markup_2(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="🔇 Mute",    callback_data=f"ADMIN Mute|{chat_id}"),
            InlineKeyboardButton(text="🔊 Unmute",  callback_data=f"ADMIN Unmute|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="🔉 Vol -10", callback_data=f"ADMIN Vol-|{chat_id}"),
            InlineKeyboardButton(text="🔊 Vol +10", callback_data=f"ADMIN Vol+|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="📋 Queue",   callback_data=f"ADMIN Queue|{chat_id}"),
            InlineKeyboardButton(text="🗑 Clear",   callback_data=f"ADMIN Clear|{chat_id}"),
        ],
        _nav_row(1, videoid, chat_id),
    ]
    return buttons


def panel_markup_3(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="⏪ -10s", callback_data=f"ADMIN 1|{chat_id}"),
            InlineKeyboardButton(text="⏩ +10s", callback_data=f"ADMIN 2|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏪ -30s", callback_data=f"ADMIN 3|{chat_id}"),
            InlineKeyboardButton(text="⏩ +30s", callback_data=f"ADMIN 4|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏪ -60s", callback_data=f"ADMIN 5|{chat_id}"),
            InlineKeyboardButton(text="⏩ +60s", callback_data=f"ADMIN 6|{chat_id}"),
        ],
        _nav_row(2, videoid, chat_id),
    ]
    return buttons
