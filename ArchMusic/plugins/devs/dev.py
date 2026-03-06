#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import os
import re
import subprocess
import sys
import traceback
from inspect import getfullargspec
from io import StringIO
from time import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ArchMusic import app
from ArchMusic.misc import SUDOERS


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


def _runtime_keyboard(elapsed: float, user_id: int = None) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(
            text="⏳",
            callback_data=f"runtime {round(elapsed, 3)} Seconds",
        )
    ]
    if user_id is not None:
        row.append(
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"forceclose abc|{user_id}",
            )
        )
    return InlineKeyboardMarkup([row])


@app.on_message(
    filters.command("eval") & SUDOERS & ~filters.forwarded & ~filters.via_bot
)
async def executor(client, message: Message):
    if len(message.command) < 2:
        return await edit_or_reply(message, text="__Give me a command to execute.__")

    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await message.delete()

    t1 = time()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = redirected_output = StringIO()
    sys.stderr = redirected_error  = StringIO()
    exc = None
    try:
        await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()
    finally:
        stdout = redirected_output.getvalue()
        stderr = redirected_error.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    evaluation = exc or stderr or stdout or "Success"
    elapsed    = time() - t1
    final_output = f"**OUTPUT**:\n```{evaluation.strip()}```"

    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(evaluation.strip())
        await message.reply_document(
            document=filename,
            caption=f"**INPUT:**\n`{cmd[:980]}`\n\n**OUTPUT:**\n`Attached Document`",
            quote=False,
            reply_markup=_runtime_keyboard(elapsed),
        )
        await message.delete()
        os.remove(filename)
    else:
        await edit_or_reply(
            message,
            text=final_output,
            reply_markup=_runtime_keyboard(elapsed, message.from_user.id),
        )


@app.on_callback_query(filters.regex(r"^runtime "))
async def runtime_func_cq(_, cq):
    await cq.answer(cq.data.split(None, 1)[1], show_alert=True)


@app.on_callback_query(filters.regex(r"^forceclose "))
async def forceclose_command(_, cq):
    _, user_id = cq.data.split(None, 1)[1].split("|")
    if cq.from_user.id != int(user_id):
        try:
            return await cq.answer("You're not allowed to close this.", show_alert=True)
        except Exception:
            return
    await cq.message.delete()
    try:
        await cq.answer()
    except Exception:
        return


@app.on_message(
    filters.command("sh") & SUDOERS & ~filters.forwarded & ~filters.via_bot
)
async def shellrunner(client, message: Message):
    if len(message.command) < 2:
        return await edit_or_reply(message, text="**Usage:**\n`/sh git pull`")

    text = message.text.split(None, 1)[1]
    _splitter = r""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)"""

    if "\n" in text:
        output_parts = []
        for line in text.split("\n"):
            shell = re.split(_splitter, line)
            try:
                process = subprocess.Popen(
                    shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                out = process.stdout.read()[:-1].decode("utf-8")
                output_parts.append(f"**{line}**\n{out}")
            except Exception as err:
                await edit_or_reply(message, text=f"**ERROR:**\n```{err}```")
                return
        output = "\n".join(output_parts)
    else:
        shell = [s.replace('"', "") for s in re.split(_splitter, text)]
        try:
            process = subprocess.Popen(
                shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as err:
            errors = traceback.format_exc()
            return await edit_or_reply(message, text=f"**ERROR:**\n```{errors}```")
        output = process.stdout.read()[:-1].decode("utf-8")

    if not output or output == "\n":
        return await edit_or_reply(message, text="**OUTPUT:**\n`No output`")

    if len(output) > 4096:
        with open("output.txt", "w+") as f:
            f.write(output)
        await client.send_document(
            message.chat.id,
            "output.txt",
            reply_to_message_id=message.id,
            caption="`Output`",
        )
        os.remove("output.txt")
    else:
        await edit_or_reply(message, text=f"**OUTPUT:**\n```{output}```")
