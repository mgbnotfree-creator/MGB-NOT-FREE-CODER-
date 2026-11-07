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
import logging
import aiohttp
from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram import enums, errors
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from ArtistMusic import app, config, db, lang, logger, preload, queue, userbot, yt
from ArtistMusic.core.autoplay import autoplay
from ArtistMusic.helpers import Media, Track, buttons, thumb, utils

# Suppress pytgcalls harmless errors (library bugs - not critical)
class PyTgCallsErrorFilter(logging.Filter):
    def filter(self, record):
        if 'UpdateGroupCall' in record.getMessage():
            return False
        if 'Connection with chat id' in record.getMessage() and 'not found' in record.getMessage():
            return False
        return True

logging.getLogger('pyrogram.dispatcher').addFilter(PyTgCallsErrorFilter())

class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []
        self._play_next_locks = {}  
        self._stream_end_cache = {}  

    async def _edit_media_with_retry(self, message: Message, media_obj: InputMediaPhoto, reply_markup):
        try:
            return await message.edit_media(media=media_obj, reply_markup=reply_markup)
        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            try:
                return await message.edit_media(media=media_obj, reply_markup=reply_markup)
            except Exception:
                return None
        except errors.MessageNotModified:
            return None
        except Exception:
            return None

    async def _send_photo_with_retry(self, chat_id: int, photo, caption: str, reply_markup):
        try:
            return await utils.send_media(chat_id=chat_id, media=photo, caption=caption, reply_markup=reply_markup)
        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            try:
                return await utils.send_media(chat_id=chat_id, media=photo, caption=caption, reply_markup=reply_markup)
            except Exception:
                return None
        except Exception:
            return None

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        try:
            await client.pause(chat_id)
            await db.playing(chat_id, paused=True)
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            await db.playing(chat_id, paused=False)
            await db.remove_call(chat_id)
            queue.clear(chat_id)
            return False
        except Exception as e:
            await db.playing(chat_id, paused=False)
            return False

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        try:
            await client.resume(chat_id)
            await db.playing(chat_id, paused=False)
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            await db.playing(chat_id, paused=False)
            await db.remove_call(chat_id)
            queue.clear(chat_id)
            return False
        except Exception as e:
            return False

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        try:
            await preload.cancel_preload(chat_id)
        except Exception:
            pass
        try:
            queue.clear(chat_id)
            await db.remove_call(chat_id)
        except Exception:
            pass
        try:
            await client.leave_call(chat_id, close=False)
            await asyncio.sleep(0.5)
        except (ConnectionNotFound, exceptions.NotInCallError):
            pass
        except Exception:
            pass

    async def play_media(
        self,
        chat_id: int,
        message: Message | None,
        media: Media | Track,
        seek_time: int = 0,
        message_chat_id: int = None,
        _retry: bool = True,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang_for(getattr(media, "user_id", None), chat_id)
        await db.get_autoplay(chat_id)

        target_chat_for_messages = message_chat_id if message_chat_id else chat_id

        if not media.file_path:
            if message:
                return await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return

        try:
            chat = await app.get_chat(chat_id)
            if chat.type not in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP, enums.ChatType.CHANNEL]:
                if message:
                    await message.edit_text("❌ Can only play in groups/channels.")
                return
            if chat.type == enums.ChatType.CHANNEL:
                userbot_client = await db.get_client(chat_id)
                if not userbot_client:
                    if message:
                        await message.edit_text("❌ No assistant available.")
                    return
                try:
                    assistant_member = await app.get_chat_member(chat_id, userbot_client.me.id)
                    if assistant_member.status == enums.ChatMemberStatus.BANNED:
                        if message:
                            await message.edit_text("❌ Assistant is banned in this channel.")
                        await db.set_cmode(chat_id, None)
                        return
                except errors.RPCError as e:
                    if "CHANNEL_INVALID" in str(e) or "USER_NOT_PARTICIPANT" in str(e):
                        if message:
                            await message.edit_text("❌ <b>Assistant not in channel!</b>")
                        await db.set_cmode(chat_id, None)
                        return
        except errors.RPCError as e:
            if "CHANNEL_INVALID" in str(e):
                if message:
                    await message.edit_text("❌ Invalid channel. Disabling channel play.")
                await db.set_cmode(chat_id, None)  
                return
            raise

        if seek_time > 1:
            ffmpeg_params = f"-ss {seek_time} -probesize 10M -analyzeduration 5M -rtbufsize 5M -fflags +genpts+igndts"
        else:
            ffmpeg_params = "-probesize 10M -analyzeduration 5M -rtbufsize 5M -fflags +genpts+igndts -sync ext"

        _src = str(media.file_path)
        if _src.startswith(("http://", "https://")) and not getattr(media, "is_live", False):
            ffmpeg_params += " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

        is_video = getattr(media, "video", False)
        video_flags = types.MediaStream.Flags.AUTO_DETECT if is_video else types.MediaStream.Flags.IGNORE

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.STUDIO,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=video_flags,
            ffmpeg_parameters=ffmpeg_params,
        )

        try:
            call = await client.get_call(chat_id)
            if call:
                await client.leave_call(chat_id, close=False)
        except (ConnectionNotFound, exceptions.NotInCallError):
            pass
        max_retries = 3
        retry_delay = 1

        try:
            for attempt in range(max_retries):
                try:
                    await client.play(chat_id=chat_id, stream=stream, config=types.GroupCallConfig(auto_start=True))
                    break
                except (exceptions.NoActiveGroupCall, errors.RPCError) as e:
                    error_msg = str(e)
                    if "GROUPCALL_INVALID" in error_msg or "GROUPCALL" in error_msg or isinstance(e, exceptions.NoActiveGroupCall):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            raise
                    else:
                        raise
                except Exception as e:
                    error_msg = str(e).lower()
                    if "cannot be initialized more than once" in error_msg or "connection" in error_msg:
                        if attempt < max_retries - 1:
                            try:
                                await client.leave_call(chat_id, close=False)
                                await asyncio.sleep(retry_delay)
                            except Exception:
                                pass
                            continue
                        else:
                            raise
                    else:
                        raise

            media.time = seek_time if seek_time else 1

            if not seek_time:
                await db.add_call(chat_id)

                if config.THUMB_GEN and isinstance(media, Track):
                    try:
                        _thumb = await thumb.generate(media)
                    except Exception:
                        _thumb = config.DEFAULT_THUMB
                else:
                    _thumb = config.DEFAULT_THUMB

                if message:
                    try:
                        await message.delete()
                    except Exception:
                        pass

                # -------------------------------------------------------------
                # 🎨 VELOCITYBOTS STYLE RICH PLAYER (BLUE LINES & HTML BUTTONS)
                # -------------------------------------------------------------
                safe_title = str(media.title).replace('\n', ' ')
                safe_user = str(media.user).replace('\n', ' ')
                duration_sec = media.duration_sec if not media.is_live else 0
                
                rich_body = (
                    f"<blockquote>🎵 STREAMING MUSIC ━━★</blockquote><br><br>"
                    f"<blockquote>"
                    f"● 🎶 TITLE ➥ <b>{safe_title}</b><br>"
                    f"● 🚀 DURATION ➥ <b>{media.duration}</b><br>"
                    f"● ⭐ REQUESTED BY ➥ {safe_user}<br>"
                    f"</blockquote><br><br>"
                    f"<blockquote>👑 POWERED BY ♡ ⇊ MOON x MUSIC ⇊</blockquote><br><br>"
                )
                
                try:
                    from ArtistMusic.helpers.inline import Inline
                    inline = Inline()
                    buttons_html = inline.controls_html(
                        chat_id=chat_id, played_sec=media.time, duration_sec=duration_sec, playing=True
                    )
                except Exception:
                    buttons_html = ""

                full_html = f'<img src="tg://photo?id=player_cover"/><br>{rich_body}{buttons_html}'
                rich_message = {
                    "html": full_html,
                    "media": [{"id": "player_cover", "media": {"type": "photo", "media": _thumb}}]
                }
                data = {"chat_id": target_chat_for_messages, "rich_message": rich_message}
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendRichMessage"
                
                sent_photo = None
                try:
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(url, json=data) as resp:
                            result = await resp.json()
                            if result.get("ok"):
                                class MockMessage:
                                    def __init__(self, msg_id):
                                        self.id = msg_id
                                sent_photo = MockMessage(result["result"]["message_id"])
                except Exception:
                    pass
                # -------------------------------------------------------------

                if sent_photo:
                    media.message_id = sent_photo.id
                try:
                    asyncio.create_task(preload.start_preload(chat_id))
                except Exception:
                    pass
        except FileNotFoundError:
            if message:
                try:
                    await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
                except Exception:
                    pass
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            if message:
                try:
                    await message.edit_text(_lang["error_vc_disabled"])
                except Exception:
                    pass
        except errors.RPCError as e:
            error_str = str(e)
            if any(x in error_str for x in ["CHAT_ADMIN_REQUIRED", "phone.CreateGroupCall", "GROUPCALL_FORBIDDEN", "GROUPCALL_CREATE_FORBIDDEN", "VOICE_MESSAGES_FORBIDDEN"]):
                await self.stop(chat_id)
                if message:
                    try:
                        await message.edit_text(_lang["error_vc_disabled"])
                    except Exception:
                        pass
            elif "GROUPCALL_INVALID" in error_str or "GROUPCALL" in error_str:
                await self.stop(chat_id)
                if message:
                    try:
                        await message.edit_text(_lang["error_no_call"])
                    except Exception:
                        pass
            else:
                await self.stop(chat_id)
        except exceptions.NoAudioSourceFound:
            media_id = getattr(media, "id", None)
            if _retry and not getattr(media, "is_live", False) and yt.is_yt_id(media_id):
                is_vid = getattr(media, "video", False)
                try:
                    await yt.purge_bad_download(media_id, video=is_vid, force=True)
                    media.file_path = await yt.download(media_id, video=is_vid)
                except Exception:
                    media.file_path = None
                if media.file_path:
                    return await self.play_media(chat_id, message, media, seek_time=seek_time, message_chat_id=message_chat_id, _retry=False)
            if message:
                try:
                    await message.edit_text(_lang["error_no_audio"])
                except Exception:
                    pass
            await self.play_next(chat_id)
        except (ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            if message:
                try:
                    await message.edit_text(_lang["error_tg_server"])
                except Exception:
                    pass
        except TimeoutError:
            await self.stop(chat_id)
            if message:
                try:
                    await message.edit_text("⏱️ <b>Connection timed out!</b>\n\n<blockquote>Failed to join voice chat. Please check your network and try again.</blockquote>")
                except Exception:
                    pass
            await asyncio.sleep(2)
            await self.play_next(chat_id)
        except Exception as e:
            await self.stop(chat_id)
            if message:
                try:
                    await message.edit_text(f"❌ Playback error: {str(e)[:100]}")
                except Exception:
                    pass

    async def replay(self, chat_id: int) -> None:
        try:
            if not await db.get_call(chat_id):
                return
            message_chat_id = None
            try:
                chat = await app.get_chat(chat_id)
                if chat.type == enums.ChatType.CHANNEL:
                    group_id = await db.get_group_for_channel(chat_id)
                    if group_id:
                        message_chat_id = group_id
            except Exception:
                pass
            media = queue.get_current(chat_id)
            _lang = await lang.get_lang_for(getattr(media, "user_id", None), chat_id)
            target_chat = message_chat_id if message_chat_id else chat_id
            msg = await app.send_message(chat_id=target_chat, text=_lang["play_again"])
            await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id)
        except Exception:
            pass

    async def seek_stream(self, chat_id: int, seconds: int) -> bool:
        try:
            if not await db.get_call(chat_id):
                return False
            media = queue.get_current(chat_id)
            if not media or media.is_live:
                return False
            _lang = await lang.get_lang_for(getattr(media, "user_id", None), chat_id)
            message_chat_id = None
            try:
                chat = await app.get_chat(chat_id)
                if chat.type == enums.ChatType.CHANNEL:
                    group_id = await db.get_group_for_channel(chat_id)
                    if group_id:
                        message_chat_id = group_id
            except Exception:
                pass
            media.time = seconds
            target_chat = message_chat_id if message_chat_id else chat_id
            try:
                msg = await app.get_messages(target_chat, media.message_id)
            except Exception:
                msg = None
            if not msg:
                msg = await app.send_message(chat_id=target_chat, text=_lang["seeking"])
            await self.play_media(chat_id, msg, media, seek_time=seconds, message_chat_id=message_chat_id)
            return True
        except Exception:
            return False

    async def play_next(self, chat_id: int) -> None:
        lock = self._play_next_locks.setdefault(chat_id, asyncio.Lock())
        if lock.locked():
            return
        async with lock:
            try:
                if not await db.get_call(chat_id):
                    return
                message_chat_id = None
                try:
                    chat = await app.get_chat(chat_id)
                    if chat.type == enums.ChatType.CHANNEL:
                        group_id = await db.get_group_for_channel(chat_id)
                        if group_id:
                            message_chat_id = group_id
                except Exception:
                    pass
                target_chat = message_chat_id if message_chat_id else chat_id
                loop_mode = await db.get_loop(chat_id)

                if loop_mode == 1:
                    media = queue.get_current(chat_id)
                    if media:
                        _lang = await lang.get_lang_for(getattr(media, "user_id", None), chat_id)
                        try:
                            msg = await app.send_message(chat_id=target_chat, text=_lang["play_again"])
                            await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id)
                        except errors.ChannelPrivate:
                            try:
                                await self.leave_call(chat_id)
                            except Exception:
                                pass
                            await db.rm_chat(chat_id)
                        return

                finished = queue.get_current(chat_id)
                media = queue.get_next(chat_id)

                if not media and loop_mode == 10:
                    all_items = queue.get_all(chat_id)
                    if all_items:
                        first_track = all_items[0]
                        try:
                            msg = await app.send_message(chat_id=target_chat, text="🔁 Looping queue...")
                            if not first_track.file_path:
                                first_track.file_path = await yt.get_play_source(first_track)
                            first_track.message_id = msg.id
                            await self.play_media(chat_id, msg, first_track, message_chat_id=message_chat_id)
                        except errors.ChannelPrivate:
                            await self.leave_call(chat_id)
                            await db.rm_chat(chat_id)
                        return

                try:
                    if media and media.message_id:
                        await app.delete_messages(chat_id=chat_id, message_ids=media.message_id, revoke=True)
                        media.message_id = 0
                except Exception:
                    pass

                if not media and finished and await self._try_autoplay(chat_id, target_chat, message_chat_id, finished):
                    return

                if not media:
                    if config.AUTO_END:
                        _lang = await lang.get_lang(chat_id)
                        try:
                            await app.send_message(chat_id=chat_id, text=_lang.get("auto_end", "✅ Queue finished. Stream ended automatically."))
                        except Exception:
                            pass
                    return await self.stop(chat_id)

                _lang = await lang.get_lang_for(getattr(media, "user_id", None), chat_id)
                msg = None
                if not media.file_path:
                    media.file_path = await yt.get_play_source(media)
                    if not media.file_path:
                        await self.stop(chat_id)
                        return

                try:
                    msg = await app.send_message(chat_id=target_chat, text=_lang["play_next"])
                except errors.FloodWait:
                    msg = None
                except errors.ChannelPrivate:
                    await self.leave_call(chat_id)
                    await db.rm_chat(chat_id)
                    return
                except Exception:
                    msg = None

                media.message_id = msg.id if msg else 0
                if msg:
                    await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id)
                else:
                    await self.play_media(chat_id, None, media, message_chat_id=message_chat_id)

                try:
                    asyncio.create_task(preload.start_preload(chat_id))
                except Exception:
                    pass
            except Exception:
                try:
                    await self.stop(chat_id)
                except Exception:
                    pass

    async def _has_listeners(self, chat_id: int) -> bool | None:
        try:
            client = await db.get_assistant(chat_id)
            participants = await client.get_participants(chat_id)
            return len(participants) >= 2
        except Exception:
            return None

    async def _try_autoplay(self, chat_id: int, target_chat: int, message_chat_id, finished) -> bool:
        try:
            if not await db.get_autoplay(chat_id):
                return False
            listeners = await self._has_listeners(chat_id)
            if listeners is not True:
                if listeners is False:
                    await db.set_autoplay(chat_id, False)
                    autoplay.forget(chat_id)
                    try:
                        await app.send_message(
                            chat_id=target_chat,
                            text="<blockquote>⏹ <b>Autoplay: OFF</b>\n\nNobody was in the VC, so autoplay has been turned off.\nUse /autoplay again to turn it on.</blockquote>",
                        )
                    except Exception:
                        pass
                return False

            try:
                msg = await app.send_message(chat_id=target_chat, text="🔎 Finding a similar song...")
            except Exception:
                msg = None

            async def _fail(text: str) -> bool:
                if msg:
                    try:
                        await msg.edit_text(text)
                    except Exception:
                        pass
                return False

            track = await autoplay.find_next(chat_id, finished)
            if not track:
                return await _fail("❌ Autoplay: no similar song found.")

            track.video = getattr(finished, "video", False)
            track.file_path = await yt.get_play_source(track)
            if not track.file_path:
                return await _fail("❌ Autoplay: failed to fetch the next song.")

            track.message_id = msg.id if msg else 0
            queue.add(chat_id, track)
            await self.play_media(chat_id, msg, track, message_chat_id=message_chat_id)

            try:
                asyncio.create_task(preload.start_preload(chat_id))
            except Exception:
                pass
            return True
        except Exception:
            queue.clear(chat_id)
            return False

    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2) if self.clients else 0.0

    async def decorators(self, client: PyTgCalls) -> None:
        for client in self.clients:
            @client.on_update()
            async def update_handler(_, update: types.Update) -> None:
                if isinstance(update, types.StreamEnded):
                    if update.stream_type == types.StreamEnded.Type.AUDIO:
                        chat_id = update.chat_id
                        current_time = asyncio.get_event_loop().time()
                        if chat_id in self._stream_end_cache:
                            if current_time - self._stream_end_cache[chat_id] < 2.0:
                                return
                        self._stream_end_cache[chat_id] = current_time
                        self._stream_end_cache = {
                            cid: t for cid, t in self._stream_end_cache.items() if current_time - t < 5.0
                        }
                        await self.play_next(chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop(update.chat_id)
                elif isinstance(update, getattr(types, "UpdatedGroupCallParticipant", ())):
                    try:
                        from ArtistMusic.Artistbots.vclog import handle_participant
                        asyncio.create_task(handle_participant(update))
                    except Exception:
                        pass

    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
                
            
