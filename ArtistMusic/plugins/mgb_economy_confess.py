# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#   PLUGIN 3: GROUP COINS, VIP CARD SHOP & ANONYMOUS CONFESSION
#   /daily | /wallet | /shop | /buy | /equip | /give | /rich
#   /setconfess | /confess (Group Auto-Delete + DM Anonymous)
# ═══════════════════════════════════════════════════════════════

import os
import io
import json
import time
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
ECO_DB_FILE = os.path.join(DATA_DIR, "economy_confess.json")
os.makedirs(DATA_DIR, exist_ok=True)

CHAT_COIN_COOLDOWN = {}  # (cid, uid) -> last_ts
CHAT_COIN_GAP_SEC = 40
CHAT_COIN_REWARD = (8, 18)

# ── VIP CARD SHOP CATALOG (THEMES, RINGS & ROYAL TITLES) ──────
SHOP_ITEMS = {
    "1": {
        "name": "ROYAL GOLD THEME",
        "kind": "theme",
        "price": 500,
        "desc": "Obsidian & 24K Gold Luxury Card",
        "c1": (30, 20, 8), "c2": (12, 10, 18), "accent": (245, 198, 92),
    },
    "2": {
        "name": "CYBER NEON THEME",
        "kind": "theme",
        "price": 750,
        "desc": "Electric Cyan & Synthwave Card",
        "c1": (6, 22, 42), "c2": (24, 8, 44), "accent": (34, 211, 238),
    },
    "3": {
        "name": "CRIMSON ROSE THEME",
        "kind": "theme",
        "price": 900,
        "desc": "Velvet Ruby & Rose Gold Card",
        "c1": (44, 8, 26), "c2": (16, 8, 28), "accent": (244, 63, 94),
    },
    "4": {
        "name": "EMERALD KING RING",
        "kind": "ring",
        "price": 600,
        "desc": "Glowing Emerald Avatar Aura",
        "ring": (16, 225, 152),
    },
    "5": {
        "name": "DIAMOND VVIP TAG",
        "kind": "title",
        "price": 1200,
        "desc": "Unlock 'DIAMOND VVIP' Badge",
        "title": "DIAMOND VVIP",
    },
    "6": {
        "name": "GROUP DON BADGE",
        "kind": "title",
        "price": 2000,
        "desc": "Unlock 'ROYAL GROUP DON' Badge",
        "title": "ROYAL GROUP DON",
    },
}

DEFAULT_THEME = {"c1": (14, 18, 42), "c2": (24, 12, 44), "accent": (129, 140, 248)}

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "Δ": "A", "α": "A", "Σ": "E", "Ω": "O", "β": "B",
    "χ": "X", "Χ": "X", "×": "X", "✗": "X", "✘": "X", "✕": "X", "✖": "X", "⨯": "X", "᙭": "X",
})

