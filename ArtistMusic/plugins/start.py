# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Project      : MGB API Telegram Music Bot
# Powered By   : ❖ MGB NOT FREE ❖
# Type         : API Based Telegram Music Bot
#
# Bot          : @Yasmeen_api_bot
# Channel      : https://t.me/MGB_CODER
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import asyncio
import aiohttp
import json
from pyrogram import enums, filters, types

from ArtistMusic import app, config, db, lang, logger
from ArtistMusic.helpers import buttons, utils

# ----------------------------------------------------------
# 🎨 COLORFUL BUTTONS (DIRECT TELEGRAM API) 🎨
# ----------------------------------------------------------
_http = None

def _get_session():
    global _http
    if _http is None or _http.closed:
        _http = aiohttp.ClientSession()
    return _http

async def _send_start_colored(chat_id: int, photo_url: str, caption: str, buttons_list: list):
    """Bypasses Pyrogram limits to send colorful buttons directly via Telegram API."""
    if not config.BOT_TOKEN:
        return None

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"
    try:
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field("photo", photo_url)
        form.add_field("caption", caption)
        form.add_field("parse_mode", "HTML")
        form.add_field("reply_markup", json.dumps({"inline_keyboard": buttons_list}))

        timeout = aiohttp.ClientTimeout(total=30, connect=8)
        session = _get_session()
        async with session.post(url, data=form, timeout=timeout) as resp:
            data = await resp.json()
        if data.get("ok"):
            res = data["result"]
            return {"chat_id": res["chat"]["id"], "message_id": res["message_id"]}
        logger.warning(f"Start colored send failed: {data.get('description')}")
    except Exception as e:
        logger.warning(f"Start colored send error: {e}")
    return None

# ----------------------------------------------------------
# ✨ ANIMATION CONFIGURATION ✨
# ----------------------------------------------------------
_LOAD_FRAMES = [
    "⏳ <b>लोड़ हो रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■□□□□□□□□□</code>",
    "⌛ <b>डेटा कनेक्ट कर रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■□□□□□□</code>",
    "⏳ <b>इफ़ेक्ट्स स्टार्ट कर रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■■■■□□□</code>",
    "✨ <b>बॉट तैयार है!</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■■■■■■■</code>",
]

async def _loading_animation(message: types.Message):
    """Show animated loading bar."""
    try:
        msg = await message.reply_text(_LOAD_FRAMES[0])
        for frame in _LOAD_FRAMES[1:]:
            await asyncio.sleep(0.3)
            try:
                await msg.edit_text(frame)
            except Exception:
                break
        await asyncio.sleep(0.3)
        await msg.delete()
    except Exception:
        pass

# ----------------------------------------------------------
# 🤖 BOT COMMANDS 🤖
# ----------------------------------------------------------

@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    """Handle /start command with Colorful Buttons and Effects!"""
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass

    if not message.from_user:
        return

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        # 1. Show Loading Animation
        await _loading_animation(message)

    # 2. Text Preparation
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    # 3. Colorful Buttons Setup (Direct JSON format for Telegram API)
    # Change the URLs and Texts according to your needs.
    colorful_buttons = [
        [
            {"text": "➕ Add Me To Your Group", "url": f"https://t.me/{app.username}?startgroup=true", "style": "primary"} # Blue Button
        ],
        [
            {"text": "🛠 Help", "callback_data": "settings_help", "style": "success"}, # Green Button
            {"text": "⚙️ Source", "url": "https://t.me/MGB_CODER", "style": "danger"}, # Red Button
            {"text": "🌐 Langs", "callback_data": "settings_lang", "style": "primary"} # Blue Button
        ],
        [
            {"text": "🎧 Support", "url": "https://t.me/MGB_CODER", "style": "primary"},
            {"text": "📢 Channel", "url": "https://t.me/MGB_CODER", "style": "primary"}
        ]
    ]
    
    sent_data = None
    try:
        if config.START_IMG and config.START_IMG.strip():
            # Send using our custom Colored Button API
            sent_data = await _send_start_colored(
                chat_id=message.chat.id,
                photo_url=config.START_IMG,
                caption=_text,
                buttons_list=colorful_buttons
            )
        else:
            raise ValueError("No Photo provided in START_IMG")
    except Exception:
        # Fallback to normal Pyrogram if image fails
        key = buttons.start_key(message.lang, private)
        try:
            sent_msg = await message.reply_text(text=_text, reply_markup=key)
            sent_data = {"chat_id": sent_msg.chat.id, "message_id": sent_msg.id}
        except Exception:
            pass

    # 4. Final Reaction Effect (❤️‍🔥)
    if private and sent_data:
        try:
            await app.send_reaction(
                chat_id=sent_data["chat_id"],
                message_id=sent_data["message_id"],
                emoji="❤️‍🔥",
            )
        except Exception:
            pass

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)
