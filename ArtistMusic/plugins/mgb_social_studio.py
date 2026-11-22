# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#    PLUGIN 1: MGB SOCIAL STUDIO (6 PRO CARDS + 100% HTML PILLS)
#    /tweet | /insta | /fakechat | /paycard | /passport | /shipday
# ═══════════════════════════════════════════════════════════════

import os
import io
import json
import html
import random
import asyncio
import hashlib
import unicodedata
from datetime import datetime, timezone, timedelta
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pyrogram import filters, enums
from pyrogram.types import Message

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

from ArtistMusic.plugins.mgb_viral_cards import (
    OWNER_UNAME,
    CHANNEL_UNAME,
    FOOTER,
    _cbtn,
    _get_user_dp,
    send_rich_card,
    send_colored_msg,
)

# ── STORAGE & CONFIG ──────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = "mgb_data"
SOCIAL_DB_FILE = os.path.join(DATA_DIR, "social_studio.json")
os.makedirs(DATA_DIR, exist_ok=True)

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "Δ": "A", "α": "A", "Σ": "E", "Ω": "O", "β": "B",
    "χ": "X", "Χ": "X", "×": "X", "✗": "X", "✘": "X", "✕": "X", "✖": "X", "⨯": "X", "᙭": "X",
})

def _load_social_db() -> dict:
    base = {"members": {}, "daily_ship": {}, "passports": {}}
    if os.path.isfile(SOCIAL_DB_FILE):
        try:
            with open(SOCIAL_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            base.update(data)
        except Exception:
            pass
    return base

SDB = _load_social_db()

def _save_social_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SOCIAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(SDB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 100% PERMANENT BOTTOM HTML PILL BUTTONS (NO CALLBACKS) ────
def _bottom_html_pills(profile_url: str = None, profile_label: str = "👤 𝐏𝐑𝐎𝐅𝐈𝐋𝐄") -> list:
    bottom_row = [
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]
    if profile_url:
        return [[_cbtn(profile_label, style="primary", url=profile_url)], bottom_row]
    return [bottom_row]

async def _send_pill_notice(client, chat_id: int, text: str, reply_to: int = None):
    await send_colored_msg(client, chat_id, text, _bottom_html_pills(), reply_to=reply_to)

async def _send_studio_card(client, chat_id: int, card_io: io.BytesIO, caption: str, rows: list):
    try:
        await send_rich_card(client, chat_id, card_io, caption, json_rows=rows)
    except TypeError:
        card_io.seek(0)
        await send_rich_card(client, chat_id, card_io, caption)

def _user_profile_link(user) -> str:
    uname = getattr(user, "username", None)
    return f"https://t.me/{uname}" if uname else f"https://t.me/{CHANNEL_UNAME}"

# ── CLEAN TEXT, FONT & STUDIO GRAPHICS HELPERS ────────────────
def _clean_name(val: str, limit: int = 22) -> str:
    s = unicodedata.normalize("NFKC", str(val or "MGB VIP")).translate(FANCY_MAP)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip()
    parts = s.split()
    if len(parts) >= 4 and all(len(p) == 1 for p in parts):
        s = "".join(parts)
    return s[:limit] or "MGB VIP"

def _clean_body(val: str, limit: int = 220) -> str:
    s = unicodedata.normalize("NFKC", str(val or "")).translate(FANCY_MAP)
    s = "".join(ch if (32 <= ord(ch) <= 126 or ch == "\n") else " " for ch in s)
    lines = [" ".join(ln.split()) for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln).strip()[:limit] or "Royal MGB Vibes Only!"

def _font(size: int, bold: bool = True):
    paths = (
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
        if bold else
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    )
    for fp in paths:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _draw_center(draw: ImageDraw.Draw, cx: int, cy: int, text: str, font, fill: tuple):
    try:
        draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")
    except TypeError:
        b = draw.textbbox((0, 0), text, font=font)
        draw.text((int(cx - (b[2] - b[0]) / 2), int(cy - (b[3] - b[1]) / 2 - b[1])), text, font=font, fill=fill)

def _make_gradient(w: int, h: int, c1: tuple, c2: tuple, horiz: bool = False) -> Image.Image:
    strip = Image.new("RGB", (256, 1) if horiz else (1, 256))
    px = strip.load()
    for i in range(256):
        t = i / 255.0
        col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        if horiz:
            px[i, 0] = col
        else:
            px[0, i] = col
    return strip.resize((w, h), Image.BICUBIC)

def _wrap_lines(draw: ImageDraw.Draw, text: str, font, max_w: int, max_lines: int = 4) -> list:
    out = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            continue
        cur = words[0]
        for w in words[1:]:
            test = f"{cur} {w}"
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                cur = test
            else:
                out.append(cur)
                cur = w
                if len(out) >= max_lines:
                    break
        if len(out) < max_lines:
            out.append(cur)
        if len(out) >= max_lines:
            break
    if len(out) == max_lines and len(text) > sum(len(x) for x in out) + 5:
        out[-1] = out[-1][:-3].rstrip() + "..."
    return out or ["..."]

def _draw_glow(canvas: Image.Image, cx: int, cy: int, r: int, color: tuple):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(int(r * 0.55))))

