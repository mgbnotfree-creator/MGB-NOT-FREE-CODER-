import html
import json
import os
import re
import time
import urllib.parse
from typing import Optional
import aiohttp

from ArtistMusic import config

_PLAYER_PHOTOS: dict[tuple[int, int], str] = {}
_PLAYER_MEDIA: dict[tuple[int, int], str] = {}
_PLAYER_LOCKS: dict[tuple[int, int], object] = {}
_PLAYER_AUTOPLAY: dict[int, bool] = {}

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

def _time(sec: int, duration: int) -> str:
    sec = max(0, int(sec or 0))
    return time.strftime("%H:%M:%S" if duration >= 3600 else "%M:%S", time.gmtime(sec))

def progress_text(media, timer: Optional[str] = None) -> str:
    duration = int(getattr(media, "duration_sec", 0) or 0)
    if duration <= 0:
        return timer or "LIVE"
    played = max(0, min(int(float(getattr(media, "time", 0) or 0)), duration))
    n = 14
    filled = int(round(n * played / duration))
    bar = "━" * filled + "●" + "━" * (n - filled)
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
        ("success", "primary", "danger", "success"),
        ("primary", "success", "success", "danger"),
        ("danger", "primary", "success", "primary"),
        ("success", "danger", "primary", "success"),
    )
    return palettes[phase]

def get_player_html(chat_id: int, played_sec: int = 0, duration_sec: int = 0, playing: bool = True, autoplay: bool = False) -> str:
    time_style, replay_style, state_style, queue_style = _styles(playing)
    state = "pause" if playing else "resume"
    label = "⏸ ᴘᴀᴜꜱᴇ" if playing else "▶️ ᴘʟᴀʏ"
    p = progress_text(None, timer=f"{_time(played_sec, duration_sec)} {'━'*7}●{'━'*7} {_time(duration_sec, duration_sec)}") if duration_sec > 0 else "LIVE"
    
    ap_label = "AUTOPLAY | ON" if autoplay else "AUTOPLAY | OFF"
    ap_style = "success" if autoplay else "danger"
    
    return (
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{time_style}" data="controls status {chat_id}">{p}</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{state_style}" data="controls {state} {chat_id}">{label}</tg-button>'
        f'<tg-button type="callback_data" style="{time_style}" data="controls replay {chat_id}">↻ ʀᴇᴘʟᴀʏ</tg-button>'
        f'<tg-button type="callback_data" style="{replay_style}" data="controls skip {chat_id}">⚠︎ ꜱᴋɪᴘ</tg-button>'
        f'<tg-button type="callback_data" style="{queue_style}" data="controls stop {chat_id}">▢ ꜱᴛᴏᴘ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{ap_style}" data="controls autoplay {chat_id}">♾ {ap_label}</tg-button>'
        f'<tg-button type="callback_data" style="primary" data="controls thumb {chat_id}">🖼 ᴛʜᴜᴍʙ | ᴏɴ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="danger" data="controls close {chat_id}">• ᴄʟᴏꜱᴇ •</tg-button>'
        f'</tg-button-row>'
    )

def rich_html(base_html: str, chat_id: int, media, *, timer=None, playing=True, remove=False, queue_mode=False, autoplay=False) -> str:
    clean = _clean_base_html(base_html)
    if remove:
        return clean
    played = getattr(media, "time", 1) or 1
    duration = getattr(media, "duration_sec", 0) or 0
    return f"{clean}\n\n{get_player_html(chat_id, played, duration, playing, autoplay)}"

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
    if autoplay is None:
        autoplay = bool(_PLAYER_AUTOPLAY.get(chat_id, False))
    else:
        autoplay = bool(autoplay)
        _PLAYER_AUTOPLAY[chat_id] = autoplay
        
    player_html = rich_html(base_html, chat_id, media, playing=playing, queue_mode=queue_mode, autoplay=autoplay)
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
        _cache_message_media(chat_id, mid, result, ref)
        return mid
    except Exception:
        sent = await app.send_message(chat_id=chat_id, text=player_html)
        return sent.id

async def edit_player(chat_id: int, message_id: int, base_html: str, media, *, timer=None, playing=True, remove=False, photo=None, autoplay=None) -> bool:
    key = (chat_id, message_id)
    if autoplay is None:
        autoplay = bool(_PLAYER_AUTOPLAY.get(chat_id, False))
    else:
        autoplay = bool(autoplay)
        _PLAYER_AUTOPLAY[chat_id] = autoplay
        
    if remove:
        try:
            await _request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
        except Exception:
            return False
        _PLAYER_PHOTOS.pop(key, None)
        _PLAYER_MEDIA.pop(key, None)
        return True

    lock = _PLAYER_LOCKS.get(key)
    if lock is None:
        import asyncio
        lock = asyncio.Lock()
        _PLAYER_LOCKS[key] = lock

    async with lock:
        ref = _photo_source(chat_id, message_id, media, photo)
        body = rich_html(base_html, chat_id, media, timer=timer, playing=playing, autoplay=autoplay)
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
                    result = await _request("editMessageText", {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "rich_message": rich,
                    })
                    return True
                except Exception:
                    pass
            return False
    
