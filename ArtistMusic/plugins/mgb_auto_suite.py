# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#     PRO AUTO SUITE — 100% HTML PILL BUTTONS & EXACT ALIGNMENT
# ═══════════════════════════════════════════════════════════════

import os
import io
import re
import json
import time
import html
import random
import asyncio
import unicodedata
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions

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
    _get_template_bg,
    _make_single_card,
    send_rich_card,
    send_colored_msg,
)

try:
    from ArtistMusic.plugins.mgb_viral_cards import _make_dual_card
except Exception:
    _make_dual_card = None

# ── PERSISTENT STORAGE & CONSTANTS ────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = "mgb_data"
DATA_FILE = os.path.join(DATA_DIR, "auto_suite.json")
os.makedirs(DATA_DIR, exist_ok=True)

CUSTOM_TPL_URLS = {
    "bday": "https://i.ibb.co/TDgyTxKj/photo-AQAD1x-Rr-G-9-WGVR8.jpg",
    "badge": "https://i.ibb.co/279TZY7j/photo-AQAD2-BRr-G-9-WGVR8.jpg",
    "anni": "https://i.ibb.co/p6FXqHL8/photo-AQAD2-RRr-G-9-WGVR8.jpg",
}
_TPL_MEM_CACHE = {}

# Exact pixel-calibrated layout per 1280x720 custom template
TEMPLATE_LAYOUTS = {
    "bday": {
        "ring_cx": 330, "ring_cy": 335, "dp_r": 141,
        "rim_color": (255, 232, 246, 225),
        "restore_pill": (232, 436, 418, 490, 26),
        "bar1": (872, 410, 440),
        "bar2": (872, 488, 440),
        "f1": 30, "f2": 26,
        "c1": (20, 16, 44), "c2": (52, 22, 82),
        "stroke": (255, 255, 255), "stroke_w": 1,
    },
    "anni": {
        "ring_cx": 332, "ring_cy": 354, "dp_r": 172,
        "rim_color": (255, 214, 172, 230),
        "restore_pill": None,
        "bar1": (907, 476, 480),
        "bar2": (907, 550, 480),
        "f1": 30, "f2": 26,
        "c1": (255, 255, 255), "c2": (255, 224, 158),
        "stroke": (18, 6, 12), "stroke_w": 2,
    },
    "badge": {
        "ring_cx": 340, "ring_cy": 360, "dp_r": 156,
        "rim_color": (255, 198, 208, 230),
        "restore_pill": None,
        "bar1": (900, 486, 480),
        "bar2": (900, 555, 480),
        "f1": 27, "f2": 23,
        "c1": (255, 255, 255), "c2": (255, 224, 158),
        "stroke": (18, 6, 12), "stroke_w": 2,
    },
}

DEFAULT_CLEAN_MIN = 30
SPAM_WINDOW_SEC = 5
DEFAULT_SPAM_MAX = 5
WELCOME_BACK_DAYS = 3
STREAK_MILESTONES = {
    7: "7-DAY LOYAL STAR",
    15: "15-DAY VVIP LEGEND",
    30: "30-DAY ROYAL KING",
}

LINK_RE = re.compile(r"(https?://\S+|t\.me/\S+|www\.\S+|@[a-zA-Z0-9_]{4,})", re.IGNORECASE)
SPAM_HITS = defaultdict(list)
SPAM_STRIKES = defaultdict(int)
SPAM_COOLDOWN = {}
_SCHEDULER_TASK = None

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "Δ": "A", "α": "A", "Σ": "E", "Ω": "O", "β": "B",
    "χ": "X", "Χ": "X", "×": "X", "✗": "X", "✘": "X", "✕": "X", "✖": "X", "⨯": "X", "᙭": "X",
})

ROAST_LINES = [
    "WiFi slow ho toh tera dimaag aur fast chalne lagta hai!",
    "Tu online aata hai toh lagta hai server mein extra load aa gaya!",
    "Itna shant rehna bhi ek kala hai, khaas kar jab kaam ki baat ho!",
    "Group ka sabse bada mystery: tu aakhir karta kya hai din bhar?",
    "Teri baatein sun kar lagta hai auto-mute button invent hona chahiye!",
    "Tera confidence dekh kar Google bhi confuse ho jaata hai!",
]

# ── CLEAN NAME & DATABASE HELPERS ─────────────────────────────
def _clean_text(val: str, limit: int = 24) -> str:
    s = unicodedata.normalize("NFKC", str(val or "MGB VIP"))
    s = s.translate(FANCY_MAP)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip().upper()
    parts = s.split()
    if len(parts) >= 4 and all(len(p) == 1 for p in parts):
        s = "".join(parts)
    return s[:limit] or "MGB VIP"

def _default_db() -> dict:
    return {
        "allclean_cfg": {},     # str(cid) -> {enabled, minutes, mode, keep_pinned, skip_admins, clean_service, cleaned_count}
        "antispam_cfg": {},     # str(cid) -> {enabled, max_msgs, block_links, auto_mute, blocked_count}
        "daily_vibes_chats": [],
        "birthdays": {},        # str(cid) -> {str(uid): {"date": "DD-MM", "name": "..."}}
        "anniversaries": {},    # str(cid) -> {str(uid): {"date": "DD-MM", "name": "..."}}
        "last_seen": {},        # str(cid) -> {str(uid): {"ts": float, "day": "YYYY-MM-DD", "streak": int}}
        "sent_flags": {},
    }

