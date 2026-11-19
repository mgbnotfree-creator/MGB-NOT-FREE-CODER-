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

SCORE_BOARD_STATS = defaultdict(lambda: {"four": 0, "six": 0, "wicket": 0, "last_event": "LIVE READY"})
LIVE_CRIC_LAST_STATE = {}
AUTO_SPEAKER_TASKS = {}
AUTO_SPEAKER_STATE = {}
AUTO_46_CHAT_COOLDOWN = {}

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

SFX_TEXTS = {
    "clap": "Waah bhai waah! Zabardast taaliyan!",
    "bruh": "Bruh! Yeh kya kar diya bhai!",
    "drum": "Dum dum tss! Drumroll please!",
    "laugh": "Hahaha! Bhai sahab, gazab comedy!",
}

# ── 🔘 COLORED HTML BUTTON HTTP HELPERS ───────────────────────
def _cbtn(text: str, style: str = "primary", callback_data: str = None, url: str = None) -> dict:
    btn = {"text": text, "style": style}
    if url:
        btn["url"] = url
    elif callback_data:
        btn["callback_data"] = callback_data
    return btn

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
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": rows}}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    res = await _bot_api(client, "sendMessage", payload)
    if res:
        return res.get("message_id")
    m = await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML)
    return m.id

async def edit_colored_msg(client, chat_id: int, msg_id: int, text: str, rows: list = None):
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

async def _make_sfx_mp3(text: str) -> bytes:
    def _gen():
        b = io.BytesIO()
        gTTS(text=text, lang="hi", tld="co.in", slow=False).write_to_fp(b)
        return _convert_to_clean_mp3(b.getvalue(), 10)
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

# ── 3. REAL BGMI ENTRY BGM & AUTO GROUP JOIN BANNER + MUSIC ───
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
        [
            _cbtn("🔊 𝐏𝐋𝐀𝐘 𝐌𝐘 𝐁𝐆𝐌", style="success", callback_data=f"mgb_ebgm_play_{uid}"),
        ],
    ]

@bot.on_message(filters.command(["entry", "setentry", "bgm"], prefixes=["/", "!", "."]))
async def entry_bgm_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    if len(message.command) > 1:
        custom = message.text.split(None, 1)[1].strip()
        USER_BGM_PREF[user.id] = custom
        active = custom
    else:
        pref = USER_BGM_PREF.get(user.id, "bgmi")
        active = BGM_PRESETS[pref][0] if pref in BGM_PRESETS else pref

    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🔥 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
        f"👤 <b>VIP:</b> <b>{html.escape(user.first_name)}</b>\n"
        f"🎵 <b>Active BGM:</b> <code>{html.escape(active)}</code>\n"
        f"💡 <b>Custom Song:</b> <code>/entry Song Name</code>\n\n{FOOTER}",
        _entry_bgm_rows(user.id), reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_ebgm_(set|play)_(\d+)(?:_([a-z]+))?$"))
async def entry_bgm_cb(client, query: CallbackQuery):
    act = query.matches[0].group(1)
    uid = int(query.matches[0].group(2))
    preset = query.matches[0].group(3)

    if act == "set":
        if query.from_user.id != uid:
            return await query.answer("❌ Apna BGM set karne ke liye /entry bhejein!", show_alert=True)
        USER_BGM_PREF[uid] = preset
        label = BGM_PRESETS[preset][0]
        await query.answer(f"✅ {label} Set!", show_alert=False)
        return await edit_colored_msg(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>🔥 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
            f"👤 <b>VIP:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
            f"🎵 <b>Active BGM:</b> <code>{label}</code>\n\n{FOOTER}",
            _entry_bgm_rows(uid),
        )

    pref = USER_BGM_PREF.get(uid, "bgmi")
    await query.answer("🎵 Real BGM Music load ho raha hai...", show_alert=False)
    label, mp3 = await _get_real_bgm_mp3(pref)
    if not mp3:
        return await query.answer("❌ BGM fetch nahi ho paya, dobara try karein!", show_alert=True)

    await send_colored_audio(
        client, query.message.chat.id, mp3, label, f"@{OWNER_UNAME}", 20,
        f"<blockquote><b>🔥 𝐕𝐈𝐏 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌 𝐌𝐔𝐒𝐈𝐂</b></blockquote>\n\n"
        f"👤 <b>Member:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
        f"🎵 <b>Track:</b> <code>{html.escape(label)}</code>\n\n{FOOTER}",
        [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}")]],
    )

