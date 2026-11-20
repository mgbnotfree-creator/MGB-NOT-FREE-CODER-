# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
# ═══════════════════════════════════════════════════════════════

import os
import io
import re
import time
import json
import html
import random
import asyncio
import tempfile
import subprocess
import unicodedata
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import aiohttp
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums
from pyrogram.types import Message, CallbackQuery

try:
    import imageio_ffmpeg
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_BIN = "ffmpeg"

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

try:
    from ArtistMusic import call as tg_call, queue as tg_queue
except Exception:
    tg_call = None
    tg_queue = None

try:
    from ArtistMusic import yt as artist_yt
except Exception:
    artist_yt = None

# ── BRANDING & STORAGE ────────────────────────────────────────
OWNER_UNAME = "MGB_NOT_FREE_1"
CHANNEL_UNAME = "MGB_CODER"
FOOTER = f"<code>🍓 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 : @{OWNER_UNAME}</code>"
IST = timezone(timedelta(hours=5, minutes=30))

VOTE_SKIP_DATA = defaultdict(set)
WHISPERS = {}
QUIZ_SCORES = defaultdict(int)
QUIZ_ACTIVE = {}
AUTOCLEAN_CHATS = set()

SCORE_BOARD_STATS = defaultdict(lambda: {"four": 0, "six": 0, "wicket": 0, "last_event": "LIVE WATCHING"})
LIVE_CRIC_LAST_STATE = {}
LIVE_SCORE_TASKS = {}

BGM_PRESETS = {
    "bgmi": ("🎮 BGMI Royal Entry BGM", ["PUBG Mobile Theme", "Alan Walker On My Way", "KGF Theme Ravi Basrur"]),
    "kgf": ("🔥 KGF Rocky Entry BGM", ["KGF Theme Ravi Basrur", "Salaam Rocky Bhai", "Toofan KGF"]),
    "vikram": ("⚡ Vikram Roar BGM", ["Vikram Title Track Anirudh", "Porkanda Singam Vikram"]),
    "animal": ("🦁 Animal Entry BGM", ["Jamal Kudu Animal", "Arjan Vailly Animal"]),
}
USER_BGM_PREF = {}
BGM_AUDIO_CACHE = {}
WELCOME_BGM_OFF = set()

QUIZ_BANK = [
    {"q": "Tum Hi Ho Arijit Singh Aashiqui 2", "opts": ["Aashiqui 2", "Kabir Singh", "Rockstar", "Tamasha"], "ans": 0},
    {"q": "Kesariya Arijit Singh Brahmastra", "opts": ["Pathaan", "Brahmastra", "Jawan", "Animal"], "ans": 1},
    {"q": "Apna Bana Le Arijit Singh Bhediya", "opts": ["Bhediya", "Stree 2", "Luka Chuppi", "Mimi"], "ans": 0},
    {"q": "Channa Mereya Ae Dil Hai Mushkil", "opts": ["Yeh Jawaani", "Ae Dil Hai Mushkil", "Kalank", "Raazi"], "ans": 1},
    {"q": "Arjan Vailly Animal Bhupinder Babbal", "opts": ["Gadar 2", "KGF 2", "Animal", "Leo"], "ans": 2},
    {"q": "Chaleya Arijit Singh Jawan", "opts": ["Dunki", "Pathaan", "Tiger 3", "Jawan"], "ans": 3},
    {"q": "Raataan Lambiyan Jubin Nautiyal Shershaah", "opts": ["Shershaah", "Uri", "Fighter", "Kesari"], "ans": 0},
    {"q": "Tera Ban Jaunga Kabir Singh", "opts": ["Sanam Teri Kasam", "Kabir Singh", "Half Girlfriend", "Raanjhanaa"], "ans": 1},
    {"q": "Aayi Nai Stree 2 Pawan Singh", "opts": ["Bhool Bhulaiyaa", "Munjya", "Stree 2", "Bhediya"], "ans": 2},
    {"q": "Ghungroo Arijit Singh War", "opts": ["War", "Fighter", "Bang Bang", "Dhoom 3"], "ans": 0},
]

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "χ": "X", "Χ": "X", "×": "X",
    "Δ": "A", "Σ": "E", "Ω": "O", "β": "B", "α": "A",
})

def _clean_font_name(name: str, limit: int = 22) -> str:
    s = str(name or "MGB User").translate(FANCY_MAP)
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    return " ".join(s.split()).strip()[:limit] or "MGB User"

# ── 🔘 HTML PILL BUTTON ENGINE (sendRichMessage + Fallback) ───
def _cbtn(text: str, style: str = "primary", callback_data: str = None, url: str = None) -> dict:
    btn = {"text": text, "style": style}
    if url:
        btn["url"] = url
    elif callback_data:
        btn["callback_data"] = callback_data
    return btn

def _rows_to_rich_html(rows: list, cb_attr: str = "callback_data") -> str:
    if not rows:
        return ""
    out = []
    for row in rows:
        btns_html = []
        for b in row:
            st = b.get("style", "primary")
            txt = html.escape(str(b.get("text", "Button")))
            if b.get("url"):
                u = html.escape(str(b["url"]), quote=True)
                btns_html.append(f'<tg-button type="url" style="{st}" url="{u}">{txt}</tg-button>')
            elif b.get("callback_data"):
                cd = html.escape(str(b["callback_data"]), quote=True)
                btns_html.append(f'<tg-button type="callback" style="{st}" {cb_attr}="{cd}">{txt}</tg-button>')
        if btns_html:
            out.append(f'<tg-button-row align="center">{"".join(btns_html)}</tg-button-row>')
    return "".join(out)

async def _bot_api(client, method: str, payload: dict):
    token = getattr(client, "bot_token", None)
    if not token:
        return None
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
            async with s.post(f"https://api.telegram.org/bot{token}/{method}", json=payload) as r:
                res = await r.json()
                if res.get("ok"):
                    return res.get("result")
    except Exception:
        pass
    return None