def _load_db() -> dict:
    base = _default_db()
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            base.update(data)
            # Backwards compatibility migration from old list keys
            for cid in data.get("allclean_chats", []):
                base["allclean_cfg"].setdefault(str(cid), {
                    "enabled": True, "minutes": DEFAULT_CLEAN_MIN, "mode": "all",
                    "keep_pinned": True, "skip_admins": False, "clean_service": True, "cleaned_count": 0,
                })
            for cid in data.get("antispam_chats", []):
                base["antispam_cfg"].setdefault(str(cid), {
                    "enabled": True, "max_msgs": DEFAULT_SPAM_MAX,
                    "block_links": False, "auto_mute": True, "blocked_count": 0,
                })
        except Exception:
            pass
    return base

DB = _load_db()

def _save_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _get_clean_cfg(cid: int) -> dict:
    return DB["allclean_cfg"].setdefault(str(cid), {
        "enabled": False,
        "minutes": DEFAULT_CLEAN_MIN,
        "mode": "all",          # "all" or "media"
        "keep_pinned": True,
        "skip_admins": False,
        "clean_service": True,
        "cleaned_count": 0,
    })

def _get_spam_cfg(cid: int) -> dict:
    return DB["antispam_cfg"].setdefault(str(cid), {
        "enabled": False,
        "max_msgs": DEFAULT_SPAM_MAX,
        "block_links": False,
        "auto_mute": True,
        "blocked_count": 0,
    })

# ── 100% PERMANENT HTML PILL BUTTONS (URL-ONLY FOR RICHGRAM) ──
def _html_pill_rows(extra_label: str = None, extra_url: str = None) -> list:
    row1 = [
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]
    if extra_label and extra_url:
        return [row1, [_cbtn(extra_label, style="primary", url=extra_url)]]
    return [row1]

async def _send_html_pill_msg(client, chat_id: int, text: str, reply_to: int = None):
    await send_colored_msg(client, chat_id, text, _html_pill_rows(), reply_to=reply_to)

async def _is_chat_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False

def _ensure_scheduler():
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK is None or _SCHEDULER_TASK.done():
        _SCHEDULER_TASK = asyncio.create_task(_daily_auto_scheduler())

# ── CUSTOM TEMPLATE ENGINE (PIXEL-PERFECT DP & TEXT ALIGNMENT) ─
async def _fetch_custom_template(kind: str) -> Image.Image:
    if kind in _TPL_MEM_CACHE:
        return _TPL_MEM_CACHE[kind].copy()

    disk_path = os.path.join(DATA_DIR, f"tpl_{kind}.jpg")
    if os.path.isfile(disk_path) and os.path.getsize(disk_path) > 2000:
        try:
            im = Image.open(disk_path).convert("RGB").resize((1280, 720), Image.LANCZOS)
            _TPL_MEM_CACHE[kind] = im
            return im.copy()
        except Exception:
            pass

    url = CUSTOM_TPL_URLS.get(kind)
    if url:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
                async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
                    if r.status == 200:
                        raw = await r.read()
                        if len(raw) > 2000:
                            with open(disk_path, "wb") as f:
                                f.write(raw)
                            im = Image.open(io.BytesIO(raw)).convert("RGB").resize((1280, 720), Image.LANCZOS)
                            _TPL_MEM_CACHE[kind] = im
                            return im.copy()
        except Exception:
            pass

    fallback = await _get_template_bg()
    return fallback.resize((1280, 720), Image.LANCZOS)

def _load_bold_font(size: int):
    for fp in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _draw_centered_fit_text(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    text: str,
    max_w: int,
    base_size: int,
    fill: tuple,
    stroke: tuple,
    stroke_w: int = 2,
):
    size = base_size
    font = _load_bold_font(size)
    while size > 15:
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            break
        size -= 2
        font = _load_bold_font(size)

    try:
        draw.text(
            (cx, cy),
            text,
            font=font,
            fill=fill,
            anchor="mm",
            stroke_width=stroke_w,
            stroke_fill=stroke,
        )
    except TypeError:
        bbox = draw.textbbox((0, 0), text, font=font)
        x = int(cx - (bbox[2] - bbox[0]) / 2)
        y = int(cy - (bbox[3] - bbox[1]) / 2 - bbox[1])
        draw.text((x, y), text, font=font, fill=fill)

def _compose_custom_template_card(kind: str, tpl_img: Image.Image, dp_img: Image.Image, bar1_text: str, bar2_text: str) -> io.BytesIO:
    W, H = 1280, 720
    cfg = TEMPLATE_LAYOUTS.get(kind, TEMPLATE_LAYOUTS["anni"])
    orig_rgba = tpl_img.convert("RGBA").resize((W, H), Image.LANCZOS)
    canvas = orig_rgba.copy()

    # 1. Exact center-aligned circular DP
    rcx, rcy, dpr = cfg["ring_cx"], cfg["ring_cy"], cfg["dp_r"]
    dp_size = dpr * 2
    av = dp_img.convert("RGBA").resize((dp_size, dp_size), Image.LANCZOS)
    mask = Image.new("L", (dp_size, dp_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, dp_size, dp_size), fill=255)
    canvas.paste(av, (rcx - dpr, rcy - dpr), mask)

    d = ImageDraw.Draw(canvas)
    d.ellipse((rcx - dpr, rcy - dpr, rcx + dpr, rcy + dpr), outline=cfg["rim_color"], width=4)

    # 2. Restore overlapping bottom badge pill (e.g. 'BIRTHDAY' pill on bday card)
    if cfg.get("restore_pill"):
        x1, y1, x2, y2, rad = cfg["restore_pill"]
        pmask = Image.new("L", (x2 - x1, y2 - y1), 0)
        ImageDraw.Draw(pmask).rounded_rectangle((0, 0, x2 - x1, y2 - y1), radius=rad, fill=255)
        canvas.paste(orig_rgba.crop((x1, y1, x2, y2)), (x1, y1), pmask)

    # 3. Crisp auto-fitted bold text dead-center in both pill bars
    d = ImageDraw.Draw(canvas)
    b1x, b1y, b1w = cfg["bar1"]
    b2x, b2y, b2w = cfg["bar2"]
    _draw_centered_fit_text(d, b1x, b1y, _clean_text(bar1_text, 22), b1w, cfg["f1"], cfg["c1"], cfg["stroke"], cfg["stroke_w"])
    _draw_centered_fit_text(d, b2x, b2y, _clean_text(bar2_text, 26), b2w, cfg["f2"], cfg["c2"], cfg["stroke"], cfg["stroke_w"])

    out = io.BytesIO()
    out.name = f"mgb_{kind}_card.jpg"
    canvas.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out
