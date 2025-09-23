#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import aiohttp
import asyncio
from typing import Optional, Union


# List of pastebin services to try in order
PASTEBIN_SERVICES = [
    {
        "name": "batbin.me",
        "url": "https://batbin.me/api/v2/paste",
        "method": "POST",
        "data_key": "data",
        "response_parser": lambda resp: f"https://batbin.me/{resp['message']}" if resp.get("success") else None
    },
    {
        "name": "ix.io",
        "url": "https://ix.io/",
        "method": "POST", 
        "data_key": "f:1",
        "response_parser": lambda resp: resp.strip() if isinstance(resp, str) and resp.startswith("http") else None
    },
    {
        "name": "paste.rs",
        "url": "https://paste.rs/",
        "method": "POST",
        "data_key": None,  # Raw data
        "response_parser": lambda resp: resp.strip() if isinstance(resp, str) and resp.startswith("http") else None
    },
    {
        "name": "0x0.st",
        "url": "https://0x0.st/",
        "method": "POST",
        "data_key": "file",
        "response_parser": lambda resp: resp.strip() if isinstance(resp, str) and resp.startswith("http") else None
    }
]


async def post(url: str, *args, **kwargs):
    """Generic POST request function with timeout and error handling."""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, *args, **kwargs) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()
                    return data
                else:
                    return None
    except Exception:
        return None


async def try_pastebin_service(service: dict, text: str) -> Optional[str]:
    """Try to upload text to a specific pastebin service."""
    try:
        if service["data_key"] is None:
            # Raw data (like paste.rs)
            data = text.encode('utf-8')
            headers = {'Content-Type': 'text/plain'}
        elif service["data_key"] == "file":
            # File upload format (like 0x0.st)
            data = aiohttp.FormData()
            data.add_field('file', text, filename='update_log.txt', content_type='text/plain')
            headers = None
        else:
            # Form data format
            data = {service["data_key"]: text}
            headers = None
        
        resp = await post(service["url"], data=data, headers=headers)
        if resp:
            return service["response_parser"](resp)
    except Exception:
        pass
    return None


async def ArchMusicbin(text: str) -> Optional[str]:
    """
    Upload text to a pastebin service with fallback support.
    
    Tries multiple pastebin services in order until one succeeds.
    Returns the URL of the uploaded paste, or None if all services fail.
    """
    if not text or not text.strip():
        return None
    
    # Try each pastebin service in order
    for service in PASTEBIN_SERVICES:
        try:
            url = await try_pastebin_service(service, text)
            if url:
                return url
        except Exception:
            continue
    
    # If all services fail, return None
    return None
