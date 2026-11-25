# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Module       : 100% Automatic Broadcast Promotion Engine
# UI Style     : Permanent Colored HTML Buttons (Uniform 2x)
# Updates/Supp : https://t.me/mgb_not_free_coder
# Commands     : /autopromo, /addpromo, /promolist,
#                /delpromo, /setpromotime, /promonow
# ==========================================================
import asyncio
import inspect
import io
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from pymongo import AsyncMongoClient as AsyncIOMotorClient
from pyrogram import enums, filters
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    ChatWriteForbidden,
    FloodWait,
    PeerIdInvalid,
    UserIsBlocked,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import ArtistMusic
from ArtistMusic import app, config, logger

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    import httpx
except Exception:
    httpx = None

try:
    import aiohttp
except Exception:
    aiohttp = None

# ----------------------------------------------------------
# Branding & Auto Defaults (Live-Synced By mgb_brand_manager)
# ----------------------------------------------------------
OWNER_URL = "https://t.me/MGB_NOT_FREE_1"
UPDATES_URL = "https://t.me/mgb_not_free_coder"
SUPPORT_URL = "https://t.me/mgb_not_free_coder"
CHANNEL_HANDLE = "@mgb_not_free_coder"
POWERED_TEXT = "🍓 <b>Powered By :</b> @MGB_NOT_FREE_1"

DEFAULT_ENABLED = True        # 100% Automatic ON by default
DEFAULT_INTERVAL_MIN = 10     # Har 10 minute mein naya banner + text
MIN_INTERVAL_MIN = 2

_MONGO_DB = None
_BG_TASK: Optional[asyncio.Task] = None
_RUN_LOCK = asyncio.Lock()
_SEEN_CHATS: Set[int] = set()

_BTN_SUPPORTS_STYLE = (
    "style" in inspect.signature(InlineKeyboardButton.__init__).parameters
)

# ----------------------------------------------------------
# 6 Built-in Rotating Promotional Styles (New Every 10 Mins)
# ----------------------------------------------------------
DEFAULT_PROMOS: List[Dict[str, Any]] = [
    {
        "title": "NON-STOP HD MUSIC",
        "subtitle": "24x7 Lag-Free Voice Chat Streaming",
        "badge": "ULTRA HD AUDIO",
        "pattern": "circles",
        "accent": (0, 212, 255),
        "bg1": (8, 18, 42),
        "bg2": (12, 56, 98),
        "text": (
            "<blockquote>🎧 <b>MGB PREMIUM MUSIC EXPERIENCE</b></blockquote>\n\n"
            "✨ <b>Apne Group Ko Banayein Sabse Active!</b>\n"
            "• 🎵 <b>Crystal Clear HD Audio &amp; Video VC</b>\n"
            "• ⚡ <b>Zero Lag Fast Streaming Engine</b>\n"
            "• 🔥 <b>Autoplay + Fun Games + Smart Cards</b>\n\n"
            "👇 <b>Abhi Apne Group Mein Add Karein!</b>\n"
            "{powered}"
        ),
    },
    {
        "title": "VIP GROUP ENTERTAINMENT",
        "subtitle": "Music + Games + Interactive Cards",
        "badge": "ALL-IN-ONE BOT",
        "pattern": "diagonal",
        "accent": (255, 196, 0),
        "bg1": (28, 16, 8),
        "bg2": (82, 44, 10),
        "text": (
            "<blockquote>👑 <b>ALL-IN-ONE MUSIC &amp; FUN BOT</b></blockquote>\n\n"
            "🚀 <b>Sirf Music Nahi, Full Group Masti!</b>\n"
            "• 🎶 <code>/play</code> — Koi Bhi Gaana Turant Bajayein\n"
            "• 💍 <b>Fun Commands &amp; Couple Cards</b>\n"
            "• 🛡️ <b>24/7 Stable Cloud Server Uptime</b>\n\n"
            "💬 <b>Apne Doston Ko Bhi Invite Karein!</b>\n"
            "{powered}"
        ),
    },
    {
        "title": "SUPERFAST VC ENGINE",
        "subtitle": "Instant Queue • Auto-Next • High Quality",
        "badge": "LIVE 24/7",
        "pattern": "grid",
        "accent": (186, 95, 255),
        "bg1": (24, 10, 44),
        "bg2": (72, 20, 112),
        "text": (
            "<blockquote>⚡ <b>SUPERFAST VOICE CHAT STREAMING</b></blockquote>\n\n"
            "🔥 <b>Kya Aapke Group Mein Music Chal Raha Hai?</b>\n"
            "• 🎙️ <b>High-Bitrate Smooth Audio Output</b>\n"
            "• 📻 <b>Auto-Queue &amp; Continuous Playback</b>\n"
            "• 💎 <b>Official MGB API Powered Bot</b>\n\n"
            "👇 <b>Updates &amp; Support Ke Liye Join Karein!</b>\n"
            "{powered}"
        ),
    },
    {
        "title": "JOIN MGB OFFICIAL",
        "subtitle": "New Features • Updates • Fast Support",
        "badge": "MGB NETWORK",
        "pattern": "bars",
        "accent": (34, 224, 140),
        "bg1": (6, 30, 24),
        "bg2": (12, 78, 56),
        "text": (
            "<blockquote>🚀 <b>MGB NOT FREE — OFFICIAL NETWORK</b></blockquote>\n\n"
            "🌟 <b>Naye Features &amp; Bots Sabse Pehle Paayein!</b>\n"
            "• 📢 <b>Daily Updates &amp; New Plugins</b>\n"
            "• 🤖 <b>Custom Telegram Music &amp; Community Bots</b>\n"
            "• 🤝 <b>Fast Support Group Available</b>\n\n"
            "👇 <b>Official Channel &amp; Support Join Karein!</b>\n"
            "{powered}"
        ),
    },
    {
        "title": "NIGHT VIBES & DJ MODE",
        "subtitle": "Bollywood • Lo-Fi • Punjabi • Global Hits",
        "badge": "DJ VC MODE",
        "pattern": "rings",
        "accent": (255, 72, 128),
        "bg1": (36, 8, 22),
        "bg2": (96, 16, 50),
        "text": (
            "<blockquote>🎶 <b>NON-STOP VC PARTY &amp; LO-FI VIBES</b></blockquote>\n\n"
            "💃 <b>Bollywood, Punjabi, Lo-Fi ya Remix — Sab Milega!</b>\n"
            "• 🎧 <b>Just Type</b> <code>/play song name</code>\n"
            "• 🔊 <b>Clean Bass &amp; Studio Sound Quality</b>\n"
            "• ✨ <b>Smooth Controls &amp; Instant Skip</b>\n\n"
            "🔥 <b>VC Join Karein Aur Maza Lein!</b>\n"
            "{powered}"
        ),
    },
    {
        "title": "ADD ME TO YOUR GROUP",
        "subtitle": "Free Premium Music Bot For Every Group",
        "badge": "FREE TO USE",
        "pattern": "corners",
        "accent": (70, 175, 255),
        "bg1": (10, 22, 38),
        "bg2": (18, 64, 114),
        "text": (
            "<blockquote>💎 <b>FREE PREMIUM MUSIC BOT FOR GROUPS</b></blockquote>\n\n"
            "🎉 <b>Apne Khud Ke Group Mein Free Mein Lagayein!</b>\n"
            "• ✅ <b>100% Free &amp; Easy Admin Setup</b>\n"
            "• ✅ <b>Fast Search &amp; Zero Buffering</b>\n"
            "• ✅ <b>Trusted By Active Telegram Communities</b>\n\n"
            "👇 <b>Neeche Button Se Abhi Add Karein!</b>\n"
            "{powered}"
        ),
    },
]


