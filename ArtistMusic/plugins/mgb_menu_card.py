# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Module       : Interactive VIP Command Menu Card
# UI Style     : Permanent Colored HTML Buttons (Uniform 2x)
# Powered By   : ❖ MGB NOT FREE ❖
# Commands     : /menu, /commands, /cmd
# ==========================================================
import inspect
import os
from typing import Any, Dict, List, Optional, Tuple

from pyrogram import enums, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ArtistMusic import app, config

try:
    import httpx
except Exception:
    httpx = None

try:
    import aiohttp
except Exception:
    aiohttp = None

# ----------------------------------------------------------
# Branding (Auto-Synced Live By mgb_brand_manager.py)
# ----------------------------------------------------------
OWNER_URL = "https://t.me/MGB_NOT_FREE_1"
UPDATES_URL = "https://t.me/mgb_not_free_coder"
SUPPORT_URL = "https://t.me/mgb_not_free_coder"
POWERED_TEXT = "🍓 <b>Powered By :</b> @MGB_NOT_FREE_1"

_BTN_SUPPORTS_STYLE = (
    "style" in inspect.signature(InlineKeyboardButton.__init__).parameters
)


# ----------------------------------------------------------
# Permission & HTML Button Engine
# ----------------------------------------------------------
def _is_owner_or_sudo(user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    owner_id = int(getattr(config, "OWNER_ID", 0) or os.getenv("OWNER_ID", "0") or 0)
    app_owner = int(getattr(app, "owner", 0) or 0)
    sudoers = getattr(app, "sudoers", set()) or set()
    return user_id in (owner_id, app_owner) or user_id in sudoers


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


def _brand_rows() -> List[List[Dict[str, Any]]]:
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


async def _bot_api_post(method: str, payload: Dict[str, Any]) -> bool:
    bot_token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not bot_token:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(url, json=payload)
                return r.status_code == 200 and r.json().get("ok", False)
        if aiohttp is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=12) as r:
                    data = await r.json()
                    return r.status == 200 and data.get("ok", False)
    except Exception:
        return False
    return False