# ── 1. ADVANCED AUTO-CLEAN (/allclean) ────────────────────────
_PINNED_CACHE = {}  # cid -> (ts, pinned_msg_id)

async def _get_pinned_msg_id(client, cid: int):
    now = time.time()
    cached = _PINNED_CACHE.get(cid)
    if cached and (now - cached[0]) < 15:
        return cached[1]
    pid = None
    try:
        chat = await client.get_chat(cid)
        if getattr(chat, "pinned_message", None):
            pid = chat.pinned_message.id
    except Exception:
        pass
    _PINNED_CACHE[cid] = (now, pid)
    return pid

def _format_clean_dashboard(cfg: dict) -> str:
    st = "ENABLED ✅" if cfg["enabled"] else "DISABLED ❌"
    mode_lbl = "ALL MESSAGES" if cfg["mode"] == "all" else "MEDIA / LINKS ONLY"
    pin_lbl = "SAFE ✅" if cfg["keep_pinned"] else "DELETE ⚠️"
    adm_lbl = "SKIPPED ✅" if cfg["skip_admins"] else "CLEANED"
    srv_lbl = "INSTANT ✅" if cfg["clean_service"] else "OFF ❌"
    return (
        f"<blockquote><b>🧹 𝐌𝐆𝐁 𝐏𝐑𝐎 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍 𝐒𝐘𝐒𝐓𝐄𝐌</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⏱ <b>Timer:</b> <code>{cfg['minutes']} Minutes</code>\n"
        f"🎯 <b>Mode:</b> <code>{mode_lbl}</code>\n"
        f"📌 <b>Pinned Msgs:</b> <code>{pin_lbl}</code>\n"
        f"👑 <b>Admin Msgs:</b> <code>{adm_lbl}</code>\n"
        f"🗑 <b>Join/Leave Clean:</b> <code>{srv_lbl}</code>\n"
        f"📊 <b>Total Cleaned:</b> <code>{cfg.get('cleaned_count', 0)}</code>\n\n"
        f"<blockquote><b>⚡ 𝐐𝐔𝐈𝐂𝐊 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>\n"
        f"• <code>/allclean on</code> | <code>/allclean off</code>\n"
        f"• <code>/allclean 30</code> <i>(1–1440 min timer)</i>\n"
        f"• <code>/allclean all</code> | <code>/allclean media</code>\n"
        f"• <code>/allclean pin</code> | <code>/allclean admin</code> | <code>/allclean service</code></blockquote>\n\n{FOOTER}"
    )

@bot.on_message(filters.group & filters.command(["allclean", "clean30", "groupclean"], prefixes=["/", "!", "."]))
async def allclean_pro_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    cfg = _get_clean_cfg(cid)
    arg = message.command[1].lower() if len(message.command) > 1 else ""

    if arg == "status":
        return await _send_html_pill_msg(client, cid, _format_clean_dashboard(cfg), reply_to=message.id)

    if message.from_user and not await _is_chat_admin(client, cid, message.from_user.id):
        return await _send_html_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Group Admins Auto-Clean settings badal sakte hain!</b>\n"
            f"📊 Status dekhne ke liye: <code>/allclean status</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if not arg:
        cfg["enabled"] = not cfg["enabled"]
    elif arg in ("on", "enable", "start"):
        cfg["enabled"] = True
    elif arg in ("off", "disable", "stop"):
        cfg["enabled"] = False
    elif arg in ("all", "everything"):
        cfg["mode"] = "all"
        cfg["enabled"] = True
    elif arg in ("media", "links", "photo"):
        cfg["mode"] = "media"
        cfg["enabled"] = True
    elif arg in ("pin", "pinned"):
        cfg["keep_pinned"] = not cfg["keep_pinned"]
    elif arg in ("admin", "admins"):
        cfg["skip_admins"] = not cfg["skip_admins"]
    elif arg in ("service", "join"):
        cfg["clean_service"] = not cfg["clean_service"]
    elif arg.isdigit():
        mins = max(1, min(1440, int(arg)))
        cfg["minutes"] = mins
        cfg["enabled"] = True
    else:
        return await _send_html_pill_msg(client, cid, _format_clean_dashboard(cfg), reply_to=message.id)

    _save_db()
    await _send_html_pill_msg(client, cid, _format_clean_dashboard(cfg), reply_to=message.id)