# ----------------------------------------------------------
# Permissions, MongoDB & Brand Sync Helpers
# ----------------------------------------------------------
def _is_owner_or_sudo(user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    owner_id = int(getattr(config, "OWNER_ID", 0) or os.getenv("OWNER_ID", "0") or 0)
    app_owner = int(getattr(app, "owner", 0) or 0)
    sudoers = getattr(app, "sudoers", set()) or set()
    return user_id in (owner_id, app_owner) or user_id in sudoers


def _get_db():
    global _MONGO_DB
    if _MONGO_DB is not None:
        return _MONGO_DB
    mongo_uri = (
        getattr(config, "MONGO_URL", None)
        or getattr(config, "MONGO_DB_URI", None)
        or os.getenv("MONGO_URL")
        or os.getenv("MONGO_DB_URI")
    )
    if not mongo_uri:
        raise RuntimeError("MONGO_URL / MONGO_DB_URI missing!")
    client = AsyncIOMotorClient(mongo_uri)
    _MONGO_DB = client["MGB_AUTO_PROMO"]
    return _MONGO_DB


async def _get_settings() -> Dict[str, Any]:
    col = _get_db()["settings"]
    doc = await col.find_one({"_id": "config"})
    if not doc:
        doc = {
            "_id": "config",
            "enabled": DEFAULT_ENABLED,
            "interval_min": DEFAULT_INTERVAL_MIN,
            "auto_clean": True,
            "cursor": 0,
            "last_run_ts": 0,
            "last_sent": 0,
            "last_failed": 0,
            "total_rounds": 0,
        }
        await col.insert_one(doc)
    return doc


async def _update_settings(updates: Dict[str, Any]) -> None:
    col = _get_db()["settings"]
    await col.update_one({"_id": "config"}, {"$set": updates}, upsert=True)


def _apply_live_brand_text(text: str) -> str:
    """Apply mgb_brand_manager text rules if loaded."""
    bm = sys.modules.get("ArtistMusic.plugins.mgb_brand_manager")
    fn = getattr(bm, "_apply_text_replace", None) if bm else None
    if callable(fn):
        try:
            return fn(text)
        except Exception:
            pass
    return text


def _current_owner_handle() -> str:
    slug = OWNER_URL.rstrip("/").split("/")[-1]
    return f"@{slug}" if slug and not slug.startswith("+") else "@MGB_NOT_FREE_1"
# ----------------------------------------------------------
# Permanent Colored HTML Button Engine (Photo + Text + Panel)
# ----------------------------------------------------------
def _hbtn(
    text: str,
    url: Optional[str] = None,
    callback_data: Optional[str] = None,
    style: str = "primary",
) -> Dict[str, Any]:
    btn: Dict[str, Any] = {"text": text, "style": style}
    if url:
        btn["url"] = url
    if callback_data:
        btn["callback_data"] = callback_data
    return btn


def _promo_rows() -> List[List[Dict[str, Any]]]:
    bot_uname = getattr(app, "username", None) or "Yasmeen_api_bot"
    return [
        [
            _hbtn(
                "➕ ADD TO GROUP",
                url=f"https://t.me/{bot_uname}?startgroup=true",
                style="success",
            ),
            _hbtn("👑 OWNER", url=OWNER_URL, style="primary"),
        ],
        [
            _hbtn("🚀 UPDATES", url=UPDATES_URL, style="primary"),
            _hbtn("💬 SUPPORT", url=SUPPORT_URL, style="success"),
        ],
    ]


def _rows_to_pyro_markup(rows: List[List[Dict[str, Any]]]) -> InlineKeyboardMarkup:
    pyro_rows = []
    for row in rows:
        pyro_row = []
        for item in row:
            kw: Dict[str, Any] = {"text": item["text"]}
            if "url" in item:
                kw["url"] = item["url"]
            if "callback_data" in item:
                kw["callback_data"] = item["callback_data"]
            if _BTN_SUPPORTS_STYLE and item.get("style"):
                kw["style"] = item["style"]
            pyro_row.append(InlineKeyboardButton(**kw))
        pyro_rows.append(pyro_row)
    return InlineKeyboardMarkup(pyro_rows)


async def _bot_api_json(method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    bot_token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not bot_token:
        return {"ok": False}
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload)
                return r.json()
        if aiohttp is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=15) as r:
                    return await r.json()
    except Exception:
        return {"ok": False}
    return {"ok": False}