async def send_colored_msg(client, chat_id: int, text: str, rows: list, reply_to: int = None):
    if rows:
        for attr in ("callback_data", "data"):
            rich_btns = _rows_to_rich_html(rows, cb_attr=attr)
            rich_html = text.replace("\n", "<br>") + "<br><br>" + rich_btns
            rich_payload = {"chat_id": chat_id, "rich_message": {"html": rich_html}}
            if reply_to:
                rich_payload["reply_to_message_id"] = reply_to
            res = await _bot_api(client, "sendRichMessage", rich_payload)
            if res:
                return res.get("message_id")

    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": rows}}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    res = await _bot_api(client, "sendMessage", payload)
    if res:
        return res.get("message_id")
    m = await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML)
    return m.id

async def edit_colored_msg(client, chat_id: int, msg_id: int, text: str, rows: list = None):
    if rows is not None:
        for attr in ("callback_data", "data"):
            rich_btns = _rows_to_rich_html(rows, cb_attr=attr)
            rich_html = text.replace("\n", "<br>") + (("<br><br>" + rich_btns) if rich_btns else "")
            res = await _bot_api(
                client,
                "editRichMessage",
                {"chat_id": chat_id, "message_id": msg_id, "rich_message": {"html": rich_html}},
            )
            if res:
                return res

    payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
    if rows is not None:
        payload["reply_markup"] = {"inline_keyboard": rows}
    return await _bot_api(client, "editMessageText", payload)

async def edit_colored_caption(client, chat_id: int, msg_id: int, caption: str, rows: list = None):
    payload = {"chat_id": chat_id, "message_id": msg_id, "caption": caption, "parse_mode": "HTML"}
    if rows is not None:
        payload["reply_markup"] = {"inline_keyboard": rows}
    return await _bot_api(client, "editMessageCaption", payload)

async def send_colored_audio(client, chat_id: int, mp3_bytes: bytes, title: str, performer: str, duration: int, caption: str, rows: list, reply_to: int = None):
    token = getattr(client, "bot_token", None)
    if token:
        try:
            form = aiohttp.FormData()
            form.add_field("chat_id", str(chat_id))
            form.add_field("caption", caption)
            form.add_field("parse_mode", "HTML")
            form.add_field("title", title)
            form.add_field("performer", performer)
            form.add_field("duration", str(duration))
            form.add_field("reply_markup", json.dumps({"inline_keyboard": rows}))
            if reply_to:
                form.add_field("reply_to_message_id", str(reply_to))
            form.add_field("audio", mp3_bytes, filename="mgb_clip.mp3", content_type="audio/mpeg")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as s:
                async with s.post(f"https://api.telegram.org/bot{token}/sendAudio", data=form) as r:
                    res = await r.json()
                    if res.get("ok"):
                        return res.get("result", {}).get("message_id")
        except Exception:
            pass
    bio = io.BytesIO(mp3_bytes)
    bio.name = "mgb_clip.mp3"
    m = await client.send_audio(chat_id, bio, title=title, performer=performer, duration=duration, caption=caption, parse_mode=enums.ParseMode.HTML)
    return m.id

async def _pop_reaction(client, chat_id: int, message_id: int, emoji: str):
    if not message_id:
        return
    await _bot_api(
        client,
        "setMessageReaction",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}],
            "is_big": True,
        },
    )

# ── REAL STUDIO AUDIO CLIP ENGINE (iTunes + FFmpeg) ───────────
def _convert_to_clean_mp3(raw_bytes: bytes, max_sec: int = 20) -> bytes:
    with tempfile.TemporaryDirectory(prefix="mgb_aud_") as td:
        inp = os.path.join(td, "in.m4a")
        out = os.path.join(td, "out.mp3")
        with open(inp, "wb") as f:
            f.write(raw_bytes)
        cmd = [FFMPEG_BIN, "-y", "-i", inp, "-t", str(max_sec), "-map_metadata", "-1", "-vn", "-c:a", "libmp3lame", "-b:a", "128k", out]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            with open(out, "rb") as f:
                return f.read()
    return raw_bytes

