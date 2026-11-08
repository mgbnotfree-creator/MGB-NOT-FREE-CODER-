# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts/ArtistMusic
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import re
import asyncio
from functools import wraps

from pyrogram import filters, types
from pyrogram.errors import FloodWait, QueryIdInvalid

from ArtistMusic import tune, app, config, db, lang, logger, queue, tg, yt
from ArtistMusic.helpers import admin_check, buttons, can_manage_vc, utils


def safe_callback(func):
    """Decorator to handle exceptions in callback handlers."""
    @wraps(func)
    async def wrapper(client, query: types.CallbackQuery):
        try:
            return await func(client, query)
        except QueryIdInvalid:
            return
        except Exception as e:
            logger.error(f"Error in callback {func.__name__}: {e}", exc_info=True)
            try:
                await query.answer("❌ An error occurred. Please try again.", show_alert=True)
            except Exception:
                pass
    return wrapper


@app.on_callback_query(filters.regex("^start$") & ~app.bl_users)
@lang.language()
@safe_callback
async def _start_callback(_, query: types.CallbackQuery):
    """Handle start button callback - return to start message."""
    await query.answer()
    
    _text = query.lang["start_pm"].format(query.from_user.first_name, app.name)
    key = buttons.start_key(query.lang, True)
    
    try:
        await query.edit_message_caption(
            caption=_text,
            reply_markup=key,
        )
    except Exception:
        try:
            await query.edit_message_text(
                text=_text,
                reply_markup=key,
            )
        except Exception:
            pass


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
@safe_callback
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


# ---------------------------------------------------------
# 🚀 SMART FIX: नया `controls` हैंडलर जो HTML प्लेयर को अपडेट करेगा
# ---------------------------------------------------------
@app.on_callback_query(filters.regex("^controls") & ~app.bl_users)
@lang.language()
@safe_callback
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])

    qaction = len(args) == 4 and args[3] == "q"
    item_id = args[3] if len(args) == 4 and args[3] != "q" else None
    user = query.from_user.mention

    if action == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    user_id = query.from_user.id
    has_permission = False
    if user_id in app.sudoers or await db.is_auth(chat_id, user_id):
        has_permission = True
    else:
        admins = await db.get_admins(chat_id)
        if user_id in admins:
            has_permission = True
            
    if not has_permission:
        return await query.answer("⚠️ You don't have permission to use this.", show_alert=True)

    if not await db.get_call(chat_id):
        return await query.answer(query.lang["not_playing"], show_alert=True)

    if action == "status":
        await query.answer()
        media = queue.get_current(chat_id)
        if media:
            try:
                from ArtistMusic.helpers.rich_player import edit_player
                await edit_player(
                    chat_id=chat_id,
                    message_id=query.message.id,
                    text=None,
                    media=media,
                    playing=await db.playing(chat_id),
                    photo=None,
                    autoplay=bool(await db.get_autoplay(chat_id))
                )
            except Exception as e:
                logger.error(f"Timer Edit Failed: {e}")
        return
    
    if action.startswith("seek_"): return await handle_seek(query, chat_id, action, user)
    if action == "loop": return await handle_loop(query, chat_id, user)
    if action == "shuffle": return await handle_shuffle(query, chat_id, user)
    
    if action == "autoplay":
        new_state = not await db.get_autoplay(chat_id)
        await db.set_autoplay(chat_id, new_state)
        await query.answer("🔁 Autoplay: ON" if new_state else "⏹ Autoplay: OFF")
        media = queue.get_current(chat_id)
        if media:
            try:
                from ArtistMusic.helpers.rich_player import edit_player
                await edit_player(
                    chat_id=chat_id,
                    message_id=query.message.id,
                    text=None,
                    media=media,
                    playing=await db.playing(chat_id),
                    photo=None,
                    autoplay=new_state
                )
            except Exception:
                pass
        return

    await query.answer(query.lang["processing"], show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id): return await query.answer(query.lang["play_already_paused"], show_alert=True)
        await tune.pause(chat_id)
    elif action == "resume":
        if await db.playing(chat_id): return await query.answer(query.lang["play_not_paused"], show_alert=True)
        await tune.resume(chat_id)
    elif action == "skip":
        await tune.play_next(chat_id, force_new_message=True)
        try: await query.message.delete()
        except: pass
        return
    elif action == "stop":
        await tune.stop(chat_id)
        try: await query.message.delete()
        except: pass
        return
    elif action == "replay":
        media = queue.get_current(chat_id)
        media.user = user
        media.user_id = query.from_user.id
        await tune.replay(chat_id)
        try: await query.message.delete()
        except: pass
        return

    media = queue.get_current(chat_id)
    if media:
        try:
            from ArtistMusic.helpers.rich_player import edit_player
            await edit_player(
                chat_id=chat_id,
                message_id=query.message.id,
                text=None,
                media=media,
                playing=await db.playing(chat_id),
                photo=None,
                autoplay=bool(await db.get_autoplay(chat_id))
            )
        except Exception:
            pass
