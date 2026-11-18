# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 MGB NOT FREE CODER 🍓
# ═══════════════════════════════════════════════════════════════

import io
import time
import json
import html
import random
import aiohttp
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

# ── IN-MEMORY HIGH-SPEED STORAGE ──────────────────────────────
AFK_USERS = {}  # {user_id: {"time": float, "reason": str, "name": str}}
MARRIAGES = {}  # {user_id: {"partner_id": int, "partner_name": str, "since": str}}
MSG_COUNTS = defaultdict(lambda: defaultdict(int))  # {chat_id: {user_id: count}}
USER_NAMES = {}  # {user_id: str}
VC_POINTS = defaultdict(lambda: defaultdict(int))   # {chat_id: {user_id: minutes}}

FOOTER = "<code>🍓 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 : @MGB_NOT_FREE2</code>"

TRUTH_LIST = [
    "Is group mein sabse zyada cute kaun lagta hai? Naam batao!",
    "Apne phone ki search history ki aakhri 3 cheezein सच-सच batao!",
    "Kya kabhi kisi group member par crush aaya hai?",
    "Sabse bada jhooth jo aapne apne ghar walon se bola hai?",
    "Apne crush ke naam ka pehla letter chat mein likho!",
]

DARE_LIST = [
    "Group mein kisi random member ko tag karke 'I Like You' likho!",
    "5 minute ke liye apna Telegram bio 'MGB Fan Forever' rakh lo!",
    "Abhi ek voice note bhejo jisme koi Hindi gaana gaa kar sunao!",
    "Is chat ke 3rd last message wale member ki tareef mein 2 line likho!",
    "Apni gallery ki 5th photo bina soche group mein bhejo!",
]

# ── 🔘 COLORED HTML BUTTON HELPERS (SINGLE EMOJI) ─────────────
def _btn(text: str, url: str = None, callback_data: str = None, style: str = "primary") -> InlineKeyboardButton:
    try:
        return InlineKeyboardButton(text=text, url=url, callback_data=callback_data, style=style)
    except TypeError:
        b = InlineKeyboardButton(text=text, url=url, callback_data=callback_data)
        setattr(b, "style", style)
        return b

def get_brand_html_btns() -> str:
    return (
        '<tg-button-row align="center">'
        '<tg-button type="url" style="primary" url="https://t.me/MGB_NOT_FREE2">👑 𝐎𝐖𝐍𝐄𝐑</tg-button>'
        '<tg-button type="url" style="success" url="https://t.me/ZOYA_SUPPROT">🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒</tg-button>'
        '</tg-button-row>'
    )

def get_brand_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("👑 𝐎𝐖𝐍𝐄𝐑", url="https://t.me/MGB_NOT_FREE2", style="primary"),
            _btn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", url="https://t.me/ZOYA_SUPPROT", style="success"),
        ]
    ])

async def send_rich_card(client, chat_id: int, photo_bio: io.BytesIO, caption: str, html_btns: str = None, fallback_kb: InlineKeyboardMarkup = None):
    if not html_btns:
        html_btns = get_brand_html_btns()
    if not fallback_kb:
        fallback_kb = get_brand_kb()

    token = getattr(client, "bot_token", None)
    if token and photo_bio:
        try:
            clean_cap = caption.replace("\n", "<br>")
            full_html = f'<img src="tg://photo?id=card_img"/><br>{clean_cap}<br><br>{html_btns}'
            payload = {
                "html": full_html,
                "media": [{"id": "card_img", "media": {"type": "photo", "media": "attach://card_img"}}]
            }
            form = aiohttp.FormData()
            form.add_field("chat_id", str(chat_id))
            form.add_field("rich_message", json.dumps(payload, ensure_ascii=False))
            photo_bio.seek(0)
            form.add_field("card_img", photo_bio.read(), filename="mgb_card.jpg", content_type="image/jpeg")

            url = f"https://api.telegram.org/bot{token}/sendRichMessage"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        if res.get("ok"):
                            return
        except Exception:
            pass

    photo_bio.seek(0)
    await client.send_photo(
        chat_id=chat_id,
        photo=photo_bio,
        caption=caption,
        reply_markup=fallback_kb,
        parse_mode=enums.ParseMode.HTML,
    )