def _paste_circle_dp(canvas: Image.Image, dp: Image.Image, cx: int, cy: int, r: int, ring_col=None, ring_w: int = 4, glow_col=None):
    if glow_col:
        _draw_glow(canvas, cx, cy, r + 14, glow_col)
    size = r * 2
    av = ImageOps.fit(dp.convert("RGBA"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    canvas.paste(av, (cx - r, cy - r), mask)
    if ring_col and ring_w > 0:
        ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring_col, width=ring_w)

def _draw_verified(draw: ImageDraw.Draw, cx: int, cy: int, r: int = 14, bg=(29, 155, 240)):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg)
    pts = [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.12, cy + r * 0.36), (cx + r * 0.48, cy - r * 0.32)]
    draw.line(pts, fill=(255, 255, 255), width=max(2, int(r * 0.24)), joint="curve")

def _save_jpg(img: Image.Image, name: str) -> io.BytesIO:
    out = io.BytesIO()
    out.name = name
    img.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out

async def _fetch_qr_image(data_url: str, size: int = 210) -> Image.Image:
    try:
        api = f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&margin=8&data={data_url}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.get(api) as r:
                if r.status == 200:
                    return Image.open(io.BytesIO(await r.read())).convert("RGB").resize((size, size), Image.NEAREST)
    except Exception:
        pass
    im = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cell, h = size // 21, hashlib.sha256(data_url.encode()).digest()
    for r in range(21):
        for c in range(21):
            finder = (r < 7 and c < 7) or (r < 7 and c >= 14) or (r >= 14 and c < 7)
            if finder:
                on = (r in (0, 6, 14, 20) or c in (0, 6, 14, 20)) or (
                    (2 <= r <= 4 and 2 <= c <= 4) or (2 <= r <= 4 and 16 <= c <= 18) or (16 <= r <= 18 and 2 <= c <= 4)
                )
            else:
                on = bool((h[(r * 21 + c) % len(h)] >> ((r + c) % 8)) & 1)
            if on:
                d.rectangle((c * cell, r * cell, (c + 1) * cell - 1, (r + 1) * cell - 1), fill=(12, 16, 30))
    return im
# ── CARD 1: FAKE X / TWITTER VERIFIED POST CARD ───────────────
def _render_tweet_card(dp: Image.Image, name: str, handle: str, text: str) -> io.BytesIO:
    W, H = 1200, 680
    bg = _make_gradient(W, H, (8, 12, 22), (18, 26, 46)).convert("RGBA")
    _draw_glow(bg, 180, 110, 220, (29, 155, 240, 80))
    _draw_glow(bg, 1050, 580, 240, (124, 58, 237, 75))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((62, 54, W - 62, H - 54), radius=34, fill=(14, 18, 28, 240), outline=(56, 88, 134, 225), width=3)

    _paste_circle_dp(bg, dp, 162, 158, 56, ring_col=(29, 155, 240, 255), ring_w=4, glow_col=(29, 155, 240, 105))
    d = ImageDraw.Draw(bg)
    cname = _clean_name(name, 22)
    f_name, f_handle = _font(34, True), _font(24, False)
    d.text((242, 118), cname, font=f_name, fill=(255, 255, 255))
    nw = d.textbbox((0, 0), cname, font=f_name)[2]
    _draw_verified(d, 242 + nw + 24, 138, r=15)
    d.text((242, 162), f"@{handle}", font=f_handle, fill=(138, 154, 178))

    # Top-right X emblem
    d.rounded_rectangle((W - 172, 104, W - 102, 174), radius=18, fill=(24, 32, 48, 255), outline=(64, 92, 134, 220), width=2)
    _draw_center(d, W - 137, 139, "X", _font(42, True), (255, 255, 255))

    # Crisp wrapped tweet text
    f_body = _font(36, False)
    y = 248
    for ln in _wrap_lines(d, _clean_body(text, 210), f_body, W - 220, max_lines=4):
        d.text((110, y), ln, font=f_body, fill=(244, 248, 255))
        y += 52

    now_str = datetime.now(IST).strftime("%I:%M %p  •  %d %b %Y  •  MGB VIP X")
    d.text((110, 488), now_str, font=_font(22, False), fill=(134, 150, 174))
    d.line((110, 532, W - 110, 532), fill=(42, 56, 78, 255), width=2)

    likes = f"{random.randint(12, 98)}.{random.randint(1, 9)}K"
    reposts = f"{random.randint(2, 19)}.{random.randint(1, 9)}K"
    views = f"{random.randint(120, 890)}K"
    d.text((110, 558), f"{reposts} Reposts     {likes} Likes     {views} Views", font=_font(24, True), fill=(198, 218, 245))
    d.text((W - 348, 560), "MGB NOT CODER", font=_font(22, True), fill=(29, 155, 240))
    return _save_jpg(bg, "mgb_tweet.jpg")

