import html
import json
import os
import re
import time
import urllib.parse
from typing import Optional
import aiohttp
import asyncio

from pyrogram import filters
from ArtistMusic import app, config, db

_PLAYER_PHOTOS: dict[tuple[int, int], str] = {}
_PLAYER_MEDIA: dict[tuple[int, int], str] = {}
_PLAYER_LOCKS: dict[tuple[int, int], object] = {}
_PLAYER_AUTOPLAY: dict[int, bool] = {}
_PLAYER_LAST_TEXT: dict[int, str] = {}
_PLAYER_LAST_MSG: dict[int, int] = {}

def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{config.BOT_TOKEN}/{method}"

def _valid_http_url(value) -> bool:
    if not value:
        return False
    try:
        p = urllib.parse.urlsplit(str(value).strip())
        return p.scheme in ("http", "https") and bool(p.netloc) and (p.port is None or 1 <= p.port <= 65535)
    except (ValueError, TypeError):
        return False

def _youtube_thumb(media) -> Optional[str]:
    vid = str(getattr(media, "id", "") or "")
    if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", vid):
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return None

def _str_to_sec(val: str) -> int:
    val = str(val or "").strip()
    if not val or ":" not in val:
        return 0
    try:
        parts = [int(p) for p in val.split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0

def _parse_duration(media, timer_str: Optional[str] = None) -> int:
    dur = int(getattr(media, "duration_sec", 0) or 0)
    if dur > 0:
        return dur
    dur = _str_to_sec(getattr(media, "duration", ""))
    if dur > 0:
        return dur
    if timer_str:
        matches = re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", str(timer_str))
        if len(matches) >= 2:
            return _str_to_sec(matches[-1])
    return 0

def _get_exact_played(media, duration: int, timer_str: Optional[str] = None) -> int:
    start_clock = getattr(media, "_start_clock", None)
    if start_clock is not None:
        if getattr(media, "_paused_at", None):
            played = int(media._paused_at - start_clock)
        else:
            played = int(time.time() - start_clock)
    elif timer_str:
        matches = re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", str(timer_str))
        if matches:
            played = _str_to_sec(matches[0])
        else:
            played = int(float(getattr(media, "time", 0) or 0))
    else:
        played = int(float(getattr(media, "time", 0) or 0))

    if duration > 0:
        return max(0, min(played, duration))
    return max(0, played)

def _time(sec: int, duration: int) -> str:
    sec = max(0, int(sec or 0))
    return time.strftime("%H:%M:%S" if duration >= 3600 else "%M:%S", time.gmtime(sec))

def progress_text(media, timer: Optional[str] = None) -> str:
    """🔥 इसमें छोटा ब्लैक ऐरो (▸) लगाया गया है जो कभी इमोजी में नहीं बदलेगा!"""
    duration = _parse_duration(media, timer)
    if duration <= 0:
        return "LIVE"
    
    played = _get_exact_played(media, duration, timer)
    if media is not None:
        media.time = played
        media.duration_sec = duration

    n = 12
    ratio = played / duration if duration > 0 else 0.0
    filled = int(round(ratio * n))
    filled = max(0, min(n, filled))
    if played >= duration - 1:
        filled = n
        
    # ▸ (Small Black Right-Pointing Triangle) - कभी भी ब्लू इमोजी नहीं बनेगा!
    bar = "—" * filled + "▸" + "—" * (n - filled)
    return f"{_time(played, duration)} {bar} {_time(duration, duration)}"

def _clean_base_html(base_html: str) -> str:
    text = base_html or ""
    text = re.sub(r"<tg-button-row\b[^>]*>.*?</tg-button-row>", "", text, flags=re.I | re.S)
    text = re.sub(r'<a\s+href=([^"\'>\s]+)>', r'<a href="\1">', text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def _styles(playing: bool):
    phase = int(time.time() // 5) % 4 if playing else 0
    palettes = (
        ("danger", "success", "primary", "danger"),
        ("primary", "danger", "success", "primary"),
        ("success", "primary", "danger", "success"),
        ("danger", "success", "primary", "danger"),
    )
    return palettes[phase]

def controls_html(chat_id: int, media, *, timer: Optional[str] = None,
                  playing: bool = True, remove: bool = False, queue_mode: bool = False,
                  autoplay: Optional[bool] = None) -> str:
    if remove:
        return ""
    return get_player_html(chat_id, media, playing=playing, autoplay=autoplay, timer=timer)

def get_player_html(chat_id: int, media, playing: bool = True, autoplay: Optional[bool] = None, timer: Optional[str] = None) -> str:
    time_style, replay_style, state_style, queue_style = _styles(playing)
    
    state = "pause" if playing else "resume"
    label = "ᴘᴀᴜꜱᴇ" if playing else "ᴘʟᴀʏ"
    
    p = html.escape(progress_text(media, timer))
    
    real_ap = bool(_PLAYER_AUTOPLAY.get(int(chat_id), False))
    ap_label = "AUTOPLAY | ON" if real_ap else "AUTOPLAY | OFF"
    ap_style = "success" if real_ap else "danger"
    
    return (
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{time_style}" data="controls status {chat_id}">{p}</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{state_style}" data="controls {state} {chat_id}">{label}</tg-button>'
        f'<tg-button type="callback_data" style="{time_style}" data="controls replay {chat_id}">↻ ʀᴇᴘʟᴀʏ</tg-button>'
        f'<tg-button type="callback_data" style="{replay_style}" data="controls skip {chat_id}">⚠️ ꜱᴋɪᴘ</tg-button>'
        f'<tg-button type="callback_data" style="{queue_style}" data="controls stop {chat_id}">▢ ꜱᴛᴏᴘ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{ap_style}" data="controls autoplay {chat_id}">♾ {ap_label}</tg-button>'
        f'<tg-button type="callback_data" style="primary" data="controls thumb {chat_id}">ᴛʜᴜᴍʙ | ᴏɴ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="danger" data="controls close {chat_id}">• ᴄʟᴏꜱᴇ •</tg-button>'
        f'</tg-button-row>'
    )

def _format_player_card(base_html: str) -> str:
    clean = _clean_base_html(base_html)
    clean = re.sub(r"</?blockquote\b[^>]*>", "", clean, flags=re.I)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    lines = [line.strip() for line in clean.splitlines() if line.strip()]

    if len(lines) >= 4:
        header = lines[0]
        title = lines[1]
        details = lines[2]
        footer = "<br>".join(lines[3:])
        return (
            f'<blockquote>{header}</blockquote>'
            f'<blockquote>{title}<br><br>{details}</blockquote>'
            f'<blockquote>{footer}</blockquote>'
        )
    if len(lines) >= 2:
        header = lines[0]
        details = "<br><br>".join(lines[1:])
        return f'<blockquote>{header}</blockquote><blockquote>{details}</blockquote>'
    return f'<blockquote>{clean}</blockquote>' if clean else ""

def rich_html(base_html: str, chat_id: int, media, *, timer=None, playing=True, remove=False, queue_mode=False, autoplay=None) -> str:
    clean = _format_player_card(base_html)
    if remove:
        return clean
    real_ap = bool(_PLAYER_AUTOPLAY.get(int(chat_id), False))
    return f"{clean}\n\n{get_player_html(chat_id, media, playing, real_ap, timer=timer)}"

async def _request(method: str, data: dict, file_path: Optional[str] = None) -> dict:
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if file_path and os.path.isfile(file_path):
            form = aiohttp.FormData()
            for k, v in data.items():
                form.add_field(k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
            with open(file_path, "rb") as fp:
                form.add_field("player_cover", fp, filename=os.path.basename(file_path), content_type="image/jpeg")
                async with session.post(_api(method), data=form) as r:
                    result = await r.json(content_type=None)
        else:
            async with session.post(_api(method), json=data) as r:
                result = await r.json(content_type=None)
    if not result.get("ok"):
        raise RuntimeError(result.get("description", f"Telegram {method} failed"))
    return result

def _photo_source(chat_id, message_id, media, photo=None):
    cached_file_id = _PLAYER_PHOTOS.get((chat_id, message_id))
    if cached_file_id:
        return cached_file_id
    cached = _PLAYER_MEDIA.get((chat_id, message_id))
    if cached:
        return cached
    if _valid_http_url(photo):
        return str(photo).strip()
    thumb = getattr(media, "thumbnail", None)
    if _valid_http_url(thumb):
        return str(thumb).strip()
    return _youtube_thumb(media)

def _cache_message_media(chat_id, message_id, result, fallback):
    try:
        msg = result.get("result") or {}
        photos = msg.get("photo") or []
        if photos:
            fid = photos[-1].get("file_id")
            if fid:
                _PLAYER_PHOTOS[(chat_id, message_id)] = fid
    except Exception:
        pass
    if fallback:
        _PLAYER_MEDIA[(chat_id, message_id)] = fallback

async def send_player(chat_id: int, base_html: str, photo=None, media=None, reply_to_message_id=None, *, playing=True, queue_mode=False, autoplay=None, **kwargs) -> int:
    chat_id = int(chat_id)
    if base_html:
        _PLAYER_LAST_TEXT[chat_id] = base_html
    if media is not None and not getattr(media, "_start_clock", None):
        media._start_clock = time.time()

    real_ap = bool(_PLAYER_AUTOPLAY.get(chat_id, False))
    player_html = rich_html(base_html, chat_id, media, playing=playing, queue_mode=queue_mode, autoplay=real_ap)
    ref = _photo_source(chat_id, 0, media, photo)
    rich = {"html": player_html}
    if ref:
        rich["html"] = f'<img src="tg://photo?id=player_cover"/>\n{player_html}'
        rich["media"] = [{"id": "player_cover", "media": {"type": "photo", "media": ref}}]
    data = {"chat_id": chat_id, "rich_message": rich}
    if reply_to_message_id:
        data["reply_parameters"] = {"message_id": int(reply_to_message_id)}
    
    try:
        result = await _request("sendRichMessage", data)
        msg = result["result"]
        mid = int(msg["message_id"])
        _PLAYER_LAST_MSG[chat_id] = mid
        _cache_message_media(chat_id, mid, result, ref)
        return mid
    except Exception:
        sent = await app.send_message(chat_id=chat_id, text=player_html)
        _PLAYER_LAST_MSG[chat_id] = sent.id
        return sent.id

async def edit_player(chat_id: int, message_id: int, base_html: str, media, *, timer=None, playing=True, remove=False, photo=None, autoplay=None) -> bool:
    chat_id = int(chat_id)
    message_id = int(message_id)
    key = (chat_id, message_id)
    real_ap = bool(_PLAYER_AUTOPLAY.get(chat_id, False))

    if remove:
        try:
            await _request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
        except Exception:
            return False
        _PLAYER_PHOTOS.pop(key, None)
        _PLAYER_MEDIA.pop(key, None)
        return True

    if base_html:
        _PLAYER_LAST_TEXT[chat_id] = base_html
    else:
        base_html = getattr(media, "player_text", "") or _PLAYER_LAST_TEXT.get(chat_id, "")

    lock = _PLAYER_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _PLAYER_LOCKS[key] = lock

    async with lock:
        ref = _photo_source(chat_id, message_id, media, photo)
        body = rich_html(base_html, chat_id, media, timer=timer, playing=playing, autoplay=real_ap)
        rich = {"html": body}
        if ref:
            rich["html"] = f'<img src="tg://photo?id=player_cover"/>\n{body}'
            rich["media"] = [{"id": "player_cover", "media": {"type": "photo", "media": ref}}]
        try:
            result = await _request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "rich_message": rich,
            })
            if isinstance(result, dict):
                _cache_message_media(chat_id, message_id, result, ref)
            elif ref:
                _PLAYER_MEDIA[key] = ref
            return True
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" in str(e):
                return True
            cached = _PLAYER_PHOTOS.get(key) or _PLAYER_MEDIA.get(key)
            if cached and cached != ref:
                try:
                    rich["html"] = f'<img src="tg://photo?id=player_cover"/>\n{body}'
                    rich["media"] = [{"id": "player_cover", "media": {"type": "photo", "media": cached}}]
                    await _request("editMessageText", {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "rich_message": rich,
                    })
                    return True
                except Exception:
                    pass
            return False

async def edit_rich_message(message, text, markup=None, photo_file_id=None, **kwargs):
    chat_id = int(message.chat.id)
    message_id = int(message.id)
    media = kwargs.get("media")
    if media is None:
        try:
            from ArtistMusic import queue
            media = queue.get_current(chat_id)
        except Exception:
            media = None
    if media is not None:
        return await edit_player(chat_id, message_id, text, media,
                                 timer=kwargs.get("timer"),
                                 playing=kwargs.get("playing", True),
                                 remove=kwargs.get("remove", False),
                                 photo=photo_file_id)
    return False

async def send_rich_message(chat_id: int, text: str, reply_markup=None, photo=None, media=None, reply_to_message_id=None, **kwargs):
    return await send_player(chat_id, text, photo=photo, media=media, reply_to_message_id=reply_to_message_id, **kwargs)

async def edit_player_message(chat_id, message_id, base_html, media, *args, **kwargs):
    return await edit_player(chat_id, message_id, base_html, media,
                             timer=kwargs.get("timer"),
                             playing=kwargs.get("playing", True),
                             remove=kwargs.get("remove", False),
                             photo=kwargs.get("photo"))

@app.on_callback_query(filters.regex(r"autoplay"), group=-1)
async def _master_autoplay_interceptor(client, query):
    try:
        parts = query.data.split()
        chat_id = int(parts[-1]) if len(parts) > 1 and parts[-1].lstrip("-").isdigit() else int(query.message.chat.id)
        new_state = not bool(_PLAYER_AUTOPLAY.get(chat_id, False))
        _PLAYER_AUTOPLAY[chat_id] = new_state
        
        try:
            await query.answer(f"♾ Autoplay: {'ON' if new_state else 'OFF'}", show_alert=False)
        except Exception:
            pass
            
        from ArtistMusic import queue
        media = queue.get_current(chat_id)
        if media:
            base_text = getattr(media, "player_text", "") or _PLAYER_LAST_TEXT.get(chat_id, "")
            playing = await db.playing(chat_id)
            await edit_player(int(query.message.chat.id), int(query.message.id), base_text, media, playing=playing, autoplay=new_state)
        query.stop_propagation()
    except Exception:
        pass