async def handle_seek(query: types.CallbackQuery, chat_id: int, action: str, user: str):
    """Handle seek forward/backward actions."""
    media = queue.get_current(chat_id)
    if not media or media.is_live:
        return await query.answer("⚠️ Cannot seek in live streams!", show_alert=True)
    
    if not media.duration_sec or media.duration_sec == 0:
        return await query.answer("⚠️ Cannot seek in this track!", show_alert=True)
    
    if action == "seek_back_10":
        seconds = -10
    elif action == "seek_back_30":
        seconds = -30
    elif action == "seek_forward_10":
        seconds = 10
    elif action == "seek_forward_30":
        seconds = 30
    else:
        return await query.answer("⚠️ Invalid seek action!", show_alert=True)
    
    current_time = getattr(media, 'time', 0)
    new_time = max(0, min(current_time + seconds, media.duration_sec - 5))
    
    if new_time == 0 and seconds < 0:
        return await query.answer(f"⏮️ Already at the beginning!", show_alert=True)
    if new_time >= media.duration_sec - 5 and seconds > 0:
        return await query.answer(f"⏭️ Too close to the end!", show_alert=True)
    
    success = await tune.seek_stream(chat_id, int(new_time))
    if success:
        import time as time_module
        if media.duration_sec >= 3600:
            time_str = time_module.strftime('%H:%M:%S', time_module.gmtime(new_time))
        else:
            time_str = time_module.strftime('%M:%S', time_module.gmtime(new_time))
        
        _dir = "⏩ ꜰᴏʀᴡᴀʀᴅᴇᴅ" if seconds > 0 else "⏪ ʀᴇᴡɪɴᴅᴇᴅ"
        await query.answer(f"Seeked to {time_str}", show_alert=True)
        
        try:
            sent_msg = await utils.reply(
                query.message,
                text=f"<blockquote><b>{_dir}</b>\n\n⏱  ᴅᴜʀᴀᴛɪᴏɴ ╌ {time_str}\n👤  ʙʏ ╌ {user}</blockquote>",
                quote=False,
            )
            await asyncio.sleep(5)
            try:
                await sent_msg.delete()
            except Exception:
                pass
        except FloodWait as e:
            pass
        except Exception:
            pass


async def handle_loop(query: types.CallbackQuery, chat_id: int, user: str):
    """Handle loop mode toggling."""
    current_loop = await db.get_loop(chat_id)
    
    if current_loop == 0:
        new_loop = 1
        text = "🔂 Loop: Single Track"
        message = f"🔂 Loop mode set to <b>Single Track</b>"
    elif current_loop == 1:
        new_loop = 10
        text = "🔁 Loop: Queue"
        message = f"🔁 Loop mode set to <b>Queue</b>"
    else:
        new_loop = 0
        text = "➡️ Loop: Off"
        message = f"➡️ Loop mode <b>Disabled</b>"
    
    await db.set_loop(chat_id, new_loop)
    await query.answer(text, show_alert=False)
    await utils.reply(query.message, text=message, quote=False)


async def handle_shuffle(query: types.CallbackQuery, chat_id: int, user: str):
    """Handle queue shuffling."""
    import random
    
    items = queue.get_queue(chat_id)
    if not items or len(items) <= 1:
        return await query.answer("⚠️ Queue is empty or has only one track!", show_alert=True)
    
    current = items[0] if items else None
    remaining = items[1:] if len(items) > 1 else []
    
    if not remaining:
        return await query.answer("⚠️ No tracks to shuffle!", show_alert=True)
    
    random.shuffle(remaining)
    
    queue.clear(chat_id)
    if current:
        queue.add(chat_id, current)
    for item in remaining:
        queue.add(chat_id, item)
    
    await query.answer("🔀 Queue shuffled!", show_alert=False)
    await utils.reply(
        query.message,
        text=f"🔀 Queue <b>shuffled</b> ({len(remaining)} tracks)",
        quote=False,
    )


