import html
import json
import os
import re
import time
import urllib.parse
from typing import Optional
import aiohttp

# 🚀 CHANGED: config और tune को इम्पोर्ट किया गया है ताकि Autoplay काम करे
from ArtistMusic import config, tune

_PLAYER_PHOTOS: dict[tuple[int, int], str] = {}
_PLAYER_MEDIA: dict[tuple[int, int], str] = {}
_PLAYER_LOCKS: dict[tuple[int, int], object] = {}

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


def controls_html(chat_id: int, media, *, timer: Optional[str] = None,
                  playing: bool = True, remove: bool = False, queue_mode: bool = False,
                  autoplay: bool = False) -> str:
    if remove:
        return ""

    time_style, replay_style, state_style, queue_style = _styles(playing)
    state = "pause" if playing else "resume"
    label = "Pause" if playing else "Resume"
    p = html.escape(progress_text(media, timer))

    if queue_mode:
        return (
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="success" data="controls resume {chat_id}">▷</tg-button>'
            f'<tg-button type="callback_data" style="primary" data="controls pause {chat_id}">∣ ∣</tg-button>'
            f'<tg-button type="callback_data" style="primary" data="controls skip {chat_id}">>></tg-button>'
            f'<tg-button type="callback_data" style="danger" data="controls stop {chat_id}">▣</tg-button>'
            f'</tg-button-row>'
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="danger" data="controls close {chat_id}">🗑</tg-button>'
            f'</tg-button-row>'
        )

    autoplay_label = "ㅤㅤㅤㅤㅤㅤㅤAutoplay: ONㅤㅤㅤㅤㅤㅤㅤ" if autoplay else "ㅤㅤㅤㅤㅤㅤㅤAutoplay: OFFㅤㅤㅤㅤㅤㅤㅤ"
    autoplay_style = "success" if autoplay else "primary"
    return (
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{time_style}" data="controls status {chat_id}">{p}</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{state_style}" data="controls {state} {chat_id}">{label}</tg-button>'
        f'<tg-button type="callback_data" style="{time_style}" data="controls replay {chat_id}">Replay</tg-button>'
        f'<tg-button type="callback_data" style="{replay_style}" data="controls shuffle {chat_id}">Shuffle</tg-button>'
        f'<tg-button type="callback_data" style="{queue_style}" data="controls skip {chat_id}">Skip</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{queue_style}" data="controls loop {chat_id}">Loop</tg-button>'
        f'<tg-button type="callback_data" style="primary" data="controls close {chat_id}">Close</tg-button>'
        f'<tg-button type="callback_data" style="danger" data="controls stop {chat_id}">Stop</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{autoplay_style}" data="controls autoplay {chat_id}">{autoplay_label}</tg-button>'
        f'</tg-button-row>'
    )


def _format_player_card(base_html: str) -> str:
    clean = _clean_base_html(base_html)
    clean = re.sub(r"</?blockquote\b[^>]*>", "", clean, flags=re.I)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    lines = [line.strip() for line in clean.splitlines() if line.strip()]

    if len(lines) >= 5:
        header = lines[0]
        details = "<br>".join(lines[1:4])
        footer = "<br>".join(lines[4:])
        return (
            f'<blockquote>{header}</blockquote>'
            f'<blockquote>{details}</blockquote>'
            f'<blockquote>{footer}</blockquote>'
        )
    if len(lines) >= 2:
        header = lines[0]
        details = "<br>".join(lines[1:])
        return f'<blockquote>{header}</blockquote><blockquote>{details}</blockquote>'
    return f'<blockquote>{clean}</blockquote>' if clean else ""


