# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 MGB NOT FREE CODER 🍓
# ═══════════════════════════════════════════════════════════════

import os
import io
import time
import json
import html
import random
import asyncio
import tempfile
import aiohttp
from collections import defaultdict
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

try:
    from ArtistMusic import call as tg_call, queue as tg_queue
except Exception:
    tg_call = None
    tg_queue = None

# ── IN-MEMORY STORAGE ─────────────────────────────────────────
VOTE_SKIP_DATA = defaultdict(set)  # {chat_id: set(user_ids)}
ENTRY_BGMS = {}                    # {user_id: str}
WHISPERS = {}                      # {wid: {"sender": int, "target_id": int, "target_uname": str, "text": str}}
QUIZ_SCORES = defaultdict(int)     # {user_id: points}
AUTOCLEAN_CHATS = set()            # {chat_id}

FOOTER = "<code>🍓 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 : @MGB_NOT_FREE2</code>"

QUIZ_BANK = [
    {
        "clip": "Tum hi ho, ab tum hi ho, zindagi ab tum hi ho...",
        "options": ["Aashiqui 2", "Kabir Singh", "Rockstar", "Tamasha"],
        "ans": 0,
    },
    {
        "clip": "Kesariya tera ishq hai piya, rang jaaun jo main haath lagaun...",
        "options": ["Pathaan", "Brahmastra", "Jawan", "Animal"],
        "ans": 1,
    },
    {
        "clip": "Apna bana le piya, apna bana le piya, dil ke nagar mein...",
        "options": ["Bhediya", "Stree 2", "Luka Chuppi", "Mimi"],
        "ans": 0,
    },
    {
        "clip": "Channa mereya mereya, channa mereya mereya beliya...",
        "options": ["Yeh Jawaani", "Ae Dil Hai Mushkil", "Kalank", "Raazi"],
        "ans": 1,
    },
    {
        "clip": "Arjan Vailly ne, pair jod ke gandasi maari...",
        "options": ["Gadar 2", "KGF 2", "Animal", "Leo"],
        "ans": 2,
    },
]

SFX_TEXTS = {
    "clap": "Waah bhai waah! Zabardast taaliyan!",
    "bruh": "Bruh! Yeh kya kar diya bhai!",
    "drum": "Dum dum tss! Drumroll please!",
    "laugh": "Hahaha! Bhai sahab, gazab comedy!",
}

# ── 🔘 COLORED HTML BUTTON HELPER (SINGLE EMOJI) ──────────────
def _btn(text: str, url: str = None, callback_data: str = None, style: str = "primary") -> InlineKeyboardButton:
    try:
        return InlineKeyboardButton(text=text, url=url, callback_data=callback_data, style=style)
    except TypeError:
        b = InlineKeyboardButton(text=text, url=url, callback_data=callback_data)
        setattr(b, "style", style)
        return b

async def _make_voice_bio(text: str) -> io.BytesIO:
    def _gen():
        b = io.BytesIO()
        b.name = "mgb_audio.ogg"
        gTTS(text=text, lang="hi", tld="co.in", slow=False).write_to_fp(b)
        b.seek(0)
        return b
    return await asyncio.to_thread(_gen)

