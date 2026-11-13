# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
# Project      : MGB API Telegram Music Bot
# ==========================================================

import asyncio
import logging
import random
import re
import time as time_mod
from collections import defaultdict

# 🔥 PYTHON 3.14 EVENT LOOP FIX
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

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
    _PLAYER_LAST_MSG,
    _PLAYER_LAST_TEXT,
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

class _AutoplayDict(dict):
    def __setitem__(self, key, value):
        key = int(key)
        val = bool(value)
        super().__setitem__(key, val)
        _PLAYER_AUTOPLAY[key] = val

    def get(self, key, default=False):
        return bool(_PLAYER_AUTOPLAY.get(int(key), default))

    def __getitem__(self, key):
        return bool(_PLAYER_AUTOPLAY.get(int(key), False))

class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []
        self._play_next_locks = {}  
        self._stream_end_cache = {}  
        self._autoplay = _AutoplayDict()
        self._last_played = {}
        self._played_history = defaultdict(list)
        self._played_titles = defaultdict(list)
        self._active_player_msg = {}
        self.active_chats = set()

    async def _delete_old_player(self, target_chat: int, *msg_ids) -> None:
        """🔥 पुराने प्लेयर मैसेज को 100% डिलीट करेगा ताकि चैट में कचरा न फैले"""
        ids = set()
        for mid in msg_ids:
            try:
                if mid and int(mid) > 0:
                    ids.add(int(mid))
            except Exception:
                pass
        last_mid = self._active_player_msg.get(target_chat) or _PLAYER_LAST_MSG.get(target_chat)
        if last_mid:
            try:
                ids.add(int(last_mid))
            except Exception:
                pass
        for mid in ids:
            try:
                await edit_player(target_chat, mid, "", None, remove=True)
            except Exception:
                pass
            try:
                await app.delete_messages(chat_id=target_chat, message_ids=[mid], revoke=True)
            except Exception:
                pass

    async def _edit_media_with_retry(self, message: Message, media_obj: InputMediaPhoto, reply_markup):
        try:
            return await message.edit_media(media=media_obj, reply_markup=reply_markup)
        except Exception:
            return None

    async def _send_photo_with_retry(self, chat_id: int, photo, caption: str, reply_markup):
        try:
            return await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
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
                except Exception:
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
                except Exception:
                    pass
        except Exception:
            pass

        if seek_time > 1:
            ffmpeg_params = f"-ss {seek_time} -probesize 2M -analyzeduration 1M -rtbufsize 2M -fflags +genpts+igndts"
        else:
            ffmpeg_params = "-probesize 2M -analyzeduration 1M -rtbufsize 2M -fflags +genpts+igndts -sync ext"

        is_video = getattr(media, "video", False)
        video_flags = types.MediaStream.Flags.AUTO_DETECT if is_video else types.MediaStream.Flags.IGNORE

        # 🔥 VIDEO QUALITY UPDATED TO HD 1080p 🔥
        video_params = types.VideoQuality.FHD_1080p if is_video else None

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.STUDIO,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_parameters=video_params,
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
                except Exception:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delays[attempt + 1])
                        continue
                    raise

            if config.THUMB_GEN and isinstance(media, Track):
                try:
                    _thumb = await thumb.generate(media)
                except Exception:
                    _thumb = config.DEFAULT_THUMB

            now = time_mod.time()
            media.time = seek_time if seek_time else 0
            media._start_clock = now - media.time
            media._paused_at = None
            media._auto_ended = False
            media.chat_id = chat_id
            media.target_chat_id = target_chat_for_messages
            media.duration_sec = _parse_duration(media)
            self._last_played[chat_id] = media

            # 🔥 जो गाना अभी बजा है, उसकी ID और उसका नाम तुरंत हिस्ट्री में लॉक कर दो!
            self._record_song(chat_id, getattr(media, "id", ""), getattr(media, "title", ""))

            if not seek_time:
                await db.add_call(chat_id)
                await db.playing(chat_id, paused=False)
                self.active_chats.add(chat_id)
                
                text = _lang["play_media"].format(media.url, media.title, media.duration, media.user)
                media.player_text = text
                _PLAYER_LAST_TEXT[target_chat_for_messages] = text
                
                if message:
                    try:
                        await message.delete()
                    except Exception:
                        pass

                # 🔥 नया प्लेयर भेजने से पहले अगर कोई पुराना प्लेयर चैट में है तो उसे उड़ा दो!
                old_mid = self._active_player_msg.get(target_chat_for_messages)
                if old_mid:
                    await self._delete_old_player(target_chat_for_messages, old_mid)

                try:
                    media.message_id = await send_player(
                        target_chat_for_messages, text, photo=_thumb, media=media, playing=True, autoplay=self.autoplay_enabled(chat_id)
                    )
                    self._active_player_msg[target_chat_for_messages] = int(media.message_id)
                except Exception:
                    pass
                
                try:
                    asyncio.create_task(preload.start_preload(chat_id, count=2))
                except Exception:
                    pass
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
            await self.play_media(chat_id, msg, media, message_chat_id=message_chat_id, reuse_message=False)
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

    def _clean_song_key(self, title: str) -> str:
        """🔥 गाने के नाम में से 'Official Video, Full Audio, Song' हटाकर असली नाम निकालेगा (जैसे 'sahiba')"""
        t = str(title or "").lower()
        t = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", t)
        t = re.sub(r"\b(official|music|video|audio|full|song|lyrics|lyrical|hd|4k|remix|lofi|slowed|reverb|ft|feat)\b", " ", t)
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        words = [w for w in t.split() if len(w) > 2]
        return " ".join(words[:2]).strip()

    def _record_song(self, chat_id: int, vid: str, title: str):
        vid = str(vid or "").strip()
        if vid:
            hist = self._played_history[chat_id]
            if vid not in hist:
                hist.append(vid)
            if len(hist) > 40:
                hist.pop(0)
        key = self._clean_song_key(title)
        if key:
            thist = self._played_titles[chat_id]
            if key not in thist:
                thist.append(key)
            if len(thist) > 30:
                thist.pop(0)

    def _is_duplicate_song(self, chat_id: int, vid: str, title: str, current_title: str = "") -> bool:
        """🔥 अगर ID पहले बज चुकी है या गाने का नाम (जैसे 'Sahiba') पहले बज चुका है, तो तुरंत रिजेक्ट कर देगा!"""
        vid = str(vid or "").strip()
        if not vid or vid in self._played_history[chat_id]:
            return True
        key = self._clean_song_key(title)
        cur_key = self._clean_song_key(current_title)
        if key and (key == cur_key or key in self._played_titles[chat_id]):
            return True
        for old_key in self._played_titles[chat_id]:
            if key and old_key and (key in old_key or old_key in key):
                return True
        return False

    async def _fetch_autoplay_track(self, chat_id: int, current) -> Track | None:
        """🔥 100% Unique Song Autoplay Finder (कभी भी सेम गाना दोबारा नहीं बजाएगा!)"""
        base_title = (getattr(current, "ytitle", None) or getattr(current, "title", "") if current else "").strip()
        channel = (getattr(current, "channel_name", "") if current else "").strip()
        if current:
            self._record_song(chat_id, getattr(current, "id", ""), base_title)

        # 🔥 कभी भी पुराने गाने का नाम सर्च मत करो वरना वही गाना फिर आएगा! सिंगर या नए हिट्स सर्च करो:
        artist_pool = [
            "Arijit Singh Superhit Song", "Atif Aslam Hit Song", "Pritam Bollywood Hit Song",
            "Vishal Mishra Hit Song", "Jubin Nautiyal Romantic Song", "KK Best Hindi Song",
            "Shreya Ghoshal Hit Song", "Darshan Raval Hit Song", "B Praak Hit Song",
            "AP Dhillon Hit Song", "Diljit Dosanjh Hit Song", "Karan Aujla Hit Song",
            "Badshah Party Song", "Yo Yo Honey Singh Hit Song", "Anuv Jain Song",
            "King New Hindi Song", "emraan hashmi hit song", "Trending Hindi Song 2025"
        ]
        random.shuffle(artist_pool)
        queries = []
        if channel and channel.lower() not in ("youtube", "unknown", "t-series", "zee music company", "sony music india"):
            queries.append(f"{channel} top hit song")
        queries.extend(artist_pool[:4])

        # LAYER 1: Direct py_yt Search
        for mod_name in ("py_yt", "youtubesearchpython.__future__"):
            try:
                mod = __import__(mod_name, fromlist=["VideosSearch"])
                VideosSearch = getattr(mod, "VideosSearch")
                for q in queries[:3]:
                    search = VideosSearch(q, limit=12)
                    res_data = await asyncio.wait_for(search.next(), timeout=10.0)
                    results = res_data.get("result", [])
                    random.shuffle(results)
                    for r in results:
                        vid = str(r.get("id") or "")
                        r_title = str(r.get("title") or "")
                        dur_str = r.get("duration") or ""
                        if not dur_str or ":" not in dur_str:
                            continue
                        parts = [int(p) for p in dur_str.split(":")]
                        dur_sec = parts[0] * 60 + parts[1] if len(parts) == 2 else 9999
                        # 8 मिनट से बड़े Jukebox और पुराने गानों को छोड़ दो!
                        if dur_sec > 480 or dur_sec < 90:
                            continue
                        if not self._is_duplicate_song(chat_id, vid, r_title, base_title):
                            self._record_song(chat_id, vid, r_title)
                            return Track(
                                id=vid,
                                channel_name=r.get("channel", {}).get("name", "YouTube"),
                                duration=dur_str,
                                duration_sec=dur_sec,
                                title=r_title[:45],
                                url=r.get("link") or f"https://www.youtube.com/watch?v={vid}",
                                thumbnail=(r.get("thumbnails") or [{}])[-1].get("url", config.DEFAULT_THUMB),
                                view_count=r.get("viewCount", {}).get("short", ""),
                            )
            except Exception:
                pass

        # LAYER 2: Fallback yt.search
        for method_name in ("search", "track"):
            fn = getattr(yt, method_name, None)
            if callable(fn):
                for q in queries:
                    try:
                        res = await asyncio.wait_for(fn(q), timeout=10.0)
                        if res:
                            items = res if isinstance(res, list) else [res]
                            for item in items:
                                vid = str(getattr(item, "id", ""))
                                r_title = str(getattr(item, "title", ""))
                                if not self._is_duplicate_song(chat_id, vid, r_title, base_title):
                                    self._record_song(chat_id, vid, r_title)
                                    return item
                    except Exception:
                        pass
        return None

    async def play_next(self, chat_id: int, control_message=None, force_new_message: bool = False) -> None:
        if chat_id not in self._play_next_locks:
            self._play_next_locks[chat_id] = asyncio.Lock()
        lock = self._play_next_locks[chat_id]
        if lock.locked():
            return
        async with lock:
            try:
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

                current = queue.get_current(chat_id) or self._last_played.get(chat_id)
                old_current_message_id = getattr(current, "message_id", None) if current else None

                if loop_mode == 1 and current:
                    current.time = 0
                    current._start_clock = time_mod.time()
                    await self._delete_old_player(target_chat, old_current_message_id)
                    await self.play_media(chat_id, None, current, message_chat_id=message_chat_id)
                    return
                
                media = queue.get_next(chat_id)

                if not media:
                    if self.autoplay_enabled(chat_id):
                        _autoplay_msg = None
                        try:
                            # 🔥 सबसे पहले पुराना प्लेयर डिलीट करो ताकि चैट एकदम साफ़ रहे!
                            await self._delete_old_player(target_chat, old_current_message_id)
                            _autoplay_msg = await app.send_message(chat_id=target_chat, text="🔄 Searching New Autoplay Song...")
                            _next_track = await self._fetch_autoplay_track(chat_id, current)
                            
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
                                    except Exception:
                                        _next_track.file_path = None
                                
                                if _next_track.file_path:
                                    queue.add(chat_id, _next_track)
                                    await self.play_media(chat_id, _autoplay_msg, _next_track, message_chat_id=message_chat_id)
                                    return
                        except Exception:
                            pass
                        
                        if _autoplay_msg:
                            try:
                                await _autoplay_msg.delete()
                            except Exception:
                                pass

                    await self._delete_old_player(target_chat, old_current_message_id)
                    if config.AUTO_END:
                        _lang = await lang.get_lang(chat_id)
                        try:
                            await app.send_message(chat_id=chat_id, text=_lang.get("auto_end", "✅ Queue finished. Stream ended automatically."))
                        except Exception:
                            pass
                    return await self.stop(chat_id)

                # 🔥 क्यू के अगले गाने से पहले पुराना प्लेयर मैसेज तुरंत डिलीट करो!
                await self._delete_old_player(target_chat, old_current_message_id, getattr(media, "message_id", None))

                if not media.file_path:
                    is_live = getattr(media, 'is_live', False)
                    media.file_path = await yt.download(media.id, is_live=is_live, video=getattr(media, 'video', False))
                    if not media.file_path:
                        await self.stop(chat_id)
                        return

                await self.play_media(chat_id, control_message, media, message_chat_id=message_chat_id)
            except Exception:
                try:
                    await self.stop(chat_id)
                except Exception:
                    pass

    async def set_autoplay(self, chat_id: int, enabled: bool | None = None) -> bool:
        chat_id = int(chat_id)
        if enabled is None:
            enabled = not bool(_PLAYER_AUTOPLAY.get(chat_id, False))
        _PLAYER_AUTOPLAY[chat_id] = bool(enabled)
        
        try:
            media = queue.get_current(chat_id) or self._last_played.get(chat_id)
            if media:
                target_chat = getattr(media, "target_chat_id", chat_id)
                msg_id = getattr(media, "message_id", None) or _PLAYER_LAST_MSG.get(target_chat)
                base_text = getattr(media, "player_text", "") or _PLAYER_LAST_TEXT.get(target_chat, "")
                playing = await db.playing(chat_id)
                if msg_id and base_text:
                    await edit_player(target_chat, msg_id, base_text, media, playing=playing, autoplay=bool(enabled))
        except Exception:
            pass
        return bool(enabled)

    def autoplay_enabled(self, chat_id: int) -> bool:
        return bool(_PLAYER_AUTOPLAY.get(int(chat_id), False))

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
                        await self.play_next(chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop(update.chat_id)

    async def auto_update_player(self):
        tick = 0
        while True:
            await asyncio.sleep(1)
            tick += 1
            for chat_id in list(self.active_chats):
                try:
                    playing = await db.playing(chat_id)
                    media = queue.get_current(chat_id) or self._last_played.get(chat_id)
                    if not media:
                        continue
                        
                    duration = _parse_duration(media)
                    media.duration_sec = duration
                    played = _get_exact_played(media, duration)
                    media.time = played
                    
                    if playing and duration > 0 and played >= duration and not getattr(media, "_auto_ended", False):
                        media._auto_ended = True
                        asyncio.create_task(self.play_next(chat_id))
                        continue
                    
                    if tick % 5 == 0:
                        target_chat = getattr(media, "target_chat_id", chat_id)
                        msg_id = getattr(media, "message_id", None) or _PLAYER_LAST_MSG.get(target_chat)
                        base_text = getattr(media, "player_text", "") or _PLAYER_LAST_TEXT.get(target_chat, "")
                        
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
        logger.info("📞 PyTgCalls client(s) started & 1s Watchdog Timer Loop is running.")
                
