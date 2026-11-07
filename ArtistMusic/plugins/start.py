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
import random
from pyrogram import enums, errors, filters, types

from ArtistMusic import app, config, db, lang, logger
from ArtistMusic.helpers import utils

# ----------------------------------------------------------
# 🎨 SMART RICH MESSAGE API WITH COLORFUL HTML BUTTONS 🎨
# ----------------------------------------------------------

async def _send_rich_start(chat_id: int, photo_url: str, text: str):
    """Sends start message using the undocumented sendRichMessage API with colorful <tg-button> HTML"""
    if not config.BOT_TOKEN:
        return None

    safe_text = text.replace('\n', '<br>')
    
    # 🎨 VELOCITYBOTS STYLE COLOR-CODED HTML BUTTONS
    rich_body = (
        f"<blockquote>{safe_text}</blockquote><br><br>"
        
        # 1. Add Me To Group (Primary / Bright Blue)
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="https://t.me/{app.username}?startgroup=true">ㅤㅤAᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘㅤㅤ</tg-button>'
        f'</tg-button-row>'
        
        # 2. Help Button (Success / Green Style)
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="success" url="https://t.me/{app.username}?start=help">ㅤㅤHᴇʟᴘㅤㅤ</tg-button>'
        f'</tg-button-row>'
        
        # 3. Support & Channel Buttons (Primary & Danger Mix)
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="https://t.me/MGB_CODER">ㅤSᴜᴘᴘᴏʀᴛㅤ</tg-button>'
        f'<tg-button type="url" style="danger" url="https://t.me/MGB_CODER">ㅤCʜᴀɴɴᴇʟㅤ</tg-button>'
        f'</tg-button-row>'
    )

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
# ✨ ANIMATION & EFFECT CONFIGURATION ✨
# ----------------------------------------------------------
RAIN_EMOJIS = ["❤️", "🔥", "🥰", "❤️‍🔥", "💥", "🤩", "⚡️", "💯", "✨", "🏆"]

_LOAD_FRAMES = [
    "⏳ <b>लोड़ हो रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■□□□□□□□□□</code>",
    "⌛ <b>डेटा कनेक्ट कर रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■□□□□□□</code>",
    "⏳ <b>इफ़ेक्ट्स स्टार्ट कर रहा है...</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■■■■□□□</code>",
    "✨ <b>बॉट तैयार है!</b>\n<blockquote>⚡ MGB NOT FREE CODER ⚡</blockquote>\n<code>■■■■■■■■■■</code>",
]

async def _emoji_rain(message: types.Message):
    emoji = random.choice(RAIN_EMOJIS)
    try:
        await app.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=emoji,
            big=True,
        )
    except Exception:
        pass
    await asyncio.sleep(1.0)
    try:
        await app.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=None,
        )
    except Exception:
        pass

async def _loading_animation(message: types.Message):
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
# 🤖 BOT COMMANDS (START & HELP) 🤖
# ----------------------------------------------------------

@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    try:
        sent = await utils.reply(
            m,
            photo=config.START_IMG,
            caption=m.lang["help_menu"],
            reply_markup=None,
            quote=True,
        )
        if sent:
            await app.send_reaction(m.chat.id, sent.id, "👏")
    except Exception:
        pass


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

    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        await _emoji_rain(message)
        await _loading_animation(message)

    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    sent_data = None
    if config.START_IMG and config.START_IMG.strip():
        sent_data = await _send_rich_start(
            chat_id=message.chat.id,
            photo_url=config.START_IMG,
            text=_text
        )

    # Final Reaction Effect on Rich Message
    if private and sent_data and "message_id" in sent_data:
        try:
            cool_reactions = ["❤️‍🔥", "⚡", "🔥", "🥰", "🎉", "💖", "🍓"]
            selected_emoji = random.choice(cool_reactions)
            
            await asyncio.sleep(0.5)
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
                                    