# ── CARD 2: FAKE INSTAGRAM VERIFIED POST CARD ─────────────────
def _render_insta_card(dp: Image.Image, post_img: Image.Image, name: str, handle: str, caption: str) -> io.BytesIO:
    W, H = 1080, 1140
    bg = _make_gradient(W, H, (28, 12, 40), (12, 14, 24)).convert("RGBA")
    _draw_glow(bg, 160, 140, 260, (245, 96, 64, 90))
    _draw_glow(bg, 940, 980, 280, (193, 53, 132, 95))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((54, 46, W - 54, H - 46), radius=34, fill=(18, 18, 24, 245), outline=(225, 48, 108, 200), width=3)

    # Top bar: Instagram DP ring + handle + blue tick
    _paste_circle_dp(bg, dp, 136, 122, 42, ring_col=(245, 96, 64, 255), ring_w=5, glow_col=(225, 48, 108, 95))
    d = ImageDraw.Draw(bg)
    f_h = _font(30, True)
    d.text((196, 92), handle, font=f_h, fill=(255, 255, 255))
    hw = d.textbbox((0, 0), handle, font=f_h)[2]
    _draw_verified(d, 196 + hw + 22, 110, r=13)
    d.text((196, 130), "MGB Royal Feed  •  India", font=_font(21, False), fill=(166, 170, 188))
    d.text((W - 142, 98), "...", font=_font(40, True), fill=(224, 228, 240))

    # Center HD photo frame
    px1, py1, px2, py2 = 88, 186, W - 88, 808
    pw, ph = px2 - px1, py2 - py1
    photo = ImageOps.fit((post_img or dp).convert("RGBA"), (pw, ph), Image.LANCZOS)
    pmask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(pmask).rounded_rectangle((0, 0, pw, ph), radius=24, fill=255)
    bg.paste(photo, (px1, py1), pmask)

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((px1, py1, px2, py2), radius=24, outline=(255, 255, 255, 70), width=2)

    # Red heart + likes + branding
    hx, hy = 118, 858
    d.ellipse((hx - 14, hy - 12, hx + 2, hy + 4), fill=(255, 48, 86))
    d.ellipse((hx - 2, hy - 12, hx + 14, hy + 4), fill=(255, 48, 86))
    d.polygon([(hx - 13, hy - 1), (hx + 13, hy - 1), (hx, hy + 16)], fill=(255, 48, 86))

    likes = f"{random.randint(14, 96)},{random.randint(100, 999)} likes"
    d.text((156, 840), likes, font=_font(28, True), fill=(255, 255, 255))
    d.text((W - 332, 844), "MGB NOT CODER", font=_font(22, True), fill=(247, 119, 55))

    # Caption lines
    cap_txt = f"{handle}  {_clean_body(caption, 150)}"
    f_cap = _font(27, False)
    cy = 896
    for ln in _wrap_lines(d, cap_txt, f_cap, W - 188, max_lines=3):
        d.text((94, cy), ln, font=f_cap, fill=(238, 240, 248))
        cy += 40

    d.text((94, H - 102), "JUST NOW  •  VERIFIED BY MGB STUDIO", font=_font(20, True), fill=(140, 146, 168))
    return _save_jpg(bg, "mgb_insta.jpg")