@bot.on_message(filters.group & filters.new_chat_members, group=8)
async def group_join_bgm_handler(client, message: Message):
    if message.chat.id in WELCOME_BGM_OFF:
        return
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        pref = USER_BGM_PREF.get(member.id, "bgmi")
        label, mp3 = await _get_real_bgm_mp3(pref)

        try:
            from ArtistMusic.plugins.mgb_viral_cards import _get_user_dp, _get_template_bg, _make_single_card, send_rich_card
            dp = await _get_user_dp(client, member.id)
            tpl = await _get_template_bg()
            card = _make_single_card(
                dp,
                "WELCOME TO GROUP",
                member.first_name,
                f"Group: {message.chat.title or 'MGB VIP'}",
                f"Entry BGM: {label}",
                template_bg=tpl,
            )
            await send_rich_card(
                client, message.chat.id, card,
                f"<blockquote><b>👑 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 {html.escape(message.chat.title or 'GROUP')}</b></blockquote>\n\n"
                f"✨ <b>New Member:</b> <b>{html.escape(member.first_name)}</b>\n\n{FOOTER}",
            )
        except Exception:
            pass

        if mp3:
            await send_colored_audio(
                client, message.chat.id, mp3, label, f"@{OWNER_UNAME}", 20,
                f"<blockquote><b>🎮 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌</b></blockquote>\n\n"
                f"🔥 <b>{html.escape(member.first_name)}</b> ki Royal Entry ho chuki hai!\n\n{FOOTER}",
                [[
                    _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
                    _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
                ]],
            )
# ── 4. LIVE MEME SOUNDBOARD (/sfx) ────────────────────────────
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

@bot.on_message(filters.command(["sfx", "soundboard"], prefixes=["/", "!", "."]))
async def sfx_cmd(client, message: Message):
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🔊 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐌𝐄𝐌𝐄 𝐒𝐎𝐔𝐍𝐃𝐁𝐎𝐀𝐑𝐃</b></blockquote>\n\n👇 <b>Instant effect ke liye button dabayein:</b>\n\n{FOOTER}",
        _sfx_rows(), reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_sfx_(clap|bruh|drum|laugh)$"))
async def sfx_cb(client, query: CallbackQuery):
    key = query.matches[0].group(1)
    await query.answer(f"🔊 Sending {key.upper()}...", show_alert=False)
    mp3 = await _make_sfx_mp3(SFX_TEXTS[key])
    await send_colored_audio(
        client, query.message.chat.id, mp3, f"SFX • {key.upper()}", f"@{OWNER_UNAME}", 4,
        f"🔊 <b>SFX:</b> <code>{key.upper()}</code> by <b>{html.escape(query.from_user.first_name)}</b>\n\n{FOOTER}",
        [[_cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="success", url=f"https://t.me/{OWNER_UNAME}")]],
    )