async def _bot_api_photo_upload(
    chat_id: int,
    raw_bytes: bytes,
    filename: str,
    caption: str,
    rows: List[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    bot_token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not bot_token:
        return {"ok": False}
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    rm_json = json.dumps({"inline_keyboard": rows})
    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.post(
                    url,
                    data={
                        "chat_id": str(chat_id),
                        "caption": caption,
                        "parse_mode": "HTML",
                        "reply_markup": rm_json,
                    },
                    files={"photo": (filename, raw_bytes, "image/png")},
                )
                return r.json()
        if aiohttp is not None:
            form = aiohttp.FormData()
            form.add_field("chat_id", str(chat_id))
            form.add_field("caption", caption)
            form.add_field("parse_mode", "HTML")
            form.add_field("reply_markup", rm_json)
            form.add_field(
                "photo",
                raw_bytes,
                filename=filename,
                content_type="image/png",
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form, timeout=25) as r:
                    return await r.json()
    except Exception:
        return {"ok": False}
    return {"ok": False}


async def _send_html_text(
    chat_id: int,
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
    reply_to_id: Optional[int] = None,
) -> Optional[int]:
    btn_rows = rows if rows is not None else _promo_rows()

    if _BTN_SUPPORTS_STYLE:
        msg = await app.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=_rows_to_pyro_markup(btn_rows),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_to_message_id=reply_to_id,
        )
        return msg.id if msg else None

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": btn_rows},
    }
    if reply_to_id:
        payload["reply_parameters"] = {
            "message_id": reply_to_id,
            "allow_sending_without_reply": True,
        }

    data = await _bot_api_json("sendMessage", payload)
    if data.get("ok") and isinstance(data.get("result"), dict):
        return int(data["result"]["message_id"])

    msg = await app.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=_rows_to_pyro_markup(btn_rows),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )
    return msg.id if msg else None


async def _edit_html_text(
    chat_id: int,
    msg_id: Optional[int],
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
) -> None:
    btn_rows = rows if rows is not None else _promo_rows()
    if not msg_id:
        await _send_html_text(chat_id, text, rows=btn_rows)
        return

    if _BTN_SUPPORTS_STYLE:
        try:
            await app.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
        return

    payload = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": btn_rows},
    }
    data = await _bot_api_json("editMessageText", payload)
    if not data.get("ok"):
        try:
            await app.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass


