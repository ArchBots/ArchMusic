#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import re
import random
import colorsys

import aiofiles
import aiohttp
import numpy as np
from PIL import (
    Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
)
from youtubesearchpython.__future__ import VideosSearch

from config import MUSIC_BOT_NAME, YOUTUBE_IMG_URL

W, H = 1280, 720
FONT_REG  = "assets/font.ttf"
FONT_BOLD = "assets/font2.ttf"

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def _rand_col(bright: bool = False) -> tuple:
    if bright:
        h = random.random()
        r, g, b = colorsys.hsv_to_rgb(h, 0.90, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))
    return (random.randint(30, 220), random.randint(30, 220), random.randint(30, 220))

def _contrast_pair() -> tuple:
    """Two complementary bright colours."""
    c1 = _rand_col(bright=True)
    c2 = tuple((v + 128) % 256 for v in c1)
    return c1, c2

def _cover_resize(img: Image.Image, w: int = W, h: int = H) -> Image.Image:
    """Scale + centre-crop to fill w×h exactly."""
    ratio = max(w / img.width, h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top  = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))

def _circle_crop(img: Image.Image, size: int) -> Image.Image:
    """Return a square image cropped to a circle (RGBA)."""
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    return img

def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple:
    """Return (width, height) for text using Pillow 10+ textbbox."""
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t

