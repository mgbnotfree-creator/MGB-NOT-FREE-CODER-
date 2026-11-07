# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Project      : MGB API Telegram Music Bot
# Powered By   : ❖ MGB NOT FREE ❖
# Bot          : @Yasmeen_api_bot
# Channel      : https://t.me/MGB_CODER
# ==========================================================

import asyncio
import aiohttp
import random
import json
import html
from pyrogram import enums, filters, types

from ArtistMusic import app, config, db, lang, logger
from ArtistMusic.helpers import utils

# ----------------------------------------------------------
# 🎨 SMART RICH MESSAGE API (LIKE VELOCITYBOTS) 🎨
# ----------------------------------------------------------

async def _send_rich_start(chat_id: int, photo_url: str, text: str):
    """Sends start message using the undocumented sendRichMessage API with <tg-button> HTML"""
    if not config.BOT_TOKEN:
        return None

    # Text को HTML Format में बदलना
    safe_text = text.replace('\n', '<br>')
    
    # 🎨 HTML BUTTONS (बिना SOURCE और LANGS के, 100% Working Help Button)
    rich_body = (
        f"<blockquote>{safe_text}</blockquote><br><br>"
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="https://t.me/{app.username}?startgroup=true">ㅤㅤAᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘㅤㅤ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="success" url="https://t.me/{app.username}?start=help">ㅤㅤHᴇʟᴘㅤㅤ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="https://t.me/MGB_CODER">ㅤSᴜᴘᴘᴏʀᴛㅤ</tg-button>'
        f'<tg-button type="url" style="primary" url="https://t.me/MGB_CODER">ㅤCʜᴀɴɴᴇʟㅤ</tg-button>'
        f'</tg-button-row>'
    )

    # Rich Message का JSON डेटा
    rich_message = {
        "html": f'<img src="tg://photo?id=player_cover"/><br>{rich_body}',
        "media": [{
            "id": "player_cover",
            "media": {"type": "photo", "media": photo_url}
        }]
    }

    data = {
        "chat_id": chat_id,
        "rich_message": rich_message
    }

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendRichMessage"
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result["result"]
                else:
                    logger.warning(f"Rich Message Start failed: {result}")
    except Exception as e:
        logger.warning(f"Rich Message Start error: {e}")
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
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass

    if not message.from_user:
        return

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        await _loading_animation(message)

    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    sent_data = None
    if config.START_IMG and config.START_IMG.strip():
        # Call the new Smart Rich Message API
        sent_data = await _send_rich_start(
            chat_id=message.chat.id,
            photo_url=config.START_IMG,
            text=_text
        )
    
    # 🌟 EXTRA RANDOM REACTION EFFECTS
    if private and sent_data:
        try:
            cool_reactions = ["❤️‍🔥", "⚡", "🔥", "🥰", "🎉", "💖", "🍓"]
            selected_emoji = random.choice(cool_reactions)
            
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=sent_data["message_id"],
                emoji=selected_emoji,
            )
        except Exception as e:
            logger.debug(f"Reaction error: {e}")

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)
    