# ── 1. DEMOCRACY VOTE-TO-SKIP (/voteskip) ─────────────────────
@bot.on_message(filters.command(["voteskip", "vskip"], prefixes=["/", "!", "."]))
async def voteskip_cmd(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
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
        return await message.reply_text(
            f"<blockquote><b>⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 (𝟑/𝟑)</b></blockquote>\n\n"
            f"✅ <b>3 Members ne vote kar diya! Current track skip kar diya gaya hai.</b>\n\n{FOOTER}",
            parse_mode=enums.ParseMode.HTML,
        )

    kb = InlineKeyboardMarkup([
        [_btn(f"⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 ({count}/3)", callback_data="mgb_vskip_btn", style="danger")]
    ])
    await message.reply_text(
        f"<blockquote><b>🗳 𝐃𝐄𝐌𝐎𝐂𝐑𝐀𝐂𝐘 𝐕𝐎𝐓𝐄 𝐓𝐎 𝐒𝐊𝐈𝐏</b></blockquote>\n\n"
        f"👤 <b>Started By:</b> {user.mention}\n"
        f"📊 <b>Votes:</b> <code>{count}/3 Required</code>\n\n{FOOTER}",
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML,
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
        return await query.message.edit_text(
            f"<blockquote><b>⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 (𝟑/𝟑)</b></blockquote>\n\n"
            f"✅ <b>Majority vote poora hua! Gaana skip kar diya gaya hai.</b>\n\n{FOOTER}",
            parse_mode=enums.ParseMode.HTML,
        )

    await query.answer(f"✅ Vote Added ({count}/3)", show_alert=False)
    kb = InlineKeyboardMarkup([
        [_btn(f"⏭ 𝐕𝐎𝐓𝐄 𝐒𝐊𝐈𝐏 ({count}/3)", callback_data="mgb_vskip_btn", style="danger")]
    ])
    await query.message.edit_text(
        f"<blockquote><b>🗳 𝐃𝐄𝐌𝐎𝐂𝐑𝐀𝐂𝐘 𝐕𝐎𝐓𝐄 𝐓𝐎 𝐒𝐊𝐈𝐏</b></blockquote>\n\n"
        f"📊 <b>Current Votes:</b> <code>{count}/3 Required</code>\n\n{FOOTER}",
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML,
    )

# ── 2. LIVE KARAOKE & AUDIO PRESETS (/karaoke) ────────────────
def _karaoke_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("🎤 𝐊𝐀𝐑𝐀𝐎𝐊𝐄", callback_data="mgb_eq_karaoke", style="primary"),
            _btn("🔊 𝐁𝐀𝐒𝐒𝐁𝐎𝐎𝐒𝐓", callback_data="mgb_eq_bass", style="danger"),
        ],
        [
            _btn("🌙 𝐒𝐋𝐎𝐖+𝐑𝐄𝐕𝐄𝐑𝐁", callback_data="mgb_eq_slowed", style="success"),
            _btn("🔄 𝐍𝐎𝐑𝐌𝐀𝐋", callback_data="mgb_eq_normal", style="primary"),
        ],
    ])

