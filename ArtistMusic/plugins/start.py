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
import random
from pyrogram import enums, errors, filters, types

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
    """Send a random big emoji reaction."""
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
# 🤖 BOT COMMANDS (START, HELP, SETTINGS) 🤖
# ----------------------------------------------------------

@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    """Handle /help command."""
    try:
        await m.delete()
    except Exception:
        pass

    try:
        sent = await utils.reply(
            m,
            photo=config.START_IMG,
            caption=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )
        # Send manual reaction for effect
        if sent:
            await app.send_reaction(m.chat.id, sent.id, "👏")
    except Exception:
        sent = await utils.reply(
            m,
            text=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )
        if sent:
            await app.send_reaction(m.chat.id, sent.id, "👏")


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    """Handle /start command with full animations!"""
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
        # 1. Start Emoji Rain
        await _emoji_rain(message)
        # 2. Show Loading Animation
        await _loading_animation(message)

    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )
    key = buttons.start_key(message.lang, private)
    
    sent = None
    try:
        if config.START_IMG and config.START_IMG.strip():
            sent = await message.reply_photo(
                photo=config.START_IMG,
                caption=_text,
                reply_markup=key,
            )
        else:
            raise ValueError("No Photo")
    except Exception:
        try:
            sent = await message.reply_text(
                text=_text,
                reply_markup=key,
            )
        except Exception:
            pass

    # 3. Final Reaction Effect on the sent image
    if private and sent:
        try:
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=sent.id,
                emoji="🥰",
            )
        except Exception:
            pass

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    """Handle settings command."""
    try:
        await message.delete()
    except Exception:
        pass

    admin_only = await db.get_play_mode(message.chat.id)
    force_admin = await db.get_force_mode(message.chat.id)
    _language = "en"
    
    sent = await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, force_admin, _language, message.chat.id
        ),
        quote=True,
    )
    if sent:
        try:
            await app.send_reaction(message.chat.id, sent.id, "❤️")
        except Exception:
            pass


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await db.add_chat(message.chat.id)
    