def _shadow_text(draw, xy, text, font, fill, shadow=(0, 0, 0), offset=3):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def _wrap_text(text: str, max_chars: int = 26) -> list:
    """Split text into max two lines of max_chars chars."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == 1:
                break
    if cur:
        lines.append(cur)
    return lines[:2]

def _recolour_white(path: str, colour: tuple) -> Image.Image:
    """Load a PNG and replace white pixels with colour (NumPy 2.x safe)."""
    img = Image.open(path).convert("RGBA")
    data = np.array(img, dtype=np.uint8)
    r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]
    white = (r > 200) & (g > 200) & (b > 200)
    data[..., 0][white] = colour[0]
    data[..., 1][white] = colour[1]
    data[..., 2][white] = colour[2]
    return Image.fromarray(data, "RGBA")

def _circle_portrait(base: Image.Image, size: int) -> Image.Image:
    """Build a circle-cropped portrait from the YouTube thumbnail."""
    sq = _cover_resize(base, size, size)
    return _circle_crop(sq, size)

def _make_vignette(w: int, h: int, strength: float = 0.70) -> Image.Image:
    """Radial dark vignette layer (RGBA, black with alpha)."""
    cx, cy = w / 2, h / 2
    xs = np.arange(w, dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)
    dx = (xx - cx) / cx
    dy = (yy - cy) / cy
    dist = np.clip(np.sqrt(dx * dx + dy * dy), 0, 1)
    alpha = (dist ** 2 * 255 * strength).astype(np.uint8)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = alpha
    return Image.fromarray(arr, "RGBA")

def _gradient_band(w: int, h: int, c1: tuple, c2: tuple,
                   alpha1: int = 210, alpha2: int = 210) -> Image.Image:
    """Vertical gradient RGBA band from c1 (top) to c2 (bottom)."""
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        t = y / max(h - 1, 1)
        col = tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3))
        alpha = int(alpha1 * (1 - t) + alpha2 * t)
        arr[y, :, :3] = col
        arr[y, :,  3] = alpha
    return Image.fromarray(arr, "RGBA")

def _style_classic(base, title, duration, views, channel, label):
    """Style 0 — Original: blurred BG, circle portrait, random coloured border."""
    colour = _rand_col()
    bg = _cover_resize(base).convert("RGBA")
    bg = bg.filter(ImageFilter.BoxBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)

    portrait = _circle_portrait(base, 560)
    bg.paste(portrait, (60, 80), portrait)

    try:
        ring = _recolour_white("assets/circle.png", colour)
        bg.paste(ring, (0, 0), ring)
    except Exception:
        pass

    d = ImageDraw.Draw(bg)
    fx, fy = 668, 100
    _shadow_text(d, (fx, fy),       label,  _font(FONT_BOLD, 66), "white")
    lines = _wrap_text(title)
    _shadow_text(d, (fx, fy + 160), lines[0] if lines else title, _font(FONT_BOLD, 42), "white")
    if len(lines) > 1:
        _shadow_text(d, (fx, fy + 215), lines[1], _font(FONT_BOLD, 42), "white")
    d.text((fx, fy + 310), f"⏱  {duration}", font=_font(FONT_REG, 34), fill="white")
    d.text((fx, fy + 355), f"👁  {views}",    font=_font(FONT_REG, 34), fill="white")
    d.text((fx, fy + 400), f"📺  {channel}",  font=_font(FONT_REG, 34), fill="white")
    d.text((W - 20, 12), MUSIC_BOT_NAME, font=_font(FONT_REG, 26), fill="white", anchor="ra")

    out = ImageOps.expand(bg.convert("RGB"), border=18, fill=colour)
    return out.resize((W, H), Image.LANCZOS)

def _style_neon(base, title, duration, views, channel, label):
    """Style 1 — Neon Glow: near-black BG, vivid neon rings, glow label."""
    c1, c2 = _contrast_pair()
    bg = _cover_resize(base).convert("RGBA")
    bg = bg.filter(ImageFilter.GaussianBlur(38))
    bg = ImageEnhance.Brightness(bg).enhance(0.20)

    portrait = _circle_portrait(base, 510)

    rings = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    cx, cy = 310, 360
    for radius, alpha, col in [(290, 90, c1), (305, 55, c2), (320, 28, c1)]:
        rd.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=col + (alpha,), width=5
        )
    bg = Image.alpha_composite(bg, rings)
    bg.paste(portrait, (cx - 255, cy - 255), portrait)

    d = ImageDraw.Draw(bg)
    lx, ly = 655, 80

    for off in (8, 5, 3):
        d.text((lx - off, ly - off), label, font=_font(FONT_BOLD, 62), fill=c1 + (40,))
    d.text((lx, ly), label, font=_font(FONT_BOLD, 62), fill=c2)

    lines = _wrap_text(title)
    d.text((lx, ly + 145), lines[0] if lines else title, font=_font(FONT_BOLD, 40), fill="white")
    if len(lines) > 1:
        d.text((lx, ly + 195), lines[1], font=_font(FONT_BOLD, 40), fill="white")

    d.line([(lx, ly + 258), (lx + 590, ly + 258)], fill=c1, width=3)
    d.text((lx, ly + 275), f"⏱  {duration}", font=_font(FONT_REG, 32), fill=c1)
    d.text((lx, ly + 318), f"👁  {views}",    font=_font(FONT_REG, 32), fill=c2)
    d.text((lx, ly + 361), f"📺  {channel}",  font=_font(FONT_REG, 32), fill="white")
    d.text((W - 20, 12), MUSIC_BOT_NAME, font=_font(FONT_REG, 24), fill=c1, anchor="ra")

    return bg.convert("RGB")

def _style_minimal(base, title, duration, views, channel, label):
    """Style 2 — Minimal Dark: desaturated BG, left semi-opaque card, accent bar."""
    c1, _ = _contrast_pair()
    bg = _cover_resize(base).convert("RGBA")
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    bg = ImageEnhance.Brightness(bg).enhance(0.32)
    bg = ImageEnhance.Color(bg).enhance(0.45)

    card = Image.new("RGBA", (590, H - 50), (10, 10, 10, 188))
    bg.paste(card, (0, 25), card)
    bar = Image.new("RGBA", (8, H - 50), c1 + (255,))
    bg.paste(bar, (0, 25), bar)

    portrait = _circle_portrait(base, 400)
    bg.paste(portrait, (W - 440, (H - 400) // 2), portrait)

    d = ImageDraw.Draw(bg)
    tx = 26
    d.text((tx, 48),  label, font=_font(FONT_BOLD, 56), fill=c1)
    lines = _wrap_text(title, 24)
    d.text((tx, 148), lines[0] if lines else title, font=_font(FONT_BOLD, 44), fill="white")
    if len(lines) > 1:
        d.text((tx, 202), lines[1], font=_font(FONT_BOLD, 44), fill="white")

    d.line([(tx, 282), (tx + 550, 282)], fill=c1, width=2)
    d.text((tx, 298), f"Duration   {duration}", font=_font(FONT_REG, 33), fill="white")
    d.text((tx, 344), f"Views      {views}",    font=_font(FONT_REG, 33), fill="white")
    d.text((tx, 390), f"Channel    {channel}",  font=_font(FONT_REG, 33), fill="white")
    d.text((tx, H - 52), MUSIC_BOT_NAME, font=_font(FONT_REG, 26), fill=c1)

    return bg.convert("RGB")

def _style_glass(base, title, duration, views, channel, label):
    """Style 3 — Glassmorphism: vivid BG, frosted translucent panel right side."""
    c1, c2 = _contrast_pair()
    bg = _cover_resize(base).convert("RGBA")
    bg = ImageEnhance.Brightness(bg).enhance(0.78)
    bg = ImageEnhance.Color(bg).enhance(1.35)

    blurred = bg.filter(ImageFilter.GaussianBlur(22))
    panel_x, panel_y = 625, 35
    panel_w, panel_h = W - panel_x - 15, H - 70
    panel_crop = blurred.crop((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h))
    tint = Image.new("RGBA", panel_crop.size, (255, 255, 255, 55))
    panel_final = Image.alpha_composite(panel_crop, tint)
    pd = ImageDraw.Draw(panel_final)
    pd.rectangle([(0, 0), (panel_w - 1, panel_h - 1)], outline=c1 + (180,), width=2)
    bg.paste(panel_final, (panel_x, panel_y))

    portrait = _circle_portrait(base, 500)
    bg.paste(portrait, (70, (H - 500) // 2), portrait)

    d = ImageDraw.Draw(bg)
    tx = panel_x + 18
    ty = panel_y + 25
    _shadow_text(d, (tx, ty),       label, _font(FONT_BOLD, 58), c2)
    lines = _wrap_text(title, 22)
    _shadow_text(d, (tx, ty + 135), lines[0] if lines else title, _font(FONT_BOLD, 40), "white")
    if len(lines) > 1:
        _shadow_text(d, (tx, ty + 185), lines[1], _font(FONT_BOLD, 40), "white")

    d.line([(tx, ty + 248), (tx + panel_w - 36, ty + 248)], fill=c1, width=2)
    d.text((tx, ty + 263), f"⏱  {duration}", font=_font(FONT_REG, 31), fill="white")
    d.text((tx, ty + 305), f"👁  {views}",    font=_font(FONT_REG, 31), fill="white")
    d.text((tx, ty + 347), f"📺  {channel}",  font=_font(FONT_REG, 31), fill="white")
    d.text((tx, panel_y + panel_h - 42), MUSIC_BOT_NAME, font=_font(FONT_REG, 24), fill=c1)

    return bg.convert("RGB")

def _style_cinema(base, title, duration, views, channel, label):
    """Style 4 — Cinema: letterbox bars, vignette, centred bold title."""
    c1, _ = _contrast_pair()
    bg = _cover_resize(base).convert("RGBA")
    bg = ImageEnhance.Brightness(bg).enhance(0.65)

    vig = _make_vignette(W, H, strength=0.75)
    bg = Image.alpha_composite(bg, vig)

    bar_h = 80
    bar = Image.new("RGBA", (W, bar_h), (0, 0, 0, 230))
    bg.paste(bar, (0, 0),       bar)
    bg.paste(bar, (0, H - bar_h), bar)

    d = ImageDraw.Draw(bg)

    d.text((22, 22), MUSIC_BOT_NAME, font=_font(FONT_REG, 30), fill="white")
    d.text((W - 22, 22), label, font=_font(FONT_BOLD, 30), fill=c1, anchor="ra")

    f_title = _font(FONT_BOLD, 68)
    lines = _wrap_text(title, 28)
    total_h = len(lines) * 82
    start_y = (H - total_h) // 2 - 20
    for i, line in enumerate(lines):
        tw, _ = _text_size(d, line, f_title)
        _shadow_text(d, ((W - tw) // 2, start_y + i * 82), line, f_title, "white")

    d.line([(W // 2 - 160, start_y + total_h + 14), (W // 2 + 160, start_y + total_h + 14)],
           fill=c1, width=3)

    meta = f"⏱ {duration}   👁 {views}   📺 {channel}"
    mw, _ = _text_size(d, meta, _font(FONT_REG, 28))
    d.text(((W - mw) // 2, H - bar_h + 22), meta, font=_font(FONT_REG, 28), fill="white")

    return bg.convert("RGB")

def _style_wave(base, title, duration, views, channel, label):
    """Style 5 — Wave: diagonal dual-colour gradient overlay, arc decoration."""
    c1, c2 = _contrast_pair()
    bg = _cover_resize(base).convert("RGBA")
    bg = ImageEnhance.Brightness(bg).enhance(0.50)

    grad = _gradient_band(620, H, c1, c2, alpha1=195, alpha2=215)
    bg.paste(grad, (0, 0), grad)

    arc_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc_layer)
    for offset, alpha in [(0, 60), (12, 35), (24, 18)]:
        ad.arc(
            (-100 + offset, -100 + offset, 780 - offset, 880 - offset),
            start=300, end=60,
            fill=c2 + (alpha,), width=18
        )
    bg = Image.alpha_composite(bg, arc_layer)

    portrait = _circle_portrait(base, 480)
    bg.paste(portrait, (W - 510, (H - 480) // 2), portrait)

    d = ImageDraw.Draw(bg)
    tx, ty = 30, 65
    _shadow_text(d, (tx, ty), label, _font(FONT_BOLD, 60), "white", shadow=c2)
    lines = _wrap_text(title, 22)
    _shadow_text(d, (tx, ty + 140), lines[0] if lines else title, _font(FONT_BOLD, 42), "white")
    if len(lines) > 1:
        _shadow_text(d, (tx, ty + 196), lines[1], _font(FONT_BOLD, 42), "white")

    d.line([(tx, ty + 265), (tx + 560, ty + 265)], fill="white", width=2)
    d.text((tx, ty + 280), f"⏱  {duration}", font=_font(FONT_REG, 33), fill="white")
    d.text((tx, ty + 325), f"👁  {views}",    font=_font(FONT_REG, 33), fill="white")
    d.text((tx, ty + 370), f"📺  {channel}",  font=_font(FONT_REG, 33), fill="white")
    d.text((tx, H - 52), MUSIC_BOT_NAME, font=_font(FONT_REG, 26), fill=c2)

    return bg.convert("RGB")

_STYLES = [
    _style_classic,
    _style_neon,
    _style_minimal,
    _style_glass,
    _style_cinema,
    _style_wave,
]

async def _fetch_yt_meta(videoid: str) -> dict:
    """Fetch title, duration, views, channel + download the hi-res thumbnail."""
    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    data = {}
    for result in (await results.next())["result"]:
        try:
            data["title"] = re.sub(r"\W+", " ", result["title"]).title()
        except Exception:
            data["title"] = "Unsupported Title"
        try:
            data["duration"] = result["duration"]
        except Exception:
            data["duration"] = "Unknown"
        try:
            data["views"] = result["viewCount"]["short"]
        except Exception:
            data["views"] = "Unknown"
        try:
            data["channel"] = result["channel"]["name"]
        except Exception:
            data["channel"] = "Unknown"

    thumb_path = f"cache/thumb{videoid}.jpg"
    if not os.path.isfile(thumb_path):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
            ) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, mode="wb") as f:
                        await f.write(await resp.read())

    return data

async def gen_thumb(videoid: str) -> str:
    """Generate and cache a NOW PLAYING thumbnail. Returns local path or fallback URL."""
    try:
        out_path = f"cache/{videoid}.jpg"
        if os.path.isfile(out_path):
            return out_path

        meta = await _fetch_yt_meta(videoid)
        base = Image.open(f"cache/thumb{videoid}.jpg")

        style_fn = random.choice(_STYLES)
        img = style_fn(
            base,
            title    = meta.get("title", "Unknown"),
            duration = meta.get("duration", "Unknown"),
            views    = meta.get("views", "Unknown"),
            channel  = meta.get("channel", "Unknown"),
            label    = "NOW PLAYING",
        )
        img.save(out_path)
        return out_path
    except Exception as e:
        print(f"[gen_thumb] {e}")
        return YOUTUBE_IMG_URL

async def gen_qthumb(videoid: str) -> str:
    """Generate and cache an ADDED TO QUEUE thumbnail. Returns local path or fallback URL."""
    try:
        out_path = f"cache/q{videoid}.jpg"
        if os.path.isfile(out_path):
            return out_path

        meta = await _fetch_yt_meta(videoid)
        base = Image.open(f"cache/thumb{videoid}.jpg")

        style_fn = random.choice(_STYLES)
        img = style_fn(
            base,
            title    = meta.get("title", "Unknown"),
            duration = meta.get("duration", "Unknown"),
            views    = meta.get("views", "Unknown"),
            channel  = meta.get("channel", "Unknown"),
            label    = "ADDED TO QUEUE",
        )
        img.save(out_path)
        return out_path
    except Exception as e:
        print(f"[gen_qthumb] {e}")
        return YOUTUBE_IMG_URL
