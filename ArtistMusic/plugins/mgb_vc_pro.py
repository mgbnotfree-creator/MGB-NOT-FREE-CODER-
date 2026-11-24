# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#    PLUGIN 2: MGB VC PRO STUDIO (100% BOTTOM HTML PILL BUTTONS)
#    /dedicate | /sleeptimer | /djvote | /vote
# ═══════════════════════════════════════════════════════════════

import os
import io
import json
import time
import math
import html
import random
import asyncio
import unicodedata
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pyrogram import filters, enums
from pyrogram.types import Message

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

try:
    from ArtistMusic import tune, yt
except Exception:
    tune, yt = None, None

from ArtistMusic.plugins.mgb_viral_cards import (
    OWNER_UNAME,
    CHANNEL_UNAME,
    FOOTER,
    _cbtn,
    _get_user_dp,
    send_rich_card,
    send_colored_msg,
)

# ── STORAGE & RUNTIME STATE ───────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = "mgb_data"
VC_DB_FILE = os.path.join(DATA_DIR, "vc_pro.json")
os.makedirs(DATA_DIR, exist_ok=True)

SLEEP_TIMERS = {}   # chat_id -> {"task": Task, "end_ts": float, "mins": int, "setter": str, "uid": int}
DJ_BATTLES = {}     # chat_id -> {"options": [str], "votes": {uid: idx}, "end_ts": float, "task": Task, "host_id": int, "host_name": str}

DEFAULT_DJ_SONGS = [
    ["Kesariya", "Apna Bana Le", "Chaleya"],
    ["Heeriye", "Satranga", "O Maahi"],
    ["Tera Fitoor", "Raataan Lambiyan", "Tum Hi Ho"],
    ["Pehle Bhi Main", "Ve Kamleya", "Sajni Re"],
]

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "Δ": "A", "α": "A", "Σ": "E", "Ω": "O", "β": "B",
    "χ": "X", "Χ": "X", "×": "X", "✗": "X", "✘": "X", "✕": "X", "✖": "X", "⨯": "X", "᙭": "X",
})

def _load_vc_db() -> dict:
    base = {"dedications_count": 0, "dj_winners": {}}
    if os.path.isfile(VC_DB_FILE):
        try:
            with open(VC_DB_FILE, "r", encoding="utf-8") as f:
                base.update(json.load(f))
        except Exception:
            pass
    return base

VCDB = _load_vc_db()

def _save_vc_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(VC_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(VCDB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 100% PERMANENT BOTTOM HTML PILL BUTTONS (URL-ONLY) ────────
def _bottom_html_pills(extra_url: str = None, extra_label: str = None) -> list:
    bottom_row = [
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]
    if extra_url and extra_label:
        return [[_cbtn(extra_label, style="primary", url=extra_url)], bottom_row]
    return [bottom_row]

async def _send_pill_msg(client, chat_id: int, text: str, reply_to: int = None, extra_url: str = None, extra_label: str = None):
    await send_colored_msg(client, chat_id, text, _bottom_html_pills(extra_url, extra_label), reply_to=reply_to)

async def _send_vc_card(client, chat_id: int, card_io: io.BytesIO, caption: str, rows: list = None):
    use_rows = rows or _bottom_html_pills()
    try:
        await send_rich_card(client, chat_id, card_io, caption, json_rows=use_rows)
    except TypeError:
        card_io.seek(0)
        await send_rich_card(client, chat_id, card_io, caption)

def _profile_url(user) -> str:
    uname = getattr(user, "username", None)
    return f"https://t.me/{uname}" if uname else f"https://t.me/{CHANNEL_UNAME}"

async def _is_chat_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False

# ── SAFE VC BRIDGE (AUTO-STOP & SONG METADATA) ────────────────
async def _safe_stop_vc(chat_id: int) -> bool:
    if tune is None:
        return False
    for method_name in ("stop", "stop_stream", "leave_call", "end", "force_stop"):
        fn = getattr(tune, method_name, None)
        if callable(fn):
            try:
                res = fn(chat_id)
                if asyncio.iscoroutine(res):
                    await res
                return True
            except Exception:
                continue
    return False

async def _safe_song_meta(query: str) -> tuple:
    clean_q = query.strip()[:50]
    if yt is None:
        return clean_q, "LIVE VC TRACK"
    for fn_name in ("search", "details", "track"):
        fn = getattr(yt, fn_name, None)
        if callable(fn):
            try:
                res = fn(clean_q)
                if asyncio.iscoroutine(res):
                    res = await asyncio.wait_for(res, timeout=6)
                if isinstance(res, dict):
                    title = str(res.get("title") or clean_q)[:42]
                    dur = str(res.get("duration") or res.get("duration_min") or "LIVE VC TRACK")[:16]
                    return title, dur
                if isinstance(res, tuple) and len(res) >= 2 and isinstance(res[0], str):
                    return res[0][:42], str(res[1])[:16]
            except Exception:
                continue
    return clean_q, "LIVE VC TRACK"

# ── CLEAN TEXT, FONTS & STUDIO GRAPHICS HELPERS ───────────────
def _clean_text(val: str, limit: int = 24) -> str:
    s = unicodedata.normalize("NFKC", str(val or "MGB VIP")).translate(FANCY_MAP)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip()
    parts = s.split()
    if len(parts) >= 4 and all(len(p) == 1 for p in parts):
        s = "".join(parts)
    return s[:limit] or "MGB VIP"

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

def _draw_fit_center(draw: ImageDraw.Draw, cx: int, cy: int, text: str, max_w: int, base_size: int, fill: tuple):
    sz = base_size
    f = _font(sz, True)
    while sz > 16:
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            break
        sz -= 2
        f = _font(sz, True)
    _draw_center(draw, cx, cy, text, f, fill)

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

def _draw_glow(canvas: Image.Image, cx: int, cy: int, r: int, color: tuple):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(int(r * 0.55))))

