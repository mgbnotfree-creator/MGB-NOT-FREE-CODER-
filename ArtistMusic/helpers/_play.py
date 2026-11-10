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

from pyrogram import enums, errors, types

from ArtistMusic import app, config, db, queue, yt
from ArtistMusic.core.mongo import NoAssistantAvailable


def checkUB(play):
    async def wrapper(_, m: types.Message):
        async def safe_reply(text):
            """Safely send reply, return None if chat doesn't allow messages"""
            try:
                return await m.reply_text(text)
            except (errors.ChatWriteForbidden, errors.ChatSendPlainForbidden):
                return None
            except Exception:
                return None
        
        # 🔥 चैनल और एनोनिमस एडमिन (Anonymous Admin) को सपोर्ट देने के लिए चेक को फ्लेक्सिबल बनाया गया है
        if not m.from_user and m.chat.type != enums.ChatType.CHANNEL:
            await safe_reply(getattr(m, "lang", {}).get("play_user_invalid", "❌ Invalid user or chat!"))
            return

        # 🔥 अब यह सुपरग्रुप के साथ-साथ सीधे चैनल (Channel) को भी अनुमति देगा!
        if m.chat.type not in [enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL, enums.ChatType.GROUP]:
            await safe_reply(getattr(m, "lang", {}).get("play_chat_invalid", "❌ This chat type is not supported!"))
            try:
                return await app.leave_chat(m.chat.id)
            except:
                return

        if not m.reply_to_message and (
            len(m.command) < 2 or (len(m.command)
                                   == 2 and m.command[1] == "-f")
        ):
            await safe_reply(getattr(m, "lang", {}).get("play_usage", "💡 Usage: /play [Song Name or YouTube Link]"))
            return

        if len(queue.get_queue(m.chat.id)) >= config.QUEUE_LIMIT:
            await safe_reply(getattr(m, "lang", {}).get("play_queue_full", "❌ Queue is full! (Limit: {})").format(config.QUEUE_LIMIT))
            return

        command = m.command[0].lower()
        force = command.endswith("force") or (
            len(m.command) > 1 and "-f" in m.command[1]
        )
        cplay = command.startswith("c")

        video_requested = command.startswith("v") or command.startswith("cv")
        if video_requested and not await db.get_vplay_enabled():
            await safe_reply(getattr(m, "lang", {}).get("play_video_disabled", "❌ Video play is disabled!"))
            return
        video = video_requested
        
        url = yt.url(m)
        if url and not m.reply_to_message and not yt.valid(url):
            return await m.reply_text(getattr(m, "lang", {}).get("play_unsupported", "❌ Unsupported URL!"))

        # चैनल के अंदर एडमिन चेक बाईपास रहेगा ताकि क्रैश न हो
        play_mode = await db.get_play_mode(m.chat.id)
        force_admin = await db.get_force_mode(m.chat.id)
        if (play_mode or (force and force_admin)) and m.from_user:
            adminlist = await db.get_admins(m.chat.id)
            if (
                m.from_user.id not in adminlist
                and not await db.is_auth(m.chat.id, m.from_user.id)
                and not m.from_user.id in app.sudoers
            ):
                await safe_reply(getattr(m, "lang", {}).get("play_admin", "❌ Only admins can use this command!"))
                return

        if m.chat.id not in db.active_calls:
            try:
                client = await db.get_client(m.chat.id)
            except NoAssistantAvailable:
                await safe_reply(getattr(m, "lang", {}).get("no_assistant", "❌ No assistant available!"))
                return
            try:
                member = await app.get_chat_member(m.chat.id, client.id)
                if member.status in [
                    enums.ChatMemberStatus.BANNED,
                    enums.ChatMemberStatus.RESTRICTED,
                ]:
                    try:
                        await app.unban_chat_member(
                            chat_id=m.chat.id, user_id=client.id
                        )
                    except:
                        await safe_reply(
                            getattr(m, "lang", {}).get("play_banned", "❌ Assistant is banned!").format(
                                app.name,
                                client.id,
                                client.mention,
                                f"@{client.username}" if client.username else None,
                            )
                        )
                        return
            except errors.ChatAdminRequired:
                await safe_reply(
                    f"<blockquote><b>🔐 Bot Admin Required</b></blockquote>\n\n"
                    f"<blockquote>To play music in this chat, I need to be an <b>administrator</b>.\n\n"
                    f"<b>Required permissions:</b>\n"
                    f"• Manage Voice Chats\n"
                    f"• Invite Users via Link\n"
                    f"• Delete Messages\n\n"
                    f"Please promote me as admin with the required permissions.</blockquote>"
                )
                return
            except errors.UserNotParticipant:
                if m.chat.username:
                    invite_link = m.chat.username
                    try:
                        await client.resolve_peer(invite_link)
                    except:
                        pass
                else:
                    try:
                        invite_link = (await app.get_chat(m.chat.id)).invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(m.chat.id)
                    except Exception:
                        pass

                try:
                    await client.join_chat(invite_link)
                except Exception:
                    pass

        try:
            if m.chat.type != enums.ChatType.CHANNEL:
                await m.delete()
        except:
            pass

        return await play(_, m, force, url, cplay, video)

    return wrapper
            
