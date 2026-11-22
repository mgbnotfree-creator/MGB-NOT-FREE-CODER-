# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#     ALL-IN-ONE AUTO SUITE (Custom Templates, 30m Clean, Guard)
# ═══════════════════════════════════════════════════════════════

import os
import io
import json
import time
import html
import asyncio
import unicodedata
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums
from pyrogram.types import Message, CallbackQuery

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
    edit_colored_msg,
)

# ── CUSTOM TEMPLATE URLS & DATA STORAGE ───────────────────────
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

ALL_CLEAN_DELAY_SEC = 30 * 60  # 30 Minutes (1800 Seconds)
SPAM_WINDOW_SEC = 5
SPAM_MAX_MSGS = 5
WELCOME_BACK_DAYS = 3
STREAK_MILESTONES = {7: "7-DAY LOYAL STAR", 15: "15-DAY VVIP LEGEND", 30: "30-DAY ROYAL KING"}

SPAM_HITS = defaultdict(list)
SPAM_COOLDOWN = {}
_SCHEDULER_TASK = None

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "χ": "X", "Χ": "X", "×": "X",
    "Δ": "A", "Σ": "E", "Ω": "O", "β": "B", "α": "A",
})

def _clean_text(val: str, limit: int = 24) -> str:
    s = str(val or "MGB VIP").translate(FANCY_MAP)
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    return " ".join(s.split()).strip()[:limit] or "MGB VIP"

def _default_db() -> dict:
    return {
        "allclean_chats": [],
        "antispam_chats": [],
        "daily_vibes_chats": [],
        "birthdays": {},       # chat_id -> {user_id: {"date": "DD-MM", "name": "..."}}
        "anniversaries": {},   # chat_id -> {user_id: {"date": "DD-MM", "name": "..."}}
        "last_seen": {},       # chat_id -> {user_id: {"ts": float, "day": "YYYY-MM-DD", "streak": int}}
        "sent_flags": {},      # "YYYY-MM-DD:kind:chat_id" -> True
    }

def _load_db() -> dict:
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = _default_db()
            base.update(data)
            return base
        except Exception:
            pass
    return _default_db()

DB = _load_db()

def _save_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _brand_rows() -> list:
    return [[
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]]

def _ensure_scheduler():
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK is None or _SCHEDULER_TASK.done():
        _SCHEDULER_TASK = asyncio.create_task(_daily_auto_scheduler())

# ── CUSTOM TEMPLATE DOWNLOADER & CRISP CARD COMPOSER ──────────
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