# ── 2. ADVANCED ANTI-SPAM / FLOOD GUARD (/antispam) ───────────
def _format_spam_dashboard(cfg: dict) -> str:
    st = "PROTECTED ✅" if cfg["enabled"] else "DISABLED ❌"
    lnk = "BLOCKED ✅" if cfg["block_links"] else "ALLOWED"
    mut = "ON (3 Strikes = 5m) ✅" if cfg["auto_mute"] else "OFF ❌"
    return (
        f"<blockquote><b>🛡 𝐌𝐆𝐁 𝐏𝐑𝐎 𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 𝐆𝐔𝐀𝐑𝐃</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⚡ <b>Flood Limit:</b> <code>{cfg['max_msgs']} Msgs / {SPAM_WINDOW_SEC}s</code>\n"
        f"🔗 <b>Anti-Link/Fwd:</b> <code>{lnk}</code>\n"
        f"🔇 <b>Auto-Mute:</b> <code>{mut}</code>\n"
        f"🚫 <b>Total Blocked:</b> <code>{cfg.get('blocked_count', 0)}</code>\n\n"
        f"<blockquote><b>⚡ 𝐐𝐔𝐈𝐂𝐊 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>\n"
        f"• <code>/antispam on</code> | <code>/antispam off</code>\n"
        f"• <code>/antispam links</code> | <code>/antispam mute</code>\n"
        f"• <code>/antispam 5</code> <i>(3–15 msgs limit)</i></blockquote>\n\n{FOOTER}"
    )

@bot.on_message(filters.group & filters.command(["antispam", "floodguard"], prefixes=["/", "!", "."]))
async def antispam_pro_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    cfg = _get_spam_cfg(cid)
    arg = message.command[1].lower() if len(message.command) > 1 else ""

    if arg == "status":
        return await _send_html_pill_msg(client, cid, _format_spam_dashboard(cfg), reply_to=message.id)

    if message.from_user and not await _is_chat_admin(client, cid, message.from_user.id):
        return await _send_html_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Group Admins Anti-Spam settings badal sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if not arg:
        cfg["enabled"] = not cfg["enabled"]
    elif arg in ("on", "enable"):
        cfg["enabled"] = True
    elif arg in ("off", "disable"):
        cfg["enabled"] = False
    elif arg in ("links", "link", "fwd"):
        cfg["block_links"] = not cfg["block_links"]
        cfg["enabled"] = True
    elif arg in ("mute", "automute"):
        cfg["auto_mute"] = not cfg["auto_mute"]
        cfg["enabled"] = True
    elif arg.isdigit():
        cfg["max_msgs"] = max(3, min(15, int(arg)))
        cfg["enabled"] = True

    _save_db()
    await _send_html_pill_msg(client, cid, _format_spam_dashboard(cfg), reply_to=message.id)

# ── 3. AUTO BIRTHDAY & ANNIVERSARY SETUP (/setbday, /setanni) ─
def _parse_dd_mm(raw: str):
    parts = raw.strip().replace("/", "-").split("-")
    if len(parts) < 2:
        return None
    try:
        d, m = int(parts[0]), int(parts[1])
        if 1 <= d <= 31 and 1 <= m <= 12:
            return f"{d:02d}-{m:02d}"
    except Exception:
        pass
    return None

@bot.on_message(filters.group & filters.command(["setbday", "birthday", "bday"], prefixes=["/", "!", "."]))
async def set_birthday_cmd(client, message: Message):
    _ensure_scheduler()
    user = message.from_user
    if not user:
        return
    cid = str(message.chat.id)

    if len(message.command) < 2:
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🎂 𝐀𝐔𝐓𝐎 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘 𝐒𝐄𝐓𝐔𝐏</b></blockquote>\n\n"
            f"📅 <b>Format:</b> <code>/setbday 15-08</code> (DD-MM)\n"
            f"🗑 <b>Remove:</b> <code>/setbday del</code>\n"
            f"⚡ <b>Test Card:</b> <code>/testbday</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    raw = message.command[1].lower()
    if raw in ("del", "remove", "off"):
        DB["birthdays"].get(cid, {}).pop(str(user.id), None)
        _save_db()
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🗑 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘 𝐑𝐄𝐌𝐎𝐕𝐄𝐃</b></blockquote>\n\n"
            f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    dt = _parse_dd_mm(raw)
    if not dt:
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐃𝐀𝐓𝐄</b></blockquote>\n\n"
            f"📅 <b>Sahi Format:</b> <code>/setbday 25-12</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    DB["birthdays"].setdefault(cid, {})[str(user.id)] = {"date": dt, "name": user.first_name}
    _save_db()
    await _send_html_pill_msg(
        client, message.chat.id,
        f"<blockquote><b>🎂 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘 𝐒𝐀𝐕𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"📅 <b>Date:</b> <code>{dt}</code> (Auto Custom Card)\n"
        f"⚡ <b>Preview:</b> <code>/testbday</code>\n\n{FOOTER}",
        reply_to=message.id,
    )

