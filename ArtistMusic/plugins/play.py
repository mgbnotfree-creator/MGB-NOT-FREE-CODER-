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
from pyrogram import filters
from pyrogram import types
from pyrogram.errors import FloodWait, MessageIdInvalid, MessageDeleteForbidden, ChatSendPlainForbidden, ChatWriteForbidden

from ArtistMusic import tune, app, config, db, lang, queue, tg, yt
from ArtistMusic.helpers import buttons, utils
from ArtistMusic.helpers._play import checkUB
import asyncio
import logging

logger = logging.getLogger(__name__)


# ── Music search animation frames ─────────────────────────────────────────
_PLAY_FRAMES = [
    "🔍 Searching and downloading...",
]


async def _play_animation(sent_msg):
    """Animate the searching message. Silently stops when message is edited externally."""
    for frame in _PLAY_FRAMES:
        await asyncio.sleep(1.5)
        try:
            await sent_msg.edit_text(frame, parse_mode="html")
        except Exception:
            return  # Message edited externally or error — stop cleanly


async def safe_edit(message, text, **kwargs):
    """
    Safely edit a message with proper error handling for common Telegram API errors.
    """
    try:
        await message.edit_text(text, **kwargs)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await message.edit_text(text, **kwargs)
            return True
        except (MessageIdInvalid, MessageDeleteForbidden, Exception):
            return False
    except (MessageIdInvalid, MessageDeleteForbidden):
        return False
    except Exception:
        return False


async def safe_reply(message, text, **kwargs):
    """
    Safely send a reply message with proper error handling for media-only chats.
    """
    try:
        return await message.reply_text(text, **kwargs)
    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning(f"Cannot send text in chat {message.chat.id} (chat write forbidden)")
        return None
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        return None


def queue_controls(chat_id: int) -> types.InlineKeyboardMarkup:
    """Buttons for the "Added to queue" message, without the replay and autoplay buttons."""
    markup = buttons.controls(chat_id)
    _hidden = ("controls replay", "controls autoplay")
    markup.inline_keyboard = [
        [b for b in row if not (b.callback_data or "").startswith(_hidden)]
        for row in markup.inline_keyboard
    ]
    markup.inline_keyboard = [row for row in markup.inline_keyboard if row]
    return markup


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    """
    Add multiple tracks to queue and format them as a message.
    """
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