def _paste_circle_dp(canvas: Image.Image, dp: Image.Image, cx: int, cy: int, r: int, ring_col=None, ring_w: int = 5, glow_col=None):
    if glow_col:
        _draw_glow(canvas, cx, cy, r + 16, glow_col)
    size = r * 2
    av = ImageOps.fit(dp.convert("RGBA"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    canvas.paste(av, (cx - r, cy - r), mask)
    if ring_col and ring_w > 0:
        ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring_col, width=ring_w)

def _draw_soundwave(draw: ImageDraw.Draw, x1: int, x2: int, cy: int, max_h: int, color: tuple, bars: int = 24):
    step = max(6, (x2 - x1) // max(1, bars))
    for i in range(bars):
        bx = x1 + i * step
        if bx > x2:
            break
        amp = 0.25 + 0.75 * abs(math.sin((i + 1) * 0.75)) * (0.65 + 0.35 * math.cos(i * 1.3))
        bh = max(6, int(max_h * amp))
        draw.rounded_rectangle((bx, cy - bh, bx + max(3, step // 2), cy + bh), radius=3, fill=color)

def _save_jpg(img: Image.Image, name: str) -> io.BytesIO:
    out = io.BytesIO()
    out.name = name
    img.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out
# ── CARD 1: SONG DEDICATION DUAL-DP LUXURY CARD ───────────────
def _render_dedication_card(
    dp1: Image.Image,
    dp2: Image.Image,
    sender_name: str,
    target_name: str,
    song_title: str,
    duration: str,
    note: str = "SPECIAL VC DEDICATION",
) -> io.BytesIO:
    W, H = 1280, 720
    bg = _make_gradient(W, H, (34, 10, 44), (12, 14, 38)).convert("RGBA")
    _draw_glow(bg, 245, 305, 250, (236, 72, 153, 95))
    _draw_glow(bg, 1035, 305, 250, (245, 158, 11, 90))
    _draw_glow(bg, 640, 295, 190, (244, 63, 94, 85))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(18, 10, 30, 228), outline=(245, 198, 112, 238), width=4)

    # Top Title Pill
    d.rounded_rectangle((330, 62, 950, 122), radius=30, fill=(225, 29, 72, 245), outline=(255, 224, 158, 245), width=3)
    _draw_center(d, 640, 92, "SONG DEDICATION  •  VIP VC REQUEST", _font(25, True), (255, 255, 255))

    # Soundwaves connecting both DPs to center vinyl badge
    _draw_soundwave(d, 386, 534, 305, 36, (255, 168, 206, 210), bars=14)
    _draw_soundwave(d, 746, 894, 305, 36, (255, 212, 134, 210), bars=14)

    # Left (Sender) & Right (Target) Circular DPs
    _paste_circle_dp(bg, dp1, 245, 305, 118, ring_col=(255, 206, 124, 255), ring_w=6, glow_col=(236, 72, 153, 115))
    _paste_circle_dp(bg, dp2, 1035, 305, 118, ring_col=(255, 206, 124, 255), ring_w=6, glow_col=(245, 158, 11, 115))

    # Center Vinyl Disc + Glowing Heart Badge
    d = ImageDraw.Draw(bg)
    d.ellipse((556, 221, 724, 389), fill=(16, 12, 28, 255), outline=(245, 198, 112, 255), width=5)
    d.ellipse((574, 239, 706, 371), outline=(92, 68, 114, 190), width=2)
    d.ellipse((596, 261, 684, 349), fill=(244, 63, 94, 255), outline=(255, 228, 168, 255), width=3)
    # Vector heart inside vinyl center
    hx, hy = 640, 302
    d.ellipse((hx - 20, hy - 16, hx + 2, hy + 6), fill=(255, 255, 255))
    d.ellipse((hx - 2, hy - 16, hx + 20, hy + 6), fill=(255, 255, 255))
    d.polygon([(hx - 19, hy - 2), (hx + 19, hy - 2), (hx, hy + 22)], fill=(255, 255, 255))

    # Sender & Receiver Name Pills
    s_name = _clean_text(sender_name, 16)
    t_name = _clean_text(target_name, 16)
    d.rounded_rectangle((105, 444, 385, 496), radius=26, fill=(44, 16, 52, 248), outline=(245, 198, 112, 225), width=3)
    _draw_fit_center(d, 245, 470, f"FROM: {s_name}", 250, 22, (255, 255, 255))

    d.rounded_rectangle((895, 444, 1175, 496), radius=26, fill=(44, 16, 52, 248), outline=(245, 198, 112, 225), width=3)
    _draw_fit_center(d, 1035, 470, f"TO: {t_name}", 250, 22, (255, 255, 255))

    # Bottom Song Track Showcase Box
    d.rounded_rectangle((105, 518, 1175, 632), radius=26, fill=(26, 14, 42, 245), outline=(245, 198, 112, 220), width=3)
    # Play button badge on left of track box
    d.ellipse((134, 543, 198, 607), fill=(245, 198, 112, 255))
    d.polygon([(158, 559), (158, 591), (184, 575)], fill=(20, 12, 32))

    _draw_fit_center(d, 660, 556, _clean_text(song_title, 38).upper(), 890, 32, (255, 255, 255))
    _draw_fit_center(
        d, 660, 602,
        f"DURATION: {_clean_text(duration, 14)}   •   {_clean_text(note, 34)}",
        890, 21, (255, 216, 144),
    )

    _draw_center(d, 640, 658, "MGB NOT CODER  •  ROYAL VC DEDICATION", _font(20, True), (220, 196, 236))
    return _save_jpg(bg, "mgb_dedicate.jpg")

# ── CARD 2: VC SLEEP TIMER / NIGHT MODE CARD ──────────────────
def _render_sleep_card(
    dp: Image.Image,
    setter_name: str,
    status_title: str,
    time_line: str,
    sub_line: str,
    is_finished: bool = False,
) -> io.BytesIO:
    W, H = 1280, 720
    bg = _make_gradient(W, H, (8, 12, 34), (20, 10, 48)).convert("RGBA")
    accent = (245, 198, 112) if is_finished else (56, 189, 248)
    _draw_glow(bg, 276, 342, 250, (accent[0], accent[1], accent[2], 95))
    _draw_glow(bg, 1040, 160, 210, (139, 92, 246, 85))

    d = ImageDraw.Draw(bg)
    # Crisp starry night sky dots
    rng = random.Random(2026)
    for _ in range(55):
        sx, sy, sr = rng.randint(56, W - 56), rng.randint(56, H - 56), rng.choice([2, 3])
        d.ellipse((sx, sy, sx + sr, sy + sr), fill=(224, 236, 255, 150))

    # Main luxury frame
    d.rounded_rectangle((44, 42, W - 44, H - 42), radius=34, fill=(12, 16, 38, 224), outline=(accent[0], accent[1], accent[2], 235), width=4)

    # Crescent Moon Emblem (top-right)
    d.ellipse((1106, 82, 1188, 164), fill=(255, 224, 134, 245))
    d.ellipse((1130, 72, 1206, 148), fill=(14, 18, 42, 255))

    # Left DP + Setter Name Pill
    _paste_circle_dp(bg, dp, 276, 332, 136, ring_col=(accent[0], accent[1], accent[2], 255), ring_w=6, glow_col=(accent[0], accent[1], accent[2], 110))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((124, 496, 428, 554), radius=28, fill=(24, 30, 62, 248), outline=(accent[0], accent[1], accent[2], 225), width=3)
    _draw_fit_center(d, 276, 525, _clean_text(setter_name, 18).upper(), 274, 24, (255, 255, 255))
    _draw_center(d, 276, 588, "SLEEP HOST", _font(19, True), accent)

    # Right Info Panel
    rx = 812
    pill_txt = "VC SLEEP MODE ACTIVE" if is_finished else "VC SLEEP TIMER ARMED"
    d.rounded_rectangle((592, 92, 1032, 148), radius=28, fill=(accent[0], accent[1], accent[2], 245))
    _draw_center(d, rx, 120, pill_txt, _font(23, True), (10, 14, 30))

    _draw_fit_center(d, rx, 214, _clean_text(status_title, 24).upper(), 560, 44, (255, 255, 255))

    # Big Digital Clock Box
    d.rounded_rectangle((524, 266, 1100, 396), radius=28, fill=(8, 12, 28, 245), outline=(accent[0], accent[1], accent[2], 225), width=3)
    _draw_fit_center(d, rx, 331, _clean_text(time_line, 22).upper(), 530, 56, (255, 226, 138) if is_finished else (125, 226, 255))

    # Sub-status Pill
    d.rounded_rectangle((524, 426, 1100, 492), radius=24, fill=(22, 28, 58, 240), outline=(120, 142, 198, 190), width=2)
    _draw_fit_center(d, rx, 459, _clean_text(sub_line, 36).upper(), 536, 23, (236, 244, 255))

    # Calm Soundwave + Brand Footer
    _draw_soundwave(d, 548, 1076, 554, 22, (accent[0], accent[1], accent[2], 210), bars=26)
    _draw_center(d, rx, 616, "MGB NOT CODER  •  NIGHT VC ENGINE", _font(21, True), (186, 204, 236))
    return _save_jpg(bg, "mgb_sleeptimer.jpg")

# ── CARD 3: VC LIVE DJ VOTING BATTLE & WINNER CARD ────────────
def _render_dj_battle_card(
    dp: Image.Image,
    options: list,
    vote_counts: list,
    host_name: str,
    time_left_txt: str,
    winner_idx: int = None,
) -> io.BytesIO:
    W, H = 1280, 720
    bg = _make_gradient(W, H, (20, 8, 38), (8, 20, 42)).convert("RGBA")
    _draw_glow(bg, 220, 140, 240, (236, 72, 153, 85))
    _draw_glow(bg, 1060, 580, 260, (34, 211, 238, 90))

    d = ImageDraw.Draw(bg)
    border_col = (245, 198, 112, 245) if winner_idx is not None else (56, 189, 248, 235)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(12, 14, 30, 236), outline=border_col, width=4)

    # Top Header Strip
    d.rounded_rectangle((70, 62, W - 70, 152), radius=24, fill=(24, 22, 52, 248), outline=(124, 96, 196, 210), width=2)
    _paste_circle_dp(bg, dp, 126, 107, 33, ring_col=(245, 198, 112, 255), ring_w=3)
    d = ImageDraw.Draw(bg)

    hdr_title = "VC DJ BATTLE  •  WINNER CROWNED!" if winner_idx is not None else "VC LIVE DJ VOTING BATTLE"
    d.text((178, 78), hdr_title, font=_font(30, True), fill=(255, 222, 128) if winner_idx is not None else (255, 255, 255))
    d.text((178, 116), f"DJ HOST: {_clean_text(host_name, 18).upper()}   •   {_clean_text(time_left_txt, 26).upper()}", font=_font(20, False), fill=(176, 204, 242))

    badge_fill = (245, 198, 112, 255) if winner_idx is not None else (236, 72, 153, 255)
    badge_txt = "TRACK READY" if winner_idx is not None else "USE /vote 1-3"
    d.rounded_rectangle((946, 82, 1184, 132), radius=22, fill=badge_fill)
    _draw_center(d, 1065, 107, badge_txt, _font(21, True), (14, 14, 28) if winner_idx is not None else (255, 255, 255))

    # 3 Equalizer Track Voting Rows
    total_votes = sum(vote_counts)
    row_colors = [(56, 189, 248), (236, 72, 153), (168, 85, 247)]
    y_starts = [182, 332, 482]

    for idx in range(min(3, len(options))):
        y1 = y_starts[idx]
        y2 = y1 + 124
        v = vote_counts[idx] if idx < len(vote_counts) else 0
        pct = int(round((v / total_votes) * 100)) if total_votes > 0 else 0
        is_win = winner_idx == idx
        col = (245, 198, 112) if is_win else row_colors[idx % len(row_colors)]

        row_bg = (42, 32, 22, 245) if is_win else (20, 24, 48, 242)
        d.rounded_rectangle((70, y1, W - 70, y2), radius=24, fill=row_bg, outline=(col[0], col[1], col[2], 235), width=3 if is_win else 2)

        # Track Number Circle
        d.ellipse((96, y1 + 26, 168, y1 + 98), fill=(col[0], col[1], col[2], 255))
        _draw_center(d, 132, y1 + 62, f"#{idx + 1}", _font(28, True), (12, 14, 26))

        # Song Name
        song_lbl = _clean_text(options[idx], 34).upper()
        if is_win:
            song_lbl = f"WINNER: {song_lbl}"
        d.text((192, y1 + 24), song_lbl[:38], font=_font(28, True), fill=(255, 232, 156) if is_win else (255, 255, 255))

        # Vote Count Pill on Right
        d.rounded_rectangle((978, y1 + 18, 1184, y1 + 64), radius=18, fill=(12, 16, 34, 245), outline=(col[0], col[1], col[2], 200), width=2)
        _draw_center(d, 1081, y1 + 41, f"{v} VOTES ({pct}%)", _font(20, True), col)

        # Neon Progress Bar
        bx1, by1, bx2, by2 = 192, y1 + 78, 1184, y1 + 102
        d.rounded_rectangle((bx1, by1, bx2, by2), radius=12, fill=(10, 14, 30, 255))
        fill_w = max(24 if v > 0 else 0, int((bx2 - bx1) * (pct / 100.0)))
        if fill_w > 0:
            d.rounded_rectangle((bx1, by1, bx1 + fill_w, by2), radius=12, fill=(col[0], col[1], col[2], 255))

    # Bottom Equalizer + Branding
    _draw_soundwave(d, 86, 340, 646, 18, (56, 189, 248, 220), bars=16)
    _draw_center(d, 640, 646, "MGB NOT CODER  •  LIVE DJ VOTING", _font(21, True), (220, 232, 252))
    _draw_soundwave(d, 940, 1194, 646, 18, (236, 72, 153, 220), bars=16)
    return _save_jpg(bg, "mgb_djvote.jpg")
# ── 1. SONG DEDICATION CARD (/dedicate) ───────────────────────
@bot.on_message(filters.command(["dedicate", "ded", "dedicatesong"], prefixes=["/", "!", "."]))
async def song_dedicate_cmd(client, message: Message):
    sender = message.from_user
    if not sender:
        return

    raw = message.text.split(None, 1)[1].strip() if (message.text and len(message.text.split(None, 1)) > 1) else ""
    if not raw:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🎵 𝐌𝐆𝐁 𝐒𝐎𝐍𝐆 𝐃𝐄𝐃𝐈𝐂𝐀𝐓𝐈𝐎𝐍 𝐒𝐓𝐔𝐃𝐈𝐎</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> Kisi dost par reply karke likhein:\n"
            f"• <code>/dedicate Kesariya</code>\n"
            f"• <code>/dedicate Apna Bana Le | For my bestie</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if "|" in raw:
        song_part, note_part = raw.split("|", 1)
        song_query = song_part.strip()
        custom_note = note_part.strip()[:40] or "SPECIAL VC DEDICATION"
    else:
        song_query = raw.strip()
        custom_note = "SPECIAL VC DEDICATION"

    if not song_query:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐒𝐎𝐍𝐆 𝐍𝐀𝐌𝐄 𝐌𝐈𝐒𝐒𝐈𝐍𝐆</b></blockquote>\n\n"
            f"🎵 <b>Example:</b> <code>/dedicate Tum Hi Ho | Royal Vibes</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else sender
    )

    (song_title, duration), dp1, dp2 = await asyncio.gather(
        _safe_song_meta(song_query),
        _get_user_dp(client, sender.id),
        _get_user_dp(client, target.id),
    )

    card = await asyncio.to_thread(
        _render_dedication_card,
        dp1, dp2, sender.first_name, target.first_name, song_title, duration, custom_note,
    )

    VCDB["dedications_count"] = int(VCDB.get("dedications_count", 0)) + 1
    _save_vc_db()

    cap = (
        f"<blockquote><b>🎵 𝐑𝐎𝐘𝐀𝐋 𝐒𝐎𝐍𝐆 𝐃𝐄𝐃𝐈𝐂𝐀𝐓𝐈𝐎𝐍 #{VCDB['dedications_count']}</b></blockquote>\n\n"
        f"💌 <b>From:</b> <b>{html.escape(sender.first_name)}</b>\n"
        f"💖 <b>Dedicated To:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"🎶 <b>Track:</b> <code>{html.escape(song_title)}</code> (<code>{html.escape(duration)}</code>)\n"
        f"✨ <b>Note:</b> <code>{html.escape(custom_note)}</code>\n"
        f"▶️ <b>VC Queue:</b> <code>/play {html.escape(song_query[:45])}</code>\n\n{FOOTER}"
    )
    await _send_vc_card(
        client, message.chat.id, card, cap,
        rows=_bottom_html_pills(_profile_url(target), "💖 𝐃𝐄𝐃𝐈𝐂𝐀𝐓𝐄𝐃 𝐓𝐎"),
    )

# ── 2. VC SLEEP TIMER (/sleeptimer) ───────────────────────────
async def _sleep_timer_worker(client, cid: int, mins: int, setter_uid: int, setter_name: str):
    try:
        await asyncio.sleep(mins * 60)
        cur = SLEEP_TIMERS.get(cid)
        if not cur or cur.get("task") is not asyncio.current_task():
            return
        SLEEP_TIMERS.pop(cid, None)

        stopped = await _safe_stop_vc(cid)
        dp = await _get_user_dp(client, setter_uid)
        sub_txt = "VC STREAM AUTO-STOPPED • SWEET DREAMS!" if stopped else "SLEEP TIMER COMPLETE • GOOD NIGHT!"
        card = await asyncio.to_thread(
            _render_sleep_card,
            dp, setter_name, "GOOD NIGHT EVERYONE", "00:00  SLEEP ON", sub_txt, True,
        )
        cap = (
            f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐌𝐎𝐃𝐄 𝐀𝐂𝐓𝐈𝐕𝐀𝐓𝐄𝐃</b></blockquote>\n\n"
            f"⏱ <b>Timer:</b> <code>{mins} Minutes Complete</code>\n"
            f"🔇 <b>VC Action:</b> <code>{'Stream Auto-Stopped ✅' if stopped else 'Sleep Alert Sent ✅'}</code>\n"
            f"😴 <b>Shubh Ratri! Kal milte hain naye gaano ke saath!</b>\n\n{FOOTER}"
        )
        await _send_vc_card(client, cid, card, cap)
    except asyncio.CancelledError:
        return
    except Exception:
        SLEEP_TIMERS.pop(cid, None)

@bot.on_message(filters.group & filters.command(["sleeptimer", "sleep", "vcsleep"], prefixes=["/", "!", "."]))
async def vc_sleep_timer_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    arg = message.command[1].lower() if len(message.command) > 1 else ""

    # Status check (open for everyone)
    if arg == "status" or (not arg and cid in SLEEP_TIMERS):
        active = SLEEP_TIMERS.get(cid)
        if not active:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑 𝐒𝐓𝐀𝐓𝐔𝐒</b></blockquote>\n\n"
                f"⚙️ <b>Status:</b> <code>NO ACTIVE TIMER ❌</code>\n"
                f"⏱ <b>Set Timer:</b> <code>/sleeptimer 30</code> <i>(1–360 min)</i>\n\n{FOOTER}",
                reply_to=message.id,
            )
        rem_sec = max(1, int(active["end_ts"] - time.time()))
        rm, rs = divmod(rem_sec, 60)
        end_ist = datetime.fromtimestamp(active["end_ts"], IST).strftime("%I:%M %p IST")
        dp = await _get_user_dp(client, active["uid"])
        card = await asyncio.to_thread(
            _render_sleep_card,
            dp, active["setter"], "TIMER RUNNING LIVE", f"{rm:02d}:{rs:02d} LEFT", f"AUTO-STOP AT {end_ist}", False,
        )
        cap = (
            f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑 𝐋𝐈𝐕𝐄</b></blockquote>\n\n"
            f"⏳ <b>Time Left:</b> <code>{rm}m {rs}s</code>\n"
            f"🕒 <b>Stops At:</b> <code>{end_ist}</code>\n"
            f"❌ <b>Cancel:</b> <code>/sleeptimer off</code>\n\n{FOOTER}"
        )
        return await _send_vc_card(client, cid, card, cap)

    if not arg:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑</b></blockquote>\n\n"
            f"⏱ <b>Set Timer:</b> <code>/sleeptimer 30</code> <i>(or 15, 45, 60)</i>\n"
            f"📊 <b>Check Live:</b> <code>/sleeptimer status</code>\n"
            f"❌ <b>Cancel:</b> <code>/sleeptimer off</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    # Cancel active timer (Admins or Setter)
    if arg in ("off", "cancel", "stop", "del"):
        active = SLEEP_TIMERS.get(cid)
        if not active:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑</b></blockquote>\n\n"
                f"⚠️ <b>Koi active sleep timer nahi chal raha!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )
        if user.id != active["uid"] and not await _is_chat_admin(client, cid, user.id):
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🔒 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
                f"⚠️ <b>Sirf Admin ya Timer Setter hi cancel kar sakta hai!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )
        SLEEP_TIMERS.pop(cid, None)
        if active.get("task") and not active["task"].done():
            active["task"].cancel()
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑 𝐂𝐀𝐍𝐂𝐄𝐋𝐋𝐄𝐃</b></blockquote>\n\n"
            f"✅ <b>Sleep timer band kar diya gaya hai — music chalta rahega!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if not arg.isdigit():
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>❌ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐓𝐈𝐌𝐄</b></blockquote>\n\n"
            f"⏱ <b>Minutes mein number likhein:</b> <code>/sleeptimer 30</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    mins = max(1, min(360, int(arg)))
    old = SLEEP_TIMERS.pop(cid, None)
    if old and old.get("task") and not old["task"].done():
        old["task"].cancel()

    end_ts = time.time() + (mins * 60)
    end_ist = datetime.fromtimestamp(end_ts, IST).strftime("%I:%M %p IST")
    task = asyncio.create_task(_sleep_timer_worker(client, cid, mins, user.id, user.first_name))
    SLEEP_TIMERS[cid] = {"task": task, "end_ts": end_ts, "mins": mins, "setter": user.first_name, "uid": user.id}

    dp = await _get_user_dp(client, user.id)
    card = await asyncio.to_thread(
        _render_sleep_card,
        dp, user.first_name, "NIGHT MODE SCHEDULED", f"{mins:02d}:00 MIN", f"VC AUTO-STOP AT {end_ist}", False,
    )
    cap = (
        f"<blockquote><b>🌙 𝐕𝐂 𝐒𝐋𝐄𝐄𝐏 𝐓𝐈𝐌𝐄𝐑 𝐒𝐄𝐓!</b></blockquote>\n\n"
        f"👤 <b>Set By:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"⏱ <b>Duration:</b> <code>{mins} Minutes</code>\n"
        f"🕒 <b>Auto-Stop:</b> <code>{end_ist}</code>\n"
        f"❌ <b>Cancel:</b> <code>/sleeptimer off</code>\n\n{FOOTER}"
    )
    await _send_vc_card(client, cid, card, cap, rows=_bottom_html_pills(_profile_url(user), "🌙 𝐒𝐋𝐄𝐄𝐏 𝐇𝐎𝐒𝐓"))

# ── 3. VC LIVE DJ VOTING BATTLE (/djvote & /vote) ─────────────
def _tally_dj_votes(battle: dict) -> list:
    counts = [0] * len(battle["options"])
    for choice in battle["votes"].values():
        if 0 <= choice < len(counts):
            counts[choice] += 1
    return counts

async def _conclude_dj_battle(client, cid: int):
    battle = DJ_BATTLES.pop(cid, None)
    if not battle:
        return

    counts = _tally_dj_votes(battle)
    max_v = max(counts) if counts else 0
    top_indices = [i for i, v in enumerate(counts) if v == max_v]
    win_idx = random.choice(top_indices) if top_indices else 0
    winner_song = battle["options"][win_idx]

    VCDB.setdefault("dj_winners", {})[str(cid)] = {
        "song": winner_song,
        "votes": counts[win_idx],
        "ts": int(time.time()),
    }
    _save_vc_db()

    dp = await _get_user_dp(client, battle["host_id"])
    card = await asyncio.to_thread(
        _render_dj_battle_card,
        dp, battle["options"], counts, battle["host_name"], f"TOTAL VOTES: {sum(counts)}", win_idx,
    )
    cap = (
        f"<blockquote><b>🎧 𝐕𝐂 𝐃𝐉 𝐁𝐀𝐓𝐓𝐋𝐄 𝐖𝐈𝐍𝐍𝐄𝐑!</b></blockquote>\n\n"
        f"🏆 <b>Winning Track:</b> <code>{html.escape(winner_song)}</code>\n"
        f"🗳 <b>Votes:</b> <code>{counts[win_idx]} / {sum(counts)}</code>\n"
        f"▶️ <b>Play Now:</b> <code>/play {html.escape(winner_song)}</code>\n\n{FOOTER}"
    )
    await _send_vc_card(client, cid, card, cap)

async def _dj_battle_timer(client, cid: int, delay_sec: int):
    try:
        await asyncio.sleep(delay_sec)
        cur = DJ_BATTLES.get(cid)
        if not cur or cur.get("task") is not asyncio.current_task():
            return
        await _conclude_dj_battle(client, cid)
    except asyncio.CancelledError:
        return
    except Exception:
        DJ_BATTLES.pop(cid, None)

@bot.on_message(filters.group & filters.command(["djvote", "djbattle", "dj"], prefixes=["/", "!", "."]))
async def dj_vote_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    raw = message.text.split(None, 1)[1].strip() if (message.text and len(message.text.split(None, 1)) > 1) else ""
    low = raw.lower()

    # Live status of ongoing DJ battle
    if low == "status" or (cid in DJ_BATTLES and low not in ("end", "stop", "finish")):
        battle = DJ_BATTLES.get(cid)
        if not battle:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🎧 𝐕𝐂 𝐋𝐈𝐕𝐄 𝐃𝐉 𝐕𝐎𝐓𝐈𝐍𝐆</b></blockquote>\n\n"
                f"⚡ <b>Quick Start:</b> <code>/djvote</code> <i>(Auto 3 Hit Songs)</i>\n"
                f"🎶 <b>Custom Songs:</b> <code>/djvote Kesariya | Chaleya | Heeriye</code>\n\n{FOOTER}",
                reply_to=message.id,
            )
        rem = max(1, int(battle["end_ts"] - time.time()))
        counts = _tally_dj_votes(battle)
        dp = await _get_user_dp(client, battle["host_id"])
        card = await asyncio.to_thread(
            _render_dj_battle_card,
            dp, battle["options"], counts, battle["host_name"], f"{rem}s LEFT • {sum(counts)} VOTES", None,
        )
        cap = (
            f"<blockquote><b>🎧 𝐃𝐉 𝐁𝐀𝐓𝐓𝐋𝐄 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒!</b></blockquote>\n\n"
            f"⏳ <b>Time Left:</b> <code>{rem} Seconds</code>\n"
            f"🗳 <b>Vote Karein:</b> <code>/vote 1</code> | <code>/vote 2</code> | <code>/vote 3</code>\n\n{FOOTER}"
        )
        return await _send_vc_card(client, cid, card, cap)

    # End battle early (Host or Admin)
    if low in ("end", "stop", "finish"):
        battle = DJ_BATTLES.get(cid)
        if not battle:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🎧 𝐃𝐉 𝐕𝐎𝐓𝐈𝐍𝐆</b></blockquote>\n\n"
                f"⚠️ <b>Abhi koi DJ Battle nahi chal raha!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )
        if user.id != battle["host_id"] and not await _is_chat_admin(client, cid, user.id):
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🔒 𝐇𝐎𝐒𝐓 / 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
                f"⚠️ <b>Sirf Host ya Admin hi DJ Battle jaldi khatam kar sakta hai!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )
        if battle.get("task") and not battle["task"].done():
            battle["task"].cancel()
        return await _conclude_dj_battle(client, cid)

    # Parse custom 2–3 songs or pick trending pack
    if raw:
        sep = "|" if "|" in raw else ","
        options = [x.strip()[:38] for x in raw.split(sep) if x.strip()][:3]
        if len(options) < 2:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🎧 𝐂𝐔𝐒𝐓𝐎𝐌 𝐃𝐉 𝐕𝐎𝐓𝐈𝐍𝐆</b></blockquote>\n\n"
                f"🎶 <b>Kam se kam 2 gaane <code>|</code> se alag likhein:</b>\n"
                f"<code>/djvote Kesariya | Chaleya | Heeriye</code>\n\n{FOOTER}",
                reply_to=message.id,
            )
    else:
        options = list(random.choice(DEFAULT_DJ_SONGS))

    duration_sec = 45
    task = asyncio.create_task(_dj_battle_timer(client, cid, duration_sec))
    DJ_BATTLES[cid] = {
        "options": options,
        "votes": {},
        "end_ts": time.time() + duration_sec,
        "task": task,
        "host_id": user.id,
        "host_name": user.first_name,
    }

    dp = await _get_user_dp(client, user.id)
    card = await asyncio.to_thread(
        _render_dj_battle_card,
        dp, options, [0] * len(options), user.first_name, f"45s VOTING OPEN", None,
    )
    opts_txt = "\n".join(f"• <code>/vote {i + 1}</code> — <b>{html.escape(s)}</b>" for i, s in enumerate(options))
    cap = (
        f"<blockquote><b>🎧 𝐕𝐂 𝐋𝐈𝐕𝐄 𝐃𝐉 𝐕𝐎𝐓𝐈𝐍𝐆 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!</b></blockquote>\n\n"
        f"{opts_txt}\n\n"
        f"⏳ <b>Result In:</b> <code>45 Seconds</code> | <b>Early End:</b> <code>/djvote end</code>\n\n{FOOTER}"
    )
    await _send_vc_card(client, cid, card, cap, rows=_bottom_html_pills(_profile_url(user), "🎧 𝐃𝐉 𝐇𝐎𝐒𝐓"))