@bot.on_message(filters.group & filters.command(["setanni", "anniversary", "anni"], prefixes=["/", "!", "."]))
async def set_anniversary_cmd(client, message: Message):
    _ensure_scheduler()
    user = message.from_user
    if not user:
        return
    cid = str(message.chat.id)

    if len(message.command) < 2:
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>💍 𝐀𝐔𝐓𝐎 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘 𝐒𝐄𝐓𝐔𝐏</b></blockquote>\n\n"
            f"📅 <b>Format:</b> <code>/setanni 14-02</code> (DD-MM)\n"
            f"🗑 <b>Remove:</b> <code>/setanni del</code>\n"
            f"⚡ <b>Test Card:</b> <code>/testanni</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    raw = message.command[1].lower()
    if raw in ("del", "remove", "off"):
        DB["anniversaries"].get(cid, {}).pop(str(user.id), None)
        _save_db()
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>🗑 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘 𝐑𝐄𝐌𝐎𝐕𝐄𝐃</b></blockquote>\n\n"
            f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    dt = _parse_dd_mm(raw)
    if not dt:
        return await _send_html_pill_msg(
            client, message.chat.id,
            f"<blockquote><b>❌ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐃𝐀𝐓𝐄</b></blockquote>\n\n"
            f"📅 <b>Sahi Format:</b> <code>/setanni 14-02</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    DB["anniversaries"].setdefault(cid, {})[str(user.id)] = {"date": dt, "name": user.first_name}
    _save_db()
    await _send_html_pill_msg(
        client, message.chat.id,
        f"<blockquote><b>💍 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘 𝐒𝐀𝐕𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"📅 <b>Date:</b> <code>{dt}</code> (Auto Custom Card)\n"
        f"⚡ <b>Preview:</b> <code>/testanni</code>\n\n{FOOTER}",
        reply_to=message.id,
    )

# ── 4. AUTO DAILY GOOD MORNING / GOOD NIGHT (/dailyvibes) ─────
@bot.on_message(filters.group & filters.command(["dailyvibes", "gmgn", "vibes"], prefixes=["/", "!", "."]))
async def daily_vibes_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    arg = message.command[1].lower() if len(message.command) > 1 else ""

    if arg != "status" and message.from_user and not await _is_chat_admin(client, cid, message.from_user.id):
        return await _send_html_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Group Admins Daily GM/GN toggle kar sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if arg in ("on", "enable"):
        if cid not in DB["daily_vibes_chats"]:
            DB["daily_vibes_chats"].append(cid)
    elif arg in ("off", "disable"):
        if cid in DB["daily_vibes_chats"]:
            DB["daily_vibes_chats"].remove(cid)
    elif arg != "status":
        if cid in DB["daily_vibes_chats"]:
            DB["daily_vibes_chats"].remove(cid)
        else:
            DB["daily_vibes_chats"].append(cid)
    _save_db()

    is_on = cid in DB["daily_vibes_chats"]
    st = "ENABLED ✅ (7:00 AM & 10:30 PM)" if is_on else "DISABLED ❌"
    await _send_html_pill_msg(
        client, cid,
        f"<blockquote><b>🌅 𝐀𝐔𝐓𝐎 𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 / 𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⚡ <b>Control:</b> <code>/dailyvibes on</code> | <code>/dailyvibes off</code>\n"
        f"🖼 <b>Preview:</b> <code>/testgm</code> | <code>/testgn</code>\n\n{FOOTER}",
        reply_to=message.id,
    )
# ── 5. INSTANT CARD PREVIEW (/testbday, /testanni, /testbadge, /testgm, /testgn)
@bot.on_message(filters.command(["testbday", "testanni", "testbadge", "testgm", "testgn"], prefixes=["/", "!", "."]))
async def test_custom_cards_cmd(client, message: Message):
    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else message.from_user
    )
    if not target:
        return

    cmd = message.command[0].lower()
    today_dm = datetime.now(IST).strftime("%d-%m")
    dp = await _get_user_dp(client, target.id)

    if cmd == "testbday":
        tpl = await _fetch_custom_template("bday")
        card = await asyncio.to_thread(_compose_custom_template_card, "bday", tpl, dp, target.first_name, f"DATE : {today_dm}")
        cap = (
            f"<blockquote><b>🎂 𝐇𝐀𝐏𝐏𝐘 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘!</b></blockquote>\n\n"
            f"🎉 <b>Janamdin Mubarak Ho</b> <b>{html.escape(target.first_name)}</b>!\n\n{FOOTER}"
        )
    elif cmd == "testanni":
        tpl = await _fetch_custom_template("anni")
        card = await asyncio.to_thread(_compose_custom_template_card, "anni", tpl, dp, target.first_name, f"DATE : {today_dm}")
        cap = (
            f"<blockquote><b>💍 𝐇𝐀𝐏𝐏𝐘 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘!</b></blockquote>\n\n"
            f"❤️ <b>Dher Saari Badhai</b> <b>{html.escape(target.first_name)}</b>!\n\n{FOOTER}"
        )
    elif cmd == "testbadge":
        tpl = await _fetch_custom_template("badge")
        card = await asyncio.to_thread(_compose_custom_template_card, "badge", tpl, dp, target.first_name, "7-DAY ROYAL STREAK")
        cap = (
            f"<blockquote><b>🏅 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐀𝐂𝐊 & 𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄 𝐁𝐀𝐃𝐆𝐄!</b></blockquote>\n\n"
            f"👑 <b>Member:</b> <b>{html.escape(target.first_name)}</b>\n\n{FOOTER}"
        )
    elif cmd == "testgm":
        tpl = await _get_template_bg()
        card = _make_single_card(dp, "GOOD MORNING", "RISE & SHINE", "Have a Royal & Productive Day!", f"Date: {today_dm}", template_bg=tpl)
        cap = (
            f"<blockquote><b>🌅 𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 𝐄𝐕𝐄𝐑𝐘𝐎𝐍𝐄!</b></blockquote>\n\n"
            f"✨ <b>Nayi subah, nayi energy! Sabka din shubh ho!</b>\n\n{FOOTER}"
        )
    else:
        tpl = await _get_template_bg()
        card = _make_single_card(dp, "GOOD NIGHT", "SWEET DREAMS", "Relax, Chill & Recharge!", f"Night Vibes: {today_dm}", template_bg=tpl)
        cap = (
            f"<blockquote><b>🌙 𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓 𝐄𝐕𝐄𝐑𝐘𝐎𝐍𝐄!</b></blockquote>\n\n"
            f"💫 <b>Shubh Ratri! Kal phir milte hain full energy ke saath!</b>\n\n{FOOTER}"
        )

    await send_rich_card(client, message.chat.id, card, cap, json_rows=_html_pill_rows())