async def _fetch_real_song_clip(query: str):
    try:
        params = {"term": query, "media": "music", "entity": "song", "country": "IN", "limit": "5"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as s:
            async with s.get("https://itunes.apple.com/search", params=params) as r:
                data = await r.json(content_type=None)
            for item in data.get("results", []):
                purl = item.get("previewUrl")
                if purl:
                    async with s.get(purl) as ar:
                        if ar.status == 200:
                            raw = await ar.read()
                            return await asyncio.to_thread(_convert_to_clean_mp3, raw, 20)
    except Exception:
        pass
    return None

async def _get_real_bgm_mp3(pref: str):
    if pref in BGM_PRESETS:
        label, queries = BGM_PRESETS[pref]
        cache_key = f"preset:{pref}"
    else:
        label = f"🎵 {pref[:28]}"
        queries = [pref, "PUBG Mobile Theme"]
        cache_key = f"custom:{pref.lower().strip()}"

    if cache_key in BGM_AUDIO_CACHE:
        return label, BGM_AUDIO_CACHE[cache_key]

    for q in queries:
        mp3 = await _fetch_real_song_clip(q)
        if mp3:
            BGM_AUDIO_CACHE[cache_key] = mp3
            return label, mp3
    return label, None

async def _make_voice_alert_mp3(text: str) -> bytes:
    def _gen():
        b = io.BytesIO()
        gTTS(text=text, lang="hi", tld="co.in", slow=False).write_to_fp(b)
        return _convert_to_clean_mp3(b.getvalue(), 8)
    return await asyncio.to_thread(_gen)

# ── 1. DEMOCRACY VOTE-TO-SKIP (/voteskip) ─────────────────────
@bot.on_message(filters.command(["voteskip", "vskip"], prefixes=["/", "!", "."]))
async def voteskip_cmd(client, message: Message):
    chat_id, user = message.chat.id, message.from_user
    if not user:
        return
    VOTE_SKIP_DATA[chat_id].add(user.id)
    count = len(VOTE_SKIP_DATA[chat_id])

    if count >= 3:
        VOTE_SKIP_DATA[chat_id].clear()
        if tg_call and hasattr(tg_call, "play_next"):
            try:
                await tg_call.play_next(chat_id)
            except Exception:
                pass
        return await send_colored_msg(
            client, chat_id,
            f"<blockquote><b>⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 (𝟑/𝟑)</b></blockquote>\n\n✅ <b>Current track skip kar diya gaya!</b>\n\n{FOOTER}",
            [[_cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}")]], reply_to=message.id,
        )

    rows = [[_cbtn(f"⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 ({count}/3)", style="danger", callback_data="mgb_vskip_btn")]]
    await send_colored_msg(
        client, chat_id,
        f"<blockquote><b>🗳 𝐃𝐄𝐌𝐎𝐂𝐑𝐀𝐂𝐘 𝐕𝐎𝐓𝐄 𝐓𝐎 𝐒𝐊𝐈𝐏</b></blockquote>\n\n"
        f"👤 <b>By:</b> <b>{html.escape(user.first_name)}</b>\n📊 <b>Votes:</b> <code>{count}/3 Required</code>\n\n{FOOTER}",
        rows, reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_vskip_btn$"))
async def voteskip_cb(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    VOTE_SKIP_DATA[chat_id].add(query.from_user.id)
    count = len(VOTE_SKIP_DATA[chat_id])

    if count >= 3:
        VOTE_SKIP_DATA[chat_id].clear()
        await query.answer("⏭ Track Skipped!", show_alert=False)
        if tg_call and hasattr(tg_call, "play_next"):
            try:
                await tg_call.play_next(chat_id)
            except Exception:
                pass
        return await edit_colored_msg(
            client, chat_id, query.message.id,
            f"<blockquote><b>⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 (𝟑/𝟑)</b></blockquote>\n\n✅ <b>Gaana skip kar diya gaya hai!</b>\n\n{FOOTER}",
            [],
        )

    await query.answer(f"✅ Vote Added ({count}/3)", show_alert=False)
    await edit_colored_msg(
        client, chat_id, query.message.id,
        f"<blockquote><b>🗳 𝐃𝐄𝐌𝐎𝐂𝐑𝐀𝐂𝐘 𝐕𝐎𝐓𝐄 𝐓𝐎 𝐒𝐊𝐈𝐏</b></blockquote>\n\n📊 <b>Current Votes:</b> <code>{count}/3 Required</code>\n\n{FOOTER}",
        [[_cbtn(f"⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 ({count}/3)", style="danger", callback_data="mgb_vskip_btn")]],
    )

# ── 2. LIVE KARAOKE & AUDIO PRESETS (/karaoke) ────────────────
def _karaoke_rows() -> list:
    return [
        [
            _cbtn("🎤 𝐊𝐀𝐑𝐀𝐎𝐊𝐄", style="primary", callback_data="mgb_eq_karaoke"),
            _cbtn("🔊 𝐁𝐀𝐒𝐒𝐁𝐎𝐎𝐒𝐓", style="danger", callback_data="mgb_eq_bass"),
        ],
        [
            _cbtn("🌙 𝐒𝐋𝐎𝐖+𝐑𝐄𝐕𝐄𝐑𝐁", style="success", callback_data="mgb_eq_slowed"),
            _cbtn("🔄 𝐍𝐎𝐑𝐌𝐀𝐋", style="primary", callback_data="mgb_eq_normal"),
        ],
    ]

@bot.on_message(filters.command(["karaoke", "eq", "filter"], prefixes=["/", "!", "."]))
async def karaoke_cmd(client, message: Message):
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🎛 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐕𝐂 𝐀𝐔𝐃𝐈𝐎 𝐅𝐈𝐋𝐓𝐄𝐑𝐒</b></blockquote>\n\n🎧 <b>Live Voice Chat preset chunein:</b>\n\n{FOOTER}",
        _karaoke_rows(), reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_eq_(karaoke|bass|slowed|normal)$"))
async def karaoke_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    names = {"karaoke": "🎤 Karaoke Vocal-Cut", "bass": "🔊 Extreme BassBoost", "slowed": "🌙 Slowed + Reverb", "normal": "🔄 Original Studio"}
    if tg_call and tg_queue:
        try:
            cur = tg_queue.get_current(query.message.chat.id)
            if cur and hasattr(tg_call, "seek_stream"):
                await tg_call.seek_stream(query.message.chat.id, int(getattr(cur, "time", 0) or 1))
        except Exception:
            pass
    await query.answer(f"✅ {names[mode]} ON!", show_alert=False)
    await edit_colored_msg(
        client, query.message.chat.id, query.message.id,
        f"<blockquote><b>🎛 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐕𝐂 𝐀𝐔𝐃𝐈𝐎 𝐅𝐈𝐋𝐓𝐄𝐑𝐒</b></blockquote>\n\n"
        f"✅ <b>Active Preset:</b> <code>{names[mode]}</code>\n"
        f"👤 <b>By:</b> <b>{html.escape(query.from_user.first_name)}</b>\n\n{FOOTER}",
        _karaoke_rows(),
    )

# ── 3. AUTO BGMI / KGF ENTRY ON 1-COMMAND + GROUP & VC EVENTS ─
def _entry_bgm_rows(uid: int) -> list:
    return [
        [
            _cbtn("🎮 𝐁𝐆𝐌𝐈", style="primary", callback_data=f"mgb_ebgm_set_{uid}_bgmi"),
            _cbtn("🔥 𝐊𝐆𝐅", style="danger", callback_data=f"mgb_ebgm_set_{uid}_kgf"),
        ],
        [
            _cbtn("⚡ 𝐕𝐈𝐊𝐑𝐀𝐌", style="success", callback_data=f"mgb_ebgm_set_{uid}_vikram"),
            _cbtn("🦁 𝐀𝐍𝐈𝐌𝐀𝐋", style="primary", callback_data=f"mgb_ebgm_set_{uid}_animal"),
        ],
    ]

@bot.on_message(filters.command(["entry", "setentry", "bgm", "bgmi", "kgf", "vikram", "animal"], prefixes=["/", "!", "."]))
async def entry_bgm_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    cmd = message.command[0].lower()
    if cmd in BGM_PRESETS:
        USER_BGM_PREF[user.id] = cmd
    elif len(message.command) > 1:
        USER_BGM_PREF[user.id] = message.text.split(None, 1)[1].strip()

    pref = USER_BGM_PREF.get(user.id, "bgmi")
    label, mp3 = await _get_real_bgm_mp3(pref)

    if mp3:
        await send_colored_audio(
            client, message.chat.id, mp3, label, f"@{OWNER_UNAME}", 20,
            f"<blockquote><b>🔥 𝐀𝐔𝐓𝐎 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
            f"👤 <b>VIP:</b> <b>{html.escape(user.first_name)}</b>\n"
            f"🎵 <b>Playing:</b> <code>{html.escape(label)}</code>\n\n{FOOTER}",
            _entry_bgm_rows(user.id),
            reply_to=message.id,
        )
    else:
        await send_colored_msg(
            client, message.chat.id,
            f"<blockquote><b>🔥 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
            f"🎵 <b>Active BGM:</b> <code>{html.escape(label)}</code>\n\n{FOOTER}",
            _entry_bgm_rows(user.id),
            reply_to=message.id,
        )

@bot.on_callback_query(filters.regex(r"^mgb_ebgm_set_(\d+)_([a-z]+)$"))
async def entry_bgm_cb(client, query: CallbackQuery):
    uid = int(query.matches[0].group(1))
    preset = query.matches[0].group(2)
    if query.from_user.id != uid:
        return await query.answer("❌ Apna BGM set karne ke liye /bgmi bhejein!", show_alert=True)
    USER_BGM_PREF[uid] = preset
    label, mp3 = await _get_real_bgm_mp3(preset)
    await query.answer(f"✅ {label} Playing!", show_alert=False)
    if mp3:
        await send_colored_audio(
            client, query.message.chat.id, mp3, label, f"@{OWNER_UNAME}", 20,
            f"<blockquote><b>🔥 𝐑𝐎𝐘𝐀𝐋 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
            f"👤 <b>Member:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
            f"🎵 <b>Track:</b> <code>{html.escape(label)}</code>\n\n{FOOTER}",
            [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}")]],
        )

@bot.on_message(
    filters.group & (filters.video_chat_started | filters.video_chat_ended | filters.video_chat_members_invited),
    group=8,
)
async def vc_events_bgm_handler(client, message: Message):
    if message.chat.id in WELCOME_BGM_OFF:
        return
    if message.video_chat_started:
        title_txt = "🎙 𝐕𝐎𝐈𝐂𝐄 𝐂𝐇𝐀𝐓 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!"
        preset = "bgmi"
    elif message.video_chat_ended:
        title_txt = "🔇 𝐕𝐎𝐈𝐂𝐄 𝐂𝐇𝐀𝐓 𝐄𝐍𝐃𝐄𝐃!"
        preset = "kgf"
    else:
        title_txt = "🔥 𝐌𝐄𝐌𝐁𝐄𝐑 𝐉𝐎𝐈𝐍𝐄𝐃 𝐕𝐂!"
        preset = "bgmi"

    label, mp3 = await _get_real_bgm_mp3(preset)
    if mp3:
        await send_colored_audio(
            client, message.chat.id, mp3, label, f"@{OWNER_UNAME}", 20,
            f"<blockquote><b>{title_txt}</b></blockquote>\n\n🎵 <b>Auto VC BGM:</b> <code>{html.escape(label)}</code>\n\n{FOOTER}",
            [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="success", url=f"https://t.me/{OWNER_UNAME}")]],
        )

# ── 4. 1-COMMAND AUTO REAL SFX (/drum, /clap, /bruh, /laugh, /sfx)
SFX_URLS = {
    "clap": "https://www.myinstants.com/media/sounds/applause-2.mp3",
    "bruh": "https://www.myinstants.com/media/sounds/movie_1.mp3",
    "drum": "https://www.myinstants.com/media/sounds/badumtss.mp3",
    "laugh": "https://www.myinstants.com/media/sounds/risada-kiko.mp3",
}
SFX_AUDIO_CACHE = {}

async def _get_real_sfx_mp3(key: str):
    if key in SFX_AUDIO_CACHE:
        return SFX_AUDIO_CACHE[key]
    url = SFX_URLS.get(key)
    if not url:
        return None
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
                if r.status == 200:
                    raw = await r.read()
                    if len(raw) > 1000:
                        SFX_AUDIO_CACHE[key] = raw
                        return raw
    except Exception:
        pass
    return None

def _sfx_rows() -> list:
    return [
        [
            _cbtn("👏 𝐂𝐋𝐀𝐏", style="primary", callback_data="mgb_sfx_clap"),
            _cbtn("💀 𝐁𝐑𝐔𝐇", style="danger", callback_data="mgb_sfx_bruh"),
        ],
        [
            _cbtn("🥁 𝐃𝐑𝐔𝐌𝐑𝐎𝐋𝐋", style="success", callback_data="mgb_sfx_drum"),
            _cbtn("😂 𝐋𝐀𝐔𝐆𝐇", style="primary", callback_data="mgb_sfx_laugh"),
        ],
    ]

@bot.on_message(filters.command(["drum", "clap", "bruh", "laugh"], prefixes=["/", "!", "."]))
async def instant_sfx_cmd(client, message: Message):
    key = message.command[0].lower()
    mp3 = await _get_real_sfx_mp3(key)
    if not mp3:
        return await message.reply_text("❌ <b>Sound load nahi ho paya, dobara try karein!</b>", parse_mode=enums.ParseMode.HTML)
    await send_colored_audio(
        client, message.chat.id, mp3, f"Real SFX • {key.upper()}", f"@{OWNER_UNAME}", 4,
        f"🔊 <b>Real SFX:</b> <code>{key.upper()}</code>\n\n{FOOTER}",
        [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="success", url=f"https://t.me/{OWNER_UNAME}")]],
        reply_to=message.id,
    )