def rich_html(base_html: str, chat_id: int, media, *, timer=None,
              playing=True, remove=False, queue_mode=False, autoplay=False) -> str:
    clean = _format_player_card(base_html)
    if remove:
        return clean
    return f"{clean}\n\n{controls_html(chat_id, media, timer=timer, playing=playing, queue_mode=queue_mode, autoplay=autoplay)}"


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
    # 🔥 FIX: अब Autoplay सही डेटाबेस से शो होगा!
    if autoplay is None:
        try:
            autoplay = tune.autoplay_enabled(chat_id)
        except Exception:
            autoplay = False
            
    player_html = rich_html(base_html, chat_id, media, playing=playing, queue_mode=queue_mode, autoplay=autoplay)
    ref = _photo_source(chat_id, 0, media, photo)
    rich = {"html": player_html}
    if ref:
        rich["html"] = f'<img src="tg://photo?id=player_cover"/>\n{player_html}'
        rich["media"] = [{"id": "player_cover", "media": {"type": "photo", "media": ref}}]
    data = {"chat_id": chat_id, "rich_message": rich}
    if reply_to_message_id:
        data["reply_parameters"] = {"message_id": int(reply_to_message_id)}
    result = await _request("sendRichMessage", data)
    msg = result["result"]
    mid = int(msg["message_id"])
    _cache_message_media(chat_id, mid, result, ref)
    return mid


async def edit_player(chat_id: int, message_id: int, base_html: str, media, *, timer=None,
                      playing=True, remove=False, photo=None, autoplay=None) -> bool:
    key = (chat_id, message_id)
    
    # 🔥 FIX: अब Autoplay लाइव अपडेट होगा!
    if autoplay is None:
        try:
            autoplay = tune.autoplay_enabled(chat_id)
        except Exception:
            autoplay = False
            
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


def queue_controls_html(chat_id: int, item_id: str) -> str:
    safe_item_id = html.escape(str(item_id or ""), quote=True)
    return (
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="success" data="queueplay|{chat_id}|{safe_item_id}">ㅤㅤㅤㅤPʟᴀʏ Nᴏᴡㅤㅤㅤㅤ</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="danger" data="controls stop {chat_id}">ㅤㅤSᴛᴏᴘㅤㅤ</tg-button>'
        f'<tg-button type="callback_data" style="primary" data="controls close {chat_id}">ㅤㅤCʟᴏsᴇㅤㅤ</tg-button>'
        f'</tg-button-row>'
    )


def queue_rich_html(base_html: str, chat_id: int, item_id: str = "") -> str:
    clean = _clean_base_html(base_html)
    lines = [line.strip() for line in clean.splitlines() if line.strip()]

    if len(lines) >= 4:
        header = lines[0]
        details = "<br>".join(lines[1:4])
        if len(lines) > 4:
            details += "<br>" + "<br>".join(lines[4:])
        formatted = (
            f'<blockquote>{header}</blockquote>'
            f'<blockquote>{details}</blockquote>'
        )
    else:
        formatted = f'<blockquote>{clean}</blockquote>'

    return f"{formatted}\n\n{queue_controls_html(chat_id, item_id)}"


async def edit_queue_rich_message(message, text: str, chat_id: int, item_id: str = "") -> bool:
    try:
        rich = {"html": queue_rich_html(text, int(chat_id), item_id)}
        result = await _request(
            "sendRichMessage",
            {
                "chat_id": int(chat_id),
                "rich_message": rich,
            },
        )
        try:
            await _request(
                "deleteMessage",
                {"chat_id": int(chat_id), "message_id": int(message.id)},
            )
        except Exception:
            pass
        msg = result.get("result") or {}
        mid = msg.get("message_id")
        if mid:
            _cache_message_media(int(chat_id), int(mid), result, None)
        return True
    except Exception:
        return False


async def send_rich_message(chat_id: int, text: str, reply_markup=None, photo=None, media=None, reply_to_message_id=None, **kwargs):
    return await send_player(
        chat_id,
        text,
        photo=photo,
        media=media,
        reply_to_message_id=reply_to_message_id,
        **kwargs,
    )


async def edit_player_message(chat_id, message_id, base_html, media, *args, **kwargs):
    return await edit_player(chat_id, message_id, base_html, media,
                             timer=kwargs.get("timer"),
                             playing=kwargs.get("playing", True),
                             remove=kwargs.get("remove", False),
                             photo=kwargs.get("photo"))
                                      