# ----------------------------------------------------------
# Dynamic HD Banner Generator (Non-Blocking Thread)
# ----------------------------------------------------------
def _load_font(size: int):
    font_paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    )
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _generate_promo_banner(
    promo: Dict[str, Any],
    round_num: int,
    bot_uname: str,
    channel_handle: str,
    owner_handle: str,
) -> Optional[bytes]:
    if not HAS_PIL:
        return None
    try:
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), promo["bg1"])
        draw = ImageDraw.Draw(img)

        r1, g1, b1 = promo["bg1"]
        r2, g2, b2 = promo["bg2"]
        accent = promo["accent"]
        soft_accent = (
            min(255, (r2 + accent[0]) // 2),
            min(255, (g2 + accent[1]) // 2),
            min(255, (b2 + accent[2]) // 2),
        )

        for y in range(h):
            ratio = y / float(h)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        pattern = promo.get("pattern", "circles")
        if pattern == "circles":
            draw.ellipse((-120, -120, 380, 380), outline=accent, width=3)
            draw.ellipse((w - 360, h - 360, w + 140, h + 140), outline=accent, width=3)
        elif pattern == "diagonal":
            for x in range(-200, w + 200, 140):
                draw.line([(x, 0), (x + 260, h)], fill=soft_accent, width=2)
        elif pattern == "grid":
            for x in range(80, w, 120):
                draw.line([(x, 48), (x, h - 48)], fill=soft_accent, width=1)
            for y in range(80, h, 120):
                draw.line([(48, y), (w - 48, y)], fill=soft_accent, width=1)
        elif pattern == "bars":
            for i in range(6):
                bx = w - 260 + i * 32
                bh = 140 + ((i * 55 + round_num * 20) % 240)
                draw.rounded_rectangle(
                    [(bx, h - 75 - bh), (bx + 18, h - 75)],
                    radius=8,
                    fill=accent if i % 2 == 0 else soft_accent,
                )
        elif pattern == "rings":
            for rad in (140, 220, 300):
                draw.ellipse(
                    (w - 220 - rad, h // 2 - rad, w - 220 + rad, h // 2 + rad),
                    outline=soft_accent,
                    width=3,
                )
        else:
            draw.rectangle([(48, 48), (180, 56)], fill=accent)
            draw.rectangle([(48, 48), (56, 180)], fill=accent)
            draw.rectangle([(w - 180, h - 56), (w - 48, h - 48)], fill=accent)
            draw.rectangle([(w - 56, h - 180), (w - 48, h - 48)], fill=accent)

        draw.rounded_rectangle(
            [(48, 48), (w - 48, h - 48)],
            radius=32,
            outline=accent,
            width=4,
        )

        badge_text = f"  {promo['badge']}  •  LIVE #{round_num}  "
        font_badge = _load_font(27)
        font_title = _load_font(64)
        font_sub = _load_font(35)
        font_brand = _load_font(29)

        draw.rounded_rectangle([(95, 95), (610, 155)], radius=28, fill=accent)
        draw.text((120, 109), badge_text, fill=(10, 12, 20), font=font_badge)

        draw.text((95, 220), promo["title"], fill=(255, 255, 255), font=font_title)
        draw.text((95, 318), promo["subtitle"], fill=(220, 232, 248), font=font_sub)
        draw.rectangle([(95, 400), (540, 408)], fill=accent)

        draw.text((95, 448), f"BOT : @{bot_uname}", fill=accent, font=font_sub)
        draw.text(
            (95, 514),
            f"UPDATES & SUPPORT : {channel_handle}",
            fill=(240, 245, 255),
            font=font_brand,
        )
        draw.text(
            (95, 588),
            f"POWERED BY MGB NOT FREE CODER  |  {owner_handle}",
            fill=(175, 195, 220),
            font=font_badge,
        )

        bio = io.BytesIO()
        img.save(bio, format="PNG", optimize=True)
        return bio.getvalue()
    except Exception as ex:
        logger.warning(f"⚠️ Promo banner generation failed: {ex}")
        return None


# ----------------------------------------------------------
# Auto Group Tracker & Promo Selector
# ----------------------------------------------------------
@app.on_message(filters.all, group=99)
async def _auto_tracker_and_wakeup(_, message: Message):
    if _BG_TASK is None or _BG_TASK.done():
        start_auto_broadcast_loop()

    try:
        if not message.chat or message.chat.type not in (
            enums.ChatType.GROUP,
            enums.ChatType.SUPERGROUP,
        ):
            return
        cid = message.chat.id
        logger_id = int(getattr(config, "LOGGER_ID", 0) or 0)
        if cid == logger_id or cid in _SEEN_CHATS:
            return
        _SEEN_CHATS.add(cid)
        await _get_db()["tracked_chats"].update_one(
            {"chat_id": cid},
            {
                "$set": {
                    "chat_id": cid,
                    "title": message.chat.title or "Group",
                    "last_seen": int(time.time()),
                }
            },
            upsert=True,
        )
    except Exception:
        pass


async def _get_target_chats() -> List[int]:
    chat_ids: Set[int] = set()
    logger_id = int(getattr(config, "LOGGER_ID", 0) or 0)

    try:
        docs = await _get_db()["tracked_chats"].find({}).to_list(length=5000)
        for d in docs:
            cid = d.get("chat_id")
            if isinstance(cid, int) and cid < 0:
                chat_ids.add(cid)
    except Exception:
        pass

    bot_db = getattr(ArtistMusic, "db", None)
    if bot_db is not None:
        for fn_name in ("get_chats", "get_served_chats"):
            fn = getattr(bot_db, fn_name, None)
            if callable(fn):
                try:
                    res = await fn()
                    for item in res or []:
                        cid = item.get("chat_id") if isinstance(item, dict) else item
                        if isinstance(cid, int) and cid < 0:
                            chat_ids.add(cid)
                except Exception:
                    pass

    chat_ids.discard(logger_id)
    return list(chat_ids)


async def _select_next_promo(
    cursor: int,
    round_num: int,
) -> Tuple[str, Optional[Any], str, int]:
    custom_col = _get_db()["custom_promos"]
    customs = await custom_col.find({}).sort("promo_id", 1).to_list(length=200)

    if customs:
        idx = cursor % len(customs)
        item = customs[idx]
        next_cursor = (idx + 1) % len(customs)
        caption = _apply_live_brand_text(
            item.get("caption") or f"📢 <b>MGB PROMOTION</b>\n\n{POWERED_TEXT}"
        )
        file_id = item.get("file_id")
        if file_id:
            return "custom", file_id, caption, next_cursor
        return "text", None, caption, next_cursor

    idx = cursor % len(DEFAULT_PROMOS)
    preset = DEFAULT_PROMOS[idx]
    next_cursor = (idx + 1) % len(DEFAULT_PROMOS)
    bot_uname = getattr(app, "username", None) or "Yasmeen_api_bot"
    caption = _apply_live_brand_text(preset["text"].format(powered=POWERED_TEXT))

    png_bytes = await asyncio.to_thread(
        _generate_promo_banner,
        preset,
        round_num,
        bot_uname,
        CHANNEL_HANDLE,
        _current_owner_handle(),
    )
    if png_bytes:
        return "generated", png_bytes, caption, next_cursor
    return "text", None, caption, next_cursor
# ----------------------------------------------------------
# Core Promotion Delivery (Colored HTML Buttons + Auto-Clean)
# ----------------------------------------------------------
async def _send_single_promo(
    cid: int,
    cached_file_id: Optional[str],
    raw_bytes: Optional[bytes],
    round_num: int,
    caption: str,
    btn_rows: List[List[Dict[str, Any]]],
    pyro_markup: InlineKeyboardMarkup,
) -> Tuple[Optional[int], Optional[str], str]:
    if not _BTN_SUPPORTS_STYLE and (httpx is not None or aiohttp is not None):
        for attempt in range(2):
            if cached_file_id:
                data = await _bot_api_json(
                    "sendPhoto",
                    {
                        "chat_id": cid,
                        "photo": cached_file_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                        "reply_markup": {"inline_keyboard": btn_rows},
                    },
                )
            elif raw_bytes:
                data = await _bot_api_photo_upload(
                    cid,
                    raw_bytes,
                    f"mgb_promo_{round_num}.png",
                    caption,
                    btn_rows,
                )
            else:
                data = await _bot_api_json(
                    "sendMessage",
                    {
                        "chat_id": cid,
                        "text": caption,
                        "parse_mode": "HTML",
                        "link_preview_options": {"is_disabled": True},
                        "reply_markup": {"inline_keyboard": btn_rows},
                    },
                )

            if data.get("ok") and isinstance(data.get("result"), dict):
                res = data["result"]
                new_fid = cached_file_id
                photos = res.get("photo")
                if not new_fid and isinstance(photos, list) and photos:
                    new_fid = photos[-1].get("file_id")
                return int(res["message_id"]), new_fid, "ok"

            err_code = data.get("error_code")
            desc = str(data.get("description") or "").lower()
            if err_code == 429 and attempt == 0:
                retry_s = min(int(data.get("parameters", {}).get("retry_after", 5)) + 2, 60)
                await asyncio.sleep(retry_s)
                continue
            if err_code == 403 or any(
                k in desc for k in ("chat not found", "kicked", "not enough rights", "have no rights")
            ):
                return None, cached_file_id, "fatal"
            break

    for attempt in range(2):
        try:
            if cached_file_id:
                msg = await app.send_photo(
                    chat_id=cid,
                    photo=cached_file_id,
                    caption=caption,
                    reply_markup=pyro_markup,
                    parse_mode=enums.ParseMode.HTML,
                )
            elif raw_bytes:
                bio = io.BytesIO(raw_bytes)
                bio.name = f"mgb_promo_{round_num}.png"
                msg = await app.send_photo(
                    chat_id=cid,
                    photo=bio,
                    caption=caption,
                    reply_markup=pyro_markup,
                    parse_mode=enums.ParseMode.HTML,
                )
                if msg and msg.photo:
                    cached_file_id = msg.photo.file_id
            else:
                msg = await app.send_message(
                    chat_id=cid,
                    text=caption,
                    reply_markup=pyro_markup,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            return (msg.id if msg else None), cached_file_id, "ok"
        except FloodWait as fw:
            if attempt == 0:
                await asyncio.sleep(min(int(fw.value) + 2, 60))
                continue
            return None, cached_file_id, "fail"
        except (
            ChatWriteForbidden,
            ChannelPrivate,
            ChatAdminRequired,
            PeerIdInvalid,
            UserIsBlocked,
        ):
            return None, cached_file_id, "fatal"
        except Exception:
            return None, cached_file_id, "fail"

    return None, cached_file_id, "fail"


async def run_promo_round(force: bool = False) -> Dict[str, int]:
    async with _RUN_LOCK:
        cfg = await _get_settings()
        if not force and not cfg.get("enabled", DEFAULT_ENABLED):
            return {"sent": 0, "failed": 0, "total": 0}

        chats = await _get_target_chats()
        if not chats:
            await _update_settings(
                {"last_run_ts": int(time.time()), "last_sent": 0, "last_failed": 0}
            )
            return {"sent": 0, "failed": 0, "total": 0}

        round_num = int(cfg.get("total_rounds", 0)) + 1
        cursor = int(cfg.get("cursor", 0))
        auto_clean = bool(cfg.get("auto_clean", True))

        mode, media_obj, caption, next_cursor = await _select_next_promo(
            cursor, round_num
        )
        btn_rows = _promo_rows()
        pyro_markup = _rows_to_pyro_markup(btn_rows)

        last_msg_col = _get_db()["last_messages"]
        tracked_col = _get_db()["tracked_chats"]

        cached_file_id: Optional[str] = media_obj if mode == "custom" else None
        raw_bytes: Optional[bytes] = media_obj if mode == "generated" else None

        sent = 0
        failed = 0

        for cid in chats:
            if auto_clean:
                try:
                    prev = await last_msg_col.find_one({"chat_id": cid})
                    if prev and prev.get("message_id"):
                        await app.delete_messages(cid, int(prev["message_id"]))
                except Exception:
                    pass

            msg_id, cached_file_id, status = await _send_single_promo(
                cid,
                cached_file_id,
                raw_bytes,
                round_num,
                caption,
                btn_rows,
                pyro_markup,
            )

            if status == "ok":
                sent += 1
                if msg_id:
                    try:
                        await last_msg_col.update_one(
                            {"chat_id": cid},
                            {
                                "$set": {
                                    "chat_id": cid,
                                    "message_id": msg_id,
                                    "ts": int(time.time()),
                                }
                            },
                            upsert=True,
                        )
                    except Exception:
                        pass
            elif status == "fatal":
                failed += 1
                _SEEN_CHATS.discard(cid)
                try:
                    await tracked_col.delete_one({"chat_id": cid})
                except Exception:
                    pass
            else:
                failed += 1

            await asyncio.sleep(0.35)

        await _update_settings(
            {
                "cursor": next_cursor,
                "last_run_ts": int(time.time()),
                "last_sent": sent,
                "last_failed": failed,
                "total_rounds": round_num,
            }
        )
        logger.info(
            f"📢 Auto Promo Round #{round_num} completed | Sent: {sent} | Failed: {failed}"
        )
        return {"sent": sent, "failed": failed, "total": len(chats)}


# ----------------------------------------------------------
# 100% Automatic Background Scheduler Loop
# ----------------------------------------------------------
async def _auto_promo_worker():
    await asyncio.sleep(20)
    logger.info("📢 MGB 100% Auto Broadcast Engine started (Every 10 mins).")
    while True:
        try:
            cfg = await _get_settings()
            if cfg.get("enabled", DEFAULT_ENABLED):
                interval_sec = (
                    max(
                        int(cfg.get("interval_min", DEFAULT_INTERVAL_MIN)),
                        MIN_INTERVAL_MIN,
                    )
                    * 60
                )
                last_ts = int(cfg.get("last_run_ts", 0))
                if int(time.time()) - last_ts >= interval_sec:
                    await run_promo_round(force=False)
        except asyncio.CancelledError:
            break
        except Exception as ex:
            logger.warning(f"⚠️ Auto promo loop error: {ex}")
        await asyncio.sleep(15)


def start_auto_broadcast_loop():
    global _BG_TASK
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    if _BG_TASK is None or _BG_TASK.done():
        _BG_TASK = loop.create_task(_auto_promo_worker())


try:
    asyncio.get_running_loop().call_soon(start_auto_broadcast_loop)
except RuntimeError:
    pass


# ----------------------------------------------------------
# Interactive Admin Control Panel (/autopromo)
# ----------------------------------------------------------
async def _build_panel() -> Tuple[str, List[List[Dict[str, Any]]]]:
    cfg = await _get_settings()
    enabled = bool(cfg.get("enabled", DEFAULT_ENABLED))
    interval = int(cfg.get("interval_min", DEFAULT_INTERVAL_MIN))
    auto_clean = bool(cfg.get("auto_clean", True))
    custom_count = await _get_db()["custom_promos"].count_documents({})
    target_count = len(await _get_target_chats())

    last_ts = int(cfg.get("last_run_ts", 0))
    last_ago = (
        f"{max(0, (int(time.time()) - last_ts) // 60)} min ago"
        if last_ts
        else "Starting Soon..."
    )

    mode_str = (
        f"Custom Pool ({custom_count} Banners)"
        if custom_count
        else f"Auto HD Cards ({len(DEFAULT_PROMOS)} Rotating Styles)"
    )

    text = (
        "<blockquote>📢 <b>MGB AUTO PROMOTION PANEL</b></blockquote>\n\n"
        f"• <b>Status:</b> {'🟢 AUTO RUNNING' if enabled else '🔴 STOPPED'}\n"
        f"• <b>Interval:</b> <code>Every {interval} Minutes</code>\n"
        f"• <b>Promo Source:</b> <code>{mode_str}</code>\n"
        f"• <b>Auto-Clean Old Promo:</b> {'✅ ON' if auto_clean else '❌ OFF'}\n"
        f"• <b>Target Groups:</b> <code>{target_count}</code>\n"
        f"• <b>Total Rounds:</b> <code>{cfg.get('total_rounds', 0)}</code>\n"
        f"• <b>Last Broadcast:</b> <code>{last_ago}</code> "
        f"(✅ {cfg.get('last_sent', 0)} | ❌ {cfg.get('last_failed', 0)})\n\n"
        "<b>Commands:</b>\n"
        "• <code>/addpromo</code> — Custom banner + text add karein\n"
        "• <code>/promolist</code> — Saved banners dekhein\n"
        "• <code>/delpromo &lt;id&gt;</code> — Banner delete karein\n"
        "• <code>/setpromotime &lt;min&gt;</code> — Timer badlein (default 10)\n"
        "• <code>/promonow</code> — Turant test broadcast chalayein\n\n"
        f"{POWERED_TEXT}"
    )

    rows = [
        [
            _hbtn(
                "⏸ STOP AUTO" if enabled else "▶️ START AUTO",
                callback_data="mgb_promo_toggle",
                style="danger" if enabled else "success",
            ),
            _hbtn("⚡ SEND NOW", callback_data="mgb_promo_now", style="primary"),
        ],
        [
            _hbtn(
                f"🧹 CLEAN: {'ON' if auto_clean else 'OFF'}",
                callback_data="mgb_promo_clean",
                style="primary",
            ),
            _hbtn("🔄 REFRESH", callback_data="mgb_promo_refresh", style="primary"),
        ],
        *_promo_rows(),
    ]
    return text, rows


# ----------------------------------------------------------
# Commands & Callbacks
# ----------------------------------------------------------
@app.on_message(filters.command(["autopromo", "autobroadcast", "promo"]))
async def auto_promo_panel_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return
    start_auto_broadcast_loop()
    text, rows = await _build_panel()
    await _send_html_text(message.chat.id, text, rows=rows, reply_to_id=message.id)


@app.on_callback_query(filters.regex("^mgb_promo_(toggle|now|clean|refresh)$"))
async def auto_promo_callbacks(_, cq: CallbackQuery):
    if not _is_owner_or_sudo(getattr(cq.from_user, "id", None)):
        return await cq.answer("Sirf Owner / Sudo users ke liye!", show_alert=True)

    start_auto_broadcast_loop()
    action = cq.data.split("_")[-1]
    cfg = await _get_settings()

    if action == "toggle":
        new_state = not bool(cfg.get("enabled", DEFAULT_ENABLED))
        await _update_settings({"enabled": new_state})
        await cq.answer(
            "Auto Promotion STARTED 🟢" if new_state else "Auto Promotion STOPPED 🔴",
            show_alert=True,
        )
    elif action == "clean":
        new_clean = not bool(cfg.get("auto_clean", True))
        await _update_settings({"auto_clean": new_clean})
        await cq.answer(f"Auto-Clean {'ON ✅' if new_clean else 'OFF ❌'}")
    elif action == "now":
        await cq.answer("⚡ Broadcast round shuru ho gaya...", show_alert=False)
        res = await run_promo_round(force=True)
        await cq.answer(
            f"✅ Sent: {res['sent']} | ❌ Failed: {res['failed']}",
            show_alert=True,
        )
    else:
        await cq.answer("Refreshed ✅")

    text, rows = await _build_panel()
    await _edit_html_text(cq.message.chat.id, cq.message.id, text, rows=rows)


@app.on_message(filters.command("addpromo"))
async def add_promo_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    file_id = None
    caption = ""

    if message.photo:
        file_id = message.photo.file_id
        raw = message.caption or ""
        parts = raw.split(None, 1)
        caption = parts[1].strip() if len(parts) > 1 else ""
    elif message.reply_to_message:
        rep = message.reply_to_message
        if rep.photo:
            file_id = rep.photo.file_id
        if len(message.command) > 1:
            caption = message.text.split(None, 1)[1].strip()
        else:
            caption = (rep.caption or rep.text or "").strip()
    elif len(message.command) > 1:
        caption = message.text.split(None, 1)[1].strip()

    if not file_id and not caption:
        return await _send_html_text(
            message.chat.id,
            "<blockquote>➕ <b>ADD NEW PROMO BANNER</b></blockquote>\n\n"
            "Kisi bhi <b>Photo + Promotional Text</b> par reply karke bhejein:\n"
            "<code>/addpromo</code>\n\n"
            "<i>Ya photo bhejte waqt caption mein likhein:</i>\n"
            "<code>/addpromo Aapka promotional text...</code>\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    col = _get_db()["custom_promos"]
    last_doc = await col.find_one(sort=[("promo_id", -1)])
    next_id = int(last_doc["promo_id"]) + 1 if last_doc else 1

    await col.insert_one(
        {
            "promo_id": next_id,
            "file_id": file_id,
            "caption": caption,
            "added_by": message.from_user.id,
            "added_at": int(time.time()),
        }
    )

    total = await col.count_documents({})
    await _send_html_text(
        message.chat.id,
        "<blockquote>✅ <b>NEW PROMO SAVED TO AUTO POOL!</b></blockquote>\n\n"
        f"• <b>Promo ID:</b> <code>#{next_id}</code>\n"
        f"• <b>Image Attached:</b> {'Yes 🖼️' if file_id else 'Text Only 📝'}\n"
        f"• <b>Total Custom Promos:</b> <code>{total}</code>\n\n"
        "<i>Ab har 10 minute mein automatic naya banner rotate hoga!</i>\n"
        f"{POWERED_TEXT}",
        reply_to_id=message.id,
    )


@app.on_message(filters.command("promolist"))
async def list_promos_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    docs = await _get_db()["custom_promos"].find({}).sort("promo_id", 1).to_list(length=100)
    if not docs:
        return await _send_html_text(
            message.chat.id,
            "<blockquote>📋 <b>PROMO LIST</b></blockquote>\n\n"
            "Abhi koi custom promo saved nahi hai.\n"
            f"Bot automatic <b>{len(DEFAULT_PROMOS)} HD MGB banners &amp; styles</b> rotate kar raha hai.\n\n"
            "Apna banner add karne ke liye photo par reply karke <code>/addpromo</code> bhejein.\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    lines = ["<blockquote>📋 <b>SAVED CUSTOM PROMOS</b></blockquote>\n"]
    for d in docs:
        pid = d["promo_id"]
        has_img = "🖼️" if d.get("file_id") else "📝"
        preview = (d.get("caption") or "No Caption").replace("\n", " ")[:48]
        lines.append(f"• <b>#{pid}</b> {has_img} — <code>{preview}...</code>")

    lines.append(f"\nDelete karne ke liye: <code>/delpromo &lt;id&gt;</code>\n{POWERED_TEXT}")
    await _send_html_text(message.chat.id, "\n".join(lines), reply_to_id=message.id)


@app.on_message(filters.command("delpromo"))
async def delete_promo_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_html_text(
            message.chat.id,
            f"Use karein: <code>/delpromo 1</code>\n\n{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    pid = int(message.command[1])
    res = await _get_db()["custom_promos"].delete_one({"promo_id": pid})
    if res.deleted_count:
        await _send_html_text(
            message.chat.id,
            f"<blockquote>🗑 <b>PROMO DELETED</b></blockquote>\n\n"
            f"Promo <code>#{pid}</code> delete kar diya gaya ✅\n\n{POWERED_TEXT}",
            reply_to_id=message.id,
        )
    else:
        await _send_html_text(
            message.chat.id,
            f"⚠️ Promo <code>#{pid}</code> nahi mila.\n\n{POWERED_TEXT}",
            reply_to_id=message.id,
        )


@app.on_message(filters.command("setpromotime"))
async def set_promo_time_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_html_text(
            message.chat.id,
            f"Use karein: <code>/setpromotime 10</code> (minimum {MIN_INTERVAL_MIN} min)\n\n{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    mins = max(int(message.command[1]), MIN_INTERVAL_MIN)
    await _update_settings({"interval_min": mins})
    await _send_html_text(
        message.chat.id,
        "<blockquote>⏱ <b>TIMER UPDATED</b></blockquote>\n\n"
        f"Auto Broadcast ab <b>Every {mins} Minutes</b> par chalega ✅\n\n{POWERED_TEXT}",
        reply_to_id=message.id,
    )


@app.on_message(filters.command("promonow"))
async def promo_now_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    wait_id = await _send_html_text(
        message.chat.id,
        f"<blockquote>⚡ <b>BROADCASTING PROMO...</b></blockquote>\n\n"
        f"Saare groups mein fresh HD banner bheja ja raha hai...\n\n{POWERED_TEXT}",
        reply_to_id=message.id,
    )
    res = await run_promo_round(force=True)
    await _edit_html_text(
        message.chat.id,
        wait_id,
        "<blockquote>📢 <b>PROMO ROUND COMPLETED</b></blockquote>\n\n"
        f"• <b>Total Groups:</b> <code>{res['total']}</code>\n"
        f"• <b>Sent Successfully:</b> <code>{res['sent']}</code> ✅\n"
        f"• <b>Failed / Removed:</b> <code>{res['failed']}</code> ❌\n\n"
        f"{POWERED_TEXT}",
    )