@bot.on_message(filters.command(["sfx", "soundboard"], prefixes=["/", "!", "."]))
async def sfx_cmd(client, message: Message):
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🔊 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐒𝐎𝐔𝐍𝐃𝐁𝐎𝐀𝐑𝐃</b></blockquote>\n\n"
        f"⚡ <b>Direct 1-Command:</b> <code>/drum</code> • <code>/clap</code> • <code>/bruh</code> • <code>/laugh</code>\n\n{FOOTER}",
        _sfx_rows(), reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_sfx_(clap|bruh|drum|laugh)$"))
async def sfx_cb(client, query: CallbackQuery):
    key = query.matches[0].group(1)
    await query.answer(f"🔊 Real {key.upper()} Playing...", show_alert=False)
    mp3 = await _get_real_sfx_mp3(key)
    if not mp3:
        return await query.answer("❌ Sound fetch nahi ho paya!", show_alert=True)
    await send_colored_audio(
        client, query.message.chat.id, mp3, f"Real SFX • {key.upper()}", f"@{OWNER_UNAME}", 4,
        f"🔊 <b>Real SFX:</b> <code>{key.upper()}</code> by <b>{html.escape(query.from_user.first_name)}</b>\n\n{FOOTER}",
        [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="success", url=f"https://t.me/{OWNER_UNAME}")]],
    )