@bot.on_message(filters.group & filters.command(["vote", "v"], prefixes=["/", "!", "."]))
async def dj_cast_vote_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    battle = DJ_BATTLES.get(cid)
    if not battle:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🎧 𝐍𝐎 𝐀𝐂𝐓𝐈𝐕𝐄 𝐃𝐉 𝐁𝐀𝐓𝐓𝐋𝐄</b></blockquote>\n\n"
            f"⚡ <b>Naya DJ Battle start karein:</b> <code>/djvote</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🗳 𝐇𝐎𝐖 𝐓𝐎 𝐕𝐎𝐓𝐄</b></blockquote>\n\n"
            f"⚡ <b>Number likhein:</b> <code>/vote 1</code>, <code>/vote 2</code> ya <code>/vote 3</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    idx = int(message.command[1]) - 1
    if not (0 <= idx < len(battle["options"])):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>❌ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐓𝐑𝐀𝐂𝐊 𝐍𝐔𝐌𝐁𝐄𝐑</b></blockquote>\n\n"
            f"🗳 <b>1 se {len(battle['options'])} ke beech choose karein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    battle["votes"][user.id] = idx
    counts = _tally_dj_votes(battle)
    rem = max(1, int(battle["end_ts"] - time.time()))
    tally_lines = "\n".join(
        f"• <b>#{i + 1} {html.escape(s)}</b> — <code>{counts[i]} votes</code>"
        for i, s in enumerate(battle["options"])
    )
    await _send_pill_msg(
        client, cid,
        f"<blockquote><b>🗳 𝐕𝐎𝐓𝐄 𝐂𝐎𝐔𝐍𝐓𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Voter:</b> <b>{html.escape(user.first_name)}</b> ➔ <code>#{idx + 1} {html.escape(battle['options'][idx])}</code>\n\n"
        f"{tally_lines}\n\n"
        f"⏳ <b>Result In:</b> <code>{rem}s</code> | <b>Live Card:</b> <code>/djvote status</code>\n\n{FOOTER}",
        reply_to=message.id,
)
  