# ── 🎨 LUXURY PIL GLASS CARD ENGINE ───────────────────────────
async def _get_user_dp(client, user_id: int) -> Image.Image:
    try:
        user = await client.get_users(user_id)
        if user and user.photo:
            bio = await client.download_media(user.photo.big_file_id, in_memory=True)
            bio.seek(0)
            return Image.open(bio).convert("RGBA")
    except Exception:
        pass
    img = Image.new("RGBA", (300, 300), (35, 25, 65, 255))
    d = ImageDraw.Draw(img)
    d.ellipse((30, 30, 270, 270), fill=(95, 55, 195, 255))
    return img

def _circle_dp(dp: Image.Image, size: int = 210) -> Image.Image:
    dp = dp.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(dp, (0, 0), mask)
    return out

def _make_single_card(dp: Image.Image, badge: str, title: str, line1: str, line2: str, accent=(255, 60, 130)) -> io.BytesIO:
    W, H = 960, 480
    bg = Image.new("RGBA", (W, H), (14, 14, 26, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-80, -80, 380, 380), fill=(*accent, 110))
    gd.ellipse((600, 150, 1020, 520), fill=(50, 140, 255, 100))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(55)))

    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle((45, 45, W - 45, H - 45), radius=32, fill=(26, 26, 46, 215), outline=(*accent, 220), width=3)

    c_dp = _circle_dp(dp, 210)
    draw.ellipse((90, 130, 310, 350), outline=(*accent, 255), width=5)
    bg.paste(c_dp, (95, 135), c_dp)

    try:
        f_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
        f_foot = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception:
        f_badge = f_title = f_sub = f_foot = ImageFont.load_default()

    draw.rounded_rectangle((355, 85, 680, 128), radius=15, fill=(*accent, 230))
    draw.text((375, 95), badge[:24], fill=(255, 255, 255), font=f_badge)
    draw.text((355, 155), title[:22], fill=(255, 255, 255), font=f_title)
    draw.text((355, 225), line1[:36], fill=(210, 215, 240), font=f_sub)
    draw.text((355, 275), line2[:36], fill=(160, 230, 255), font=f_sub)
    draw.text((355, 375), "MGB NOT FREE CODER  |  t.me/ZOYA_SUPPROT", fill=(*accent, 255), font=f_foot)

    out = io.BytesIO()
    out.name = "mgb_card.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=95)
    out.seek(0)
    return out

def _make_dual_card(dp1: Image.Image, dp2: Image.Image, name1: str, name2: str) -> io.BytesIO:
    W, H = 960, 480
    bg = Image.new("RGBA", (W, H), (20, 10, 28, 255))
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle((40, 40, W - 40, H - 40), radius=32, fill=(35, 18, 50, 230), outline=(255, 75, 145), width=4)

    c1 = _circle_dp(dp1, 190)
    c2 = _circle_dp(dp2, 190)
    bg.paste(c1, (110, 120), c1)
    bg.paste(c2, (660, 120), c2)

    try:
        f_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        f_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        f_h = f_s = ImageFont.load_default()

    draw.text((310, 65), "MARRIAGE CERTIFICATE", fill=(255, 215, 90), font=f_h)
    draw.text((445, 190), "❤️", fill=(255, 80, 130), font=f_h)
    draw.text((110, 335), f"{name1[:14]}  weds  {name2[:14]}", fill=(255, 255, 255), font=f_h)
    draw.text((295, 390), "Certified By : MGB NOT FREE CODER", fill=(255, 120, 180), font=f_s)

    out = io.BytesIO()
    out.name = "marriage.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=95)
    out.seek(0)
    return out
# ── 1. SMART AFK CARD (/afk) & MESSAGE TRACKER ────────────────
def _fmt_time(sec: int) -> str:
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")