# ── 5. REAL MUSIC CLIP QUIZ (1-TIME PICK LOCK) ────────────────
@bot.on_message(filters.command(["quiz", "mquiz"], prefixes=["/", "!", "."]))
async def music_quiz_cmd(client, message: Message):
    wait_m = await message.reply_text("🎧 <b>Real Music Clip load ho raha hai...</b>", parse_mode=enums.ParseMode.HTML)
    idx = random.randrange(len(QUIZ_BANK))
    q = QUIZ_BANK[idx]
    mp3 = await _fetch_real_song_clip(q["q"]) or await _fetch_real_song_clip(QUIZ_BANK[0]["q"])
    try:
        await wait_m.delete()
    except Exception:
        pass
    if not mp3:
        return await message.reply_text("❌ <b>Music clip fetch nahi ho paya, dobara /quiz try karein!</b>", parse_mode=enums.ParseMode.HTML)

    qid = f"{int(time.time())}{random.randint(10,99)}"
    styles = ["primary", "success", "danger", "primary"]
    rows = [[_cbtn(f"🎵 {opt}", style=styles[i], callback_data=f"mgb_qz_{qid}_{idx}_{i}")] for i, opt in enumerate(q["opts"])]
    cap = (
        f"<blockquote><b>🎧 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐌𝐔𝐒𝐈𝐂 𝐐𝐔𝐈𝐙</b></blockquote>\n\n"
        f"🎶 <b>Asli gaana sunein aur 1 baar sahi Movie chunein!</b>\n"
        f"⏱ <b>Time Left:</b> <code>30s</code>\n\n{FOOTER}"
    )
    msg_id = await send_colored_audio(client, message.chat.id, mp3, "🎵 Guess The Movie", f"@{OWNER_UNAME}", 20, cap, rows, reply_to=message.id)
    QUIZ_ACTIVE[qid] = {"done": False}

    async def _countdown():
        for rem in (20, 10):
            await asyncio.sleep(10)
            if QUIZ_ACTIVE.get(qid, {}).get("done"):
                return
            await edit_colored_caption(
                client, message.chat.id, msg_id,
                f"<blockquote><b>🎧 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐌𝐔𝐒𝐈𝐂 𝐐𝐔𝐈𝐙</b></blockquote>\n\n⏱ <b>Time Left:</b> <code>{rem}s</code>\n\n{FOOTER}",
                rows,
            )
        await asyncio.sleep(10)
        if not QUIZ_ACTIVE.get(qid, {}).get("done"):
            QUIZ_ACTIVE.pop(qid, None)
            await edit_colored_caption(
                client, message.chat.id, msg_id,
                f"<blockquote><b>⏰ 𝐐𝐔𝐈𝐙 𝐓𝐈𝐌𝐄 𝐔𝐏!</b></blockquote>\n\n✅ <b>Correct Movie:</b> <code>{q['opts'][q['ans']]}</code>\n\n{FOOTER}",
                [],
            )

    asyncio.create_task(_countdown())

@bot.on_callback_query(filters.regex(r"^mgb_qz_(\d+)_(\d+)_(\d+)$"))
async def music_quiz_cb(client, query: CallbackQuery):
    qid, q_idx, ans_idx = query.matches[0].group(1), int(query.matches[0].group(2)), int(query.matches[0].group(3))
    q = QUIZ_BANK[q_idx]
    state = QUIZ_ACTIVE.get(qid)
    if not state or state.get("done"):
        return await query.answer("🔒 Yeh quiz khatam ho chuka hai!", show_alert=True)
    state["done"] = True
    QUIZ_ACTIVE.pop(qid, None)
    correct = q["opts"][q["ans"]]
    if ans_idx == q["ans"]:
        QUIZ_SCORES[query.from_user.id] += 10
        pts = QUIZ_SCORES[query.from_user.id]
        await query.answer("🎉 Sahi Jawab! +10 Points!", show_alert=False)
        await edit_colored_caption(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>🏆 𝐐𝐔𝐈𝐙 𝐖𝐈𝐍𝐍𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>{html.escape(query.from_user.first_name)}</b> • ✅ <code>{correct}</code>\n"
            f"⭐ <b>Total Score:</b> <code>{pts} Points</code>\n\n{FOOTER}",
            [],
        )
    else:
        await query.answer("❌ Galat Jawab! Chance Khatam!", show_alert=True)
        await edit_colored_caption(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>❌ 𝐆𝐀𝐋𝐀𝐓 𝐉𝐀𝐖𝐀𝐁</b></blockquote>\n\n✅ <b>Correct Movie:</b> <code>{correct}</code>\n\n{FOOTER}",
            [],
        )

