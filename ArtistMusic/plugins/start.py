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
# ==========================================================

import asyncio
import random
import aiohttp
from pyrogram import enums, errors, filters, types
from pyrogram import StopPropagation  # 🚀 Added to intercept old buttons!

from ArtistMusic import app, config, db, lang, logger
from ArtistMusic.helpers import buttons, utils

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
        await app.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji, big=True)
    except Exception:
        pass
    await asyncio.sleep(1.0)
    try:
        await app.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=None)
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
# 🎨 SMART RICH MESSAGE API WITH COLORFUL HTML BUTTONS 🎨
# ----------------------------------------------------------

async def _send_rich_start(chat_id: int, photo_url: str, text: str):
    if not config.BOT_TOKEN: return None
    safe_text = text.replace('\n', '<br>')
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
        f'<tg-button type="url" style="danger" url="https://t.me/MGB_CODER">ㅤCʜᴀɴɴᴇʟㅤ</tg-button>'
        f'</tg-button-row>'
    )
    rich_message = {
        "html": f'<img src="tg://photo?id=player_cover"/><br>{rich_body}',
        "media": [{"id": "player_cover", "media": {"type": "photo", "media": photo_url}}]
    }
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendRichMessage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"chat_id": chat_id, "rich_message": rich_message}) as resp:
                result = await resp.json()
                if result.get("ok"): return result["result"]
    except Exception: pass
    return None

async def _send_rich_help(chat_id: int, photo_url: str, text: str, html_buttons: str):
    if not config.BOT_TOKEN: return None
    safe_text = text.replace('\n', '<br>')
    rich_body = f"<blockquote>{safe_text}</blockquote><br><br>{html_buttons}"
    rich_message = {
        "html": f'<img src="tg://photo?id=help_cover"/><br>{rich_body}',
        "media": [{"id": "help_cover", "media": {"type": "photo", "media": photo_url}}]
    }
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendRichMessage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"chat_id": chat_id, "rich_message": rich_message}) as resp:
                result = await resp.json()
                if result.get("ok"): return result["result"]
    except Exception: pass
    return None


# ----------------------------------------------------------
# 🚀 SUPER OVERRIDES (FIXES GREY BUTTONS ON CLOSE/BACK) 🚀
# ----------------------------------------------------------

@app.on_callback_query(filters.regex(r"^start$") & ~app.bl_users, group=-1)
@lang.language()
async def rich_start_cb(_, query: types.CallbackQuery):
    """जब आप '❌ CLOSE' दबाएंगे, तो यह ग्रे बटन्स को रोककर नया कलरफुल स्टार्ट मेन्यू लाएगा!"""
    await query.answer()
    _text = (
        query.lang["start_pm"].format(query.from_user.first_name, app.name)
        if query.message.chat.type == enums.ChatType.PRIVATE
        else query.lang["start_gp"].format(app.name)
    )
    try:
        await query.message.delete()
        if config.START_IMG and config.START_IMG.strip():
            await _send_rich_start(query.message.chat.id, config.START_IMG, _text)
    except Exception:
        pass
    raise StopPropagation  # पुराने ग्रे बटन वाले कोड को चलने से रोक देता है

@app.on_callback_query(filters.regex(r"^help_(.*)$") & ~app.bl_users, group=-1)
@lang.language()
async def rich_help_categories_cb(_, query: types.CallbackQuery):
    """हेल्प मेन्यू के सारे बटन्स (Play, Info, Back) को कलरफुल HTML में लोड करने के लिए!"""
    category = query.matches[0].group(1)
    
    # Language menu को न छेड़ें
    if category == "langs":
        return
        
    await query.answer()
    
    if category == "main":
        help_text = (
            f"<b>✨ {app.name} - HELP MENU ✨</b>\n\n"
            "• <b>/play [Song Name / URL]</b> - Play music in voice chat\n"
            "• <b>/vplay [Video Name / URL]</b> - Play video in voice chat\n"
            "• <b>/skip</b> - Skip to the next song\n"
            "• <b>/pause</b> - Pause the music stream\n"
            "• <b>/resume</b> - Resume the music stream\n"
            "• <b>/stop</b> - Stop music and clear queue\n"
            "• <b>/settings</b> - Configure bot settings (Admin only)"
        )
        html_buttons = buttons.help_markup(query.lang)
    else:
        help_text = buttons.help_text(query.lang, category) or query.lang.get(f"help_{category}") or "Help content not found."
        html_buttons = buttons.help_markup(query.lang, back=True)
        
    try:
        await query.message.delete()
        await _send_rich_help(query.message.chat.id, config.START_IMG, help_text, html_buttons)
    except Exception:
        pass
    raise StopPropagation  # पुराने क्रैश होने वाले कोड को रोक देता है


# ----------------------------------------------------------
# 🤖 BOT COMMANDS (START, HELP, SETTINGS) 🤖
# ----------------------------------------------------------

@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    try: await m.delete()
    except Exception: pass

    help_text = (
        f"<b>✨ {app.name} - HELP MENU ✨</b>\n\n"
        "• <b>/play [Song Name / URL]</b> - Play music in voice chat\n"
        "• <b>/vplay [Video Name / URL]</b> - Play video in voice chat\n"
        "• <b>/skip</b> - Skip to the next song\n"
        "• <b>/pause</b> - Pause the music stream\n"
        "• <b>/resume</b> - Resume the music stream\n"
        "• <b>/stop</b> - Stop music and clear queue\n"
        "• <b>/settings</b> - Configure bot settings (Admin only)"
    )
    html_buttons = buttons.help_markup(m.lang)
    sent_data = None
    try:
        if config.START_IMG and config.START_IMG.strip():
            sent_data = await _send_rich_help(m.chat.id, config.START_IMG, help_text, html_buttons)
    except Exception: pass
    if sent_data and "message_id" in sent_data:
        try: await app.send_reaction(m.chat.id, sent_data["message_id"], "👏")
        except Exception: pass

@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if message.chat.type != enums.ChatType.PRIVATE:
        try: await message.delete()
        except Exception: pass

    if not message.from_user: return
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
        if private else message.lang["start_gp"].format(app.name)
    )

    sent_data = None
    try:
        if config.START_IMG and config.START_IMG.strip():
            sent_data = await _send_rich_start(message.chat.id, config.START_IMG, _text)
    except Exception:
        try:
            key = buttons.start_key(message.lang, private)
            sent_msg = await message.reply_text(text=_text, reply_markup=key)
            if sent_msg: sent_data = {"message_id": sent_msg.id}
        except Exception: pass

    if private and sent_data and "message_id" in sent_data:
        try:
            selected_emoji = random.choice(["❤️‍🔥", "⚡", "🔥", "🥰", "🎉", "💖", "🍓"])
            await asyncio.sleep(0.5)
            await app.send_reaction(message.chat.id, sent_data["message_id"], selected_emoji)
        except Exception: pass

    if private:
        if await db.is_user(message.from_user.id): return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)

@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    try: await message.delete()
    except Exception: pass
    admin_only = await db.get_play_mode(message.chat.id)
    force_admin = await db.get_force_mode(message.chat.id)
    sent = await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(message.lang, admin_only, force_admin, "en", message.chat.id),
        quote=True,
    )
    if sent:
        try: await app.send_reaction(message.chat.id, sent.id, "❤️")
        except Exception: pass

@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()
    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id): return
            await db.add_chat(message.chat.id)
