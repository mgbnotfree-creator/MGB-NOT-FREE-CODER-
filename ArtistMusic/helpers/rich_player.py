import time
from pyrogram import types
from ArtistMusic import app

def _time_format(sec: int, duration: int) -> str:
    sec = max(0, int(sec or 0))
    return time.strftime("%H:%M:%S" if duration >= 3600 else "%M:%S", time.gmtime(sec))

def progress_text(played_sec: int, duration_sec: int) -> str:
    if duration_sec <= 0:
        return "LIVE"
    played = max(0, min(played_sec, duration_sec))
    n = 14
    filled = int(round(n * played / duration_sec))
    bar = "━" * filled + "●" + "━" * (n - filled)
    return f"{_time_format(played, duration_sec)} {bar} {_time_format(duration_sec, duration_sec)}"

def _styles(playing: bool):
    """🔥 हर 5 सेकंड में कलर्स बदलेगा"""
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
    label = "II Pause" if playing else "▷ Resume"
    p = progress_text(played_sec, duration_sec)
    
    ap_label = "AUTOPLAY : ON" if autoplay else "AUTOPLAY : OFF"
    ap_style = "success" if autoplay else "primary"
    
    return (
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{time_style}" data="controls status {chat_id}">{p}</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{state_style}" data="controls {state} {chat_id}">{label}</tg-button>'
        f'<tg-button type="callback_data" style="{time_style}" data="controls replay {chat_id}">↻ Replay</tg-button>'
        f'<tg-button type="callback_data" style="{replay_style}" data="controls skip {chat_id}">⚠︎ Skip</tg-button>'
        f'<tg-button type="callback_data" style="{queue_style}" data="controls stop {chat_id}">▢ Stop</tg-button>'
        f'</tg-button-row>'
        f'<tg-button-row align="center">'
        f'<tg-button type="callback_data" style="{ap_style}" data="controls autoplay {chat_id}">{ap_label}</tg-button>'
        f'<tg-button type="callback_data" style="danger" data="controls close {chat_id}">• CLOSE •</tg-button>'
        f'</tg-button-row>'
    )

async def send_player(chat_id, text, photo, media, playing=True, autoplay=False):
    played = getattr(media, "time", 1) or 1
    duration = getattr(media, "duration_sec", 0) or 0
    markup = get_player_html(chat_id, played, duration, playing, autoplay)
    
    sent = await app.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=text,
        reply_markup=markup
    )
    return sent.id

async def edit_player(chat_id, message_id, text, media, playing=True, photo=None, autoplay=False):
    try:
        played = getattr(media, "time", 1) or 1
        duration = getattr(media, "duration_sec", 0) or 0
        markup = get_player_html(chat_id, played, duration, playing, autoplay)

        if photo:
            from pyrogram.types import InputMediaPhoto
            await app.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=photo, caption=text if text else None),
                reply_markup=markup
            )
        else:
            await app.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup
            )
        return True
    except Exception as e:
        return False
    