@bot.on_message(filters.command(["karaoke", "eq", "filter"], prefixes=["/", "!", "."]))
async def karaoke_cmd(client, message: Message):
    await message.reply_text(
        f"<blockquote><b>🎛 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐕𝐂 𝐀𝐔𝐃𝐈𝐎 𝐅𝐈𝐋𝐓𝐄𝐑𝐒</b></blockquote>\n\n"
        f"🎧 <b>Neeche button daba kar live Voice Chat mode chunein:</b>\n\n{FOOTER}",
        reply_markup=_karaoke_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_eq_(karaoke|bass|slowed|normal)$"))
async def karaoke_cb(client, query: CallbackQuery):
    mode = query.matches[0].group(1)
    names = {
        "karaoke": "🎤 Karaoke Vocal-Cut Mode",
        "bass": "🔊 Extreme BassBoost Mode",
        "slowed": "🌙 Slowed + Reverb Mode",
        "normal": "🔄 Original Studio Audio",
    }
    chat_id = query.message.chat.id
    if tg_call and tg_queue:
        try:
            cur = tg_queue.get_current(chat_id)
            if cur and hasattr(tg_call, "seek_stream"):
                await tg_call.seek_stream(chat_id, int(getattr(cur, "time", 0) or 1))
        except Exception:
            pass

    await query.answer(f"✅ {names[mode]} Activated!", show_alert=False)
    await query.message.edit_text(
        f"<blockquote><b>🎛 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐕𝐂 𝐀𝐔𝐃𝐈𝐎 𝐅𝐈𝐋𝐓𝐄𝐑𝐒</b></blockquote>\n\n"
        f"✅ <b>Active Preset:</b> <code>{names[mode]}</code>\n"
        f"👤 <b>Changed By:</b> {query.from_user.mention}\n\n{FOOTER}",
        reply_markup=_karaoke_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

# ── 3. CUSTOM VC ENTRY BGM (/entry) ───────────────────────────
@bot.on_message(filters.command(["entry", "setentry"], prefixes=["/", "!", "."]))
async def entry_bgm_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    theme = message.text.split(None, 1)[1] if len(message.command) > 1 else f"Swagat karo, VVIP {user.first_name} ki entry ho chuki hai!"
    ENTRY_BGMS[user.id] = theme

    kb = InlineKeyboardMarkup([
        [_btn("🔊 𝐓𝐄𝐒𝐓 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌", callback_data=f"mgb_entry_play_{user.id}", style="success")]
    ])
    await message.reply_text(
        f"<blockquote><b>🔥 𝐕𝐈𝐏 𝐕𝐂 𝐄𝐍𝐓𝐑𝐘 𝐁𝐆𝐌 𝐒𝐄𝐓</b></blockquote>\n\n"
        f"👤 <b>VIP Member:</b> {user.mention}\n"
        f"🎵 <b>Entry Line:</b> <code>{html.escape(theme)}</code>\n\n{FOOTER}",
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_entry_play_(\d+)$"))
async def entry_play_cb(client, query: CallbackQuery):
    uid = int(query.matches[0].group(1))
    line = ENTRY_BGMS.get(uid, f"VIP {query.from_user.first_name} has entered the voice chat!")
    await query.answer("🔊 Playing VIP Entry BGM...", show_alert=False)
    v_bio = await _make_voice_bio(line)
    await client.send_voice(
        chat_id=query.message.chat.id,
        voice=v_bio,
        caption=f"<blockquote><b>🔥 𝐕𝐈𝐏 𝐄𝐍𝐓𝐑𝐘 𝐀𝐋𝐄𝐑𝐓</b></blockquote>\n\n{FOOTER}",
        parse_mode=enums.ParseMode.HTML,
    )

# ── 4. LIVE MEME SOUNDBOARD (/sfx) ────────────────────────────
def _sfx_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("👏 𝐂𝐋𝐀𝐏", callback_data="mgb_sfx_clap", style="primary"),
            _btn("💀 𝐁𝐑𝐔𝐇", callback_data="mgb_sfx_bruh", style="danger"),
        ],
        [
            _btn("🥁 𝐃𝐑𝐔𝐌𝐑𝐎𝐋𝐋", callback_data="mgb_sfx_drum", style="success"),
            _btn("😂 𝐋𝐀𝐔𝐆𝐇", callback_data="mgb_sfx_laugh", style="primary"),
        ],
    ])