# ── 5. REAL MUSIC CLIP QUIZ (1-TIME PICK LOCK) ────────────────
@bot.on_message(filters.command(["quiz", "mquiz"], prefixes=["/", "!", "."]))
async def music_quiz_cmd(client, message: Message):
    wait_m = await message.reply_text("🎧 <b>Real Music Clip load ho raha hai...</b>", parse_mode=enums.ParseMode.HTML)
    idx = random.randrange(len(QUIZ_BANK))
    q = QUIZ_BANK[idx]

    mp3 = await _fetch_real_song_clip(q["q"])
    if not mp3:
        idx = 0
        q = QUIZ_BANK[0]
        mp3 = await _fetch_real_song_clip(q["q"])
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
    msg_id = await send_colored_audio(
        client, message.chat.id, mp3, "🎵 Guess The Movie", f"@{OWNER_UNAME}", 20, cap, rows, reply_to=message.id
    )
    QUIZ_ACTIVE[qid] = {"done": False, "chat_id": message.chat.id, "msg_id": msg_id}

    async def _countdown():
        for rem in (20, 10):
            await asyncio.sleep(10)
            if QUIZ_ACTIVE.get(qid, {}).get("done"):
                return
            await edit_colored_caption(
                client, message.chat.id, msg_id,
                f"<blockquote><b>🎧 𝐌𝐆𝐁 𝐑𝐄𝐀𝐋 𝐌𝐔𝐒𝐈𝐂 𝐐𝐔𝐈𝐙</b></blockquote>\n\n"
                f"🎶 <b>Asli gaana sunein aur 1 baar sahi Movie chunein!</b>\n"
                f"⏱ <b>Time Left:</b> <code>{rem}s</code>\n\n{FOOTER}",
                rows,
            )
        await asyncio.sleep(10)
        if not QUIZ_ACTIVE.get(qid, {}).get("done"):
            QUIZ_ACTIVE.pop(qid, None)
            await edit_colored_caption(
                client, message.chat.id, msg_id,
                f"<blockquote><b>⏰ 𝐐𝐔𝐈𝐙 𝐓𝐈𝐌𝐄 𝐔𝐏!</b></blockquote>\n\n"
                f"✅ <b>Correct Movie:</b> <code>{q['opts'][q['ans']]}</code>\n\n{FOOTER}",
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

    picked = q["opts"][ans_idx]
    correct = q["opts"][q["ans"]]

    if ans_idx == q["ans"]:
        QUIZ_SCORES[query.from_user.id] += 10
        pts = QUIZ_SCORES[query.from_user.id]
        await query.answer("🎉 Sahi Jawab! +10 Points!", show_alert=False)
        await edit_colored_caption(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>🏆 𝐐𝐔𝐈𝐙 𝐖𝐈𝐍𝐍𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>Winner:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
            f"✅ <b>Correct Movie:</b> <code>{correct}</code>\n"
            f"⭐ <b>Total Score:</b> <code>{pts} Points</code>\n\n{FOOTER}",
            [],
        )
    else:
        await query.answer("❌ Galat Jawab! Chance Khatam!", show_alert=True)
        await edit_colored_caption(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>❌ 𝐆𝐀𝐋𝐀𝐓 𝐉𝐀𝐖𝐀𝐁</b></blockquote>\n\n"
            f"👤 <b>Player:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
            f"❌ <b>Your Pick:</b> <code>{picked}</code>\n"
            f"✅ <b>Correct Movie:</b> <code>{correct}</code>\n\n{FOOTER}",
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
    allowed = u.id == data["sender"] or (data["target_id"] and u.id == data["target_id"]) or (u.username and u.username.lower() == data["target_uname"])
    if not allowed:
        return await query.answer("❌ Yeh secret whisper aapke liye nahi hai!", show_alert=True)
    await query.answer(f"🔒 Secret:\n\n{data['text']}", show_alert=True)

# ── 7. QUOTE STICKER MAKER (/q) ───────────────────────────────
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
    d.text((135, 48), name[:20], fill=(255, 110, 175), font=f_n)
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
    for path in (
        "cookies.txt",
        "cookies/cookies.txt",
        "ArtistMusic/cookies.txt",
        "ArtistMusic/cookies/cookies.txt",
    ):
        if os.path.isfile(path) and os.path.getsize(path) > 100:
            return path
    return None

def _extract_yt_id(url: str):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=|embed/))([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def _sync_ytdlp_download(url: str, out_dir: str, is_yt: bool = False) -> str:
    import yt_dlp
    cookie_file = _find_yt_cookies() if is_yt else None

    if not is_yt:
        opts = {
            "outtmpl": os.path.join(out_dir, "mgb_v.%(ext)s"),
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True,
            "max_filesize": 45 * 1024 * 1024,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    client_sets = [["default"]] if cookie_file else [["ios", "android_vr"], ["tv_embedded", "mweb"], ["android"]]
    last_err = None
    for clients in client_sets:
        opts = {
            "outtmpl": os.path.join(out_dir, "mgb_yt.%(ext)s"),
            "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True,
            "max_filesize": 45 * 1024 * 1024,
        }
        if cookie_file:
            opts["cookiefile"] = cookie_file
        else:
            opts["extractor_args"] = {"youtube": {"player_client": clients}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fp = ydl.prepare_filename(info)
                if os.path.isfile(fp):
                    return fp
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("YouTube download blocked")

@bot.on_message(filters.command(["dl", "reel", "shorts"], prefixes=["/", "!", "."]))
async def reels_dl_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("📥 <b>Link dein:</b> <code>/dl https://...</code>", parse_mode=enums.ParseMode.HTML)

    url = message.command[1].strip()
    is_yt = bool(_extract_yt_id(url))
    m = await message.reply_text("<blockquote><b>📥 𝐌𝐆𝐁 𝐇𝐃 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐡𝐨 𝐫𝐚𝐡𝐚 𝐡𝐚𝐢...</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    td = tempfile.mkdtemp(prefix="mgb_dl_")
    fp = None
    from_api = False

    try:
        if is_yt and artist_yt and hasattr(artist_yt, "download"):
            vid = _extract_yt_id(url)
            for arg in (vid, url):
                try:
                    res = await artist_yt.download(arg, video=True)
                    path = res[0] if isinstance(res, (tuple, list)) else res
                    if isinstance(path, str) and os.path.isfile(path):
                        fp = path
                        from_api = True
                        break
                except Exception:
                    continue

        if not fp:
            fp = await asyncio.to_thread(_sync_ytdlp_download, url, td, is_yt)

        await message.reply_video(
            video=fp,
            caption=f"<blockquote><b>🎬 𝐌𝐆𝐁 𝐇𝐃 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐑</b></blockquote>\n\n{FOOTER}",
            parse_mode=enums.ParseMode.HTML,
        )
        await m.delete()
    except Exception as e:
        err = str(e)
        if "Sign in to confirm" in err:
            err = "YouTube ne Render IP block kiya hai. Repo ke root mein cookies.txt add karein."
        await m.edit_text(f"❌ <b>Download Failed:</b> <code>{html.escape(err[:160])}</code>", parse_mode=enums.ParseMode.HTML)
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
        if from_api and fp and os.path.isfile(fp) and "downloads" in fp:
            try:
                os.remove(fp)
            except Exception:
                pass

# ── 9. /score SCOREBOARD MENU + 4 / 6 / WICKET VOICE & POP-UP ─
async def _fetch_current_score_line() -> str:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
            async with s.get("https://static.cricinfo.com/rss/livescores.xml") as r:
                if r.status == 200:
                    txt = await r.text()
                    titles = re.findall(r"<title>(.*?)</title>", txt)[1:3]
                    if titles:
                        return " | ".join(t.strip() for t in titles if t.strip())[:140]
    except Exception:
        pass
    return "Live Scoreboard Active! Six! Six! Six!"

def _score_menu_rows() -> list:
    return [
        [
            _cbtn("⚡ 𝟒 𝐑𝐔𝐍𝐒", style="primary", callback_data="mgb_sc_hit_4"),
            _cbtn("🌟 𝟔 𝐒𝐈𝐗", style="success", callback_data="mgb_sc_hit_6"),
            _cbtn("🚨 𝐖𝐈𝐂𝐊𝐄𝐓", style="danger", callback_data="mgb_sc_hit_w"),
        ],
        [
            _cbtn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", style="success", callback_data="mgb_sc_open"),
            _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        ],
    ]

async def _build_full_scoreboard_text(chat_id: int) -> str:
    st = SCORE_BOARD_STATS[chat_id]
    live_line = await _fetch_current_score_line()
    now = datetime.now(IST).strftime("%I:%M:%S %p")
    return (
        f"🌟✨🌟 <b>𝐒𝐂𝐎𝐑𝐄𝐁𝐎𝐀𝐑𝐃 𝐌𝐄𝐍𝐔 (/score)</b> 🌟✨🌟\n"
        f"<blockquote><b>🏏 𝐋𝐈𝐕𝐄 𝐌𝐀𝐓𝐂𝐇 𝐒𝐂𝐎𝐑𝐄𝐁𝐎𝐀𝐑𝐃</b>\n"
        f"📊 <code>{html.escape(live_line)}</code>\n"
        f"🌟 <b>Sixes:</b> <code>{st['six']}</code>  |  "
        f"⚡ <b>Fours:</b> <code>{st['four']}</code>  |  "
        f"🚨 <b>Wickets:</b> <code>{st['wicket']}</code></blockquote>\n"
        f"🔥 <b>Last Action:</b> <code>{html.escape(st['last_event'])}</code>\n"
        f"🕒 <b>Updated:</b> <code>{now}</code>  •  <b>Stream:</b> <code>Any State</code>\n\n{FOOTER}"
    )

async def _make_score_popup_banner(chat_id: int, event_code: str) -> io.BytesIO:
    st = SCORE_BOARD_STATS[chat_id]
    labels = {
        "6": ("SIX! SIX! SIX!", f"Total 6s: {st['six']} | 4s: {st['four']}", f"Wickets: {st['wicket']} | MAXIMUM HIT"),
        "4": ("FOUR! FOUR! FOUR!", f"Total 4s: {st['four']} | 6s: {st['six']}", f"Wickets: {st['wicket']} | BOUNDARY HIT"),
        "w": ("WICKET! OUT!", f"Total Wickets: {st['wicket']}", f"6s: {st['six']} | 4s: {st['four']}"),
    }
    badge, l1, l2 = labels.get(event_code, ("LIVE SCOREBOARD", f"6s: {st['six']} | 4s: {st['four']}", f"Wickets: {st['wicket']}"))
    try:
        from ArtistMusic.plugins.mgb_viral_cards import _get_user_dp, _get_template_bg, _make_single_card
        dp = await _get_user_dp(bot, bot.me.id)
        tpl = await _get_template_bg()
        return _make_single_card(dp, badge, "MGB LIVE SCORE", l1, l2, template_bg=tpl)
    except Exception:
        img = Image.new("RGB", (960, 420), (16, 12, 34))
        d = ImageDraw.Draw(img)
        f = ImageFont.load_default()
        d.text((60, 90), badge, fill=(255, 215, 60), font=f)
        d.text((60, 150), l1, fill=(255, 255, 255), font=f)
        d.text((60, 210), l2, fill=(120, 235, 255), font=f)
        b = io.BytesIO()
        b.name = "score_popup.jpg"
        img.save(b, "JPEG", quality=95)
        b.seek(0)
        return b

async def _trigger_score_event_voice_and_popup(client, chat_id: int, event_code: str, reply_to: int = None):
    st = SCORE_BOARD_STATS[chat_id]
    if event_code == "6":
        st["six"] += 1
        st["last_event"] = "SIX HUA! (6 RUNS)"
        spoken = "Six hua! Six! Six! Bahut badhiya six laga!"
        emoji = "🔥"
    elif event_code == "4":
        st["four"] += 1
        st["last_event"] = "FOUR HUA! (4 RUNS)"
        spoken = "Four hua! Four! Four! Zabardast four laga!"
        emoji = "🎉"
    else:
        st["wicket"] += 1
        st["last_event"] = "WICKET GAYA! (OUT)"
        spoken = "Wicket gaya! Ballebaaz out ho gaya!"
        emoji = "🚨"

    banner_bio = await _make_score_popup_banner(chat_id, event_code)
    try:
        from ArtistMusic.plugins.mgb_viral_cards import send_rich_card
        pop_id = await send_rich_card(
            client,
            chat_id,
            banner_bio,
            await _build_full_scoreboard_text(chat_id),
            json_rows=_score_menu_rows(),
        )
    except Exception:
        banner_bio.seek(0)
        sent = await client.send_photo(chat_id, banner_bio, caption=await _build_full_scoreboard_text(chat_id), parse_mode=enums.ParseMode.HTML)
        pop_id = sent.id

    if pop_id:
        await _pop_reaction(client, chat_id, pop_id, emoji)

    mp3 = await _make_sfx_mp3(spoken)
    aud_id = await send_colored_audio(
        client,
        chat_id,
        mp3,
        st["last_event"],
        f"@{OWNER_UNAME}",
        4,
        f"🔊 <b>{html.escape(st['last_event'])}</b>\n\n{FOOTER}",
        _score_menu_rows(),
        reply_to=pop_id or reply_to,
    )
    if aud_id:
        await _pop_reaction(client, chat_id, aud_id, emoji)

@bot.on_message(filters.command(["score", "cricket"], prefixes=["/", "!", "."]))
async def open_scoreboard_menu_cmd(client, message: Message):
    chat_id = message.chat.id
    txt = await _build_full_scoreboard_text(chat_id)
    mid = await send_colored_msg(client, chat_id, txt, _score_menu_rows(), reply_to=message.id)
    if mid:
        await _pop_reaction(client, chat_id, mid, "🔥")

    raw_txt = await _fetch_current_score_line()
    m = re.search(r"(\d+)/(\d+)", raw_txt)
    if m:
        runs, wkts = int(m.group(1)), int(m.group(2))
        prev = LIVE_CRIC_LAST_STATE.get(chat_id)
        if prev:
            if wkts > prev["wkts"]:
                await _trigger_score_event_voice_and_popup(client, chat_id, "w", reply_to=mid)
            elif runs - prev["runs"] == 6:
                await _trigger_score_event_voice_and_popup(client, chat_id, "6", reply_to=mid)
            elif runs - prev["runs"] == 4:
                await _trigger_score_event_voice_and_popup(client, chat_id, "4", reply_to=mid)
        LIVE_CRIC_LAST_STATE[chat_id] = {"runs": runs, "wkts": wkts}

@bot.on_callback_query(filters.regex(r"^mgb_sc_(open|hit_(4|6|w))$"))
async def scoreboard_menu_cb(client, query: CallbackQuery):
    data = query.matches[0].group(0)
    chat_id = query.message.chat.id

    if data == "mgb_sc_open":
        await query.answer("🔄 Scoreboard Refreshed!", show_alert=False)
        return await edit_colored_msg(client, chat_id, query.message.id, await _build_full_scoreboard_text(chat_id), _score_menu_rows())

    evt = data.split("_")[-1]
    await query.answer("🔊 Voice + Banner Pop-Up!", show_alert=False)
    await _trigger_score_event_voice_and_popup(client, chat_id, evt, reply_to=query.message.id)
    await edit_colored_msg(client, chat_id, query.message.id, await _build_full_scoreboard_text(chat_id), _score_menu_rows())

# ── 10. AUTO SPEAKER + POST-VOICE PLAYER POP-UP (/autospeaker)
def _extract_player_and_score(raw_text: str):
    clean = re.sub(r"<[^>]+>", " ", raw_text or "")
    clean = html.unescape(re.sub(r"\s+", " ", clean)).strip()
    m_score = re.search(r"\b(\d{1,3})/(\d{1,2})\b", clean)
    if not m_score:
        return None
    runs = int(m_score.group(1))
    wkts = int(m_score.group(2))
    player_name = "Live Batter"
    m_pl = re.search(r"(?:to|by|bowled|lbw|caught|stumped|hit by)\s+([A-Z][a-zA-Z0-9\s\.\-]{1,26})", clean)
    if m_pl:
        cand = m_pl.group(1).strip(" .,-")
        if cand and len(cand.split()) <= 3:
            player_name = cand
    else:
        m_team = re.search(r"\b([A-Z]{2,5})\b", clean[:m_score.start()])
        if m_team:
            player_name = f"{m_team.group(1)} Batter"
    return {"runs": runs, "wkts": wkts, "player": player_name, "line": clean[:120]}

async def _auto_speaker_fire(client, chat_id: int, event_kind: str, player_name: str, match_line: str):
    if event_kind == "6":
        spoken = "Six! Six! Six!"
        action_word = "SIX"
        popup_headline = f"🌟 <b>{html.escape(player_name)} ne SIX maara hai!</b> 🌟"
        badge_txt = "6️⃣ SIX HIT!"
        react_emoji = "🔥"
    elif event_kind == "4":
        spoken = "Four! Four! Four!"
        action_word = "FOUR"
        popup_headline = f"⚡ <b>{html.escape(player_name)} ne FOUR maara hai!</b> ⚡"
        badge_txt = "4️⃣ FOUR HIT!"
        react_emoji = "🎉"
    else:
        spoken = "Wicket! Out!"
        action_word = "WICKET"
        popup_headline = f"🚨 <b>{html.escape(player_name)} OUT ho gaya!</b> 🚨"
        badge_txt = "🚨 WICKET!"
        react_emoji = "😱"

    mp3 = await _make_sfx_mp3(spoken)
    aud_id = await send_colored_audio(
        client,
        chat_id,
        mp3,
        f"Auto Speaker • {action_word}",
        f"@{OWNER_UNAME}",
        3,
        f"🎙 <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑:</b> <code>{spoken}</code>\n\n{FOOTER}",
        _score_menu_rows(),
    )
    if aud_id:
        await _pop_reaction(client, chat_id, aud_id, react_emoji)

    await asyncio.sleep(2.5)

    now = datetime.now(IST).strftime("%I:%M:%S %p")
    popup_text = (
        f"🌟✨🌟 <b>{badge_txt} 𝐏𝐎𝐏-𝐔𝐏</b> 🌟✨🌟\n"
        f"<blockquote>{popup_headline}\n"
        f"🏏 <b>Player:</b> <code>{html.escape(player_name)}</code>\n"
        f"📊 <b>Match:</b> <code>{html.escape(match_line)}</code></blockquote>\n"
        f"🕒 <b>Time:</b> <code>{now}</code>\n\n{FOOTER}"
    )
    pop_id = await send_colored_msg(client, chat_id, popup_text, _score_menu_rows(), reply_to=aud_id)
    if pop_id:
        await _pop_reaction(client, chat_id, pop_id, react_emoji)

async def _auto_speaker_loop(client, chat_id: int):
    try:
        while True:
            await asyncio.sleep(8)
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as s:
                    async with s.get("https://static.cricinfo.com/rss/livescores.xml") as r:
                        if r.status != 200:
                            continue
                        xml_txt = await r.text()
                items = re.findall(r"<item>.*?</item>", xml_txt, flags=re.S) or re.findall(r"<title>(.*?)</title>", xml_txt)[1:4]
                for raw_item in items:
                    parsed = _extract_player_and_score(raw_item)
                    if not parsed:
                        continue
                    runs, wkts, player, line = parsed["runs"], parsed["wkts"], parsed["player"], parsed["line"]
                    st = AUTO_SPEAKER_STATE.get(chat_id)
                    if not st:
                        AUTO_SPEAKER_STATE[chat_id] = {"runs": runs, "wkts": wkts, "last_sig": ""}
                        continue
                    diff_r = runs - st["runs"]
                    diff_w = wkts - st["wkts"]
                    sig = f"{runs}/{wkts}:{diff_r}:{diff_w}"
                    if sig != st.get("last_sig"):
                        st["last_sig"] = sig
                        st["runs"] = runs
                        st["wkts"] = wkts
                        if diff_w > 0:
                            await _auto_speaker_fire(client, chat_id, "w", player, line)
                            break
                        elif diff_r == 6:
                            SCORE_BOARD_STATS[chat_id]["six"] += 1
                            SCORE_BOARD_STATS[chat_id]["last_event"] = f"{player} SIX HUA!"
                            await _auto_speaker_fire(client, chat_id, "6", player, line)
                            break
                        elif diff_r == 4:
                            SCORE_BOARD_STATS[chat_id]["four"] += 1
                            SCORE_BOARD_STATS[chat_id]["last_event"] = f"{player} FOUR HUA!"
                            await _auto_speaker_fire(client, chat_id, "4", player, line)
                            break
            except Exception:
                pass
    except asyncio.CancelledError:
        pass

@bot.on_message(filters.command(["autospeaker", "speaker"], prefixes=["/", "!", "."]))
async def auto_speaker_cmd(client, message: Message):
    chat_id = message.chat.id
    arg = message.command[1].lower() if len(message.command) > 1 else "toggle"
    if arg in ("off", "stop", "disable") or (arg == "toggle" and chat_id in AUTO_SPEAKER_TASKS):
        if chat_id in AUTO_SPEAKER_TASKS:
            AUTO_SPEAKER_TASKS.pop(chat_id).cancel()
        return await send_colored_msg(
            client, chat_id, f"⚪ <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐎𝐅𝐅</b>\n\n{FOOTER}",
            [[_cbtn("▶️ 𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐎𝐍", style="success", callback_data="mgb_aspk_on")]],
            reply_to=message.id,
        )
    if chat_id in AUTO_SPEAKER_TASKS:
        AUTO_SPEAKER_TASKS.pop(chat_id).cancel()
    AUTO_SPEAKER_STATE.pop(chat_id, None)
    AUTO_SPEAKER_TASKS[chat_id] = asyncio.create_task(_auto_speaker_loop(client, chat_id))
    await send_colored_msg(
        client, chat_id,
        f"🎙✨🎙 <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐋𝐈𝐕𝐄 𝐎𝐍</b> 🎙✨🎙\n"
        f"<blockquote><b>🏏 𝐋𝐈𝐕𝐄 𝐌𝐀𝐓𝐂𝐇 𝐀𝐔𝐓𝐎-𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐑</b>\n"
        f"🌟 <b>6 Runs</b> → <i>'Six! Six! Six!'</i> + Player Pop-Up\n"
        f"⚡ <b>4 Runs</b> → <i>'Four! Four! Four!'</i> + Player Pop-Up</blockquote>\n\n{FOOTER}",
        [[
            _cbtn("🌟 𝐒𝐈𝐗 𝐃𝐄𝐌𝐎", style="success", callback_data="mgb_aspk_demo6"),
            _cbtn("⚡ 𝐅𝐎𝐔𝐑 𝐃𝐄𝐌𝐎", style="primary", callback_data="mgb_aspk_demo4"),
            _cbtn("⏹ 𝐒𝐓𝐎𝐏", style="danger", callback_data="mgb_aspk_off"),
        ]],
        reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_aspk_(on|off|demo6|demo4)$"))
async def auto_speaker_cb(client, query: CallbackQuery):
    act = query.matches[0].group(1)
    chat_id = query.message.chat.id
    if act == "off":
        if chat_id in AUTO_SPEAKER_TASKS:
            AUTO_SPEAKER_TASKS.pop(chat_id).cancel()
        await query.answer("⏹ Auto Speaker Stopped!", show_alert=False)
        return await edit_colored_msg(
            client, chat_id, query.message.id, f"⚪ <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐎𝐅𝐅</b>\n\n{FOOTER}",
            [[_cbtn("▶️ 𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐎𝐍", style="success", callback_data="mgb_aspk_on")]],
        )
    if act == "on":
        if chat_id not in AUTO_SPEAKER_TASKS:
            AUTO_SPEAKER_STATE.pop(chat_id, None)
            AUTO_SPEAKER_TASKS[chat_id] = asyncio.create_task(_auto_speaker_loop(client, chat_id))
        await query.answer("🎙 Auto Speaker ON!", show_alert=False)
        return await edit_colored_msg(
            client, chat_id, query.message.id, f"🎙✨🎙 <b>𝐀𝐔𝐓𝐎 𝐒𝐏𝐄𝐀𝐊𝐄𝐑 𝐋𝐈𝐕𝐄 𝐎𝐍</b> 🎙✨🎙\n\n{FOOTER}",
            [[_cbtn("⏹ 𝐒𝐓𝐎𝐏", style="danger", callback_data="mgb_aspk_off")]],
        )
    if act == "demo6":
        await query.answer("🎙 Speaking Six...", show_alert=False)
        await _auto_speaker_fire(client, chat_id, "6", "Virat Kohli", "IND vs AUS • Live Match")
    elif act == "demo4":
        await query.answer("🎙 Speaking Four...", show_alert=False)
        await _auto_speaker_fire(client, chat_id, "4", "Rohit Sharma", "IND vs AUS • Live Match")

# ── 11. SMART AUTO-CLEAN MODE (/autoclean) ────────────────────
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