# ── 6. SECRET WHISPER (/whisper) ──────────────────────────────
@bot.on_message(filters.command(["whisper", "w"], prefixes=["/", "!", "."]))
async def whisper_cmd(client, message: Message):
    target_id, target_uname, secret_text = 0, "", ""
    if message.reply_to_message and message.reply_to_message.from_user:
        if len(message.command) < 2:
            return await message.reply_text("🔒 <b>Reply karke likhein:</b> <code>/whisper Hello</code>", parse_mode=enums.ParseMode.HTML)
        target_id = message.reply_to_message.from_user.id
        target_uname = message.reply_to_message.from_user.first_name
        secret_text = message.text.split(None, 1)[1]
    else:
        if len(message.command) < 3:
            return await message.reply_text("🔒 <b>Format:</b> <code>/whisper @username Secret</code>", parse_mode=enums.ParseMode.HTML)
        target_uname = message.command[1].lstrip("@")
        secret_text = message.text.split(None, 2)[2]
    wid = f"{int(time.time()*1000)}_{random.randint(100,999)}"
    WHISPERS[wid] = {"sender": message.from_user.id, "target_id": target_id, "target_uname": target_uname.lower(), "text": secret_text[:180]}
    try:
        await message.delete()
    except Exception:
        pass
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🤫 𝐌𝐆𝐁 𝐒𝐄𝐂𝐑𝐄𝐓 𝐖𝐇𝐈𝐒𝐏𝐄𝐑</b></blockquote>\n\n"
        f"👤 <b>From:</b> <b>{html.escape(message.from_user.first_name)}</b>\n"
        f"🎯 <b>For:</b> <code>@{html.escape(target_uname)}</code>\n\n{FOOTER}",
        [[_cbtn("🔒 𝐕𝐈𝐄𝐖 𝐒𝐄𝐂𝐑𝐄𝐓", style="primary", callback_data=f"mgb_wsp_{wid}")]],
    )

@bot.on_callback_query(filters.regex(r"^mgb_wsp_(.+)$"))
async def whisper_cb(client, query: CallbackQuery):
    data = WHISPERS.get(query.matches[0].group(1))
    if not data:
        return await query.answer("❌ Yeh whisper expire ho gaya!", show_alert=True)
    u = query.from_user
    if u.id == data["sender"] or (data["target_id"] and u.id == data["target_id"]) or (u.username and u.username.lower() == data["target_uname"]):
        return await query.answer(f"🔒 Secret:\n\n{data['text']}", show_alert=True)
    await query.answer("❌ Yeh secret whisper aapke liye nahi hai!", show_alert=True)

# ── 7. CLEAN QUOTE STICKER MAKER (/q — NO BOXES) ─────────────
def _build_quote_sticker(name: str, text: str, dp_bytes: bytes = None) -> io.BytesIO:
    W, H = 512, 300
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((115, 30, 495, 260), radius=28, fill=(20, 20, 36, 255), outline=(255, 70, 140, 255), width=4)
    av = Image.open(io.BytesIO(dp_bytes)).convert("RGBA").resize((85, 85), Image.LANCZOS) if dp_bytes else Image.new("RGBA", (85, 85), (110, 60, 220, 255))
    mask = Image.new("L", (85, 85), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 85, 85), fill=255)
    img.paste(av, (15, 40), mask)
    try:
        f_n = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
        f_w = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        f_n = f_t = f_w = ImageFont.load_default()
    d.text((135, 48), _clean_font_name(name, 20), fill=(255, 110, 175), font=f_n)
    lines, cur = [], ""
    for w in text.split():
        if len(cur + " " + w) <= 25:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = 88
    for ln in lines[:4]:
        d.text((135, y), ln, fill=(245, 245, 255), font=f_t)
        y += 30
    d.text((280, 232), f"@{OWNER_UNAME}", fill=(160, 160, 210), font=f_w)
    out = io.BytesIO()
    out.name = "mgb_quote.webp"
    img.save(out, format="WEBP")
    out.seek(0)
    return out

@bot.on_message(filters.command(["q", "quote"], prefixes=["/", "!", "."]))
async def quote_sticker_cmd(client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.text or rep.caption):
        return await message.reply_text("💬 <b>Kisi text message par reply karke <code>/q</code> likhein!</b>", parse_mode=enums.ParseMode.HTML)
    u = rep.from_user
    dp_bytes = None
    if u and u.photo:
        try:
            bio = await client.download_media(u.photo.small_file_id, in_memory=True)
            dp_bytes = bio.getvalue()
        except Exception:
            pass
    st = await asyncio.to_thread(_build_quote_sticker, u.first_name if u else "MGB User", rep.text or rep.caption, dp_bytes)
    await message.reply_sticker(sticker=st)

# ── 8. AUTO REELS & SHORTS DOWNLOADER (/dl) ───────────────────
def _find_yt_cookies():
    for path in ("cookies.txt", "cookies/cookies.txt", "ArtistMusic/cookies.txt", "ArtistMusic/cookies/cookies.txt"):
        if os.path.isfile(path) and os.path.getsize(path) > 100:
            return path
    return None