async def _send_html_card(
    message: Message,
    text: str,
    rows: List[List[Dict[str, Any]]],
) -> None:
    if _BTN_SUPPORTS_STYLE:
        await message.reply_text(
            text,
            reply_markup=_rows_to_pyro_markup(rows),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    payload: Dict[str, Any] = {
        "chat_id": message.chat.id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": rows},
        "reply_parameters": {
            "message_id": message.id,
            "allow_sending_without_reply": True,
        },
    }
    ok = await _bot_api_post("sendMessage", payload)
    if not ok:
        await message.reply_text(
            text,
            reply_markup=_rows_to_pyro_markup(rows),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def _edit_html_card(
    cq: CallbackQuery,
    text: str,
    rows: List[List[Dict[str, Any]]],
) -> None:
    if _BTN_SUPPORTS_STYLE:
        try:
            await cq.message.edit_text(
                text,
                reply_markup=_rows_to_pyro_markup(rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
        return

    payload = {
        "chat_id": cq.message.chat.id,
        "message_id": cq.message.id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": rows},
    }
    ok = await _bot_api_post("editMessageText", payload)
    if not ok:
        try:
            await cq.message.edit_text(
                text,
                reply_markup=_rows_to_pyro_markup(rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass


# ----------------------------------------------------------
# Menu Page Templates (Formatted Live With Updated Branding)
# ----------------------------------------------------------
MENU_TEMPLATES: Dict[str, str] = {
    "home": (
        "<blockquote>💎 <b>MGB VIP COMMAND MENU CARD</b></blockquote>\n\n"
        "✨ <b>Neeche kisi bhi category button par tap karein aur saare commands dekhein:</b>\n\n"
        "• 🎵 <b>Music &amp; VC Pro</b> — Audio, Video, DJ &amp; Filters\n"
        "• 🎮 <b>Fun &amp; Party Games</b> — Adalat, Mafia, Truth/Dare\n"
        "• 📸 <b>Social &amp; Viral Cards</b> — Tweet, Insta, Passport, News\n"
        "• 💰 <b>Economy &amp; Shop</b> — Daily Coins, Wallet, Confess\n"
        "• ⚙️ <b>Auto Suite &amp; Tools</b> — Clean, AntiSpam, Reels, Score\n"
        "• 👑 <b>Owner Control</b> — Assistants, Auto Promo &amp; Brand\n\n"
        "{powered}"
    ),
    "music": (
        "<blockquote>🎵 <b>MUSIC &amp; VC PRO STUDIO</b></blockquote>\n\n"
        "<b>Core Playback:</b>\n"
        "• <code>/play</code> | <code>/vplay</code> — Audio / Video stream\n"
        "• <code>/playforce</code> | <code>/vplayforce</code> — Force play\n"
        "• <code>/pause</code> | <code>/resume</code> | <code>/skip</code>\n"
        "• <code>/stop</code> | <code>/end</code> | <code>/queue</code> | <code>/shuffle</code>\n"
        "• <code>/loop</code> | <code>/seek</code> | <code>/seekback</code>\n\n"
        "<b>Channel &amp; VC Studio:</b>\n"
        "• <code>/cplay</code> | <code>/cvplay</code> | <code>/channelplay</code>\n"
        "• <code>/karaoke</code> — Karaoke, Bass &amp; Slowed filters\n"
        "• <code>/entry</code> | <code>/sfx</code> — VC Entry BGM &amp; Meme SFX\n"
        "• <code>/dedicate</code> — Dual-DP Song Dedication card\n"
        "• <code>/sleeptimer</code> — Night VC auto-stop timer\n"
        "• <code>/djvote</code> | <code>/vote</code> | <code>/voteskip</code>\n\n"
        "{powered}"
    ),
    "games": (
        "<blockquote>🎮 <b>FUN &amp; PARTY GAMES</b></blockquote>\n\n"
        "<b>Group Adalat (Courtroom):</b>\n"
        "• <code>/case</code> — Naya courtroom trial shuru karein\n"
        "• <code>/guilty</code> | <code>/innocent</code> — Vote daalein\n"
        "• <code>/verdict</code> — Final faisla sunayein\n\n"
        "<b>Chor-Police (Mafia Game):</b>\n"
        "• <code>/mafia</code> | <code>/join</code> | <code>/startmafia</code>\n"
        "• <code>/suspect</code> | <code>/endmafia</code>\n\n"
        "<b>Classic Fun &amp; Romance:</b>\n"
        "• <code>/marry</code> | <code>/divorce</code> — Group marriage card\n"
        "• <code>/truth</code> | <code>/dare</code> | <code>/rps</code> | <code>/quiz</code>\n"
        "• <code>/roast</code> | <code>/vibe</code> | <code>/shipday</code>\n\n"
        "{powered}"
    ),
    "social": (
        "<blockquote>📸 <b>SOCIAL STUDIO &amp; VIRAL CARDS</b></blockquote>\n\n"
        "<b>Fake Social Cards:</b>\n"
        "• <code>/tweet</code> — Verified X / Twitter post card\n"
        "• <code>/insta</code> — Verified Instagram post card\n"
        "• <code>/fakechat</code> — Leaked WhatsApp chat card\n"
        "• <code>/paycard</code> — Royal Bank prank payment card\n"
        "• <code>/passport</code> — VIP Passport with QR code\n\n"
        "<b>Viral &amp; Profile Cards:</b>\n"
        "• <code>/news</code> | <code>/wanted</code> | <code>/q</code>\n"
        "• <code>/profile</code> | <code>/top</code> | <code>/vcstats</code>\n"
        "• <code>/setbday</code> | <code>/setanni</code> — Auto wish cards\n"
        "• <code>/testbday</code> | <code>/testanni</code> | <code>/testbadge</code>\n"
        "• <code>/testgm</code> | <code>/testgn</code> — Preview cards\n\n"
        "{powered}"
    ),
    "eco": (
        "<blockquote>💰 <b>ECONOMY, CARD SHOP &amp; CONFESS</b></blockquote>\n\n"
        "<b>MGB Coins &amp; VIP Shop:</b>\n"
        "• <code>/daily</code> — Daily streak coin bonus claim karein\n"
        "• <code>/wallet</code> — Apne coins aur custom card dekhein\n"
        "• <code>/shop</code> — Themes, rings &amp; VIP tags dekhein\n"
        "• <code>/buy</code> — Shop item khareedein (1–6)\n"
        "• <code>/equip</code> — Owned VIP style apply karein\n"
        "• <code>/give</code> — Kisi member ko coins bhejein\n"
        "• <code>/rich</code> — Top 5 richest leaderboard\n\n"
        "<b>Secret Confession Box:</b>\n"
        "• <code>/setconfess</code> — Group mein confession ON/OFF\n"
        "• <code>/confess</code> — 100% anonymous confession card\n\n"
        "{powered}"
    ),
    "tools": (
        "<blockquote>⚙️ <b>AUTO SUITE &amp; GROUP TOOLS</b></blockquote>\n\n"
        "<b>Group Protection &amp; Auto Cards:</b>\n"
        "• <code>/autoclean</code> — Bot commands auto-delete\n"
        "• <code>/allclean</code> — 30 min auto message cleaner\n"
        "• <code>/antispam</code> — Flood guard &amp; warning card\n"
        "• <code>/dailyvibes</code> — Auto Good Morning / Night card\n"
        "• <code>/tagall</code> — Sabhi members ko mention karein\n\n"
        "<b>Smart Utilities:</b>\n"
        "• <code>/afk</code> — Smart AFK status card\n"
        "• <code>/whisper</code> — Group mein private secret message\n"
        "• <code>/dl</code> — Instagram Reels &amp; YT Shorts download\n"
        "• <code>/score</code> — Live cricket scorecard\n"
        "• <code>/ping</code> | <code>/stats</code> — Bot health &amp; uptime\n\n"
        "{powered}"
    ),
    "owner": (
        "<blockquote>👑 <b>OWNER &amp; SUDO MASTER PANEL</b></blockquote>\n\n"
        "<b>Dynamic Assistant Manager:</b>\n"
        "• <code>/addass</code> — String session se live assistant add\n"
        "• <code>/loginass</code> — DM mein Phone + OTP login\n"
        "• <code>/asslist</code> | <code>/delass</code> — Manage assistants\n\n"
        "<b>10-Min Auto Broadcast Promotion:</b>\n"
        "• <code>/autopromo</code> — Live promotion control panel\n"
        "• <code>/addpromo</code> | <code>/promolist</code> | <code>/delpromo</code>\n"
        "• <code>/setpromotime</code> | <code>/promonow</code>\n\n"
        "<b>Global Brand &amp; Ban Recovery:</b>\n"
        "• <code>/brand</code> — Global live link panel\n"
        "• <code>/setall</code> — Owner + Channel + Group 1-click update\n"
        "• <code>/setchannel</code> | <code>/setgroup</code> | <code>/setownerlink</code>\n"
        "• <code>/replace</code> | <code>/delreplace</code> — Global text replace\n"
        "• <code>/claimowner</code> — Secret key takeover (DM only)\n\n"
        "{powered}"
    ),
      }
# ----------------------------------------------------------
# Uniform 2-Column Keyboard Layouts & Handlers
# ----------------------------------------------------------
def _build_menu_page(page: str) -> Tuple[str, List[List[Dict[str, Any]]]]:
    tpl = MENU_TEMPLATES.get(page, MENU_TEMPLATES["home"])
    text = tpl.format(powered=POWERED_TEXT)

    if page == "home":
        rows = [
            [
                _hbtn("🎵 MUSIC & VC", callback_data="mgb_menu_music", style="primary"),
                _hbtn("🎮 FUN & GAMES", callback_data="mgb_menu_games", style="success"),
            ],
            [
                _hbtn("📸 SOCIAL CARDS", callback_data="mgb_menu_social", style="primary"),
                _hbtn("💰 ECO & SHOP", callback_data="mgb_menu_eco", style="success"),
            ],
            [
                _hbtn("⚙️ AUTO & TOOLS", callback_data="mgb_menu_tools", style="primary"),
                _hbtn("👑 OWNER PANEL", callback_data="mgb_menu_owner", style="danger"),
            ],
            *_brand_rows(),
        ]
        return text, rows

    rows = [
        [
            _hbtn("⬅️ BACK TO MENU", callback_data="mgb_menu_home", style="primary"),
            _hbtn("❌ CLOSE", callback_data="mgb_menu_close", style="danger"),
        ],
        [
            _hbtn("👑 OWNER", url=OWNER_URL, style="primary"),
            _hbtn("🚀 UPDATES", url=UPDATES_URL, style="success"),
        ],
    ]
    return text, rows


@app.on_message(filters.command(["menu", "commands", "cmd"]))
async def vip_menu_card_cmd(_, message: Message):
    text, rows = _build_menu_page("home")
    await _send_html_card(message, text, rows)


@app.on_callback_query(
    filters.regex("^mgb_menu_(home|music|games|social|eco|tools|owner|close)$")
)
async def vip_menu_card_cb(_, cq: CallbackQuery):
    page = cq.data.split("_")[-1]

    if page == "close":
        try:
            await cq.message.delete()
        except Exception:
            pass
        return await cq.answer("Menu closed ❌")

    if page == "owner" and not _is_owner_or_sudo(getattr(cq.from_user, "id", None)):
        return await cq.answer("🔒 Ye panel sirf Owner / Sudo users ke liye hai!", show_alert=True)

    text, rows = _build_menu_page(page)
    await _edit_html_card(cq, text, rows)
    await cq.answer()