# ── CARD 3: FAKE WHATSAPP DARK CHAT SCREENSHOT CARD ───────────
def _render_whatsapp_card(dp: Image.Image, name: str, msg_text: str) -> io.BytesIO:
    W, H = 1200, 620
    bg = _make_gradient(W, H, (11, 20, 26), (17, 29, 38)).convert("RGBA")
    d = ImageDraw.Draw(bg)

    for gx in range(30, W, 54):
        for gy in range(132, H - 40, 54):
            d.ellipse((gx, gy, gx + 4, gy + 4), fill=(34, 52, 62, 115))

    # Top WhatsApp Header
    d.rectangle((0, 0, W, 118), fill=(31, 44, 52, 255))
    _paste_circle_dp(bg, dp, 92, 59, 40, ring_col=(37, 211, 102, 225), ring_w=3)
    d = ImageDraw.Draw(bg)
    cname = _clean_name(name, 22)
    d.text((152, 26), cname, font=_font(32, True), fill=(242, 246, 250))
    d.text((152, 68), "online", font=_font(22, False), fill=(37, 211, 102))
    d.text((W - 296, 44), "MGB NOT CODER", font=_font(22, True), fill=(134, 150, 160))

    # Today pill
    d.rounded_rectangle((W // 2 - 86, 146, W // 2 + 86, 190), radius=18, fill=(24, 34, 41, 245))
    _draw_center(d, W // 2, 168, "TODAY", _font(20, True), (156, 172, 182))

    # Incoming chat bubble
    f_msg = _font(34, False)
    lines = _wrap_lines(d, _clean_body(msg_text, 200), f_msg, 820, max_lines=4)
    line_h = 48
    max_lw = max(d.textbbox((0, 0), ln, font=f_msg)[2] for ln in lines)
    bw = max(360, min(910, max_lw + 124))
    bh = max(142, len(lines) * line_h + 98)
    bx1, by1 = 96, 226
    bx2, by2 = bx1 + bw, by1 + bh

    d.polygon([(bx1 - 18, by1), (bx1 + 20, by1), (bx1 + 10, by1 + 28)], fill=(32, 44, 51, 255))
    d.rounded_rectangle((bx1, by1, bx2, by2), radius=24, fill=(32, 44, 51, 255), outline=(48, 68, 78, 255), width=2)
    d.text((bx1 + 28, by1 + 18), f"~ {cname}", font=_font(24, True), fill=(37, 211, 102))

    ty = by1 + 56
    for ln in lines:
        d.text((bx1 + 28, ty), ln, font=f_msg, fill=(238, 244, 248))
        ty += line_h

    tstr = datetime.now(IST).strftime("%I:%M %p")
    d.text((bx2 - 154, by2 - 36), tstr, font=_font(20, False), fill=(142, 158, 168))
    tx, ty_t = bx2 - 48, by2 - 22
    for off in (0, 9):
        d.line([(tx + off, ty_t), (tx + off + 6, ty_t + 6), (tx + off + 16, ty_t - 6)], fill=(83, 189, 235), width=3)

    # Bottom fake input bar
    d.rounded_rectangle((46, H - 84, W - 46, H - 24), radius=28, fill=(31, 44, 52, 255))
    d.text((86, H - 66), "Message...", font=_font(24, False), fill=(134, 150, 160))
    return _save_jpg(bg, "mgb_fakechat.jpg")

# ── CARD 4: FUNNY ROYAL BANK PAYMENT PRANK CARD ───────────────
def _render_paycard(dp: Image.Image, receiver_name: str, sender_name: str, amount: str, note: str) -> io.BytesIO:
    W, H = 1200, 740
    bg = _make_gradient(W, H, (6, 28, 22), (10, 18, 34)).convert("RGBA")
    _draw_glow(bg, 600, 160, 240, (16, 185, 129, 100))
    _draw_glow(bg, 1020, 620, 230, (245, 196, 81, 85))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((58, 44, W - 58, H - 44), radius=34, fill=(10, 22, 26, 242), outline=(218, 180, 62, 230), width=4)

    _draw_verified(d, W // 2, 126, r=42, bg=(16, 185, 129))
    _draw_center(d, W // 2, 198, "PAYMENT SUCCESSFUL", _font(32, True), (16, 230, 156))
    _draw_center(d, W // 2, 274, f"Rs. {amount}", _font(72, True), (255, 222, 122))

    # Receiver Box + DP
    d.rounded_rectangle((122, 344, W - 122, 514), radius=26, fill=(18, 36, 40, 242), outline=(58, 126, 108, 215), width=2)
    _paste_circle_dp(bg, dp, 212, 429, 56, ring_col=(245, 200, 90, 255), ring_w=4, glow_col=(245, 200, 90, 85))
    d = ImageDraw.Draw(bg)
    rname, sname = _clean_name(receiver_name, 22), _clean_name(sender_name, 18)
    d.text((294, 372), f"PAID TO :  {rname}", font=_font(30, True), fill=(255, 255, 255))
    d.text((294, 418), f"FROM    :  {sname}  (MGB Royal Bank)", font=_font(23, False), fill=(178, 210, 200))
    d.text((294, 456), f"NOTE    :  {_clean_body(note, 34)}", font=_font(22, False), fill=(255, 220, 134))

    # UTR + Timestamp + Royal Bank Stamp
    utr = f"MGB{random.randint(100000000, 999999999)}"
    ts = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    d.text((128, 554), f"UTR / REF NO :  {utr}", font=_font(23, True), fill=(182, 206, 202))
    d.text((128, 596), f"DATE & TIME  :  {ts}", font=_font(22, False), fill=(142, 166, 162))
    d.rounded_rectangle((W - 418, 558, W - 122, 624), radius=18, fill=(218, 180, 62, 245))
    _draw_center(d, W - 270, 591, "MGB ROYAL BANK", _font(23, True), (12, 18, 22))
    return _save_jpg(bg, "mgb_paycard.jpg")

# ── CARD 5: OFFICIAL VIP PASSPORT CARD (SCANNABLE QR) ─────────
def _render_passport_card(dp: Image.Image, qr_img: Image.Image, name: str, uid: int, handle: str, pass_no: str, group_name: str, rank_title: str) -> io.BytesIO:
    W, H = 1280, 760
    bg = _make_gradient(W, H, (10, 18, 44), (26, 12, 50)).convert("RGBA")
    _draw_glow(bg, 240, 380, 260, (218, 180, 62, 85))
    _draw_glow(bg, 1060, 200, 250, (56, 189, 248, 75))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((36, 36, W - 36, H - 36), radius=34, fill=(13, 20, 42, 244), outline=(236, 196, 94, 248), width=5)
    d.rounded_rectangle((54, 54, W - 54, H - 54), radius=26, outline=(126, 106, 58, 185), width=2)

    # Top Passport Header
    d.rounded_rectangle((74, 72, W - 74, 166), radius=20, fill=(24, 34, 74, 248), outline=(236, 196, 94, 195), width=2)
    d.text((112, 96), "REPUBLIC OF MGB  •  OFFICIAL VIP PASSPORT", font=_font(31, True), fill=(255, 220, 124))
    d.text((112, 134), f"ISSUING AUTHORITY: {_clean_name(group_name, 30)}   |   STATUS: VERIFIED", font=_font(19, False), fill=(184, 208, 244))

    # Left DP + Rank Badge
    _paste_circle_dp(bg, dp, 242, 374, 134, ring_col=(244, 202, 98, 255), ring_w=6, glow_col=(244, 202, 98, 100))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((110, 532, 374, 586), radius=24, fill=(236, 196, 94, 255))
    _draw_center(d, 242, 559, rank_title, _font(22, True), (14, 18, 36))

    # Center Details
    cname = _clean_name(name, 20)
    today = datetime.now(IST).strftime("%d %b %Y")
    fields = [
        ("PASSPORT HOLDER", cname),
        ("PASSPORT NUMBER", pass_no),
        ("TELEGRAM HANDLE", f"@{handle}" if handle else f"ID {uid}"),
        ("ISSUED DATE", f"{today}  (LIFETIME VALID)"),
    ]
    fy = 212
    for lbl, val in fields:
        d.text((426, fy), lbl, font=_font(18, True), fill=(236, 196, 94))
        d.text((426, fy + 24), val, font=_font(30, True), fill=(255, 255, 255))
        fy += 88

    # Right Scannable QR Box
    qx, qy, qs = 964, 240, 214
    d.rounded_rectangle((qx - 18, qy - 18, qx + qs + 18, qy + qs + 62), radius=24, fill=(255, 255, 255, 255), outline=(236, 196, 94, 255), width=4)
    bg.paste(qr_img.resize((qs, qs), Image.NEAREST), (qx, qy))
    d = ImageDraw.Draw(bg)
    _draw_center(d, qx + qs // 2, qy + qs + 28, "SCAN PROFILE QR", _font(20, True), (14, 20, 42))

    # Bottom MRZ Code Strip
    d.rounded_rectangle((74, 622, W - 74, 694), radius=14, fill=(8, 12, 28, 255), outline=(94, 84, 56, 185), width=2)
    mrz = f"P<MGB{cname.replace(' ', '<')[:16]}<<<{pass_no}<<<MGB<NOT<CODER<<<<<2026"
    d.text((104, 646), mrz[:58], font=_font(22, True), fill=(168, 196, 228))
    return _save_jpg(bg, "mgb_passport.jpg")

# ── CARD 6: AAJ KI BEST JODI (ROYAL DUO OF THE DAY) ───────────
def _render_shipday_card(dp1: Image.Image, dp2: Image.Image, name1: str, name2: str, pct: int, date_str: str) -> io.BytesIO:
    W, H = 1280, 720
    bg = _make_gradient(W, H, (40, 10, 38), (16, 12, 44)).convert("RGBA")
    _draw_glow(bg, 300, 360, 260, (244, 63, 94, 100))
    _draw_glow(bg, 980, 360, 260, (236, 72, 153, 100))
    _draw_glow(bg, 640, 340, 200, (251, 191, 36, 90))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((42, 42, W - 42, H - 42), radius=34, fill=(22, 10, 30, 224), outline=(246, 182, 120, 240), width=4)

    # Top Title Pill
    d.rounded_rectangle((W // 2 - 285, 68, W // 2 + 285, 134), radius=32, fill=(244, 63, 94, 245), outline=(255, 226, 168, 245), width=3)
    _draw_center(d, W // 2, 101, "AAJ KI BEST JODI  •  ROYAL DUO", _font(26, True), (255, 255, 255))

    # Left & Right Glowing DPs
    _paste_circle_dp(bg, dp1, 310, 344, 146, ring_col=(255, 206, 134, 255), ring_w=6, glow_col=(244, 63, 94, 125))
    _paste_circle_dp(bg, dp2, 970, 344, 146, ring_col=(255, 206, 134, 255), ring_w=6, glow_col=(236, 72, 153, 125))

    # Center Match % Badge
    d = ImageDraw.Draw(bg)
    d.ellipse((W // 2 - 86, 258, W // 2 + 86, 430), fill=(244, 63, 94, 255), outline=(255, 226, 152, 255), width=5)
    _draw_center(d, W // 2, 330, f"{pct}%", _font(50, True), (255, 255, 255))
    _draw_center(d, W // 2, 382, "MATCH", _font(20, True), (255, 234, 178))

    # Name Pills
    n1, n2 = _clean_name(name1, 18), _clean_name(name2, 18)
    d.rounded_rectangle((130, 520, 490, 584), radius=30, fill=(48, 18, 54, 248), outline=(246, 182, 120, 225), width=3)
    _draw_center(d, 310, 552, n1, _font(28, True), (255, 255, 255))
    d.rounded_rectangle((790, 520, 1150, 584), radius=30, fill=(48, 18, 54, 248), outline=(246, 182, 120, 225), width=3)
    _draw_center(d, 970, 552, n2, _font(28, True), (255, 255, 255))

    _draw_center(d, W // 2, 638, f"DATE: {date_str}   •   MGB NOT CODER", _font(23, True), (255, 216, 154))
    return _save_jpg(bg, "mgb_shipday.jpg")
# ── HELPER: EXTRACT TARGET USER, TEXT & OPTIONAL PHOTO ────────
def _extract_target_and_text(message: Message):
    reply = message.reply_to_message
    raw_args = message.text.split(None, 1)[1].strip() if (message.text and len(message.text.split(None, 1)) > 1) else ""
    if reply and reply.from_user:
        target = reply.from_user
        body = raw_args or (reply.text or reply.caption or "").strip()
    else:
        target = message.from_user
        body = raw_args
    return target, body

async def _download_replied_photo(client, message: Message):
    src = message.reply_to_message if (message.reply_to_message and message.reply_to_message.photo) else (message if message.photo else None)
    if not src:
        return None
    try:
        bio = await client.download_media(src, in_memory=True)
        if bio:
            bio.seek(0)
            return Image.open(bio).convert("RGB")
    except Exception:
        pass
    return None

def _make_handle(user) -> str:
    if getattr(user, "username", None):
        return user.username
    base = "".join(ch for ch in _clean_name(user.first_name, 14).lower() if ch.isalnum())
    return base or f"mgb_{str(user.id)[-4:]}"

def _format_inr(raw_amt: str) -> str:
    cleaned = "".join(ch for ch in raw_amt if ch.isdigit())
    if not cleaned:
        return "50,000"
    val = min(999999999, max(1, int(cleaned)))
    return f"{val:,}"

# ── 1. FAKE X / TWITTER POST CARD (/tweet) ────────────────────
@bot.on_message(filters.command(["tweet", "faketweet", "xpost"], prefixes=["/", "!", "."]))
async def fake_tweet_cmd(client, message: Message):
    target, body = _extract_target_and_text(message)
    if not target:
        return
    if not body:
        return await _send_pill_notice(
            client, message.chat.id,
            f"<blockquote><b>🐦 𝐌𝐆𝐁 𝐅𝐀𝐊𝐄 𝐓𝐖𝐄𝐄𝐓 𝐒𝐓𝐔𝐃𝐈𝐎</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> <code>/tweet Aaj mausam bahut royal hai!</code>\n"
            f"💬 <b>Ya kisi ke message par reply karke likhein:</b> <code>/tweet</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    dp = await _get_user_dp(client, target.id)
    handle = _make_handle(target)
    card = await asyncio.to_thread(_render_tweet_card, dp, target.first_name, handle, body)
    cap = (
        f"<blockquote><b>🐦 𝐕𝐄𝐑𝐈𝐅𝐈𝐄𝐃 𝐗 (𝐓𝐖𝐈𝐓𝐓𝐄𝐑) 𝐏𝐎𝐒𝐓</b></blockquote>\n\n"
        f"👤 <b>Author:</b> <b>{html.escape(target.first_name)}</b> (<code>@{html.escape(handle)}</code>)\n\n{FOOTER}"
    )
    await _send_studio_card(client, message.chat.id, card, cap, _bottom_html_pills(_user_profile_link(target), "🐦 𝐕𝐈𝐄𝐖 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 2. FAKE INSTAGRAM POST CARD (/insta) ──────────────────────
@bot.on_message(filters.command(["insta", "instapost", "ig"], prefixes=["/", "!", "."]))
async def fake_insta_cmd(client, message: Message):
    target, body = _extract_target_and_text(message)
    if not target:
        return
    post_photo = await _download_replied_photo(client, message)
    if not body and not post_photo:
        return await _send_pill_notice(
            client, message.chat.id,
            f"<blockquote><b>📸 𝐌𝐆𝐁 𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌 𝐒𝐓𝐔𝐃𝐈𝐎</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> <code>/insta Royal vibes only!</code>\n"
            f"🖼 <b>Photo ke saath:</b> Kisi photo par reply karke <code>/insta Caption</code> likhein!\n\n{FOOTER}",
            reply_to=message.id,
        )

    caption_txt = body or "Living the Royal MGB Lifestyle!"
    dp = await _get_user_dp(client, target.id)
    handle = _make_handle(target)
    card = await asyncio.to_thread(_render_insta_card, dp, post_photo or dp, target.first_name, handle, caption_txt)
    cap = (
        f"<blockquote><b>📸 𝐕𝐄𝐑𝐈𝐅𝐈𝐄𝐃 𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌 𝐏𝐎𝐒𝐓</b></blockquote>\n\n"
        f"👤 <b>Account:</b> <b>{html.escape(target.first_name)}</b> (<code>@{html.escape(handle)}</code>)\n\n{FOOTER}"
    )
    await _send_studio_card(client, message.chat.id, card, cap, _bottom_html_pills(_user_profile_link(target), "📸 𝐕𝐈𝐄𝐖 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 3. FAKE WHATSAPP CHAT CARD (/fakechat) ────────────────────
@bot.on_message(filters.command(["fakechat", "whatsapp", "wa"], prefixes=["/", "!", "."]))
async def fake_whatsapp_cmd(client, message: Message):
    target, body = _extract_target_and_text(message)
    if not target:
        return
    if not body:
        return await _send_pill_notice(
            client, message.chat.id,
            f"<blockquote><b>💬 𝐅𝐀𝐊𝐄 𝐖𝐇𝐀𝐓𝐒𝐀𝐏𝐏 𝐂𝐇𝐀𝐓 𝐒𝐓𝐔𝐃𝐈𝐎</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> Kisi dost par reply karke likhein <code>/fakechat Bhai party kab de raha hai?</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    dp = await _get_user_dp(client, target.id)
    card = await asyncio.to_thread(_render_whatsapp_card, dp, target.first_name, body)
    cap = (
        f"<blockquote><b>💬 𝐋𝐄𝐀𝐊𝐄𝐃 𝐖𝐇𝐀𝐓𝐒𝐀𝐏𝐏 𝐂𝐇𝐀𝐓</b></blockquote>\n\n"
        f"👤 <b>Sender:</b> <b>{html.escape(target.first_name)}</b>\n\n{FOOTER}"
    )
    await _send_studio_card(client, message.chat.id, card, cap, _bottom_html_pills(_user_profile_link(target), "💬 𝐕𝐈𝐄𝐖 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 4. FUNNY ROYAL BANK PRANK PAYMENT CARD (/paycard) ─────────
@bot.on_message(filters.command(["paycard", "payprank", "royalpay"], prefixes=["/", "!", "."]))
async def paycard_prank_cmd(client, message: Message):
    sender = message.from_user
    if not sender:
        return
    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else sender
    )
    args = message.command[1:] if len(message.command) > 1 else []
    if args and any(ch.isdigit() for ch in args[0]):
        amount = _format_inr(args[0])
        note = " ".join(args[1:]).strip() or "Royal Party & VIP Treat!"
    else:
        amount = _format_inr(str(random.choice([5000, 11000, 25000, 50000, 100000])))
        note = " ".join(args).strip() or "Royal Party & VIP Treat!"

    dp = await _get_user_dp(client, target.id)
    card = await asyncio.to_thread(_render_paycard, dp, target.first_name, sender.first_name, amount, note)
    cap = (
        f"<blockquote><b>💳 𝐌𝐆𝐁 𝐑𝐎𝐘𝐀𝐋 𝐁𝐀𝐍𝐊 𝐓𝐑𝐀𝐍𝐒𝐅𝐄𝐑</b></blockquote>\n\n"
        f"✅ <b>Amount:</b> <code>Rs. {amount}</code>\n"
        f"👤 <b>Paid To:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"😂 <b>Note:</b> <code>{html.escape(note[:40])}</code> <i>(Fun Prank Card)</i>\n\n{FOOTER}"
    )
    await _send_studio_card(client, message.chat.id, card, cap, _bottom_html_pills(_user_profile_link(target), "💳 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐑"))

# ── 5. OFFICIAL VIP PASSPORT CARD (/passport) ─────────────────
@bot.on_message(filters.command(["passport", "vipid", "mgbid"], prefixes=["/", "!", "."]))
async def vip_passport_cmd(client, message: Message):
    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else message.from_user
    )
    if not target:
        return

    uid_str = str(target.id)
    pass_no = SDB["passports"].get(uid_str)
    if not pass_no:
        pass_no = f"MGB26{str(abs(hash(uid_str)))[:6]}"
        SDB["passports"][uid_str] = pass_no
        _save_social_db()

    rank_title = "OFFICIAL VIP"
    if message.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        try:
            mem = await client.get_chat_member(message.chat.id, target.id)
            if mem.status == enums.ChatMemberStatus.OWNER:
                rank_title = "GROUP OWNER"
            elif mem.status == enums.ChatMemberStatus.ADMINISTRATOR:
                rank_title = "ROYAL ADMIN"
        except Exception:
            pass

    group_name = message.chat.title or "MGB ROYAL CLUB"
    profile_url = _user_profile_link(target)
    dp, qr_img = await asyncio.gather(
        _get_user_dp(client, target.id),
        _fetch_qr_image(profile_url, size=214),
    )
    card = await asyncio.to_thread(
        _render_passport_card,
        dp, qr_img, target.first_name, target.id, target.username or "", pass_no, group_name, rank_title,
    )
    cap = (
        f"<blockquote><b>🛂 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝐌𝐆𝐁 𝐕𝐈𝐏 𝐏𝐀𝐒𝐒𝐏𝐎𝐑𝐓</b></blockquote>\n\n"
        f"👤 <b>Holder:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"🆔 <b>Passport No:</b> <code>{pass_no}</code>\n"
        f"👑 <b>Rank:</b> <code>{rank_title}</code>\n\n{FOOTER}"
    )
    await _send_studio_card(client, message.chat.id, card, cap, _bottom_html_pills(profile_url, "🛂 𝐕𝐄𝐑𝐈𝐅𝐘 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 6. AAJ KI BEST JODI (/shipday) + AUTO MEMBER TRACKER ──────
@bot.on_message(filters.group, group=14)
async def _track_active_members(client, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return
    cid_str, uid_str = str(message.chat.id), str(user.id)
    pool = SDB["members"].setdefault(cid_str, {})
    prev = pool.get(uid_str)
    if not prev or prev.get("name") != user.first_name:
        pool[uid_str] = {"name": user.first_name, "uname": user.username or ""}
        if len(pool) > 80:
            pool.pop(next(iter(pool)), None)
        _save_social_db()

@bot.on_message(filters.group & filters.command(["shipday", "jodi", "bestjodi"], prefixes=["/", "!", "."]))
async def ship_of_the_day_cmd(client, message: Message):
    cid = message.chat.id
    cid_str = str(cid)
    today_ymd = datetime.now(IST).strftime("%Y-%m-%d")
    today_dm = datetime.now(IST).strftime("%d %b %Y")
    force_new = len(message.command) > 1 and message.command[1].lower() in ("new", "reset", "reroll")

    pool = SDB["members"].setdefault(cid_str, {})
    if len(pool) < 2:
        try:
            async for m in client.get_chat_members(cid, limit=30):
                if m.user and not m.user.is_bot:
                    pool[str(m.user.id)] = {"name": m.user.first_name, "uname": m.user.username or ""}
            _save_social_db()
        except Exception:
            pass

    if len(pool) < 2:
        return await _send_pill_notice(
            client, cid,
            f"<blockquote><b>💞 𝐀𝐀𝐉 𝐊𝐈 𝐁𝐄𝐒𝐓 𝐉𝐎𝐃𝐈</b></blockquote>\n\n"
            f"⚠️ <b>Kam se kam 2 active members hone chahiye group mein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    saved = SDB["daily_ship"].get(cid_str)
    if not force_new and saved and saved.get("date") == today_ymd:
        u1_id, u2_id, pct = saved["u1"], saved["u2"], saved["pct"]
        n1, n2 = saved["n1"], saved["n2"]
    else:
        u1_id, u2_id = random.sample(list(pool.keys()), 2)
        n1, n2 = pool[u1_id]["name"], pool[u2_id]["name"]
        pct = random.randint(78, 99)
        SDB["daily_ship"][cid_str] = {"date": today_ymd, "u1": u1_id, "u2": u2_id, "n1": n1, "n2": n2, "pct": pct}
        _save_social_db()

    dp1, dp2 = await asyncio.gather(
        _get_user_dp(client, int(u1_id)),
        _get_user_dp(client, int(u2_id)),
    )
    card = await asyncio.to_thread(_render_shipday_card, dp1, dp2, n1, n2, pct, today_dm)
    cap = (
        f"<blockquote><b>💞 𝐀𝐀𝐉 𝐊𝐈 𝐁𝐄𝐒𝐓 𝐉𝐎𝐃𝐈 ({today_dm})</b></blockquote>\n\n"
        f"👑 <b>Royal Duo:</b> <b>{html.escape(n1)}</b> ❤️ <b>{html.escape(n2)}</b>\n"
        f"🔥 <b>Love Chemistry:</b> <code>{pct}% PERFECT MATCH</code>\n"
        f"🔄 <b>Nayi Jodi:</b> <code>/shipday new</code>\n\n{FOOTER}"
    )
    await _send_studio_card(client, cid, card, cap, _bottom_html_pills())