# ── 6. AUTO ROAST (/roast) & VIBE METER (/vibe) — 100% HTML PILL
@bot.on_message(filters.command(["roast"], prefixes=["/", "!", "."]))
async def auto_roast_pro_cmd(client, message: Message):
    target = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else message.from_user
    )
    if not target:
        return

    line = random.choice(ROAST_LINES)
    dp = await _get_user_dp(client, target.id)
    tpl = await _get_template_bg()
    card = _make_single_card(
        dp,
        "SAVAGE ROAST ALERT",
        _clean_text(target.first_name, 20),
        line[:34],
        "MODE : FULL FUNNY ROAST",
        template_bg=tpl,
    )
    cap = (
        f"<blockquote><b>🔥 𝐌𝐆𝐁 𝐀𝐔𝐓𝐎 𝐑𝐎𝐀𝐒𝐓 𝐂𝐀𝐑𝐃</b></blockquote>\n\n"
        f"🎯 <b>Target:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"😂 <b>Roast:</b> <code>{html.escape(line)}</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap, json_rows=_html_pill_rows())

@bot.on_message(filters.command(["vibe", "chem"], prefixes=["/", "!", "."]))
async def auto_vibe_pro_cmd(client, message: Message):
    u1 = message.from_user
    u2 = (
        message.reply_to_message.from_user
        if (message.reply_to_message and message.reply_to_message.from_user)
        else None
    )
    if not u1:
        return

    tpl = await _get_template_bg()
    if not u2 or u2.id == u1.id or _make_dual_card is None:
        pct = random.randint(74, 99)
        dp = await _get_user_dp(client, u1.id)
        card = _make_single_card(
            dp,
            f"VIBE METER : {pct}%",
            _clean_text(u1.first_name, 20),
            f"Aura Score: {pct}% ROYAL VIBE",
            "STATUS : UNSTOPPABLE",
            template_bg=tpl,
        )
        cap = (
            f"<blockquote><b>⚡ 𝐌𝐆𝐁 𝐀𝐔𝐓𝐎 𝐕𝐈𝐁𝐄 𝐂𝐀𝐑𝐃</b></blockquote>\n\n"
            f"👤 <b>Member:</b> <b>{html.escape(u1.first_name)}</b>\n"
            f"📊 <b>Vibe Meter:</b> <code>{pct}%</code>\n\n{FOOTER}"
        )
        return await send_rich_card(client, message.chat.id, card, cap, json_rows=_html_pill_rows())

    pct = random.randint(68, 99)
    dp1 = await _get_user_dp(client, u1.id)
    dp2 = await _get_user_dp(client, u2.id)
    card = _make_dual_card(
        dp1, dp2,
        f"{_clean_text(u1.first_name, 14)} ({pct}%)",
        _clean_text(u2.first_name, 16),
        template_bg=tpl,
    )
    cap = (
        f"<blockquote><b>💞 𝐌𝐆𝐁 𝐃𝐔𝐎 𝐕𝐈𝐁𝐄 𝐂𝐇𝐄𝐂𝐊</b></blockquote>\n\n"
        f"👥 <b>Duo:</b> <b>{html.escape(u1.first_name)}</b> × <b>{html.escape(u2.first_name)}</b>\n"
        f"⚡ <b>Match Vibe:</b> <code>{pct}% ROYAL BOND</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap, json_rows=_html_pill_rows())

# ── 7. DAILY AUTO SCHEDULER (GM, GN, BIRTHDAYS, ANNIVERSARIES)
async def _daily_auto_scheduler():
    while True:
        try:
            now = datetime.now(IST)
            today_ymd = now.strftime("%Y-%m-%d")
            today_dm = now.strftime("%d-%m")

            # Prune old sent_flags (>3 days) to keep JSON small
            cutoff = (now - timedelta(days=3)).strftime("%Y-%m-%d")
            stale = [k for k in DB["sent_flags"] if k[:10] < cutoff]
            if stale:
                for k in stale:
                    DB["sent_flags"].pop(k, None)
                _save_db()

            # A. Morning 07:00 - 07:10 AM IST
            if now.hour == 7 and now.minute <= 10:
                for cid in list(DB["daily_vibes_chats"]):
                    flag = f"{today_ymd}:gm:{cid}"
                    if not DB["sent_flags"].get(flag):
                        DB["sent_flags"][flag] = True
                        _save_db()
                        try:
                            dp = await _get_user_dp(bot, bot.me.id)
                            tpl = await _get_template_bg()
                            card = _make_single_card(dp, "GOOD MORNING", "RISE & SHINE", "Have a Royal & Productive Day!", f"Date: {today_dm}", template_bg=tpl)
                            await send_rich_card(
                                bot, cid, card,
                                f"<blockquote><b>🌅 𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 𝐄𝐕𝐄𝐑𝐘𝐎𝐍𝐄!</b></blockquote>\n\n"
                                f"✨ <b>Nayi subah, nayi energy! Sabka din shubh ho!</b>\n\n{FOOTER}",
                                json_rows=_html_pill_rows(),
                            )
                        except Exception:
                            pass

                for cid_str, users in list(DB["birthdays"].items()):
                    for uid_str, info in users.items():
                        if info.get("date") == today_dm:
                            flag = f"{today_ymd}:bday:{cid_str}:{uid_str}"
                            if not DB["sent_flags"].get(flag):
                                DB["sent_flags"][flag] = True
                                _save_db()
                                try:
                                    dp = await _get_user_dp(bot, int(uid_str))
                                    tpl = await _fetch_custom_template("bday")
                                    card = await asyncio.to_thread(_compose_custom_template_card, "bday", tpl, dp, info["name"], f"DATE : {today_dm}")
                                    await send_rich_card(
                                        bot, int(cid_str), card,
                                        f"<blockquote><b>🎂 𝐇𝐀𝐏𝐏𝐘 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘!</b></blockquote>\n\n"
                                        f"🎉 <b>Janamdin Mubarak Ho</b> <b>{html.escape(info['name'])}</b>!\n\n{FOOTER}",
                                        json_rows=_html_pill_rows(),
                                    )
                                except Exception:
                                    pass

                for cid_str, users in list(DB["anniversaries"].items()):
                    for uid_str, info in users.items():
                        if info.get("date") == today_dm:
                            flag = f"{today_ymd}:anni:{cid_str}:{uid_str}"
                            if not DB["sent_flags"].get(flag):
                                DB["sent_flags"][flag] = True
                                _save_db()
                                try:
                                    dp = await _get_user_dp(bot, int(uid_str))
                                    tpl = await _fetch_custom_template("anni")
                                    card = await asyncio.to_thread(_compose_custom_template_card, "anni", tpl, dp, info["name"], f"DATE : {today_dm}")
                                    await send_rich_card(
                                        bot, int(cid_str), card,
                                        f"<blockquote><b>💍 𝐇𝐀𝐏𝐏𝐘 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘!</b></blockquote>\n\n"
                                        f"❤️ <b>Dher Saari Badhai</b> <b>{html.escape(info['name'])}</b>!\n\n{FOOTER}",
                                        json_rows=_html_pill_rows(),
                                    )
                                except Exception:
                                    pass

            # B. Night 10:30 - 10:40 PM IST
            if now.hour == 22 and 30 <= now.minute <= 40:
                for cid in list(DB["daily_vibes_chats"]):
                    flag = f"{today_ymd}:gn:{cid}"
                    if not DB["sent_flags"].get(flag):
                        DB["sent_flags"][flag] = True
                        _save_db()
                        try:
                            dp = await _get_user_dp(bot, bot.me.id)
                            tpl = await _get_template_bg()
                            card = _make_single_card(dp, "GOOD NIGHT", "SWEET DREAMS", "Relax, Chill & Recharge!", f"Night Vibes: {today_dm}", template_bg=tpl)
                            await send_rich_card(
                                bot, cid, card,
                                f"<blockquote><b>🌙 𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓 𝐄𝐕𝐄𝐑𝐘𝐎𝐍𝐄!</b></blockquote>\n\n"
                                f"💫 <b>Shubh Ratri! Kal phir milte hain full energy ke saath!</b>\n\n{FOOTER}",
                                json_rows=_html_pill_rows(),
                            )
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(45)

# ── 8. MASTER WATCHER: PRO AUTO-CLEAN + ANTI-SPAM + WELCOME BACK & BADGE
def _is_media_or_link(msg: Message) -> bool:
    if any((msg.photo, msg.video, msg.animation, msg.sticker, msg.document, msg.audio, msg.voice, msg.video_note)):
        return True
    txt = msg.text or msg.caption or ""
    return bool(LINK_RE.search(txt))

@bot.on_message(filters.group, group=12)
async def master_group_auto_watcher(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    now_ts = time.time()
    clean_cfg = _get_clean_cfg(cid)
    spam_cfg = _get_spam_cfg(cid)

    # A. Instant Service Message Cleanup (Join / Leave / Pin alerts)
    if clean_cfg["enabled"] and clean_cfg.get("clean_service") and message.service:
        try:
            await message.delete()
            clean_cfg["cleaned_count"] = clean_cfg.get("cleaned_count", 0) + 1
        except Exception:
            pass
        return

    user = message.from_user
    is_admin = False
    if user and not user.is_bot and (clean_cfg.get("skip_admins") or spam_cfg["enabled"]):
        is_admin = await _is_chat_admin(client, cid, user.id)

    # B. Pro Auto-Clean Scheduler (30m default / custom timer / pin-safe / admin-safe / mode)
    if clean_cfg["enabled"]:
        should_clean = True
        if clean_cfg.get("skip_admins") and (is_admin or message.sender_chat):
            should_clean = False
        if clean_cfg.get("mode") == "media" and not _is_media_or_link(message):
            should_clean = False

        if should_clean:
            delay_sec = max(60, int(clean_cfg.get("minutes", DEFAULT_CLEAN_MIN)) * 60)

            async def _delayed_clean(msg: Message, chat_id: int, wait_s: int):
                await asyncio.sleep(wait_s)
                c_now = _get_clean_cfg(chat_id)
                if not c_now.get("enabled"):
                    return
                if c_now.get("keep_pinned"):
                    pinned_id = await _get_pinned_msg_id(client, chat_id)
                    if pinned_id and pinned_id == msg.id:
                        return
                try:
                    await msg.delete()
                    c_now["cleaned_count"] = c_now.get("cleaned_count", 0) + 1
                    if c_now["cleaned_count"] % 10 == 0:
                        _save_db()
                except Exception:
                    pass

            asyncio.create_task(_delayed_clean(message, cid, delay_sec))

    if not user or user.is_bot:
        return

    # C. Pro Anti-Spam / Anti-Link / 3-Strike Auto-Mute (Admins exempt)
    if spam_cfg["enabled"] and not is_admin:
        skey = (cid, user.id)
        reason = None

        # Link or forward spam check
        if spam_cfg.get("block_links"):
            txt = message.text or message.caption or ""
            if message.forward_date or LINK_RE.search(txt):
                reason = "Unauthorized Link / Forward Blocked"

        # Flood rate check
        if not reason:
            hits = [t for t in SPAM_HITS[skey] if now_ts - t <= SPAM_WINDOW_SEC]
            hits.append(now_ts)
            SPAM_HITS[skey] = hits
            if len(hits) >= int(spam_cfg.get("max_msgs", DEFAULT_SPAM_MAX)):
                SPAM_HITS[skey] = []
                reason = f"Flood Detected ({spam_cfg['max_msgs']} Msgs / {SPAM_WINDOW_SEC}s)"

        if reason:
            try:
                await message.delete()
            except Exception:
                pass
            spam_cfg["blocked_count"] = spam_cfg.get("blocked_count", 0) + 1
            SPAM_STRIKES[skey] += 1
            strikes = SPAM_STRIKES[skey]
            muted_note = ""

            if spam_cfg.get("auto_mute") and strikes >= 3:
                SPAM_STRIKES[skey] = 0
                try:
                    until = datetime.now(timezone.utc) + timedelta(minutes=5)
                    await client.restrict_chat_member(cid, user.id, ChatPermissions(can_send_messages=False), until_date=until)
                    muted_note = "\n🔇 <b>Action:</b> <code>Auto-Muted for 5 Minutes (3 Strikes)</code>"
                except Exception:
                    pass

            if now_ts - SPAM_COOLDOWN.get(skey, 0) >= 20 or muted_note:
                SPAM_COOLDOWN[skey] = now_ts
                _save_db()
                try:
                    dp = await _get_user_dp(client, user.id)
                    tpl = await _get_template_bg()
                    card = _make_single_card(dp, "ANTI-SPAM ALERT", _clean_text(user.first_name, 20), reason[:34], f"Strikes: {strikes}/3", template_bg=tpl)
                    await send_rich_card(
                        client, cid, card,
                        f"<blockquote><b>🛡 𝐌𝐆𝐁 𝐀𝐔𝐓𝐎 𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 𝐆𝐔𝐀𝐑𝐃</b></blockquote>\n\n"
                        f"⚠️ <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
                        f"🚫 <b>Reason:</b> <code>{html.escape(reason)}</code>{muted_note}\n\n{FOOTER}",
                        json_rows=_html_pill_rows(),
                    )
                except Exception:
                    pass
            return

    # D. Auto Welcome Back (3+ Days Inactive) & Daily Streak Milestone Badge (7 / 15 / 30 Days)
    cid_str, uid_str = str(cid), str(user.id)
    now_dt = datetime.now(IST)
    today_str = now_dt.strftime("%Y-%m-%d")
    yesterday_str = (now_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    chat_seen = DB["last_seen"].setdefault(cid_str, {})
    prev = chat_seen.get(uid_str)

    if prev:
        gap_days = (now_ts - float(prev.get("ts", now_ts))) / 86400.0
        prev_day = prev.get("day", "")
        streak = int(prev.get("streak", 1))

        if gap_days >= WELCOME_BACK_DAYS:
            streak = 1
            try:
                dp = await _get_user_dp(client, user.id)
                tpl = await _fetch_custom_template("badge")
                days_away = int(gap_days)
                card = await asyncio.to_thread(_compose_custom_template_card, "badge", tpl, dp, user.first_name, f"BACK AFTER {days_away} DAYS")
                await send_rich_card(
                    client, cid, card,
                    f"<blockquote><b>👑 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐓𝐇𝐄 𝐆𝐑𝐎𝐔𝐏!</b></blockquote>\n\n"
                    f"✨ <b>{html.escape(user.first_name)}</b> <code>{days_away} din</code> baad wapas aaye hain!\n\n{FOOTER}",
                    json_rows=_html_pill_rows(),
                )
            except Exception:
                pass
        elif prev_day != today_str:
            streak = (streak + 1) if prev_day == yesterday_str else 1
            if streak in STREAK_MILESTONES:
                badge_title = STREAK_MILESTONES[streak]
                try:
                    dp = await _get_user_dp(client, user.id)
                    tpl = await _fetch_custom_template("badge")
                    card = await asyncio.to_thread(_compose_custom_template_card, "badge", tpl, dp, user.first_name, badge_title)
                    await send_rich_card(
                        client, cid, card,
                        f"<blockquote><b>🏅 𝐀𝐔𝐓𝐎 𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄 𝐁𝐀𝐃𝐆𝐄 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃!</b></blockquote>\n\n"
                        f"👑 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
                        f"🔥 <b>Badge:</b> <code>{badge_title}</code>\n\n{FOOTER}",
                        json_rows=_html_pill_rows(),
                    )
                except Exception:
                    pass
    else:
        streak = 1

    chat_seen[uid_str] = {"ts": now_ts, "day": today_str, "streak": streak}
    _save_db()
    
