# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
# Project      : MGB API Telegram Music Bot
# ==========================================================

import asyncio
import logging
import random
import time as time_mod
from collections import defaultdict
from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram import enums, errors
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls import filters as call_filters
from pytgcalls.pytgcalls_session import PyTgCallsSession

from ArtistMusic import app, config, db, lang, logger, preload, queue, userbot, yt
from ArtistMusic.helpers import Media, Track, thumb
from ArtistMusic.helpers.rich_player import (
    _PLAYER_AUTOPLAY,
    _get_exact_played,
    _parse_duration,
    edit_player,
    send_player,
)

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
        self._autoplay = _PLAYER_AUTOPLAY
        self._last_played = {}  # 🔥 गाना खत्म होने पर भी याद रखेगा कि कौन सा गाना बज रहा था!
        self.active_chats = set()

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
            return await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            try:
                return await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
            except Exception:
                return None
        except Exception:
            return None

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        try:
            await client.pause(chat_id)
            await db.playing(chat_id, paused=True)
            media = queue.get_current(chat_id)
            if media:
                media._paused_at = time_mod.time()
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            await db.playing(chat_id, paused=False)
            await db.remove_call(chat_id)
            queue.clear(chat_id)
            self.active_chats.discard(chat_id)
            return False
        except Exception:
            await db.playing(chat_id, paused=False)
            return False

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        try:
            await client.resume(chat_id)
            await db.playing(chat_id, paused=False)
            media = queue.get_current(chat_id)
            if media and getattr(media, "_paused_at", None):
                paused_duration = time_mod.time() - media._paused_at
                media._start_clock = getattr(media, "_start_clock", time_mod.time()) + paused_duration
                media._paused_at = None
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            await db.playing(chat_id, paused=False)
            await db.remove_call(chat_id)
            queue.clear(chat_id)
            self.active_chats.discard(chat_id)
            return False
        except Exception:
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
            self.active_chats.discard(chat_id)
            self._last_played.pop(chat_id, None)
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
        reuse_message: bool = False,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)

        target_chat_for_messages = message_chat_id if message_chat_id else chat_id
        _thumb = config.DEFAULT_THUMB

        if not media.file_path:
            if message:
                return await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            else:
                return

        try:
            chat = None
            if message_chat_id is not None:
                try:
                    chat = await app.get_chat(chat_id)
                except errors.RPCError:
                    chat = None
            if chat is not None and chat.type == enums.ChatType.CHANNEL:
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
            ffmpeg_params = f"-ss {seek_time} -probesize 2M -analyzeduration 1M -rtbufsize 2M -fflags +genpts+igndts"
        else:
            ffmpeg_params = "-probesize 2M -analyzeduration 1M -rtbufsize 2M -fflags +genpts+igndts -sync ext"

        is_video = getattr(media, "video", False)
        video_flags = types.MediaStream.Flags.AUTO_DETECT if is_video else types.MediaStream.Flags.IGNORE

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.STUDIO,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=video_flags,
            ffmpeg_parameters=ffmpeg_params,
        )

        max_retries = 3
        retry_delays = (0.0, 0.20, 0.45)

        try:
            for attempt in range(max_retries):
                try:
                    await client.play(chat_id=chat_id, stream=stream, config=types.GroupCallConfig(auto_start=True))
                    break
                except (exceptions.NoActiveGroupCall, errors.RPCError) as e:
                    error_msg = str(e)
                    if "GROUPCALL_INVALID" in error_msg or "GROUPCALL" in error_msg or isinstance(e, exceptions.NoActiveGroupCall):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delays[attempt + 1])
                            continue
                        raise
                    raise
                except Exception as e:
                    error_msg = str(e).lower()
                    if "cannot be initialized more than once" in error_msg or "connection" in error_msg:
                        if attempt < max_retries - 1:
                            try:
                                await client.leave_call(chat_id, close=False)
                            except Exception:
                                pass
                            await asyncio.sleep(retry_delays[attempt + 1])
                            continue
                    raise

            if config.THUMB_GEN and isinstance(media, Track):
                try:
                    _thumb = await thumb.generate(media)
                except Exception:
                    _thumb = config.DEFAULT_THUMB

            # 🔥 100% EXACT CLOCK RESET & SAVE LAST PLAYED FOR AUTOPLAY
            now = time_mod.time()
            media.time = seek_time if seek_time else 0
            media._start_clock = now - media.time
            media._paused_at = None
            media._auto_ended = False
            media.target_chat_id = target_chat_for_messages
            media.duration_sec = _parse_duration(media)
            self._last_played[chat_id] = media  # 🔥 ऑटोप्ले के लिए गाना सेव कर लिया!

            if not seek_time:
                await db.add_call(chat_id)
                await db.playing(chat_id, paused=False)
                self.active_chats.add(chat_id)
                
                text = _lang["play_media"].format(media.url, media.title, media.duration, media.user)
                media.player_text = text 
                
                if reuse_message and message is not None and int(getattr(message, "id", 0) or 0):
                    media.message_id = int(message.id)
                    try:
                        ok = await edit_player(
                            target_chat_for_messages, media.message_id, text, media,
                            playing=True, photo=_thumb, autoplay=self.autoplay_enabled(chat_id),
                        )
                    except Exception:
                        ok = False
                    if not ok:
                        try:
                            media.message_id = await send_player(
                                target_chat_for_messages, text, photo=_thumb, media=media, playing=True, autoplay=self.autoplay_enabled(chat_id)
                            )
                        except Exception:
                            pass
                else:
                    if message:
                        try:
                            await message.delete()
                        except Exception:
                            pass
                    try:
                        media.message_id = await send_player(
                            target_chat_for_messages, text, photo=_thumb, media=media, playing=True, autoplay=self.autoplay_enabled(chat_id)
                        )
                    except Exception:
                        pass
                
                try:
                    asyncio.create_task(preload.start_preload(chat_id, count=2))
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
        except errors.RPCError:
            await self.stop(chat_id)
        except exceptions.NoAudioSourceFound:
            if message:
                try:
                    await message.edit_text(_lang["error_no_audio"])
                except Exception:
                    pass
            await self.play_next(chat_id)
        except (ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
        except TimeoutError:
            await self.stop(chat_id)
            await asyncio.sleep(2)
            await self.play_next(chat_id)
        except Exception:
            await self.stop(chat_id)

    async def replay(self, chat_id: int, control_message=None) -> None:
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
            media = queue.get_current(chat_id) or self._last_played.get(chat_id)
            if media:
                media.time = 0
                media._start_clock = time_mod.time()
            _lang = await lang.get_lang(chat_id)
            target_chat = message_chat_id if message_chat_id else chat_id
            msg = control_message or await app.send_message(chat_id=target_chat, text=_lang["play_again"])
            await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id, reuse_message=bool(control_message))
        except Exception:
            pass

    async def seek_stream(self, chat_id: int, seconds: int) -> bool:
        try:
            if not await db.get_call(chat_id):
                return False
            media = queue.get_current(chat_id)
            if not media or media.is_live:
                return False
            _lang = await lang.get_lang(chat_id)
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
            media._start_clock = time_mod.time() - seconds
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
    async def _fetch_autoplay_track(self, current) -> Track | None:
        """🔥 3-Layer Bulletproof Autoplay Finder (कभी फेल नहीं होगा!)"""
        exclude_id = getattr(current, "id", None) if current else None
        base_title = (getattr(current, "ytitle", None) or getattr(current, "title", "") if current else "").strip()
        channel = getattr(current, "channel_name", None) if current else None

        # LAYER 1: बॉट का अपना yt.search_related()
        if hasattr(yt, "search_related") and base_title:
            try:
                res = await asyncio.wait_for(
                    yt.search_related(title=base_title, channel_name=channel, exclude_id=exclude_id),
                    timeout=10.0,
                )
                if res:
                    cand = res[0] if isinstance(res, list) else res
                    if getattr(cand, "id", None) and getattr(cand, "id", None) != exclude_id:
                        return cand
            except Exception as e:
                logger.warning(f"Autoplay Layer 1 failed: {e}")

        # LAYER 2: बॉट का yt.search() अलग-अलग कीवर्ड्स के साथ
        queries = [
            f"{base_title} related songs" if base_title else "Latest Hindi Songs",
            f"{channel} hit songs" if channel else "Bollywood Trending Songs",
            random.choice(["Arijit Singh Hit Songs", "Yo Yo Honey Singh Songs", "Punjabi Hit Songs", "Bollywood Top Hits"]),
        ]
        if hasattr(yt, "search"):
            for q in queries:
                try:
                    res = await asyncio.wait_for(yt.search(q), timeout=10.0)
                    if res:
                        items = res if isinstance(res, list) else [res]
                        for item in items:
                            if getattr(item, "id", None) and getattr(item, "id", None) != exclude_id:
                                return item
                except Exception as e:
                    logger.warning(f"Autoplay Layer 2 ({q}) failed: {e}")

        # LAYER 3: Direct py_yt VideosSearch (अगर yt.search में कोई गड़बड़ हो तो सीधा YouTube से निकालेगा!)
        try:
            from py_yt import VideosSearch
            q = queries[0]
            search = VideosSearch(q, limit=5)
            results = (await asyncio.wait_for(search.next(), timeout=10.0)).get("result", [])
            for r in results:
                vid = r.get("id")
                if vid and vid != exclude_id:
                    dur_str = r.get("duration") or "03:30"
                    dur_sec = 0
                    try:
                        parts = [int(p) for p in dur_str.split(":")]
                        dur_sec = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
                    except Exception:
                        dur_sec = 210
                    return Track(
                        id=vid,
                        channel_name=r.get("channel", {}).get("name", "YouTube"),
                        duration=dur_str,
                        duration_sec=dur_sec,
                        title=r.get("title", "Autoplay Song")[:45],
                        url=r.get("link") or f"https://www.youtube.com/watch?v={vid}",
                        thumbnail=(r.get("thumbnails") or [{}])[-1].get("url", config.DEFAULT_THUMB),
                        view_count=r.get("viewCount", {}).get("short", ""),
                    )
        except Exception as e:
            logger.warning(f"Autoplay Layer 3 failed: {e}")

        return None

    async def play_next(self, chat_id: int, control_message=None, force_new_message: bool = False) -> None:
        if chat_id not in self._play_next_locks:
            self._play_next_locks[chat_id] = asyncio.Lock()
        lock = self._play_next_locks[chat_id]
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
                    media = queue.get_current(chat_id) or self._last_played.get(chat_id)
                    if media:
                        media.time = 0
                        media._start_clock = time_mod.time()
                        _lang = await lang.get_lang(chat_id)
                        try:
                            if force_new_message:
                                old_id = getattr(media, "message_id", None)
                                if old_id:
                                    try:
                                        await app.delete_messages(chat_id=target_chat, message_ids=[int(old_id)], revoke=True)
                                    except Exception:
                                        pass
                                msg = await app.send_message(chat_id=target_chat, text=_lang["play_again"])
                            else:
                                msg = control_message or await app.send_message(chat_id=target_chat, text=_lang["play_again"])
                            await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id, reuse_message=bool(control_message and not force_new_message))
                        except errors.ChannelPrivate:
                            try:
                                await self.leave_call(chat_id)
                            except Exception:
                                pass
                            await db.rm_chat(chat_id)
                        return
                
                # 🔥 _last_played की वजह से अब current कभी None नहीं होगा!
                current = queue.get_current(chat_id) or self._last_played.get(chat_id)
                old_current_message_id = getattr(current, "message_id", None) if current else None
                media = queue.get_next(chat_id)

                if not media:
                    # 🔥 अगर AUTOPLAY ON है, तो 100% नया गाना ढूंढकर बजाएगा!
                    if self.autoplay_enabled(chat_id):
                        _autoplay_msg = None
                        try:
                            _autoplay_msg = await app.send_message(chat_id=target_chat, text="🔄 Searching Autoplay Track...")
                            _next_track = await self._fetch_autoplay_track(current)
                            
                            if _next_track:
                                _next_track.user = "♾ Autoplay"
                                if not getattr(_next_track, "file_path", None):
                                    try:
                                        _next_track.file_path = await asyncio.wait_for(
                                            yt.download(
                                                _next_track.id,
                                                is_live=getattr(_next_track, "is_live", False),
                                                video=getattr(_next_track, "video", False),
                                            ),
                                            timeout=50.0
                                        )
                                    except Exception as dl_err:
                                        logger.error(f"Autoplay download failed: {dl_err}")
                                        _next_track.file_path = None
                                
                                if _next_track.file_path:
                                    queue.add(chat_id, _next_track)
                                    await self.play_media(chat_id, _autoplay_msg, _next_track, message_chat_id=message_chat_id)
                                    try:
                                        asyncio.create_task(preload.start_preload(chat_id, count=2))
                                    except Exception:
                                        pass
                                    return
                        except Exception as ap_err:
                            logger.error(f"Autoplay error: {ap_err}")
                        
                        if _autoplay_msg:
                            try:
                                await _autoplay_msg.delete()
                            except Exception:
                                pass

                    if config.AUTO_END:
                        _lang = await lang.get_lang(chat_id)
                        try:
                            await app.send_message(chat_id=chat_id, text=_lang.get("auto_end", "✅ Queue finished. Stream ended automatically."))
                        except Exception:
                            pass
                    return await self.stop(chat_id)

                _lang = await lang.get_lang(chat_id)
                if force_new_message:
                    ids_to_delete = []
                    for mid in (old_current_message_id, getattr(media, "message_id", None)):
                        try:
                            mid = int(mid)
                        except (TypeError, ValueError):
                            continue
                        if mid and mid not in ids_to_delete:
                            ids_to_delete.append(mid)
                    if ids_to_delete:
                        try:
                            await app.delete_messages(chat_id=target_chat, message_ids=ids_to_delete, revoke=True)
                        except Exception:
                            pass
                
                msg = None
                if not media.file_path:
                    is_live = getattr(media, 'is_live', False)
                    media.file_path = await yt.download(media.id, is_live=is_live, video=getattr(media, 'video', False))
                    if not media.file_path:
                        await self.stop(chat_id)
                        return

                try:
                    if force_new_message:
                        msg = await app.send_message(chat_id=target_chat, text=_lang["play_next"])
                    else:
                        msg = control_message or await app.send_message(chat_id=target_chat, text=_lang["play_next"])
                except errors.FloodWait:
                    msg = None
                except errors.ChannelPrivate:
                    await self.leave_call(chat_id)
                    await db.rm_chat(chat_id)
                    return
                except Exception:
                    msg = None

                media.message_id = (msg.id if msg else 0) if (force_new_message or not control_message) else int(control_message.id)
                if msg:
                    await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id, reuse_message=bool(control_message and not force_new_message))
                else:
                    await self.play_media(chat_id, None, media, message_chat_id=message_chat_id)
            except Exception:
                try:
                    await self.stop(chat_id)
                except Exception:
                    pass

    # ---------------------------------------------------------
    # 🚀 AUTOPLAY STATUS (100% LOCKED & UNIFIED)
    # ---------------------------------------------------------
    async def set_autoplay(self, chat_id: int, enabled: bool | None = None) -> bool:
        if enabled is None:
            enabled = not _PLAYER_AUTOPLAY.get(chat_id, False)
        _PLAYER_AUTOPLAY[chat_id] = bool(enabled)
        
        try:
            media = queue.get_current(chat_id) or self._last_played.get(chat_id)
            if media and getattr(media, "message_id", None):
                target_chat = getattr(media, "target_chat_id", chat_id)
                base_text = getattr(media, "player_text", "")
                playing = await db.playing(chat_id)
                asyncio.create_task(edit_player(
                    target_chat, media.message_id, base_text, media,
                    playing=playing, autoplay=bool(enabled)
                ))
        except Exception:
            pass
        return bool(enabled)

    def autoplay_enabled(self, chat_id: int) -> bool:
        return bool(_PLAYER_AUTOPLAY.get(chat_id, False))

    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)

    async def decorators(self, client: PyTgCalls) -> None:
        for client in self.clients:
            @client.on_update(call_filters.call_participant())
            async def participant_handler(_, update: types.UpdatedGroupCallParticipant) -> None:
                try:
                    from ArtistMusic.plugins.Artistbots.vclog import handle_participant
                    await handle_participant(update)
                except Exception:
                    pass

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
                            cid: t for cid, t in self._stream_end_cache.items()
                            if current_time - t < 5.0
                        }
                        await self.play_next(chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop(update.chat_id)

    # ---------------------------------------------------------
    # 🚀 EXACT CLOCK SYNC + AUTO-TRIGGER AUTOPLAY LOOP
    # ---------------------------------------------------------
    async def auto_update_player(self):
        while True:
            await asyncio.sleep(5)
            for chat_id in list(self.active_chats):
                try:
                    playing = await db.playing(chat_id)
                    media = queue.get_current(chat_id) or self._last_played.get(chat_id)
                    if not media:
                        continue
                        
                    duration = _parse_duration(media)
                    media.duration_sec = duration
                    played = _get_exact_played(media)
                    media.time = played
                    
                    # 🔥 अगर गाना पूरा बज गया है, तो तुरंत Autoplay / Play Next ट्रिगर करो!
                    if playing and duration > 0 and played >= duration and not getattr(media, "_auto_ended", False):
                        media._auto_ended = True
                        asyncio.create_task(self.play_next(chat_id))
                        continue
                    
                    msg_id = getattr(media, "message_id", None)
                    target_chat = getattr(media, "target_chat_id", chat_id)
                    base_text = getattr(media, "player_text", "")
                    
                    if msg_id and base_text:
                        await edit_player(
                            chat_id=target_chat,
                            message_id=msg_id,
                            base_html=base_text,
                            media=media,
                            playing=playing,
                            autoplay=self.autoplay_enabled(chat_id)
                        )
                except Exception:
                    pass

    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
            
        asyncio.create_task(self.auto_update_player())
        logger.info("📞 PyTgCalls client(s) started & Smart Timer Loop is running.")
        