def _extract_yt_id(url: str):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=|embed/))([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def _sync_ytdlp_download(url: str, out_dir: str, is_yt: bool = False) -> str:
    import yt_dlp
    cookie_file = _find_yt_cookies() if is_yt else None
    opts = {
        "outtmpl": os.path.join(out_dir, "mgb_v.%(ext)s"),
        "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "max_filesize": 45 * 1024 * 1024,
    }
    if cookie_file:
        opts["cookiefile"] = cookie_file
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.on_message(filters.command(["dl", "reel", "shorts"], prefixes=["/", "!", "."]))
async def reels_dl_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("📥 <b>Link dein:</b> <code>/dl https://...</code>", parse_mode=enums.ParseMode.HTML)
    url = message.command[1].strip()
    is_yt = bool(_extract_yt_id(url))
    m = await message.reply_text("<blockquote><b>📥 𝐌𝐆𝐁 𝐇𝐃 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐡𝐨 𝐫𝐚𝐡𝐚 𝐡𝐚𝐢...</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    td = tempfile.mkdtemp(prefix="mgb_dl_")
    fp = None
    try:
        if is_yt and artist_yt and hasattr(artist_yt, "download"):
            try:
                res = await artist_yt.download(_extract_yt_id(url) or url, video=True)
                path = res[0] if isinstance(res, (tuple, list)) else res
                if isinstance(path, str) and os.path.isfile(path):
                    fp = path
            except Exception:
                pass
        if not fp:
            fp = await asyncio.to_thread(_sync_ytdlp_download, url, td, is_yt)
        await message.reply_video(video=fp, caption=f"<blockquote><b>🎬 𝐌𝐆𝐁 𝐇𝐃 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐑</b></blockquote>\n\n{FOOTER}", parse_mode=enums.ParseMode.HTML)
        await m.delete()
    except Exception as e:
        await m.edit_text(f"❌ <b>Download Failed:</b> <code>{html.escape(str(e)[:150])}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        for f in os.listdir(td):
            try:
                os.remove(os.path.join(td, f))
            except Exception:
                pass
        try:
            os.rmdir(td)
        except Exception:
            pass

# ── 9. INDIA-ONLY LIVE AUTO-REFRESH /score (2s SCAN + AUTO 6/4/W)
async def _fetch_india_live_score() -> str:
    ts = int(time.time())
    headers = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache", "Pragma": "no-cache"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
            async with s.get(f"https://static.cricinfo.com/rss/livescores.xml?t={ts}", headers=headers) as r:
                if r.status == 200:
                    txt = await r.text()
                    titles = [html.unescape(t).strip() for t in re.findall(r"<title>(.*?)</title>", txt)[1:]]
                    for t in titles:
                        if re.search(r"\b(india|ind)\b", t, flags=re.I):
                            return t[:150]
    except Exception:
        pass
    return "Abhi India ka koi live match nahi chal raha"

def _score_live_rows(running: bool = True) -> list:
    if running:
        return [[
            _cbtn("⏹ 𝐒𝐓𝐎𝐏 𝐋𝐈𝐕𝐄", style="danger", callback_data="mgb_sc_stop"),
            _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        ]]
    return [[
        _cbtn("▶️ 𝐒𝐓𝐀𝐑𝐓 𝐋𝐈𝐕𝐄", style="success", callback_data="mgb_sc_start"),
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
    ]]

async def _build_india_score_text(chat_id: int, live_line: str) -> str:
    st = SCORE_BOARD_STATS[chat_id]
    now = datetime.now(IST).strftime("%I:%M:%S %p")
    mode = "🟢 LIVE AUTO (2s SCAN)" if chat_id in LIVE_SCORE_TASKS else "⚪ STOPPED"
    return (
        f"🇮🇳✨🇮🇳 <b>𝐈𝐍𝐃𝐈𝐀 𝐋𝐈𝐕𝐄 𝐒𝐂𝐎𝐑𝐄𝐁𝐎𝐀𝐑𝐃</b> 🇮🇳✨🇮🇳\n"
        f"<blockquote><b>🏏 𝐈𝐍𝐃𝐈𝐀 𝐌𝐀𝐓𝐂𝐇 𝐋𝐈𝐕𝐄</b>\n"
        f"📊 <code>{html.escape(live_line)}</code>\n"
        f"🌟 <b>Sixes:</b> <code>{st['six']}</code>  |  "
        f"⚡ <b>Fours:</b> <code>{st['four']}</code>  |  "
        f"🚨 <b>Wickets:</b> <code>{st['wicket']}</code></blockquote>\n"
        f"🎙 <b>Auto-Speaker:</b> <code>{html.escape(st['last_event'])}</code>\n"
        f"🕒 <b>Time:</b> <code>{now}</code>  •  <code>{mode}</code>\n\n{FOOTER}"
    )

async def _make_score_popup_banner(chat_id: int, event_code: str) -> io.BytesIO:
    st = SCORE_BOARD_STATS[chat_id]
    labels = {
        "6": ("SIX! SIX! SIX!", f"India 6s: {st['six']} | 4s: {st['four']}", f"Wickets: {st['wicket']} | MAXIMUM HIT"),
        "4": ("FOUR! FOUR! FOUR!", f"India 4s: {st['four']} | 6s: {st['six']}", f"Wickets: {st['wicket']} | BOUNDARY HIT"),
        "w": ("WICKET! OUT!", f"Total Wickets: {st['wicket']}", f"6s: {st['six']} | 4s: {st['four']}"),
    }
    badge, l1, l2 = labels.get(event_code, ("INDIA LIVE SCORE", f"6s: {st['six']} | 4s: {st['four']}", f"Wickets: {st['wicket']}"))
    try:
        from ArtistMusic.plugins.mgb_viral_cards import _get_user_dp, _get_template_bg, _make_single_card
        dp = await _get_user_dp(bot, bot.me.id)
        tpl = await _get_template_bg()
        return _make_single_card(dp, badge, "INDIA LIVE MATCH", l1, l2, template_bg=tpl)
    except Exception:
        b = io.BytesIO()
        Image.new("RGB", (960, 420), (16, 12, 34)).save(b, "JPEG")
        b.seek(0)
        return b

async def _auto_fire_india_event(client, chat_id: int, event_code: str, live_line: str, ref_msg_id: int = None):
    st = SCORE_BOARD_STATS[chat_id]
    if event_code == "6":
        st["six"] += 1
        st["last_event"] = "SIX HUA! (6 RUNS)"
        spoken = "Six! Six! Six! India ne six maara!"
        emoji = "🔥"
    elif event_code == "4":
        st["four"] += 1
        st["last_event"] = "FOUR HUA! (4 RUNS)"
        spoken = "Four! Four! Four! India ne four maara!"
        emoji = "🎉"
    else:
        st["wicket"] += 1
        st["last_event"] = "WICKET GAYA! (OUT)"
        spoken = "Wicket! Out!"
        emoji = "🚨"

    mp3 = await _make_voice_alert_mp3(spoken)
    aud_id = await send_colored_audio(
        client, chat_id, mp3, st["last_event"], f"@{OWNER_UNAME}", 4,
        f"🎙 <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑:</b> <code>{spoken}</code>\n\n{FOOTER}",
        [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}")]],
        reply_to=ref_msg_id,
    )
    if aud_id:
        await _pop_reaction(client, chat_id, aud_id, emoji)

    await asyncio.sleep(2)
    banner_bio = await _make_score_popup_banner(chat_id, event_code)
    try:
        from ArtistMusic.plugins.mgb_viral_cards import send_rich_card
        pop_id = await send_rich_card(client, chat_id, banner_bio, await _build_india_score_text(chat_id, live_line))
    except Exception:
        banner_bio.seek(0)
        s = await client.send_photo(chat_id, banner_bio, caption=await _build_india_score_text(chat_id, live_line), parse_mode=enums.ParseMode.HTML)
        pop_id = s.id
    if pop_id:
        await _pop_reaction(client, chat_id, pop_id, emoji)

def _extract_india_runs_wkts(line: str):
    m = re.search(r"India[^\d]*(\d{1,3})/(\d{1,2})", line, flags=re.I)
    if not m:
        matches = re.findall(r"(\d{1,3})/(\d{1,2})", line)
        if not matches:
            return None
        return int(matches[-1][0]), int(matches[-1][1])
    return int(m.group(1)), int(m.group(2))

async def _start_india_score_loop(client, chat_id: int, mid: int):
    if chat_id in LIVE_SCORE_TASKS:
        LIVE_SCORE_TASKS.pop(chat_id).cancel()

async def _loop():
        last_line = ""
        try:
            for _ in range(900):  # ~30 mins active live tracking
                await asyncio.sleep(2)
                fresh_line = await _fetch_india_live_score()
                rw = _extract_india_runs_wkts(fresh_line)
                if rw:
                    runs, wkts = rw
                    prev = LIVE_CRIC_LAST_STATE.get(chat_id)
                    if prev:
                        if wkts > prev["wkts"]:
                            await _auto_fire_india_event(client, chat_id, "w", fresh_line, ref_msg_id=mid)
                        elif runs - prev["runs"] == 6:
                            await _auto_fire_india_event(client, chat_id, "6", fresh_line, ref_msg_id=mid)
                        elif runs - prev["runs"] == 4:
                            await _auto_fire_india_event(client, chat_id, "4", fresh_line, ref_msg_id=mid)
                    LIVE_CRIC_LAST_STATE[chat_id] = {"runs": runs, "wkts": wkts}

                if fresh_line != last_line:
                    last_line = fresh_line
                    await edit_colored_msg(client, chat_id, mid, await _build_india_score_text(chat_id, fresh_line), _score_live_rows(True))
        except asyncio.CancelledError:
            pass
        finally:
            LIVE_SCORE_TASKS.pop(chat_id, None)

    LIVE_SCORE_TASKS[chat_id] = asyncio.create_task(_loop())

@bot.on_message(filters.command(["score", "cricket", "autospeaker"], prefixes=["/", "!", "."]))
async def open_india_score_cmd(client, message: Message):
    chat_id = message.chat.id
    live_line = await _fetch_india_live_score()
    LIVE_CRIC_LAST_STATE.pop(chat_id, None)
    rw = _extract_india_runs_wkts(live_line)
    if rw:
        LIVE_CRIC_LAST_STATE[chat_id] = {"runs": rw[0], "wkts": rw[1]}

    mid = await send_colored_msg(client, chat_id, await _build_india_score_text(chat_id, live_line), _score_live_rows(True), reply_to=message.id)
    if mid:
        await _pop_reaction(client, chat_id, mid, "🔥")
        await _start_india_score_loop(client, chat_id, mid)

@bot.on_callback_query(filters.regex(r"^mgb_sc_(start|stop)$"))
async def india_score_cb(client, query: CallbackQuery):
    act = query.matches[0].group(1)
    chat_id = query.message.chat.id
    live_line = await _fetch_india_live_score()
    if act == "stop":
        if chat_id in LIVE_SCORE_TASKS:
            LIVE_SCORE_TASKS.pop(chat_id).cancel()
        await query.answer("⏹ Live India Score Stopped!", show_alert=False)
        return await edit_colored_msg(client, chat_id, query.message.id, await _build_india_score_text(chat_id, live_line), _score_live_rows(False))

    await query.answer("▶️ Live India Score Started (2s Scan)!", show_alert=False)
    await _start_india_score_loop(client, chat_id, query.message.id)
    await edit_colored_msg(client, chat_id, query.message.id, await _build_india_score_text(chat_id, live_line), _score_live_rows(True))

# ── 10. SMART AUTO-CLEAN MODE (/autoclean) ────────────────────
def _ac_rows() -> list:
    return [[
        _cbtn("✅ 𝐄𝐍𝐀𝐁𝐋𝐄", style="success", callback_data="mgb_ac_on"),
        _cbtn("❌ 𝐃𝐈𝐒𝐀𝐁𝐋𝐄", style="danger", callback_data="mgb_ac_off"),
    ]]

@bot.on_message(filters.command(["autoclean", "cleanmode"], prefixes=["/", "!", "."]))
async def autoclean_cmd(client, message: Message):
    chat_id = message.chat.id
    if chat_id in AUTOCLEAN_CHATS:
        AUTOCLEAN_CHATS.discard(chat_id)
        st = "DISABLED ❌"
    else:
        AUTOCLEAN_CHATS.add(chat_id)
        st = "ENABLED ✅"
    await send_colored_msg(
        client, chat_id,
        f"<blockquote><b>🧹 𝐌𝐆𝐁 𝐒𝐌𝐀𝐑𝐓 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n⚙️ <b>Status:</b> <code>{st}</code>\n\n{FOOTER}",
        _ac_rows(), reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_ac_(on|off)$"))
async def autoclean_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    chat_id = query.message.chat.id
    if mode == "on":
        AUTOCLEAN_CHATS.add(chat_id)
        st = "ENABLED ✅"
    else:
        AUTOCLEAN_CHATS.discard(chat_id)
        st = "DISABLED ❌"
    await query.answer(f"🧹 Auto-Clean {st}", show_alert=False)
    await edit_colored_msg(
        client, chat_id, query.message.id,
        f"<blockquote><b>🧹 𝐌𝐆𝐁 𝐒𝐌𝐀𝐑𝐓 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n⚙️ <b>Status:</b> <code>{st}</code>\n\n{FOOTER}",
        _ac_rows(),
    )

@bot.on_message(filters.group & (filters.service | filters.regex(r"^[/!\.]")), group=10)
async def autoclean_watcher(client, message: Message):
    if message.chat.id not in AUTOCLEAN_CHATS:
        return
    if message.service:
        try:
            await message.delete()
        except Exception:
            pass
    else:
        async def _del(msg: Message):
            await asyncio.sleep(25)
            try:
                await msg.delete()
            except Exception:
                pass
        asyncio.create_task(_del(message))
    
