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

import speedtest
from pyrogram import filters

from strings import get_command
from ArchMusic import app
from ArchMusic.misc import SUDOERS

SPEEDTEST_COMMAND = get_command("SPEEDTEST_COMMAND")


def testspeed(m):
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        test.download()
        test.upload()
        test.results.share()
        result = test.results.dict()
    except Exception as e:
        return None, str(e)
    return result, None


@app.on_message(filters.command(SPEEDTEST_COMMAND) & SUDOERS)
async def speedtest_function(client, message):
    m = await message.reply_text("Running Speed test")
    loop = asyncio.get_event_loop()
    result, err = await loop.run_in_executor(None, testspeed, m)
    if err or not result:
        return await m.edit(f"Speedtest failed: {err}")
    output = f"""**Speedtest Results**

<u>**Client:**</u>
**__ISP:__** {result['client']['isp']}
**__Country:__** {result['client']['country']}

<u>**Server:**</u>
**__Name:__** {result['server']['name']}
**__Country:__** {result['server']['country']}, {result['server']['cc']}
**__Sponsor:__** {result['server']['sponsor']}
**__Latency:__** {result['server']['latency']}
**__Ping:__** {result['ping']}"""
    await app.send_photo(
        chat_id=message.chat.id,
        photo=result["share"],
        caption=output,
    )
    await m.delete()