@bot.on_message(filters.command("afk", prefixes=["/", "!", "."]))
async def set_afk_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    reason = message.text.split(None, 1)[1] if len(message.command) > 1 else "Busy Right Now"
    AFK_USERS[user.id] = {"time": time.time(), "reason": reason, "name": user.first_name}

    dp = await _get_user_dp(client, user.id)
    card = _make_single_card(dp, "AFK MODE ON", user.first_name, f"Reason: {reason}", "Status: Offline", (130, 80, 255))
    cap = (
        f"<blockquote><b>🌙 {html.escape(user.first_name)} अब AFK हैं!</b></blockquote>\n"
        f"💬 <b>Reason:</b> <code>{html.escape(reason)}</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap)

@bot.on_message(filters.group & ~filters.bot, group=9)
async def group_watcher(client, message: Message):
    user = message.from_user
    if not user:
        return

    MSG_COUNTS[message.chat.id][user.id] += 1
    USER_NAMES[user.id] = user.first_name
    if message.voice or message.audio:
        VC_POINTS[message.chat.id][user.id] += 3

    if user.id in AFK_USERS and not (message.text and message.text.lower().startswith(("/afk", "!afk", ".afk"))):
        info = AFK_USERS.pop(user.id)
        dur = _fmt_time(time.time() - info["time"])
        await message.reply_text(
            f"<blockquote><b>✨ {html.escape(user.first_name)} वापस आ गए!</b></blockquote>\n"
            f"⏱ <b>Offline Time:</b> <code>{dur}</code>\n\n{FOOTER}",
            parse_mode=enums.ParseMode.HTML,
        )

    if message.reply_to_message and message.reply_to_message.from_user:
        t_id = message.reply_to_message.from_user.id
        if t_id in AFK_USERS:
            info = AFK_USERS[t_id]
            dur = _fmt_time(time.time() - info["time"])
            dp = await _get_user_dp(client, t_id)
            card = _make_single_card(dp, "USER IS AFK", info["name"], f"Since: {dur}", f"Reason: {info['reason']}", (255, 140, 50))
            cap = (
                f"<blockquote><b>💤 {html.escape(info['name'])} अभी Offline हैं!</b></blockquote>\n"
                f"⏱ <b>Since:</b> <code>{dur}</code>\n"
                f"💬 <b>Reason:</b> <code>{html.escape(info['reason'])}</code>\n\n{FOOTER}"
            )
            await send_rich_card(client, message.chat.id, card, cap)

# ── 2. GROUP MARRIAGE & CERTIFICATE (/marry, /divorce) ────────
@bot.on_message(filters.command(["marry", "propose"], prefixes=["/", "!", "."]))
async def marry_cmd(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("💍 <b>Kisi member ke message par reply karke <code>/marry</code> likhein!</b>", parse_mode=enums.ParseMode.HTML)

    u1 = message.from_user
    u2 = message.reply_to_message.from_user
    if u1.id == u2.id or u2.is_bot:
        return await message.reply_text("😅 <b>Kisi real group member ko propose karein!</b>", parse_mode=enums.ParseMode.HTML)
    if u1.id in MARRIAGES:
        return await message.reply_text(f"💍 <b>Aap pehle se {MARRIAGES[u1.id]['partner_name']} ke saath married hain! (<code>/divorce</code> karein)</b>", parse_mode=enums.ParseMode.HTML)

    kb = InlineKeyboardMarkup([
        [
            _btn("💍 𝐀𝐂𝐂𝐄𝐏𝐓", callback_data=f"mgb_marry_yes_{u1.id}_{u2.id}", style="success"),
            _btn("💔 𝐑𝐄𝐉𝐄𝐂𝐓", callback_data=f"mgb_marry_no_{u1.id}_{u2.id}", style="danger"),
        ]
    ])
    await message.reply_text(
        f"<blockquote><b>💍 𝐌𝐆𝐁 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄 𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋</b></blockquote>\n\n"
        f"❤️ <b>{u1.mention} ne {u2.mention} ko shadi ke liye propose kiya hai!</b>\n\n{FOOTER}",
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_marry_(yes|no)_(\d+)_(\d+)$"))
async def marry_cb(client, query: CallbackQuery):
    action, id1, id2 = query.matches[0].group(1), int(query.matches[0].group(2)), int(query.matches[0].group(3))
    if query.from_user.id != id2:
        return await query.answer("❌ Yeh proposal aapke liye nahi hai!", show_alert=True)

    u1 = await client.get_users(id1)
    u2 = query.from_user

    if action == "no":
        return await query.message.edit_text(
            f"<blockquote><b>💔 𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋 𝐑𝐄𝐉𝐄𝐂𝐓𝐄𝐃</b></blockquote>\n\n"
            f"😢 <b>{u2.mention} ne {u1.mention} ka proposal reject kar diya!</b>\n\n{FOOTER}",
            parse_mode=enums.ParseMode.HTML,
        )

    MARRIAGES[id1] = {"partner_id": id2, "partner_name": u2.first_name}
    MARRIAGES[id2] = {"partner_id": id1, "partner_name": u1.first_name}

    await query.answer("💍 Shadi Mubarak Ho!", show_alert=False)
    dp1 = await _get_user_dp(client, id1)
    dp2 = await _get_user_dp(client, id2)
    cert = _make_dual_card(dp1, dp2, u1.first_name, u2.first_name)

    cap = (
        f"<blockquote><b>💍 𝐌𝐆𝐁 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄 𝐂𝐄𝐑𝐓𝐈𝐅𝐈𝐂𝐀𝐓𝐄</b></blockquote>\n\n"
        f"❤️ <b>Couple:</b> {u1.mention} 💞 {u2.mention}\n"
        f"✨ <b>Status:</b> <code>Officially Married</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, query.message.chat.id, cert, cap)
    try:
        await query.message.delete()
    except Exception:
        pass

@bot.on_message(filters.command("divorce", prefixes=["/", "!", "."]))
async def divorce_cmd(client, message: Message):
    uid = message.from_user.id
    if uid not in MARRIAGES:
        return await message.reply_text("😅 <b>Aapki abhi shadi hi nahi hui hai!</b>", parse_mode=enums.ParseMode.HTML)
    p = MARRIAGES.pop(uid)
    MARRIAGES.pop(p["partner_id"], None)
    await message.reply_text(
        f"<blockquote><b>💔 𝐃𝐈𝐕𝐎𝐑𝐂𝐄 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃</b></blockquote>\n\n"
        f"<b>{message.from_user.mention} aur {html.escape(p['partner_name'])} ab alag ho gaye hain!</b>\n\n{FOOTER}",
        parse_mode=enums.ParseMode.HTML,
    )

# ── 3. BREAKING NEWS & WANTED CARDS (/news, /wanted) ──────────
@bot.on_message(filters.command(["news", "wanted"], prefixes=["/", "!", "."]))
async def news_wanted_cmd(client, message: Message):
    target = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else message.from_user
    cmd = message.command[0].lower()
    dp = await _get_user_dp(client, target.id)

    if cmd == "news":
        headline = message.text.split(None, 1)[1] if len(message.command) > 1 else "Group mein bina gaana suney sote hue pakde gaye!"
        card = _make_single_card(dp, "BREAKING NEWS 24x7", target.first_name, headline[:35], "Live Report: MGB TV", (235, 35, 35))
        cap = (
            f"<blockquote><b>📺 𝐌𝐆𝐁 𝐁𝐑𝐄𝐀𝐊𝐈𝐍𝐆 𝐍𝐄𝐖𝐒</b></blockquote>\n\n"
            f"👤 <b>Target:</b> {target.mention}\n"
            f"🗞 <b>Headline:</b> <code>{html.escape(headline)}</code>\n\n{FOOTER}"
        )
    else:
        bounty = f"Rs. {random.randint(5, 99)},00,000"
        card = _make_single_card(dp, "WANTED DEAD OR ALIVE", target.first_name, f"Reward: {bounty}", "Crime: Group VVIP Member", (220, 150, 30))
        cap = (
            f"<blockquote><b>🚨 𝐌𝐆𝐁 𝐖𝐀𝐍𝐓𝐄𝐃 𝐏𝐎𝐒𝐓𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>Criminal:</b> {target.mention}\n"
            f"💰 <b>Bounty:</b> <code>{bounty}</code>\n\n{FOOTER}"
        )
    await send_rich_card(client, message.chat.id, card, cap)

# ── 4. MUSIC STATS & VIP PROFILE CARD (/profile) ──────────────
@bot.on_message(filters.command(["profile", "vipcard"], prefixes=["/", "!", "."]))
async def profile_cmd(client, message: Message):
    target = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else message.from_user
    msgs = MSG_COUNTS[message.chat.id][target.id] + 1
    partner = MARRIAGES.get(target.id, {}).get("partner_name", "Single")
    rank = "VVIP Legend" if msgs > 150 else ("Pro Listener" if msgs > 40 else "Rising Star")

    dp = await _get_user_dp(client, target.id)
    card = _make_single_card(dp, f"VIP RANK : {rank.upper()}", target.first_name, f"Chat Score: {msgs} Msgs", f"Partner: {partner}", (40, 195, 130))
    cap = (
        f"<blockquote><b>💎 𝐌𝐆𝐁 𝐕𝐈𝐏 𝐏𝐑𝐎𝐅𝐈𝐋𝐄 𝐂𝐀𝐑𝐃</b></blockquote>\n\n"
        f"👤 <b>User:</b> {target.mention}\n"
        f"🏆 <b>Rank:</b> <code>{rank}</code>\n"
        f"💬 <b>Messages:</b> <code>{msgs}</code>  |  💍 <b>Partner:</b> <code>{html.escape(partner)}</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap)

# ── 5. GROUP CHAT & VC LEADERBOARD (/top, /vcstats) ───────────
@bot.on_message(filters.command(["top", "leaderboard", "vcstats"], prefixes=["/", "!", "."]))
async def leaderboard_cmd(client, message: Message):
    cmd = message.command[0].lower()
    data = VC_POINTS[message.chat.id] if cmd == "vcstats" else MSG_COUNTS[message.chat.id]
    if not data:
        MSG_COUNTS[message.chat.id][message.from_user.id] += 1
        USER_NAMES[message.from_user.id] = message.from_user.first_name
        data = MSG_COUNTS[message.chat.id]

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]
    top_uid, top_score = sorted_users[0]
    top_name = USER_NAMES.get(top_uid, "VIP Member")

    dp = await _get_user_dp(client, top_uid)
    title_badge = "TOP VC ADDICTS" if cmd == "vcstats" else "GROUP CHAT LEADERBOARD"
    unit = "Pts" if cmd == "vcstats" else "Msgs"
    card = _make_single_card(dp, title_badge, f"#1 {top_name}", f"Top Score: {top_score} {unit}", f"Total Active: {len(data)} Users", (255, 95, 60))

    lines = [f"<b>{i}.</b> {html.escape(USER_NAMES.get(uid, 'User'))} — <code>{sc} {unit}</code>" for i, (uid, sc) in enumerate(sorted_users, 1)]
    cap = (
        f"<blockquote><b>🏆 𝐌𝐆𝐁 {title_badge}</b></blockquote>\n\n"
        + "\n".join(lines)
        + f"\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap)

# ── 6. TRUTH OR DARE (/truth, /dare) ──────────────────────────
def _td_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("🔥 𝐓𝐑𝐔𝐓𝐇", callback_data="mgb_td_truth", style="primary"),
            _btn("⚡ 𝐃𝐀𝐑𝐄", callback_data="mgb_td_dare", style="danger"),
        ]
    ])

@bot.on_message(filters.command(["truth", "dare"], prefixes=["/", "!", "."]))
async def truth_dare_cmd(client, message: Message):
    is_truth = message.command[0].lower() == "truth"
    q = random.choice(TRUTH_LIST if is_truth else DARE_LIST)
    tag = "🔥 𝐓𝐑𝐔𝐓𝐇" if is_truth else "⚡ 𝐃𝐀𝐑𝐄"
    await message.reply_text(
        f"<blockquote><b>{tag} 𝐂𝐇𝐀𝐋𝐋𝐄𝐍𝐆𝐄</b></blockquote>\n\n"
        f"👤 <b>Player:</b> {message.from_user.mention}\n"
        f"💬 <b>Task:</b> <code>{q}</code>\n\n{FOOTER}",
        reply_markup=_td_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_td_(truth|dare)$"))
async def truth_dare_cb(client, query: CallbackQuery):
    is_truth = query.matches[0].group(1) == "truth"
    q = random.choice(TRUTH_LIST if is_truth else DARE_LIST)
    tag = "🔥 𝐓𝐑𝐔𝐓𝐇" if is_truth else "⚡ 𝐃𝐀𝐑𝐄"
    await query.message.edit_text(
        f"<blockquote><b>{tag} 𝐂𝐇𝐀𝐋𝐋𝐄𝐍𝐆𝐄</b></blockquote>\n\n"
        f"👤 <b>Player:</b> {query.from_user.mention}\n"
        f"💬 <b>Task:</b> <code>{q}</code>\n\n{FOOTER}",
        reply_markup=_td_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

# ── 7. COLORED BUTTON GAME: ROCK PAPER SCISSORS (/rps) ────────
def _rps_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("🪨 𝐑𝐎𝐂𝐊", callback_data="mgb_rps_rock", style="primary"),
            _btn("📄 𝐏𝐀𝐏𝐄𝐑", callback_data="mgb_rps_paper", style="success"),
            _btn("✂️ 𝐒𝐂𝐈𝐒𝐒𝐎𝐑", callback_data="mgb_rps_scissor", style="danger"),
        ]
    ])

@bot.on_message(filters.command(["rps", "game"], prefixes=["/", "!", "."]))
async def rps_cmd(client, message: Message):
    await message.reply_text(
        f"<blockquote><b>🎮 𝐌𝐆𝐁 𝐂𝐎𝐋𝐎𝐑𝐄𝐃 𝐁𝐔𝐓𝐓𝐎𝐍 𝐆𝐀𝐌𝐄</b></blockquote>\n\n"
        f"👇 <b>Apna move chunein ({message.from_user.mention}):</b>\n\n{FOOTER}",
        reply_markup=_rps_kb(),
        parse_mode=enums.ParseMode.HTML,
    )

@bot.on_callback_query(filters.regex(r"^mgb_rps_(rock|paper|scissor)$"))
async def rps_cb(client, query: CallbackQuery):
    u_move = query.matches[0].group(1)
    b_move = random.choice(["rock", "paper", "scissor"])
    wins = {"rock": "scissor", "paper": "rock", "scissor": "paper"}

    if u_move == b_move:
        res = "🤝 Match Draw!"
    elif wins[u_move] == b_move:
        res = f"🏆 {query.from_user.first_name} Jeet Gaye!"
    else:
        res = "🤖 MGB Bot Jeet Gaya!"

    await query.message.edit_text(
        f"<blockquote><b>🎮 𝐌𝐆𝐁 𝐆𝐀𝐌𝐄 𝐑𝐄𝐒𝐔𝐋𝐓</b></blockquote>\n\n"
        f"👤 <b>You:</b> <code>{u_move.upper()}</code>  |  🤖 <b>Bot:</b> <code>{b_move.upper()}</code>\n"
        f"✨ <b>Result:</b> <b>{res}</b>\n\n{FOOTER}",
        reply_markup=_rps_kb(),
        parse_mode=enums.ParseMode.HTML,
    )
    