def _draw_crisp_pill_text(draw: ImageDraw.Draw, cx: int, cy: int, text: str, font, fill=(255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = int(cx - tw / 2)
    y = int(cy - th / 2 - bbox[1])
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        draw.text((x + ox, y + oy), text, font=font, fill=(10, 8, 22))
    draw.text((x, y), text, font=font, fill=fill)

def _compose_custom_template_card(tpl_img: Image.Image, dp_img: Image.Image, bar1_text: str, bar2_text: str) -> io.BytesIO:
    W, H = 1280, 720
    canvas = tpl_img.convert("RGBA").resize((W, H), Image.LANCZOS)

    # Center of left circular DP ring on 1280x720 custom templates
    ring_cx, ring_cy, dp_r = 314, 344, 152
    dp_size = dp_r * 2
    av = dp_img.convert("RGBA").resize((dp_size, dp_size), Image.LANCZOS)
    mask = Image.new("L", (dp_size, dp_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, dp_size, dp_size), fill=255)
    canvas.paste(av, (ring_cx - dp_r, ring_cy - dp_r), mask)

    # Subtle crisp rim inside ring so DP blends cleanly
    d = ImageDraw.Draw(canvas)
    d.ellipse((ring_cx - dp_r, ring_cy - dp_r, ring_cx + dp_r, ring_cy + dp_r), outline=(255, 225, 150, 220), width=4)

    # Crisp bold text centered inside the two right-side frosted/dark pill bars
    f1 = _load_bold_font(31)
    f2 = _load_bold_font(27)
    _draw_crisp_pill_text(d, 902, 468, _clean_text(bar1_text, 22), f1, fill=(255, 255, 255))
    _draw_crisp_pill_text(d, 902, 540, _clean_text(bar2_text, 26), f2, fill=(255, 232, 165))

    out = io.BytesIO()
    out.name = "mgb_custom_card.jpg"
    canvas.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out

# ── 1. 30-MINUTE ALL-MESSAGE AUTO-CLEAN (/allclean) ───────────
def _clean30_rows(is_on: bool) -> list:
    return [
        [
            _cbtn("✅ 𝐎𝐍 (𝟑𝟎 𝐌𝐈𝐍)" if not is_on else "🟢 𝐀𝐂𝐓𝐈𝐕𝐄 (𝟑𝟎 𝐌𝐈𝐍)", style="success", callback_data="mgb_c30_on"),
            _cbtn("❌ 𝐎𝐅𝐅" if is_on else "🔴 𝐎𝐅𝐅", style="danger", callback_data="mgb_c30_off"),
        ],
        [
            _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        ],
    ]

@bot.on_message(filters.group & filters.command(["allclean", "clean30", "groupclean"], prefixes=["/", "!", "."]))
async def allclean30_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    if cid in DB["allclean_chats"]:
        DB["allclean_chats"].remove(cid)
        is_on = False
    else:
        DB["allclean_chats"].append(cid)
        is_on = True
    _save_db()

    st = "ENABLED ✅ (30 Minutes)" if is_on else "DISABLED ❌"
    await send_colored_msg(
        client,
        cid,
        f"<blockquote><b>🧹 𝟑𝟎-𝐌𝐈𝐍 𝐀𝐋𝐋 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⏱ <b>Timer:</b> <code>30 Minutes (Every Message)</code>\n\n{FOOTER}",
        _clean30_rows(is_on),
        reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_c30_(on|off)$"))
async def allclean30_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    cid = query.message.chat.id
    is_on = mode == "on"
    if is_on and cid not in DB["allclean_chats"]:
        DB["allclean_chats"].append(cid)
    elif not is_on and cid in DB["allclean_chats"]:
        DB["allclean_chats"].remove(cid)
    _save_db()

    st = "ENABLED ✅ (30 Minutes)" if is_on else "DISABLED ❌"
    await query.answer(f"🧹 30-Min Auto-Clean {st}", show_alert=False)
    await edit_colored_msg(
        client,
        cid,
        query.message.id,
        f"<blockquote><b>🧹 𝟑𝟎-𝐌𝐈𝐍 𝐀𝐋𝐋 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⏱ <b>Timer:</b> <code>30 Minutes (Every Message)</code>\n\n{FOOTER}",
        _clean30_rows(is_on),
    )

# ── 2. AUTO ANTI-SPAM / FLOOD GUARD (/antispam) ───────────────
def _antispam_rows(is_on: bool) -> list:
    return [[
        _cbtn("🛡 𝐄𝐍𝐀𝐁𝐋𝐄" if not is_on else "🟢 𝐏𝐑𝐎𝐓𝐄𝐂𝐓𝐄𝐃", style="success", callback_data="mgb_as_on"),
        _cbtn("❌ 𝐃𝐈𝐒𝐀𝐁𝐋𝐄", style="danger", callback_data="mgb_as_off"),
    ]]

@bot.on_message(filters.group & filters.command(["antispam", "floodguard"], prefixes=["/", "!", "."]))
async def antispam_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    if cid in DB["antispam_chats"]:
        DB["antispam_chats"].remove(cid)
        is_on = False
    else:
        DB["antispam_chats"].append(cid)
        is_on = True
    _save_db()

    st = "ENABLED ✅" if is_on else "DISABLED ❌"
    await send_colored_msg(
        client,
        cid,
        f"<blockquote><b>🛡 𝐀𝐔𝐓𝐎 𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 / 𝐅𝐋𝐎𝐎𝐃 𝐆𝐔𝐀𝐑𝐃</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⚡ <b>Limit:</b> <code>{SPAM_MAX_MSGS} Msgs / {SPAM_WINDOW_SEC}s</code>\n\n{FOOTER}",
        _antispam_rows(is_on),
        reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_as_(on|off)$"))
async def antispam_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    cid = query.message.chat.id
    is_on = mode == "on"
    if is_on and cid not in DB["antispam_chats"]:
        DB["antispam_chats"].append(cid)
    elif not is_on and cid in DB["antispam_chats"]:
        DB["antispam_chats"].remove(cid)
    _save_db()

    st = "ENABLED ✅" if is_on else "DISABLED ❌"
    await query.answer(f"🛡 Anti-Spam {st}", show_alert=False)
    await edit_colored_msg(
        client,
        cid,
        query.message.id,
        f"<blockquote><b>🛡 𝐀𝐔𝐓𝐎 𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 / 𝐅𝐋𝐎𝐎𝐃 𝐆𝐔𝐀𝐑𝐃</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"⚡ <b>Limit:</b> <code>{SPAM_MAX_MSGS} Msgs / {SPAM_WINDOW_SEC}s</code>\n\n{FOOTER}",
        _antispam_rows(is_on),
    )
# ── 3. AUTO BIRTHDAY & ANNIVERSARY WISH CARDS + INSTANT TEST ──
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
    if len(message.command) < 2:
        return await send_colored_msg(
            client,
            message.chat.id,
            f"<blockquote><b>🎂 𝐀𝐔𝐓𝐎 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘 𝐒𝐄𝐓𝐔𝐏</b></blockquote>\n\n"
            f"📅 <b>Format:</b> <code>/setbday 15-08</code> (DD-MM)\n"
            f"⚡ <b>Test Card:</b> <code>/testbday</code>\n\n{FOOTER}",
            _brand_rows(),
            reply_to=message.id,
        )

    dt = _parse_dd_mm(message.command[1])
    if not dt:
        return await message.reply_text("❌ <b>Sahi date likhein! Example:</b> <code>/setbday 25-12</code>", parse_mode=enums.ParseMode.HTML)

    cid = str(message.chat.id)
    DB["birthdays"].setdefault(cid, {})[str(user.id)] = {"date": dt, "name": user.first_name}
    _save_db()

    await send_colored_msg(
        client,
        message.chat.id,
        f"<blockquote><b>🎂 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘 𝐒𝐀𝐕𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"📅 <b>Date:</b> <code>{dt}</code> (Auto Custom Card)\n\n{FOOTER}",
        _brand_rows(),
        reply_to=message.id,
    )

@bot.on_message(filters.group & filters.command(["setanni", "anniversary", "anni"], prefixes=["/", "!", "."]))
async def set_anniversary_cmd(client, message: Message):
    _ensure_scheduler()
    user = message.from_user
    if not user:
        return
    if len(message.command) < 2:
        return await send_colored_msg(
            client,
            message.chat.id,
            f"<blockquote><b>💍 𝐀𝐔𝐓𝐎 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘 𝐒𝐄𝐓𝐔𝐏</b></blockquote>\n\n"
            f"📅 <b>Format:</b> <code>/setanni 14-02</code> (DD-MM)\n"
            f"⚡ <b>Test Card:</b> <code>/testanni</code>\n\n{FOOTER}",
            _brand_rows(),
            reply_to=message.id,
        )

    dt = _parse_dd_mm(message.command[1])
    if not dt:
        return await message.reply_text("❌ <b>Sahi date likhein! Example:</b> <code>/setanni 14-02</code>", parse_mode=enums.ParseMode.HTML)

    cid = str(message.chat.id)
    DB["anniversaries"].setdefault(cid, {})[str(user.id)] = {"date": dt, "name": user.first_name}
    _save_db()

    await send_colored_msg(
        client,
        message.chat.id,
        f"<blockquote><b>💍 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘 𝐒𝐀𝐕𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"📅 <b>Date:</b> <code>{dt}</code> (Auto Custom Card)\n\n{FOOTER}",
        _brand_rows(),
        reply_to=message.id,
    )

@bot.on_message(filters.command(["testbday", "testanni", "testbadge"], prefixes=["/", "!", "."]))
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
        card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, target.first_name, f"DATE : {today_dm}")
        cap = (
            f"<blockquote><b>🎂 𝐇𝐀𝐏𝐏𝐘 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘!</b></blockquote>\n\n"
            f"🎉 <b>Janamdin Mubarak Ho</b> <b>{html.escape(target.first_name)}</b>!\n\n{FOOTER}"
        )
    elif cmd == "testanni":
        tpl = await _fetch_custom_template("anni")
        card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, target.first_name, f"DATE : {today_dm}")
        cap = (
            f"<blockquote><b>💍 𝐇𝐀𝐏𝐏𝐘 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘!</b></blockquote>\n\n"
            f"❤️ <b>Dher Saari Badhai</b> <b>{html.escape(target.first_name)}</b>!\n\n{FOOTER}"
        )
    else:
        tpl = await _fetch_custom_template("badge")
        card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, target.first_name, "7-DAY ROYAL STREAK")
        cap = (
            f"<blockquote><b>🏅 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐀𝐂𝐊 & 𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄 𝐁𝐀𝐃𝐆𝐄!</b></blockquote>\n\n"
            f"👑 <b>Member:</b> <b>{html.escape(target.first_name)}</b>\n\n{FOOTER}"
        )

    await send_rich_card(client, message.chat.id, card, cap)

# ── 4. AUTO DAILY GOOD MORNING / GOOD NIGHT (/dailyvibes) ─────
def _vibes_rows(is_on: bool) -> list:
    return [[
        _cbtn("🌅 𝐄𝐍𝐀𝐁𝐋𝐄 𝐆𝐌/𝐆𝐍" if not is_on else "🟢 𝐆𝐌/𝐆𝐍 𝐀𝐂𝐓𝐈𝐕𝐄", style="success", callback_data="mgb_dv_on"),
        _cbtn("❌ 𝐃𝐈𝐒𝐀𝐁𝐋𝐄", style="danger", callback_data="mgb_dv_off"),
    ]]

@bot.on_message(filters.group & filters.command(["dailyvibes", "gmgn", "vibes"], prefixes=["/", "!", "."]))
async def daily_vibes_cmd(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    if cid in DB["daily_vibes_chats"]:
        DB["daily_vibes_chats"].remove(cid)
        is_on = False
    else:
        DB["daily_vibes_chats"].append(cid)
        is_on = True
    _save_db()

    st = "ENABLED ✅ (7:00 AM & 10:30 PM)" if is_on else "DISABLED ❌"
    await send_colored_msg(
        client,
        cid,
        f"<blockquote><b>🌅 𝐀𝐔𝐓𝐎 𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 / 𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n\n{FOOTER}",
        _vibes_rows(is_on),
        reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_dv_(on|off)$"))
async def daily_vibes_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    cid = query.message.chat.id
    is_on = mode == "on"
    if is_on and cid not in DB["daily_vibes_chats"]:
        DB["daily_vibes_chats"].append(cid)
    elif not is_on and cid in DB["daily_vibes_chats"]:
        DB["daily_vibes_chats"].remove(cid)
    _save_db()

    st = "ENABLED ✅ (7:00 AM & 10:30 PM)" if is_on else "DISABLED ❌"
    await query.answer(f"🌅 Daily GM/GN {st}", show_alert=False)
    await edit_colored_msg(
        client,
        cid,
        query.message.id,
        f"<blockquote><b>🌅 𝐀𝐔𝐓𝐎 𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 / 𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n\n{FOOTER}",
        _vibes_rows(is_on),
    )

# ── 5. AUTO SCHEDULER (BIRTHDAY, ANNIVERSARY, GM & GN) ────────
async def _daily_auto_scheduler():
    while True:
        try:
            now = datetime.now(IST)
            today_ymd = now.strftime("%Y-%m-%d")
            today_dm = now.strftime("%d-%m")

            # A. Morning 07:00 - 07:10 AM IST -> Good Morning + Birthdays + Anniversaries
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
                                    card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, info["name"], f"DATE : {today_dm}")
                                    await send_rich_card(
                                        bot, int(cid_str), card,
                                        f"<blockquote><b>🎂 𝐇𝐀𝐏𝐏𝐘 𝐁𝐈𝐑𝐓𝐇𝐃𝐀𝐘!</b></blockquote>\n\n"
                                        f"🎉 <b>Janamdin Mubarak Ho</b> <b>{html.escape(info['name'])}</b>!\n\n{FOOTER}",
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
                                    card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, info["name"], f"DATE : {today_dm}")
                                    await send_rich_card(
                                        bot, int(cid_str), card,
                                        f"<blockquote><b>💍 𝐇𝐀𝐏𝐏𝐘 𝐀𝐍𝐍𝐈𝐕𝐄𝐑𝐒𝐀𝐑𝐘!</b></blockquote>\n\n"
                                        f"❤️ <b>Dher Saari Badhai</b> <b>{html.escape(info['name'])}</b>!\n\n{FOOTER}",
                                    )
                                except Exception:
                                    pass

            # B. Night 10:30 - 10:40 PM IST -> Good Night
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
                            )
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(45)

# ── 6. MASTER WATCHER: 30-MIN ALL-CLEAN + ANTI-SPAM + WELCOME BACK & BADGE
@bot.on_message(filters.group, group=12)
async def master_group_auto_watcher(client, message: Message):
    _ensure_scheduler()
    cid = message.chat.id
    now_ts = time.time()

    # A. 30-Minute All-Message Auto-Clean (Deletes EVERYTHING after 30 mins)
    if cid in DB["allclean_chats"]:
        async def _del_30m(msg: Message):
            await asyncio.sleep(ALL_CLEAN_DELAY_SEC)
            try:
                await msg.delete()
            except Exception:
                pass
        asyncio.create_task(_del_30m(message))

    user = message.from_user
    if not user or user.is_bot:
        return

    # B. Auto Anti-Spam / Flood Guard
    if cid in DB["antispam_chats"]:
        skey = (cid, user.id)
        hits = [t for t in SPAM_HITS[skey] if now_ts - t <= SPAM_WINDOW_SEC]
        hits.append(now_ts)
        SPAM_HITS[skey] = hits
        if len(hits) >= SPAM_MAX_MSGS:
            SPAM_HITS[skey] = []
            try:
                await message.delete()
            except Exception:
                pass
            if now_ts - SPAM_COOLDOWN.get(skey, 0) >= 20:
                SPAM_COOLDOWN[skey] = now_ts
                try:
                    dp = await _get_user_dp(client, user.id)
                    tpl = await _get_template_bg()
                    card = _make_single_card(dp, "ANTI-SPAM ALERT", user.first_name, "Flood Detected: Slow Down!", f"Limit: {SPAM_MAX_MSGS} Msgs / {SPAM_WINDOW_SEC}s", template_bg=tpl)
                    await send_rich_card(
                        client, cid, card,
                        f"<blockquote><b>🛡 𝐀𝐔𝐓𝐎 𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 𝐆𝐔𝐀𝐑𝐃</b></blockquote>\n\n"
                        f"⚠️ <b>Member:</b> <b>{html.escape(user.first_name)}</b> • Spam Cleaned!\n\n{FOOTER}",
                    )
                except Exception:
                    pass
            return

    # C. Auto Welcome Back (3+ Days Inactive) & Daily Streak Milestone Badge (7 / 15 / 30 Days)
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
                card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, user.first_name, f"BACK AFTER {days_away} DAYS")
                await send_rich_card(
                    client, cid, card,
                    f"<blockquote><b>👑 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐓𝐇𝐄 𝐆𝐑𝐎𝐔𝐏!</b></blockquote>\n\n"
                    f"✨ <b>{html.escape(user.first_name)}</b> <code>{days_away} din</code> baad wapas aaye hain!\n\n{FOOTER}",
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
                    card = await asyncio.to_thread(_compose_custom_template_card, tpl, dp, user.first_name, badge_title)
                    await send_rich_card(
                        client, cid, card,
                        f"<blockquote><b>🏅 𝐀𝐔𝐓𝐎 𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄 𝐁𝐀𝐃𝐆𝐄 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃!</b></blockquote>\n\n"
                        f"👑 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
                        f"🔥 <b>Badge:</b> <code>{badge_title}</code>\n\n{FOOTER}",
                    )
                except Exception:
                    pass
    else:
        streak = 1

    chat_seen[uid_str] = {"ts": now_ts, "day": today_str, "streak": streak}
    _save_db()
  