def _load_eco_db() -> dict:
    base = {
        "users": {},             # str(uid) -> {name, coins, daily_date, streak, owned, theme, ring, title, msgs}
        "confess_chats": {},     # str(cid) -> {title, enabled, count, code}
        "user_last_group": {},   # str(uid) -> str(cid)
        "confess_total": 0,
    }
    if os.path.isfile(ECO_DB_FILE):
        try:
            with open(ECO_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            base.update(data)
        except Exception:
            pass
    return base

EDB = _load_eco_db()

def _save_eco_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ECO_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(EDB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _get_user_rec(uid: int, name: str = "MGB VIP") -> dict:
    rec = EDB["users"].setdefault(str(uid), {
        "name": name,
        "coins": 100,
        "daily_date": "",
        "streak": 0,
        "owned": [],
        "theme": "",
        "ring": "",
        "title": "MGB MEMBER",
        "msgs": 0,
    })
    if name and rec.get("name") != name:
        rec["name"] = name
    return rec

def _get_confess_chat(cid: int, title: str = "MGB GROUP") -> dict:
    cid_str = str(cid)
    cfg = EDB["confess_chats"].get(cid_str)
    if not cfg:
        code = f"MGB{abs(cid) % 10000:04d}"
        cfg = {"title": title, "enabled": True, "count": 0, "code": code}
        EDB["confess_chats"][cid_str] = cfg
        _save_eco_db()
    elif title and cfg.get("title") != title:
        cfg["title"] = title
    return cfg

# ── 100% PERMANENT BOTTOM HTML PILL BUTTONS (NO CALLBACKS) ────
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

async def _send_eco_card(client, chat_id: int, card_io: io.BytesIO, caption: str, rows: list = None):
    use_rows = rows or _bottom_html_pills()
    try:
        await send_rich_card(client, chat_id, card_io, caption, json_rows=use_rows)
    except TypeError:
        card_io.seek(0)
        await send_rich_card(client, chat_id, card_io, caption)

def _profile_url(user) -> str:
    uname = getattr(user, "username", None)
    return f"https://t.me/{uname}" if uname else f"https://t.me/{CHANNEL_UNAME}"

async def _bot_dm_url(client) -> str:
    try:
        uname = getattr(client.me, "username", None) or (await client.get_me()).username
        if uname:
            return f"https://t.me/{uname}?start=confess"
    except Exception:
        pass
    return f"https://t.me/{CHANNEL_UNAME}"

async def _is_chat_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False

# ── CLEAN TEXT, FONT & STUDIO GRAPHICS HELPERS ────────────────
def _clean_name(val: str, limit: int = 20) -> str:
    s = unicodedata.normalize("NFKC", str(val or "MGB VIP")).translate(FANCY_MAP)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip()
    parts = s.split()
    if len(parts) >= 4 and all(len(p) == 1 for p in parts):
        s = "".join(parts)
    return s[:limit] or "MGB VIP"

def _clean_body(val: str, limit: int = 240) -> str:
    s = unicodedata.normalize("NFKC", str(val or "")).translate(FANCY_MAP)
    s = "".join(ch if (32 <= ord(ch) <= 126 or ch == "\n") else " " for ch in s)
    lines = [" ".join(ln.split()) for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln).strip()[:limit] or "Secret thoughts from the heart..."

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
    while sz > 15:
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            break
        sz -= 2
        f = _font(sz, True)
    _draw_center(draw, cx, cy, text, f, fill)

def _wrap_lines(draw: ImageDraw.Draw, text: str, font, max_w: int, max_lines: int = 5) -> list:
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

def _paste_circle_dp(canvas: Image.Image, dp: Image.Image, cx: int, cy: int, r: int, ring_col=None, ring_w: int = 6, glow_col=None):
    if glow_col:
        _draw_glow(canvas, cx, cy, r + 16, glow_col)
    size = r * 2
    av = ImageOps.fit(dp.convert("RGBA"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    canvas.paste(av, (cx - r, cy - r), mask)
    if ring_col and ring_w > 0:
        ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring_col, width=ring_w)

def _save_jpg(img: Image.Image, name: str) -> io.BytesIO:
    out = io.BytesIO()
    out.name = name
    img.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out
# ── THEME & RING RESOLVER FROM USER INVENTORY ─────────────────
def _resolve_user_style(rec: dict) -> tuple:
    t_id = str(rec.get("theme") or "")
    r_id = str(rec.get("ring") or "")
    theme = SHOP_ITEMS.get(t_id) if (t_id in SHOP_ITEMS and SHOP_ITEMS[t_id]["kind"] == "theme") else DEFAULT_THEME
    accent = theme["accent"]
    ring = SHOP_ITEMS[r_id]["ring"] if (r_id in SHOP_ITEMS and SHOP_ITEMS[r_id]["kind"] == "ring") else accent
    title = str(rec.get("title") or "MGB MEMBER")
    return theme["c1"], theme["c2"], accent, ring, title

# ── CARD 1: VIP GROUP WALLET & EQUITY CARD ────────────────────
def _render_wallet_card(dp: Image.Image, rec: dict, rank_pos: int, bonus_note: str = "") -> io.BytesIO:
    W, H = 1280, 720
    c1, c2, accent, ring_col, title = _resolve_user_style(rec)
    bg = _make_gradient(W, H, c1, c2).convert("RGBA")
    _draw_glow(bg, 268, 344, 250, (ring_col[0], ring_col[1], ring_col[2], 95))
    _draw_glow(bg, 1040, 170, 230, (accent[0], accent[1], accent[2], 80))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(10, 12, 26, 232), outline=(accent[0], accent[1], accent[2], 238), width=4)
    d.rounded_rectangle((56, 54, W - 56, H - 54), radius=26, outline=(accent[0], accent[1], accent[2], 90), width=2)

    # Left DP + Custom Ring + VIP Tag Pill
    _paste_circle_dp(bg, dp, 268, 326, 134, ring_col=(ring_col[0], ring_col[1], ring_col[2], 255), ring_w=7, glow_col=(ring_col[0], ring_col[1], ring_col[2], 125))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((112, 492, 424, 548), radius=26, fill=(accent[0], accent[1], accent[2], 255))
    _draw_fit_center(d, 268, 520, _clean_name(title, 20).upper(), 284, 22, (12, 14, 24))
    _draw_center(d, 268, 584, f"GLOBAL RANK  #{rank_pos}", _font(21, True), (222, 232, 248))

    # Right Side Header + Name
    rx1, rx2, rcx = 472, 1188, 830
    d.rounded_rectangle((rx1, 86, rx2, 152), radius=24, fill=(22, 26, 52, 242), outline=(accent[0], accent[1], accent[2], 190), width=2)
    d.text((rx1 + 28, 104), "MGB ROYAL VAULT  •  VIP WALLET", font=_font(24, True), fill=accent)
    d.text((rx2 - 220, 106), f"OWNED: {len(rec.get('owned', []))}/6", font=_font(21, True), fill=(224, 236, 255))

    cname = _clean_name(rec.get("name", "MGB VIP"), 22).upper()
    _draw_fit_center(d, rcx, 206, cname, 680, 42, (255, 255, 255))

    # Big Coin Balance Vault Box
    coins_str = f"{int(rec.get('coins', 0)):,}"
    d.rounded_rectangle((rx1, 248, rx2, 392), radius=28, fill=(8, 10, 22, 248), outline=(245, 198, 92, 235), width=3)
    _draw_center(d, rcx, 286, "AVAILABLE MGB COINS", _font(20, True), (245, 198, 92))
    _draw_fit_center(d, rcx, 344, f"{coins_str} COINS", 650, 56, (255, 228, 140))

    # 3 Mini Stat Pills (Streak | Messages | Status)
    stats = [
        ("DAILY STREAK", f"{int(rec.get('streak', 0))} DAYS"),
        ("CHAT MSGS", f"{int(rec.get('msgs', 0)):,}"),
        ("SHOP ITEMS", f"{len(rec.get('owned', []))} UNLOCKED"),
    ]
    bw = 222
    gap = 25
    for idx, (lbl, val) in enumerate(stats):
        bx1 = rx1 + idx * (bw + gap)
        bx2 = bx1 + bw
        d.rounded_rectangle((bx1, 422, bx2, 534), radius=22, fill=(18, 22, 44, 244), outline=(accent[0], accent[1], accent[2], 180), width=2)
        _draw_center(d, (bx1 + bx2) // 2, 456, lbl, _font(17, True), accent)
        _draw_fit_center(d, (bx1 + bx2) // 2, 498, val, bw - 22, 24, (255, 255, 255))

    # Bottom Bonus / Brand Bar
    foot_txt = _clean_name(bonus_note, 42).upper() if bonus_note else "USE /shop TO UNLOCK VIP THEMES & TAGS"
    d.rounded_rectangle((rx1, 560, rx2, 620), radius=22, fill=(18, 22, 42, 235), outline=(accent[0], accent[1], accent[2], 150), width=2)
    _draw_fit_center(d, rcx, 590, foot_txt, 680, 21, (255, 226, 154) if bonus_note else (206, 220, 242))
    _draw_center(d, 268, 636, "MGB NOT CODER", _font(20, True), accent)
    return _save_jpg(bg, "mgb_wallet.jpg")

# ── CARD 2: VIP CARD SHOP SHOWCASE GRID (2x3 CARDS) ───────────
def _render_shop_card(user_coins: int, owned_ids: list) -> io.BytesIO:
    W, H = 1280, 820
    bg = _make_gradient(W, H, (10, 14, 34), (26, 10, 42)).convert("RGBA")
    _draw_glow(bg, 220, 130, 250, (245, 198, 92, 85))
    _draw_glow(bg, 1060, 700, 260, (56, 189, 248, 85))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((36, 34, W - 36, H - 34), radius=34, fill=(12, 14, 30, 236), outline=(245, 198, 92, 238), width=4)

    # Top Header Banner
    d.rounded_rectangle((68, 60, W - 68, 152), radius=24, fill=(22, 22, 50, 248), outline=(245, 198, 92, 200), width=2)
    d.text((100, 78), "MGB VIP CARD SHOP  •  CUSTOMIZE YOUR PROFILE", font=_font(30, True), fill=(255, 222, 130))
    d.text((100, 118), "BUY WITH /buy <id>   |   EQUIP WITH /equip <id>", font=_font(20, False), fill=(184, 206, 240))

    # User Balance Pill (Top Right)
    d.rounded_rectangle((940, 80, 1184, 132), radius=24, fill=(245, 198, 92, 255))
    _draw_fit_center(d, 1062, 106, f"{user_coins:,} COINS", 220, 23, (14, 16, 28))

    # 2x3 Grid of 6 Shop Items
    card_w, card_h = 360, 254
    gap_x, gap_y = 32, 26
    start_x, start_y = 68, 180

    for i, item_id in enumerate(("1", "2", "3", "4", "5", "6")):
        item = SHOP_ITEMS[item_id]
        col_i = i % 3
        row_i = i // 3
        x1 = start_x + col_i * (card_w + gap_x)
        y1 = start_y + row_i * (card_h + gap_y)
        x2, y2 = x1 + card_w, y1 + card_h

        swatch = item.get("accent") or item.get("ring") or (245, 198, 92)
        is_owned = item_id in owned_ids
        outline_col = (16, 225, 152, 245) if is_owned else (swatch[0], swatch[1], swatch[2], 225)

        d.rounded_rectangle((x1, y1, x2, y2), radius=26, fill=(18, 22, 44, 244), outline=outline_col, width=3)
        # Top color ribbon bar
        d.rounded_rectangle((x1 + 16, y1 + 16, x2 - 16, y1 + 66), radius=16, fill=(swatch[0], swatch[1], swatch[2], 230))
        _draw_center(d, (x1 + x2) // 2, y1 + 41, f"#{item_id}  •  {item['kind'].upper()}", _font(21, True), (12, 14, 26))

        # Item Name & Description
        _draw_fit_center(d, (x1 + x2) // 2, y1 + 106, item["name"], card_w - 32, 24, (255, 255, 255))
        _draw_fit_center(d, (x1 + x2) // 2, y1 + 146, item["desc"], card_w - 32, 18, (186, 202, 232))

        # Price / Owned Footer Pill
        pill_col = (16, 185, 129, 255) if is_owned else (34, 40, 74, 255)
        pill_txt = "OWNED  •  /equip " + item_id if is_owned else f"{item['price']:,} COINS  •  /buy {item_id}"
        txt_col = (10, 22, 18) if is_owned else (255, 224, 134)
        d.rounded_rectangle((x1 + 22, y2 - 66, x2 - 22, y2 - 18), radius=20, fill=pill_col, outline=outline_col, width=2)
        _draw_fit_center(d, (x1 + x2) // 2, y2 - 42, pill_txt, card_w - 64, 19, txt_col)

    _draw_center(d, W // 2, H - 56, "EARN FREE COINS BY CHATTING & /daily   •   MGB NOT CODER", _font(20, True), (206, 220, 244))
    return _save_jpg(bg, "mgb_shop.jpg")

# ── CARD 3: RICHEST MEMBERS LEADERBOARD CARD (/rich) ──────────
def _render_rich_leaderboard_card(top_rows: list, group_title: str) -> io.BytesIO:
    W, H = 1280, 760
    bg = _make_gradient(W, H, (14, 12, 34), (28, 16, 10)).convert("RGBA")
    _draw_glow(bg, 640, 120, 260, (245, 198, 92, 95))
    _draw_glow(bg, 1060, 640, 220, (236, 72, 153, 75))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(14, 14, 28, 238), outline=(245, 198, 92, 240), width=4)

    # Top Title Banner
    d.rounded_rectangle((280, 62, 1000, 128), radius=30, fill=(245, 198, 92, 250))
    _draw_center(d, 640, 95, "MGB RICHEST BILLIONAIRES  •  TOP 5", _font(27, True), (16, 14, 24))
    _draw_fit_center(d, 640, 156, _clean_name(group_title, 36).upper(), 820, 22, (214, 226, 246))

    medals = [(255, 215, 0), (203, 213, 225), (217, 119, 6), (56, 189, 248), (168, 85, 247)]
    y = 192
    for idx, (dp_img, rec) in enumerate(top_rows[:5]):
        col = medals[idx % len(medals)]
        d.rounded_rectangle((78, y, W - 78, y + 90), radius=24, fill=(22, 24, 46, 242), outline=(col[0], col[1], col[2], 225), width=3 if idx == 0 else 2)

        # Rank Circle
        d.ellipse((100, y + 17, 156, y + 73), fill=(col[0], col[1], col[2], 255))
        _draw_center(d, 128, y + 45, f"#{idx + 1}", _font(25, True), (12, 14, 26))

        # Member DP
        _paste_circle_dp(bg, dp_img, 212, y + 45, 32, ring_col=(col[0], col[1], col[2], 255), ring_w=3)
        d = ImageDraw.Draw(bg)

        # Name + Title
        d.text((264, y + 16), _clean_name(rec.get("name", "MGB VIP"), 22).upper(), font=_font(27, True), fill=(255, 255, 255))
        d.text((264, y + 52), f"{_clean_name(rec.get('title', 'MGB MEMBER'), 20).upper()}  •  STREAK: {rec.get('streak', 0)}d", font=_font(18, False), fill=(176, 196, 228))

        # Coins Badge on Right
        d.rounded_rectangle((918, y + 18, W - 102, y + 72), radius=20, fill=(10, 12, 24, 250), outline=(col[0], col[1], col[2], 210), width=2)
        _draw_fit_center(d, 1048, y + 45, f"{int(rec.get('coins', 0)):,} COINS", 240, 23, col)
        y += 102

    _draw_center(d, 640, H - 56, "USE /daily & /shop TO CLIMB THE BOARD   •   MGB NOT CODER", _font(20, True), (245, 206, 122))
    return _save_jpg(bg, "mgb_rich.jpg")

# ── CARD 4: DARK LUXURY ANONYMOUS CONFESSION CARD (/confess) ──
def _render_confession_card(confess_no: int, secret_text: str, group_title: str) -> io.BytesIO:
    W, H = 1280, 720
    bg = _make_gradient(W, H, (24, 6, 28), (8, 8, 22)).convert("RGBA")
    _draw_glow(bg, 220, 160, 260, (225, 29, 72, 95))
    _draw_glow(bg, 1060, 560, 260, (147, 51, 234, 90))
    _draw_glow(bg, 640, 360, 220, (245, 158, 11, 45))

    d = ImageDraw.Draw(bg)
    # Outer Velvet-Gold Frame
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(14, 8, 24, 232), outline=(244, 178, 118, 238), width=4)
    d.rounded_rectangle((56, 54, W - 56, H - 54), radius=26, outline=(225, 29, 72, 130), width=2)

    # Top Masked Secret Header Pill
    d.rounded_rectangle((340, 64, 940, 126), radius=30, fill=(190, 18, 60, 245), outline=(255, 220, 150, 245), width=3)
    _draw_center(d, 640, 95, f"ANONYMOUS CONFESSION  #{confess_no}", _font(26, True), (255, 255, 255))

    # Decorative oversized quotation marks
    d.text((92, 140), '"', font=_font(120, True), fill=(244, 63, 94, 120))
    d.text((W - 168, 446), '"', font=_font(120, True), fill=(244, 63, 94, 120))

    # Frosted Dark Secret Message Box
    d.rounded_rectangle((112, 168, W - 112, 544), radius=28, fill=(24, 14, 38, 235), outline=(244, 178, 118, 165), width=2)

    cleaned = _clean_body(secret_text, 240)
    f_size = 38 if len(cleaned) <= 95 else (32 if len(cleaned) <= 165 else 28)
    f_body = _font(f_size, True)
    lines = _wrap_lines(d, cleaned, f_body, W - 310, max_lines=5)
    line_h = f_size + 18
    total_h = len(lines) * line_h
    start_y = int(356 - total_h / 2 + line_h / 2)

    for idx, ln in enumerate(lines):
        _draw_center(d, 640, start_y + idx * line_h, ln, f_body, (255, 248, 252))

    # Bottom Identity Hidden + Group & Timestamp Strip
    ts = datetime.now(IST).strftime("%d %b %Y  •  %I:%M %p IST")
    d.rounded_rectangle((112, 568, 520, 626), radius=24, fill=(36, 16, 46, 245), outline=(225, 29, 72, 210), width=2)
    _draw_center(d, 316, 597, "SENDER : 100% HIDDEN", _font(21, True), (255, 198, 214))

    d.rounded_rectangle((548, 568, W - 112, 626), radius=24, fill=(36, 16, 46, 245), outline=(244, 178, 118, 210), width=2)
    _draw_fit_center(d, 858, 597, f"{_clean_name(group_title, 20).upper()}  •  {ts}", 580, 19, (255, 224, 162))

    _draw_center(d, 640, 658, "DM BOT /confess TO SEND SECRETLY   •   MGB NOT CODER", _font(19, True), (206, 184, 224))
    return _save_jpg(bg, "mgb_confess.jpg")
# ── HELPER: GLOBAL COIN RANK & AUTO CHAT EARNER ───────────────
def _get_rank_pos(uid: int) -> int:
    ordered = sorted(
        EDB["users"].items(),
        key=lambda kv: int(kv[1].get("coins", 0)),
        reverse=True,
    )
    uid_str = str(uid)
    for idx, (k, _) in enumerate(ordered, start=1):
        if k == uid_str:
            return idx
    return len(ordered) + 1

def _apply_item_to_rec(rec: dict, item_id: str):
    item = SHOP_ITEMS[item_id]
    if item["kind"] == "theme":
        rec["theme"] = item_id
    elif item["kind"] == "ring":
        rec["ring"] = item_id
    elif item["kind"] == "title":
        rec["title"] = item["title"]

@bot.on_message(filters.group, group=15)
async def _eco_chat_coin_watcher(client, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return
    cid = message.chat.id
    uid = user.id
    now_ts = time.time()

    # Track user's active group for seamless DM /confess routing
    _get_confess_chat(cid, message.chat.title or "MGB GROUP")
    EDB["user_last_group"][str(uid)] = str(cid)

    rec = _get_user_rec(uid, user.first_name)
    rec["msgs"] = int(rec.get("msgs", 0)) + 1

    key = (cid, uid)
    if now_ts - CHAT_COIN_COOLDOWN.get(key, 0) >= CHAT_COIN_GAP_SEC:
        CHAT_COIN_COOLDOWN[key] = now_ts
        rec["coins"] = int(rec.get("coins", 0)) + random.randint(*CHAT_COIN_REWARD)
        _save_eco_db()

# ── 1. DAILY STREAK COIN REWARD (/daily) ──────────────────────
@bot.on_message(filters.command(["daily", "claim", "bonus"], prefixes=["/", "!", "."]))
async def daily_coins_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return

    now_dt = datetime.now(IST)
    today_ymd = now_dt.strftime("%Y-%m-%d")
    yesterday_ymd = (now_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    rec = _get_user_rec(user.id, user.first_name)
    if rec.get("daily_date") == today_ymd:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>⏳ 𝐃𝐀𝐈𝐋𝐘 𝐁𝐎𝐍𝐔𝐒 𝐀𝐋𝐑𝐄𝐀𝐃𝐘 𝐂𝐋𝐀𝐈𝐌𝐄𝐃!</b></blockquote>\n\n"
            f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
            f"💰 <b>Balance:</b> <code>{rec['coins']:,} Coins</code>\n"
            f"🔥 <b>Streak:</b> <code>{rec['streak']} Days</code>\n"
            f"🕒 <b>Kal phir aayein naye bonus ke liye!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    streak = (int(rec.get("streak", 0)) + 1) if rec.get("daily_date") == yesterday_ymd else 1
    reward = 150 + min(streak * 25, 350)
    rec["streak"] = streak
    rec["daily_date"] = today_ymd
    rec["coins"] = int(rec.get("coins", 0)) + reward
    _save_eco_db()

    dp = await _get_user_dp(client, user.id)
    rank_pos = _get_rank_pos(user.id)
    card = await asyncio.to_thread(_render_wallet_card, dp, rec, rank_pos, f"+{reward} DAILY BONUS CLAIMED!")
    cap = (
        f"<blockquote><b>🎁 𝐃𝐀𝐈𝐋𝐘 𝐑𝐎𝐘𝐀𝐋 𝐑𝐄𝐖𝐀𝐑𝐃 𝐂𝐋𝐀𝐈𝐌𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"💸 <b>Earned:</b> <code>+{reward:,} Coins</code> (🔥 <code>{streak}-Day Streak</code>)\n"
        f"🏦 <b>Total Vault:</b> <code>{rec['coins']:,} Coins</code>\n"
        f"🛍 <b>Card Shop:</b> <code>/shop</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills(_profile_url(user), "👤 𝐕𝐈𝐄𝐖 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 2. VIP WALLET CARD (/wallet, /coins, /bal) ────────────────
@bot.on_message(filters.command(["wallet", "coins", "bal", "balance"], prefixes=["/", "!", "."]))
async def wallet_card_cmd(client, message: Message):
    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else message.from_user
    )
    if not target:
        return

    rec = _get_user_rec(target.id, target.first_name)
    _save_eco_db()
    dp = await _get_user_dp(client, target.id)
    rank_pos = _get_rank_pos(target.id)
    card = await asyncio.to_thread(_render_wallet_card, dp, rec, rank_pos, "")
    cap = (
        f"<blockquote><b>🏦 𝐌𝐆𝐁 𝐑𝐎𝐘𝐀𝐋 𝐕𝐈𝐏 𝐖𝐀𝐋𝐋𝐄𝐓</b></blockquote>\n\n"
        f"👤 <b>Holder:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"💰 <b>Balance:</b> <code>{rec['coins']:,} Coins</code> (🏆 Rank <code>#{rank_pos}</code>)\n"
        f"👑 <b>Badge:</b> <code>{html.escape(rec.get('title', 'MGB MEMBER'))}</code>\n"
        f"⚡ <b>Commands:</b> <code>/daily</code> | <code>/shop</code> | <code>/rich</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills(_profile_url(target), "🏦 𝐖𝐀𝐋𝐋𝐄𝐓 𝐇𝐎𝐋𝐃𝐄𝐑"))

# ── 3. VIP CARD SHOP (/shop), BUY (/buy) & EQUIP (/equip) ─────
@bot.on_message(filters.command(["shop", "cardshop", "store"], prefixes=["/", "!", "."]))
async def card_shop_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    rec = _get_user_rec(user.id, user.first_name)
    card = await asyncio.to_thread(_render_shop_card, int(rec["coins"]), list(rec.get("owned", [])))
    cap = (
        f"<blockquote><b>🛍 𝐌𝐆𝐁 𝐕𝐈𝐏 𝐂𝐀𝐑𝐃 𝐒𝐇𝐎𝐏</b></blockquote>\n\n"
        f"💰 <b>Your Vault:</b> <code>{rec['coins']:,} Coins</code>\n"
        f"🛒 <b>Buy Item:</b> <code>/buy 1</code> to <code>/buy 6</code>\n"
        f"🎨 <b>Equip Owned:</b> <code>/equip 1</code> | <b>Reset:</b> <code>/equip reset</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills())

@bot.on_message(filters.command(["buy", "buycard"], prefixes=["/", "!", "."]))
async def buy_shop_item_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    if len(message.command) < 2 or message.command[1] not in SHOP_ITEMS:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🛒 𝐌𝐆𝐁 𝐂𝐀𝐑𝐃 𝐒𝐇𝐎𝐏 𝐁𝐔𝐘</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> <code>/buy 1</code> se <code>/buy 6</code>\n"
            f"🛍 <b>Catalog dekhne ke liye:</b> <code>/shop</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    item_id = message.command[1]
    item = SHOP_ITEMS[item_id]
    rec = _get_user_rec(user.id, user.first_name)
    owned = rec.setdefault("owned", [])

    if item_id in owned:
        _apply_item_to_rec(rec, item_id)
        _save_eco_db()
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>✅ 𝐀𝐋𝐑𝐄𝐀𝐃𝐘 𝐎𝐖𝐍𝐄𝐃 — 𝐄𝐐𝐔𝐈𝐏𝐏𝐄𝐃!</b></blockquote>\n\n"
            f"🎨 <b>Item:</b> <code>{item['name']}</code> aapke wallet card par lag gaya hai!\n"
            f"🏦 <b>Check Card:</b> <code>/wallet</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    price = int(item["price"])
    if int(rec["coins"]) < price:
        need = price - int(rec["coins"])
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐈𝐍𝐒𝐔𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓 𝐂𝐎𝐈𝐍𝐒</b></blockquote>\n\n"
            f"🏷 <b>Item:</b> <code>{item['name']}</code> (<code>{price:,} Coins</code>)\n"
            f"💰 <b>Aapke Paas:</b> <code>{rec['coins']:,} Coins</code>\n"
            f"📉 <b>Aur Chahiye:</b> <code>{need:,} Coins</code> — <code>/daily</code> claim karein!\n\n{FOOTER}",
            reply_to=message.id,
        )

    rec["coins"] = int(rec["coins"]) - price
    owned.append(item_id)
    _apply_item_to_rec(rec, item_id)
    _save_eco_db()

    dp = await _get_user_dp(client, user.id)
    card = await asyncio.to_thread(_render_wallet_card, dp, rec, _get_rank_pos(user.id), f"UNLOCKED: {item['name']}")
    cap = (
        f"<blockquote><b>🎉 𝐕𝐈𝐏 𝐈𝐓𝐄𝐌 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃 & 𝐄𝐐𝐔𝐈𝐏𝐏𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Buyer:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"✨ <b>Item:</b> <code>{item['name']}</code> (<code>-{price:,} Coins</code>)\n"
        f"💰 <b>Remaining:</b> <code>{rec['coins']:,} Coins</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills(_profile_url(user), "👑 𝐕𝐈𝐏 𝐁𝐔𝐘𝐄𝐑"))

@bot.on_message(filters.command(["equip", "useitem"], prefixes=["/", "!", "."]))
async def equip_shop_item_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    if len(message.command) < 2:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🎨 𝐄𝐐𝐔𝐈𝐏 𝐕𝐈𝐏 𝐒𝐓𝐘𝐋𝐄</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> <code>/equip 1</code> (ya <code>/equip reset</code>)\n\n{FOOTER}",
            reply_to=message.id,
        )

    arg = message.command[1].lower()
    rec = _get_user_rec(user.id, user.first_name)

    if arg == "reset":
        rec["theme"] = ""
        rec["ring"] = ""
        rec["title"] = "MGB MEMBER"
        _save_eco_db()
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🔄 𝐂𝐀𝐑𝐃 𝐒𝐓𝐘𝐋𝐄 𝐑𝐄𝐒𝐄𝐓</b></blockquote>\n\n"
            f"✅ <b>Default Royal Theme wapas set ho gaya hai!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if arg not in SHOP_ITEMS or arg not in rec.get("owned", []):
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🔒 𝐈𝐓𝐄𝐌 𝐍𝐎𝐓 𝐎𝐖𝐍𝐄𝐃</b></blockquote>\n\n"
            f"🛒 <b>Pehle ise kharidein:</b> <code>/buy {html.escape(arg)}</code> ya <code>/shop</code> dekhein!\n\n{FOOTER}",
            reply_to=message.id,
        )

    _apply_item_to_rec(rec, arg)
    _save_eco_db()
    dp = await _get_user_dp(client, user.id)
    card = await asyncio.to_thread(_render_wallet_card, dp, rec, _get_rank_pos(user.id), f"EQUIPPED: {SHOP_ITEMS[arg]['name']}")
    cap = (
        f"<blockquote><b>🎨 𝐕𝐈𝐏 𝐂𝐀𝐑𝐃 𝐒𝐓𝐘𝐋𝐄 𝐔𝐏𝐃𝐀𝐓𝐄𝐃!</b></blockquote>\n\n"
        f"✨ <b>Equipped:</b> <code>{SHOP_ITEMS[arg]['name']}</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills(_profile_url(user), "🎨 𝐕𝐈𝐏 𝐏𝐑𝐎𝐅𝐈𝐋𝐄"))

# ── 4. TRANSFER COINS (/give) & RICHEST LEADERBOARD (/rich) ───
@bot.on_message(filters.group & filters.command(["give", "paycoins", "sendcoins"], prefixes=["/", "!", "."]))
async def give_coins_cmd(client, message: Message):
    sender = message.from_user
    reply = message.reply_to_message
    if not sender or not reply or not reply.from_user or reply.from_user.is_bot:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>💸 𝐓𝐑𝐀𝐍𝐒𝐅𝐄𝐑 𝐌𝐆𝐁 𝐂𝐎𝐈𝐍𝐒</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> Kisi member par reply karke likhein <code>/give 250</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    target = reply.from_user
    if target.id == sender.id:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>⚠️ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐓𝐑𝐀𝐍𝐒𝐅𝐄𝐑</b></blockquote>\n\n"
            f"😂 <b>Khud ko hi coins nahi bhej sakte!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐀𝐌𝐎𝐔𝐍𝐓 𝐌𝐈𝐒𝐒𝐈𝐍𝐆</b></blockquote>\n\n"
            f"⚡ <b>Example:</b> <code>/give 200</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    amt = int(message.command[1])
    s_rec = _get_user_rec(sender.id, sender.first_name)
    if amt < 10 or int(s_rec["coins"]) < amt:
        return await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐓𝐑𝐀𝐍𝐒𝐅𝐄𝐑 𝐅𝐀𝐈𝐋𝐄𝐃</b></blockquote>\n\n"
            f"💰 <b>Minimum 10 Coins chahiye! Aapka Balance:</b> <code>{s_rec['coins']:,} Coins</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    t_rec = _get_user_rec(target.id, target.first_name)
    s_rec["coins"] = int(s_rec["coins"]) - amt
    t_rec["coins"] = int(t_rec["coins"]) + amt
    _save_eco_db()

    await _send_pill_msg(
        client, message.chat.id,
        f"<blockquote><b>💸 𝐌𝐆𝐁 𝐂𝐎𝐈𝐍𝐒 𝐓𝐑𝐀𝐍𝐒𝐅𝐄𝐑 𝐒𝐔𝐂𝐂𝐄𝐒𝐒!</b></blockquote>\n\n"
        f"👤 <b>From:</b> <b>{html.escape(sender.first_name)}</b>\n"
        f"🎁 <b>To:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"💰 <b>Amount:</b> <code>{amt:,} Coins</code>\n"
        f"🏦 <b>Your New Balance:</b> <code>{s_rec['coins']:,} Coins</code>\n\n{FOOTER}",
        reply_to=message.id,
        extra_url=_profile_url(target),
        extra_label="🎁 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐑",
    )

@bot.on_message(filters.command(["rich", "topcoins", "richest"], prefixes=["/", "!", "."]))
async def richest_board_cmd(client, message: Message):
    if not EDB["users"]:
        if message.from_user:
            _get_user_rec(message.from_user.id, message.from_user.first_name)
            _save_eco_db()

    ordered = sorted(
        EDB["users"].items(),
        key=lambda kv: int(kv[1].get("coins", 0)),
        reverse=True,
    )[:5]

    dps = await asyncio.gather(*(_get_user_dp(client, int(uid_s)) for uid_s, _ in ordered))
    top_rows = [(dps[i], ordered[i][1]) for i in range(len(ordered))]
    group_title = message.chat.title or "MGB GLOBAL BILLIONAIRES"
    card = await asyncio.to_thread(_render_rich_leaderboard_card, top_rows, group_title)

    lines = "\n".join(
        f"• <b>#{i + 1} {html.escape(rec.get('name', 'MGB VIP'))}</b> — <code>{int(rec.get('coins', 0)):,} Coins</code>"
        for i, (_, rec) in enumerate(ordered)
    )
    cap = (
        f"<blockquote><b>🏆 𝐌𝐆𝐁 𝐑𝐈𝐂𝐇𝐄𝐒𝐓 𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃</b></blockquote>\n\n"
        f"{lines}\n\n"
        f"⚡ <b>Roz free coins ke liye:</b> <code>/daily</code>\n\n{FOOTER}"
    )
    await _send_eco_card(client, message.chat.id, card, cap, rows=_bottom_html_pills())

# ── 5. ANONYMOUS SECRET CONFESSION (/setconfess & /confess) ───
@bot.on_message(filters.group & filters.command(["setconfess", "confessbox"], prefixes=["/", "!", "."]))
async def set_confess_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    cfg = _get_confess_chat(cid, message.chat.title or "MGB GROUP")
    arg = message.command[1].lower() if len(message.command) > 1 else ""

    if arg != "status" and user and not await _is_chat_admin(client, cid, user.id):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Group Admins Confession Box ON/OFF kar sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if arg in ("on", "enable"):
        cfg["enabled"] = True
    elif arg in ("off", "disable"):
        cfg["enabled"] = False
    elif arg != "status":
        cfg["enabled"] = not cfg["enabled"]
    _save_eco_db()

    dm_url = await _bot_dm_url(client)
    st = "ENABLED ✅" if cfg["enabled"] else "DISABLED ❌"
    await _send_pill_msg(
        client, cid,
        f"<blockquote><b>💌 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍 𝐁𝐎𝐗</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"🔑 <b>Group Code:</b> <code>{cfg['code']}</code>\n"
        f"📊 <b>Total Secrets:</b> <code>{cfg['count']}</code>\n\n"
        f"<blockquote><b>🤫 𝐒𝐄𝐂𝐑𝐄𝐓 𝐁𝐇𝐄𝐉𝐍𝐄 𝐊𝐄 2 𝐓𝐀𝐑𝐄𝐄𝐊𝐄:</b>\n"
        f"1️⃣ Bot ke DM mein likhein: <code>/confess Mera secret...</code>\n"
        f"2️⃣ Ya Group mein likhein: <code>/confess Mera secret...</code> <i>(Msg instant delete ho jayega!)</i></blockquote>\n\n{FOOTER}",
        reply_to=message.id,
        extra_url=dm_url,
        extra_label="💌 𝐒𝐄𝐍𝐃 𝐒𝐄𝐂𝐑𝐄𝐓 𝐈𝐍 𝐃𝐌",
    )

@bot.on_message(filters.command(["confess", "secret", "confession"], prefixes=["/", "!", "."]))
async def anonymous_confess_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return

    raw = message.text.split(None, 1)[1].strip() if (message.text and len(message.text.split(None, 1)) > 1) else ""
    dm_url = await _bot_dm_url(client)

    # A. Sent directly inside a Group (Instant Auto-Delete for 100% Privacy)
    if message.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        cid = message.chat.id
        cfg = _get_confess_chat(cid, message.chat.title or "MGB GROUP")
        EDB["user_last_group"][str(user.id)] = str(cid)

        try:
            await message.delete()
        except Exception:
            pass

        if not cfg.get("enabled", True):
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>🔒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍 𝐁𝐎𝐗 𝐎𝐅𝐅</b></blockquote>\n\n"
                f"⚠️ <b>Admin ise <code>/setconfess on</code> se chalu kar sakte hain!</b>\n\n{FOOTER}",
            )

        if not raw:
            return await _send_pill_msg(
                client, cid,
                f"<blockquote><b>💌 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍</b></blockquote>\n\n"
                f"🤫 <b>DM ya Group mein likhein:</b> <code>/confess Koi bahut pasand hai is group mein!</code>\n"
                f"🔑 <b>Group Code:</b> <code>{cfg['code']}</code>\n\n{FOOTER}",
                extra_url=dm_url,
                extra_label="💌 𝐂𝐎𝐍𝐅𝐄𝐒𝐒 𝐈𝐍 𝐃𝐌",
            )

        target_cid = cid
        secret_text = raw
    else:
        # B. Sent privately in Bot DM (100% Untraceable)
        if not raw:
            return await _send_pill_msg(
                client, message.chat.id,
                f"<blockquote><b>💌 𝐃𝐌 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍</b></blockquote>\n\n"
                f"🤫 <b>Direct likhein:</b> <code>/confess Aapka secret message...</code>\n"
                f"🔑 <b>Specific Group ke liye:</b> <code>/confess MGB1234 Aapka secret...</code>\n\n{FOOTER}",
                reply_to=message.id,
            )

        target_cid = None
        secret_text = raw
        first_tok = raw.split(None, 1)[0].upper()

        # Match optional MGBxxxx group code
        for cid_s, cinfo in EDB["confess_chats"].items():
            if cinfo.get("code", "").upper() == first_tok:
                target_cid = int(cid_s)
                secret_text = raw.split(None, 1)[1].strip() if len(raw.split(None, 1)) > 1 else ""
                break

        if target_cid is None:
            last_cid = EDB["user_last_group"].get(str(user.id))
            if last_cid and last_cid in EDB["confess_chats"]:
                target_cid = int(last_cid)
            elif len(EDB["confess_chats"]) == 1:
                target_cid = int(next(iter(EDB["confess_chats"])))

        if target_cid is None:
            return await _send_pill_msg(
                client, message.chat.id,
                f"<blockquote><b>❌ 𝐆𝐑𝐎𝐔𝐏 𝐍𝐎𝐓 𝐋𝐈𝐍𝐊𝐄𝐃</b></blockquote>\n\n"
                f"📌 <b>Pehle apne group mein koi 1 message bhejein, ya group code use karein:</b>\n"
                f"<code>/confess MGB1234 Mera secret message</code>\n\n{FOOTER}",
                reply_to=message.id,
            )

        cfg = EDB["confess_chats"].get(str(target_cid), {})
        if not cfg.get("enabled", True):
            return await _send_pill_msg(
                client, message.chat.id,
                f"<blockquote><b>🔒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍 𝐃𝐈𝐒𝐀𝐁𝐋𝐄𝐃</b></blockquote>\n\n"
                f"⚠️ <b>Is group mein Confession Box abhi OFF hai!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )

        if not secret_text:
            return await _send_pill_msg(
                client, message.chat.id,
                f"<blockquote><b>❌ 𝐒𝐄𝐂𝐑𝐄𝐓 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐄𝐌𝐏𝐓𝐘</b></blockquote>\n\n"
                f"✍️ <b>Code ke baad apna secret message bhi likhein!</b>\n\n{FOOTER}",
                reply_to=message.id,
            )

    # Render & Post Dark Luxury Secret Confession Card
    cfg = _get_confess_chat(target_cid)
    EDB["confess_total"] = int(EDB.get("confess_total", 0)) + 1
    cfg["count"] = int(cfg.get("count", 0)) + 1
    c_no = EDB["confess_total"]
    _save_eco_db()

    card = await asyncio.to_thread(_render_confession_card, c_no, secret_text, cfg.get("title", "MGB GROUP"))
    cap = (
        f"<blockquote><b>💌 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍 #{c_no}</b></blockquote>\n\n"
        f"🕵️ <b>Sender:</b> <code>100% SECRET & HIDDEN</code>\n"
        f"💬 <b>Message:</b> <i>\"{html.escape(secret_text[:240])}\"</i>\n\n"
        f"🤫 <b>Apna secret bhejne ke liye niche button dabao ya DM mein <code>/confess</code> likho!</b>\n\n{FOOTER}"
    )
    await _send_eco_card(
        client, target_cid, card, cap,
        rows=_bottom_html_pills(dm_url, "💌 𝐒𝐄𝐍𝐃 𝐒𝐄𝐂𝐑𝐄𝐓 𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍"),
    )

    if message.chat.type == enums.ChatType.PRIVATE:
        await _send_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>✅ 𝐒𝐄𝐂𝐑𝐄𝐓 𝐃𝐄𝐋𝐈𝐕𝐄𝐑𝐄𝐃 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒𝐋𝐘!</b></blockquote>\n\n"
            f"💌 <b>Confession:</b> <code>#{c_no}</code>\n"
            f"👥 <b>Group:</b> <b>{html.escape(cfg.get('title', 'MGB GROUP'))}</b>\n"
            f"🕵️ <b>Aapka naam 100% chhupa rakha gaya hai!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )
