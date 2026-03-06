#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

from ArchMusic.core.bot import ArchMusic
from ArchMusic.core.dir import dirr
from ArchMusic.core.git import git
from ArchMusic.core.userbot import Userbot
from ArchMusic.misc import dbb, heroku, sudo

from .logging import LOGGER

dirr()
git()
dbb()
heroku()
sudo()

app = ArchMusic()
userbot = Userbot()

from .platforms import *

YouTube = YouTubeAPI()
Carbon = CarbonAPI()
Spotify = SpotifyAPI()
Apple = AppleAPI()
Resso = RessoAPI()
SoundCloud = SoundAPI()
Telegram = TeleAPI()