@app.on_callback_query(filters.regex(r"^help") & ~app.bl_users)
@lang.language()
async def _help(_, query: types.CallbackQuery):
    await query.answer()
    
    if query.data == "help":
        try:
            await query.edit_message_caption(
                caption=query.lang["help_menu"], 
                reply_markup=buttons.help_markup(query.lang)
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=query.lang["help_menu"], 
                    reply_markup=buttons.help_markup(query.lang)
                )
            except Exception:
                pass
        return
    
    category = query.data.replace("help_", "")
    
    if category == "main":
        try:
            await query.edit_message_caption(
                caption=query.lang["help_menu"], 
                reply_markup=buttons.help_markup(query.lang)
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=query.lang["help_menu"], 
                    reply_markup=buttons.help_markup(query.lang)
                )
            except Exception:
                pass
        return

    if category == "langs":
        try:
            await query.edit_message_caption(
                caption=query.lang["lang_select"],
                reply_markup=buttons.langs_markup(),
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=query.lang["lang_select"],
                    reply_markup=buttons.langs_markup(),
                )
            except Exception:
                pass
        return

    help_text = (
        buttons.help_text(query.lang, category)
        or query.lang.get(f"help_{category}")
        or query.lang["help_admins"]
    )
    
    try:
        await query.edit_message_caption(
            caption=help_text,
            reply_markup=buttons.help_markup(query.lang, True),
        )
    except Exception:
        try:
            await query.edit_message_text(
                text=help_text,
                reply_markup=buttons.help_markup(query.lang, True),
            )
        except Exception:
            pass


_LANG_NAMES = {
    "en": "🇬🇧 English", "hi": "🇮🇳 Hindi", "te": "🇮🇳 Telugu",
    "ko": "🇰🇷 Korean", "my": "🇲🇲 Myanmar", "id": "🇮🇩 Indonesian",
    "pt": "🇧🇷 Portuguese", "ar": "🇸🇦 Arabic", "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French", "ru": "🇷🇺 Russian", "de": "🇩🇪 German",
    "tr": "🇹🇷 Turkish", "bn": "🇧🇩 Bengali", "th": "🇹🇭 Thai",
    "vi": "🇻🇳 Vietnamese", "ja": "🇯🇵 Japanese", "zh": "🇨🇳 Chinese",
    "ur": "🇵🇰 Urdu", "fa": "🇮🇷 Persian",
    "bho": "🇮🇳 Bhojpuri", "ne": "🇳🇵 Nepali",
}


@app.on_callback_query(filters.regex(r"^setlang_") & ~app.bl_users)
async def _setlang(_, query: types.CallbackQuery):
    code = query.data.replace("setlang_", "")
    if code not in _LANG_NAMES:
        return await query.answer("❌ Invalid language.", show_alert=True)
    lang_name = _LANG_NAMES[code]
    await db.set_user_lang(query.from_user.id, code)
    new_lang = lang.get_merged_lang(code)
    confirmation = new_lang["lang_changed"].format(lang_name)
    await query.answer()
    try:
        await query.edit_message_caption(
            caption=confirmation,
            reply_markup=buttons.langs_markup(),
        )
    except Exception:
        try:
            await query.edit_message_text(
                text=confirmation,
                reply_markup=buttons.langs_markup(),
            )
        except Exception:
            pass


@app.on_callback_query(filters.regex("^playmode$") & ~app.bl_users)
@lang.language()
@admin_check
async def _playmode(_, query: types.CallbackQuery):
    await query.answer(query.lang["processing"], show_alert=True)
    chat_id = query.message.chat.id
    admin_only = await db.get_play_mode(chat_id)
    force_admin = await db.get_force_mode(chat_id)
    _language = "en"
    await db.set_play_mode(chat_id, admin_only)
    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            not admin_only,
            force_admin,
            _language,
            chat_id,
        )
    )


@app.on_callback_query(filters.regex("^forcemode$") & ~app.bl_users)
@lang.language()
@admin_check
async def _forcemode(_, query: types.CallbackQuery):
    await query.answer(query.lang["processing"], show_alert=True)
    chat_id = query.message.chat.id
    admin_only = await db.get_play_mode(chat_id)
    force_admin = await db.get_force_mode(chat_id)
    _language = "en"
    await db.set_force_mode(chat_id, force_admin)
    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            admin_only,
            not force_admin,
            _language,
            chat_id,
        )
            )
                    