@app.on_message(
    filters.command(
        [
            "play",
            "playforce",
            "cplay",
            "cplayforce",
            "vplay",
            "vplayforce",
            "cvplay",
            "cvplayforce",
        ]
    )
    & (filters.group | filters.channel)
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    url: str = None,
    cplay: bool = False,
    video: bool = False,
) -> None:
    # Auto-delete command message if allowed
    try:
        if m.chat.type != filters.enums.ChatType.CHANNEL:
            await m.delete()
    except Exception:
        pass
    
    chat_id = m.chat.id
    message_chat_id = m.chat.id
    
    # Handle user/mention info safely for channels vs groups
    if m.from_user:
        mention = m.from_user.mention
        user_id = m.from_user.id
        user_name = m.from_user.first_name or "User"
    else:
        # If triggered directly from a channel post
        mention = m.chat.title or "Channel"
        user_id = m.chat.id
        user_name = m.chat.title or "Channel"

    if cplay:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await safe_reply(m,
                "<blockquote>❌ Channel play is not enabled.\n\n"
                "To enable for linked channel:\n"
                "`/channelplay linked`\n\n"
                "To enable for any channel:\n"
                "`/channelplay [channel_id]`</blockquote>"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except:
            await db.set_cmode(m.chat.id, None)
            return await safe_reply(m,
                "<blockquote>❌ Cannot find channel!\n\n"
                "Please make sure I'm admin in the channel and channel exists.</blockquote>"
            )
        
        client = await db.get_client(channel_id)
        try:
            await app.get_chat_member(channel_id, client.id)
        except Exception:
            try:
                if chat.username:
                    invite_link = chat.username
                else:
                    try:
                        invite_link = chat.invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(channel_id)
                    except Exception:
                        return await safe_reply(m,
                            f"<blockquote>❌ Assistant cannot join channel!\n\n"
                            f"Please add @{client.username if client.username else client.mention} "
                            f"to the channel as an admin with permission to join.</blockquote>"
                        )
                
                join_msg = await safe_reply(m, f"<blockquote>🔌 Joining assistant to channel...</blockquote>")
                await client.join_chat(invite_link)
                await asyncio.sleep(1)
                try:
                    await join_msg.delete()
                except:
                    pass
            except Exception as e:
                return await safe_reply(m,
                    f"<blockquote>❌ Failed to join assistant to channel!\n\n"
                    f"Error: {str(e)}</blockquote>"
                )

    if m.chat.type == filters.enums.ChatType.CHANNEL:
        chat_id = m.chat.id
        message_chat_id = m.chat.id

    # Send searching message
    try:
        sent = await safe_reply(m, _PLAY_FRAMES[0])
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            sent = await safe_reply(m, _PLAY_FRAMES[0])
        except Exception:
            return
    except Exception:
        return

    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []
    file = None

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif url:
        if "playlist" in url:
            await safe_edit(sent, m.lang["playlist_fetch"])
            try:
                tracks = await yt.playlist(config.PLAYLIST_LIMIT, mention, url)
            except Exception:
                await safe_edit(sent, f"<blockquote>❌ Failed to fetch playlist. Try a single track.</blockquote>")
                return

            if not tracks:
                await safe_edit(sent, m.lang["playlist_error"])
                return

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id)

        if not file:
            await safe_edit(sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT))
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id)
        if not file:
            await safe_edit(sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT))
            return

    if not file:
        return

    file.video = getattr(file, "video", False) or video
    if file.video:
        for track in tracks:
            track.video = True

    if not file.is_live and file.duration_sec > config.DURATION_LIMIT:
        await safe_edit(sent, m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60))
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    file.user_id = user_id
    
    if force:
        queue.force_add(chat_id, file)
    else:
        position = queue.add(chat_id, file)

        if await db.get_call(chat_id):
            await safe_edit(
                sent,
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    mention,
                ),
                reply_markup=queue_controls(chat_id),
            )
            if tracks:
                added = playlist_to_queue(chat_id, tracks)
                try:
                    await app.send_message(
                        chat_id=m.chat.id,
                        text=m.lang["playlist_queued"].format(len(tracks)) + added,
                    )
                except Exception:
                    pass
            
            try:
                from ArtistMusic import preload
                asyncio.create_task(preload.start_preload(chat_id))
            except Exception:
                pass
            
            return

    if not file.file_path:
        if file.is_live:
            file.file_path = await yt.download(file.id, is_live=True, video=False)
        else:
            file.file_path = await yt.get_play_source(file)

        if not file.file_path:
            await safe_edit(
                sent,
                "<blockquote>❌ Failed to stream media.\n\n"
                f"Support: {config.SUPPORT_CHAT}</blockquote>"
            )
            return

    try:
        await tune.play_media(
            chat_id=chat_id, 
            message=sent, 
            media=file, 
            message_chat_id=message_chat_id if chat_id != message_chat_id else None
        )
        try:
            if m.chat.type != filters.enums.ChatType.CHANNEL:
                emoji = m.lang["play_emoji"]
                await m.react(emoji)
        except Exception:
            pass
    except Exception as e:
        error_msg = str(e)
        await safe_edit(sent, f"<blockquote>❌ Playback error:\n{error_msg}</blockquote>")
        return

    if not tracks:
        return
    added = playlist_to_queue(chat_id, tracks)
    try:
        from ArtistMusic import preload
        asyncio.create_task(preload.start_preload(chat_id))
    except Exception:
        pass
    try:
        await app.send_message(
            chat_id=m.chat.id,
            text=m.lang["playlist_queued"].format(len(tracks)) + added,
        )
    except Exception:
        pass
    