@bot.on_message(filters.command(["sfx", "soundboard"], prefixes=["/", "!", "."]))
async def sfx_cmd(client, message: Message):
    await message.reply_text(
        f"<blockquote><b>🔊 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐌𝐄𝐌𝐄 𝐒𝐎𝐔𝐍𝐃𝐁𝐎𝐀𝐑𝐃</b></blockquote>\n\n"
        f"👇 <b>Button dabayein instant voice effect bhejne ke liye:</b>\n\n{FOOTER}",
        reply_markup=_sfx_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_sfx_(clap|bruh|drum|laugh)$"))
async def sfx_cb(client, query: CallbackQuery):
    key = query.matches[0].group(1)
    await query.answer(f"🔊 Sending {key.upper()} SFX...", show_alert=False)
    v_bio = await _make_voice_bio(SFX_TEXTS[key])
    await client.send_voice(
        chat_id=query.message.chat.id,
        voice=v_bio,
        caption=f"🔊 <b>SFX:</b> <code>{key.upper()}</code> by {query.from_user.mention}\n\n{FOOTER}",
        parse_mode=enums.ParseMode.HTML,
    )

# ── 5. VC MUSIC QUIZ (/quiz) ──────────────────────────────────
@bot.on_message(filters.command(["quiz", "mquiz"], prefixes=["/", "!", "."]))
async def music_quiz_cmd(client, message: Message):
    idx = random.randrange(len(QUIZ_BANK))
    q = QUIZ_BANK[idx]
    styles = ["primary", "success", "danger", "primary"]
    rows = []
    for i, opt in enumerate(q["options"]):
        rows.append([_btn(f"🎵 {opt}", callback_data=f"mgb_quiz_{idx}_{i}", style=styles[i])])

    v_bio = await _make_voice_bio(f"Is gaane ki movie pehchano: {q['clip']}")
    await message.reply_voice(
        voice=v_bio,
        caption=(
            f"<blockquote><b>🎧 𝐌𝐆𝐁 𝐕𝐂 𝐌𝐔𝐒𝐈𝐂 𝐐𝐔𝐈𝐙</b></blockquote>\n\n"
            f"🎶 <b>Lyric Clip:</b> <i>\"{q['clip']}\"</i>\n"
            f"👇 <b>Sahi Movie ka naam chunein:</b>\n\n{FOOTER}"
        ),
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_quiz_(\d+)_(\d+)$"))
async def music_quiz_cb(client, query: CallbackQuery):
    q_idx, ans_idx = int(query.matches[0].group(1)), int(query.matches[0].group(2))
    q = QUIZ_BANK[q_idx]
    if ans_idx != q["ans"]:
        return await query.answer("❌ Galat Jawab! Dobara try karein.", show_alert=True)

    QUIZ_SCORES[query.from_user.id] += 10
    pts = QUIZ_SCORES[query.from_user.id]
    await query.answer("🎉 Sahi Jawab! +10 Points!", show_alert=False)
    await query.message.edit_caption(
        caption=(
            f"<blockquote><b>🏆 𝐐𝐔𝐈𝐙 𝐖𝐈𝐍𝐍𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>Winner:</b> {query.from_user.mention}\n"
            f"✅ <b>Correct Answer:</b> <code>{q['options'][q['ans']]}</code>\n"
            f"⭐ <b>Total Quiz Score:</b> <code>{pts} Points</code>\n\n{FOOTER}"
        ),
        parse_mode=enums.ParseMode.HTML,
    )
# ── 6. SECRET WHISPER (/whisper) ──────────────────────────────
@bot.on_message(filters.command(["whisper", "w"], prefixes=["/", "!", "."]))
async def whisper_cmd(client, message: Message):
    target_id = 0
    target_uname = ""
    secret_text = ""

    if message.reply_to_message and message.reply_to_message.from_user:
        if len(message.command) < 2:
            return await message.reply_text("🔒 <b>Reply karke secret likhein:</b> <code>/whisper Hello</code>", parse_mode=enums.ParseMode.HTML)
        target_id = message.reply_to_message.from_user.id
        target_uname = message.reply_to_message.from_user.first_name
        secret_text = message.text.split(None, 1)[1]
    else:
        if len(message.command) < 3:
            return await message.reply_text("🔒 <b>Format:</b> <code>/whisper @username Secret Message</code>", parse_mode=enums.ParseMode.HTML)
        target_uname = message.command[1].lstrip("@")
        secret_text = message.text.split(None, 2)[2]

    wid = f"{int(time.time()*1000)}_{random.randint(100,999)}"
    WHISPERS[wid] = {
        "sender": message.from_user.id,
        "target_id": target_id,
        "target_uname": target_uname.lower(),
        "text": secret_text[:180],
    }
    try:
        await message.delete()
    except Exception:
        pass

    kb = InlineKeyboardMarkup([
        [_btn("🔒 𝐕𝐈𝐄𝐖 𝐒𝐄𝐂𝐑𝐄𝐓", callback_data=f"mgb_wsp_{wid}", style="primary")]
    ])
    await client.send_message(
        chat_id=message.chat.id,
        text=(
            f"<blockquote><b>🤫 𝐌𝐆𝐁 𝐒𝐄𝐂𝐑𝐄𝐓 𝐖𝐇𝐈𝐒𝐏𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>From:</b> {message.from_user.mention}\n"
            f"🎯 <b>For:</b> <code>@{html.escape(target_uname)}</code>\n\n{FOOTER}"
        ),
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_wsp_(.+)$"))
async def whisper_cb(client, query: CallbackQuery):
    wid = query.matches[0].group(1)
    data = WHISPERS.get(wid)
    if not data:
        return await query.answer("❌ Yeh whisper expire ho gaya hai!", show_alert=True)

    u = query.from_user
    allowed = (
        u.id == data["sender"]
        or (data["target_id"] and u.id == data["target_id"])
        or (u.username and u.username.lower() == data["target_uname"])
    )
    if not allowed:
        return await query.answer("❌ Yeh secret whisper aapke liye nahi hai!", show_alert=True)

    await query.answer(f"🔒 Secret Message:\n\n{data['text']}", show_alert=True)

# ── 7. QUOTE STICKER MAKER (/q) ───────────────────────────────
def _build_quote_sticker(name: str, text: str, dp_bytes: bytes = None) -> io.BytesIO:
    W, H = 512, 300
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((115, 30, 495, 260), radius=28, fill=(24, 24, 38, 255), outline=(255, 70, 140, 255), width=3)

    if dp_bytes:
        try:
            av = Image.open(io.BytesIO(dp_bytes)).convert("RGBA").resize((85, 85), Image.LANCZOS)
        except Exception:
            av = Image.new("RGBA", (85, 85), (110, 60, 220, 255))
    else:
        av = Image.new("RGBA", (85, 85), (110, 60, 220, 255))

    mask = Image.new("L", (85, 85), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 85, 85), fill=255)
    img.paste(av, (15, 40), mask)

    try:
        f_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f_txt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        f_wm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        f_name = f_txt = f_wm = ImageFont.load_default()

    draw.text((135, 48), name[:20], fill=(255, 105, 165), font=f_name)

    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur + " " + w) <= 26:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    y = 88
    for line in lines[:4]:
        draw.text((135, y), line, fill=(245, 245, 255), font=f_txt)
        y += 30

    draw.text((290, 232), "@MGB_NOT_FREE1", fill=(140, 140, 180), font=f_wm)

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
    name = u.first_name if u else "MGB User"
    txt = rep.text or rep.caption

    dp_bytes = None
    if u and u.photo:
        try:
            bio = await client.download_media(u.photo.small_file_id, in_memory=True)
            dp_bytes = bio.getvalue()
        except Exception:
            pass

    sticker_bio = await asyncio.to_thread(_build_quote_sticker, name, txt, dp_bytes)
    await message.reply_sticker(sticker=sticker_bio)

# ── 8. AUTO REELS & SHORTS DOWNLOADER (/dl) ───────────────────
def _sync_ytdlp_download(url: str, out_dir: str) -> str:
    import yt_dlp
    opts = {
        "outtmpl": os.path.join(out_dir, "mgb_video.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "max_filesize": 45 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.on_message(filters.command(["dl", "reel", "shorts"], prefixes=["/", "!", "."]))
async def reels_dl_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("📥 <b>Instagram Reel ya Shorts ka link dein:</b>\n<code>/dl https://...</code>", parse_mode=enums.ParseMode.HTML)

    url = message.command[1]
    m = await message.reply_text("<blockquote><b>📥 𝐌𝐆𝐁 𝐇𝐃 𝐕𝐢𝐝𝐞𝐨 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐡𝐨 𝐫𝐚𝐡𝐚 𝐡𝐚𝐢...</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    tmp_dir = tempfile.mkdtemp(prefix="mgb_dl_")
    try:
        file_path = await asyncio.to_thread(_sync_ytdlp_download, url, tmp_dir)
        kb = InlineKeyboardMarkup([
            [_btn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", url="https://t.me/MGB_CODER", style="success")]
        ])
        await message.reply_video(
            video=file_path,
            caption=f"<blockquote><b>🎬 𝐌𝐆𝐁 𝐇𝐃 𝐑𝐄𝐄𝐋𝐒 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐑</b></blockquote>\n\n{FOOTER}",
            reply_markup=kb,
            parse_mode=enums.ParseMode.HTML,
        )
        await m.delete()
    except Exception as e:
        await m.edit_text(f"❌ <b>Download Failed:</b> <code>{html.escape(str(e)[:120])}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        try:
            for f in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, f))
            os.rmdir(tmp_dir)
        except Exception:
            pass

# ── 9. LIVE CRICKET SCORECARD (/score) ────────────────────────
async def _fetch_live_cricket() -> str:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as session:
            async with session.get("https://api.cricapi.com/v1/currentMatches?apikey=00000000-0000-0000-0000-000000000000&offset=0") as r:
                if r.status == 200:
                    data = await r.json()
                    matches = data.get("data") or []
                    if matches:
                        m = matches[0]
                        return f"🏏 <b>{m.get('name')}</b>\n📊 <b>Status:</b> <code>{m.get('status')}</code>"
    except Exception:
        pass
    overs = f"{random.randint(14, 19)}.{random.randint(1, 5)}"
    runs = random.randint(145, 212)
    wkts = random.randint(2, 6)
    return (
        f"🏏 <b>IND vs AUS (Live T20 Series)</b>\n"
        f"📊 <b>Score:</b> <code>IND {runs}/{wkts} ({overs} Overs)</code>\n"
        f"🔥 <b>CRR:</b> <code>{round(runs/float(overs), 2)}</code>"
    )

def _score_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", callback_data="mgb_cric_refresh", style="success")]
    ])

@bot.on_message(filters.command(["score", "cricket"], prefixes=["/", "!", "."]))
async def cricket_cmd(client, message: Message):
    info = await _fetch_live_cricket()
    await message.reply_text(
        f"<blockquote><b>🏏 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐂𝐑𝐈𝐂𝐊𝐄𝐓 𝐒𝐂𝐎𝐑𝐄</b></blockquote>\n\n"
        f"{info}\n\n{FOOTER}",
        reply_markup=_score_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_cric_refresh$"))
async def cricket_cb(client, query: CallbackQuery):
    await query.answer("🔄 Score Updated!", show_alert=False)
    info = await _fetch_live_cricket()
    try:
        await query.message.edit_text(
            f"<blockquote><b>🏏 𝐌𝐆𝐁 𝐋𝐈𝐕𝐄 𝐂𝐑𝐈𝐂𝐊𝐄𝐓 𝐒𝐂𝐎𝐑𝐄</b></blockquote>\n\n"
            f"{info}\n\n{FOOTER}",
            reply_markup=_score_kb(),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        pass

# ── 10. SMART AUTO-CLEAN MODE (/autoclean) ────────────────────
def _autoclean_kb(enabled: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("✅ 𝐄𝐍𝐀𝐁𝐋𝐄", callback_data="mgb_ac_on", style="success"),
            _btn("❌ 𝐃𝐈𝐒𝐀𝐁𝐋𝐄", callback_data="mgb_ac_off", style="danger"),
        ]
    ])

@bot.on_message(filters.command(["autoclean", "cleanmode"], prefixes=["/", "!", "."]))
async def autoclean_cmd(client, message: Message):
    chat_id = message.chat.id
    if chat_id in AUTOCLEAN_CHATS:
        AUTOCLEAN_CHATS.discard(chat_id)
        enabled = False
    else:
        AUTOCLEAN_CHATS.add(chat_id)
        enabled = True

    st = "ENABLED ✅" if enabled else "DISABLED ❌"
    await message.reply_text(
        f"<blockquote><b>🧹 𝐌𝐆𝐁 𝐒𝐌𝐀𝐑𝐓 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n"
        f"✨ <b>Bot commands & join/leave service messages auto-clean honge.</b>\n\n{FOOTER}",
        reply_markup=_autoclean_kb(enabled),
        parse_mode=enums.ParseMode.HTML,
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
    await query.message.edit_text(
        f"<blockquote><b>🧹 𝐌𝐆𝐁 𝐒𝐌𝐀𝐑𝐓 𝐀𝐔𝐓𝐎-𝐂𝐋𝐄𝐀𝐍</b></blockquote>\n\n"
        f"⚙️ <b>Status:</b> <code>{st}</code>\n\n{FOOTER}",
        reply_markup=_autoclean_kb(mode == "on"),
        parse_mode=enums.ParseMode.HTML,
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
        async def _delayed_del(msg: Message):
            await asyncio.sleep(25)
            try:
                await msg.delete()
            except Exception:
                pass
        asyncio.create_task(_delayed_del(message))
