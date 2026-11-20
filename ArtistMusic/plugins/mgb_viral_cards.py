# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
# ═══════════════════════════════════════════════════════════════

import os
import io
import time
import json
import html
import random
import asyncio
import unicodedata
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pyrogram import filters, enums
from pyrogram.types import Message, CallbackQuery

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

# ── BRANDING & AUTO TEMPLATE ──────────────────────────────────
OWNER_UNAME = "MGB_NOT_FREE_1"
CHANNEL_UNAME = "MGB_CODER"
FOOTER = f"<code>🍓 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 : @{OWNER_UNAME}</code>"
IST = timezone(timedelta(hours=5, minutes=30))

CARD_TEMPLATE_URL = "https://i.ibb.co/MDRnVS7r/photo-AQADc-BRr-G5-SZ-Vd8.jpg"
_CACHED_TEMPLATE = None

AFK_USERS = {}
MARRIAGES = {}
MARRY_PENDING = {}
MSG_COUNTS = defaultdict(lambda: defaultdict(int))
USER_NAMES = {}
VC_POINTS = defaultdict(lambda: defaultdict(int))
LIVE_LB_TASKS = {}
TD_ACTIVE = {}
RPS_ACTIVE = {}
RANK_MILESTONES = {50: "PRO LISTENER", 150: "VVIP LEGEND", 300: "ROYAL KING"}

TRUTH_LIST = [
    "Is group mein sabse zyada cute kaun lagta hai? Naam batao!",
    "Apne phone ki search history ki aakhri 3 cheezein sach-sach batao!",
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

def _brand_html_btns() -> str:
    return (
        '<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="https://t.me/{OWNER_UNAME}">👑 𝐎𝐖𝐍𝐄𝐑</tg-button>'
        f'<tg-button type="url" style="success" url="https://t.me/{CHANNEL_UNAME}">🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒</tg-button>'
        '</tg-button-row>'
    )

def _brand_json_kb() -> list:
    return [[
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]]

async def _bot_api_req(client, method: str, data: dict):
    token = getattr(client, "bot_token", None)
    if not token:
        return None
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as s:
            async with s.post(f"https://api.telegram.org/bot{token}/{method}", json=data) as r:
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
            res = await _bot_api_req(client, "sendRichMessage", rich_payload)
            if res:
                return res.get("message_id")

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": rows},
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    res = await _bot_api_req(client, "sendMessage", payload)
    if res:
        return res.get("message_id")
    m = await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML)
    return m.id

async def edit_colored_msg(client, chat_id: int, msg_id: int, text: str, rows: list = None):
    if rows is not None:
        for attr in ("callback_data", "data"):
            rich_btns = _rows_to_rich_html(rows, cb_attr=attr)
            rich_html = text.replace("\n", "<br>") + (("<br><br>" + rich_btns) if rich_btns else "")
            res = await _bot_api_req(
                client,
                "editRichMessage",
                {"chat_id": chat_id, "message_id": msg_id, "rich_message": {"html": rich_html}},
            )
            if res:
                return res

    payload = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if rows is not None:
        payload["reply_markup"] = {"inline_keyboard": rows}
    return await _bot_api_req(client, "editMessageText", payload)

async def send_rich_card(client, chat_id: int, photo_bio: io.BytesIO, caption: str, json_rows: list = None):
    token = getattr(client, "bot_token", None)
    if token and photo_bio:
        for attr in ("callback_data", "data"):
            try:
                clean_cap = caption.replace("\n", "<br>")
                btns_html = _rows_to_rich_html(json_rows, cb_attr=attr) if json_rows else _brand_html_btns()
                full_html = f'<img src="tg://photo?id=card_img"/><br>{clean_cap}<br><br>{btns_html}'
                payload = {
                    "html": full_html,
                    "media": [{"id": "card_img", "media": {"type": "photo", "media": "attach://card_img"}}],
                }
                form = aiohttp.FormData()
                form.add_field("chat_id", str(chat_id))
                form.add_field("rich_message", json.dumps(payload, ensure_ascii=False))
                photo_bio.seek(0)
                form.add_field("card_img", photo_bio.read(), filename="mgb_banner.jpg", content_type="image/jpeg")
                async with aiohttp.ClientSession() as s:
                    async with s.post(f"https://api.telegram.org/bot{token}/sendRichMessage", data=form) as r:
                        res = await r.json()
                        if res.get("ok"):
                            return res.get("result", {}).get("message_id")
            except Exception:
                pass
            if not json_rows:
                break

        try:
            form = aiohttp.FormData()
            form.add_field("chat_id", str(chat_id))
            form.add_field("caption", caption)
            form.add_field("parse_mode", "HTML")
            form.add_field("reply_markup", json.dumps({"inline_keyboard": json_rows or _brand_json_kb()}))
            photo_bio.seek(0)
            form.add_field("photo", photo_bio.read(), filename="mgb_banner.jpg", content_type="image/jpeg")
            async with aiohttp.ClientSession() as s:
                async with s.post(f"https://api.telegram.org/bot{token}/sendPhoto", data=form) as r:
                    res = await r.json()
                    if res.get("ok"):
                        return res.get("result", {}).get("message_id")
        except Exception:
            pass

    photo_bio.seek(0)
    m = await client.send_photo(chat_id, photo_bio, caption=caption, parse_mode=enums.ParseMode.HTML)
    return m.id

# ── 🎨 ULTRA-CRISP 4K STYLISH BOLD BANNER ENGINE (NO BLUR) ───
FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "χ": "X", "Χ": "X", "×": "X",
    "Δ": "A", "Σ": "E", "Ω": "O", "β": "B", "α": "A",
})

def _clean_pil_text(text: str, limit: int = 34, upper: bool = True) -> str:
    s = str(text or "VIP MEMBER").translate(FANCY_MAP)
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip()
    if upper:
        s = s.upper()
    if len(s) > limit:
        s = s[: limit - 2].rstrip() + ".."
    return s or "VIP MEMBER"

async def _get_template_bg():
    global _CACHED_TEMPLATE
    if _CACHED_TEMPLATE is not None:
        return _CACHED_TEMPLATE.copy()

    for path in (
        "mgb_card_bg.png",
        "mgb_card_bg.jpg",
        "assets/mgb_card_bg.png",
        "ArtistMusic/assets/mgb_card_bg.png",
    ):
        if os.path.isfile(path):
            try:
                _CACHED_TEMPLATE = Image.open(path).convert("RGBA").resize((1280, 720), Image.LANCZOS)
                return _CACHED_TEMPLATE.copy()
            except Exception:
                pass

    if CARD_TEMPLATE_URL:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
                async with s.get(CARD_TEMPLATE_URL, headers=headers) as r:
                    if r.status == 200:
                        raw = await r.read()
                        _CACHED_TEMPLATE = Image.open(io.BytesIO(raw)).convert("RGBA").resize((1280, 720), Image.LANCZOS)
                        return _CACHED_TEMPLATE.copy()
        except Exception:
            pass
    return None

async def _get_user_dp(client, user_id: int) -> Image.Image:
    try:
        user = await client.get_users(user_id)
        if user and user.photo:
            bio = await client.download_media(user.photo.big_file_id, in_memory=True)
            bio.seek(0)
            return Image.open(bio).convert("RGBA")
    except Exception:
        pass
    img = Image.new("RGBA", (380, 380), (20, 12, 42, 255))
    ImageDraw.Draw(img).ellipse((25, 25, 355, 355), fill=(115, 45, 220, 255))
    return img

def _circle_dp(dp: Image.Image, size: int = 374) -> Image.Image:
    dp = ImageOps.fit(dp.convert("RGBA"), (size, size), method=Image.LANCZOS, centering=(0.5, 0.35))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(dp, (0, 0), mask)
    return out

def _detect_ring_circle(tpl: Image.Image):
    rgb = tpl.convert("RGB")
    px = rgb.load()
    _, h = rgb.size
    cx, cy = 286, 334

    def _bright(x, y):
        r, g, b = px[x, y]
        return (r + g + b) / 3

    lx, rx = cx, cx
    while lx > 50 and _bright(lx, cy) < 110:
        lx -= 1
    while rx < 540 and _bright(rx, cy) < 110:
        rx += 1
    cx = (lx + rx) // 2

    ty, by = cy, cy
    while ty > 80 and _bright(cx, ty) < 110:
        ty -= 1
    while by < h - 80 and _bright(cx, by) < 110:
        by += 1
    cy = (ty + by) // 2

    diam = max(rx - lx, by - ty) + 10
    if not (340 <= diam <= 420):
        return 286, 334, 376
    return cx, cy, diam

def _load_bold_font(size: int, italic: bool = False):
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if italic
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _fit_font(text: str, max_width: int, start_size: int, min_size: int = 20, italic: bool = False):
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    for sz in range(start_size, min_size - 1, -2):
        f = _load_bold_font(sz, italic=italic)
        box = dummy.textbbox((0, 0), text, font=f)
        if (box[2] - box[0]) <= max_width:
            return f
    return _load_bold_font(min_size, italic=italic)

def _draw_crisp_stylish_text(
    img: Image.Image,
    xy: tuple,
    text: str,
    font,
    fill=(255, 255, 255),
    accent=(255, 210, 50),
    anchor="lm",
    stroke_w: int = 3,
) -> Image.Image:
    x, y = xy
    # 1. Very light tight ambient backlight (NO blur over letters)
    glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text((x, y), text, font=font, fill=(*accent, 95), anchor=anchor, stroke_width=2, stroke_fill=(*accent, 80))
    img = Image.alpha_composite(img, glow_layer.filter(ImageFilter.GaussianBlur(3)))

    # 2. Sharp solid 3D dark drop-shadow for crystal-clear pop
    d = ImageDraw.Draw(img)
    d.text((x + 3, y + 4), text, font=font, fill=(4, 2, 12, 245), anchor=anchor, stroke_width=stroke_w, stroke_fill=(4, 2, 12, 245))

    # 3. Ultra-sharp dark outline + pure bright solid fill (100% crisp, zero haze)
    d.text((x, y), text, font=font, fill=(*fill, 255), anchor=anchor, stroke_width=stroke_w, stroke_fill=(12, 6, 26, 255))
    return img

def _make_single_card(dp: Image.Image, badge: str, title: str, line1: str, line2: str, accent=(255, 215, 50), template_bg=None) -> io.BytesIO:
    W, H = 1280, 720
    if template_bg is not None:
        bg = template_bg.copy()
        cx, cy, diam = _detect_ring_circle(bg)
        c_dp = _circle_dp(dp, diam)
        bg.paste(c_dp, (cx - diam // 2, cy - diam // 2), c_dp)
    else:
        bg = Image.new("RGBA", (W, H), (8, 5, 18, 255))
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle((44, 44, W - 44, H - 44), radius=40, fill=(14, 10, 28, 232), outline=(255, 205, 65, 255), width=5)
        c_dp = _circle_dp(dp, 360)
        bg.paste(c_dp, (106, 154), c_dp)
        d.ellipse((102, 150, 470, 518), outline=(255, 210, 70, 255), width=6)

    t_badge = _clean_pil_text(badge, 26, upper=True)
    t_name = _clean_pil_text(title, 22, upper=True)
    t_l1 = _clean_pil_text(line1, 34, upper=False)
    t_l2 = _clean_pil_text(line2, 32, upper=True)
    t_foot = f"POWERED BY : @{OWNER_UNAME}"

    f_badge = _fit_font(t_badge, 460, 40, 24, italic=True)
    f_name = _fit_font(t_name, 540, 58, 30, italic=True)
    f_l1 = _fit_font(t_l1, 560, 38, 22, italic=False)
    f_l2 = _fit_font(t_l2, 560, 36, 22, italic=True)
    f_foot = _fit_font(t_foot, 540, 30, 20, italic=False)

    # Crystal-clear high-contrast bold colors
    bg = _draw_crisp_stylish_text(bg, (802, 138), t_badge, f_badge, fill=(255, 224, 66), accent=(255, 185, 20), anchor="mm", stroke_w=3)
    bg = _draw_crisp_stylish_text(bg, (525, 234), t_name, f_name, fill=(255, 255, 255), accent=(210, 120, 255), anchor="lm", stroke_w=4)
    bg = _draw_crisp_stylish_text(bg, (525, 332), t_l1, f_l1, fill=(255, 215, 45), accent=(255, 165, 0), anchor="lm", stroke_w=3)
    bg = _draw_crisp_stylish_text(bg, (525, 426), t_l2, f_l2, fill=(56, 242, 255), accent=(0, 195, 255), anchor="lm", stroke_w=3)
    bg = _draw_crisp_stylish_text(bg, (802, 540), t_foot, f_foot, fill=(255, 235, 95), accent=(255, 190, 30), anchor="mm", stroke_w=3)

    out = io.BytesIO()
    out.name = "mgb_banner.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=98, subsampling=0)
    out.seek(0)
    return out

def _make_dual_card(dp1: Image.Image, dp2: Image.Image, name1: str, name2: str, template_bg=None) -> io.BytesIO:
    W, H = 1280, 720
    bg = template_bg.copy() if template_bg is not None else Image.new("RGBA", (W, H), (12, 6, 24, 255))
    c1, c2 = _circle_dp(dp1, 240), _circle_dp(dp2, 240)
    bg.paste(c1, (140, 160), c1)
    bg.paste(c2, (900, 160), c2)
    d = ImageDraw.Draw(bg)
    d.ellipse((136, 156, 384, 404), outline=(255, 225, 95), width=6)
    d.ellipse((896, 156, 1144, 404), outline=(255, 80, 165), width=6)

    f_h = _fit_font("MARRIAGE CERTIFICATE", 650, 48, 28, italic=True)
    f_w = _fit_font("ROYAL WEDS", 320, 44, 26, italic=True)
    couple = f"{_clean_pil_text(name1, 14)}  &  {_clean_pil_text(name2, 14)}"
    f_n = _fit_font(couple, 1050, 50, 28, italic=True)
    f_s = _fit_font(f"POWERED BY : @{OWNER_UNAME}", 650, 30, 20, italic=False)

    bg = _draw_crisp_stylish_text(bg, (640, 112), "MARRIAGE CERTIFICATE", f_h, fill=(255, 225, 70), accent=(255, 165, 25), anchor="mm", stroke_w=3)
    bg = _draw_crisp_stylish_text(bg, (640, 280), "ROYAL WEDS", f_w, fill=(255, 115, 190), accent=(255, 50, 130), anchor="mm", stroke_w=3)
    bg = _draw_crisp_stylish_text(bg, (640, 468), couple, f_n, fill=(255, 255, 255), accent=(190, 95, 255), anchor="mm", stroke_w=4)
    bg = _draw_crisp_stylish_text(bg, (640, 560), f"POWERED BY : @{OWNER_UNAME}", f_s, fill=(255, 230, 90), accent=(255, 175, 20), anchor="mm", stroke_w=3)

    out = io.BytesIO()
    out.name = "marriage_banner.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=98, subsampling=0)
    out.seek(0)
    return out
# ── 1. SMART AFK BANNER (/afk) & AUTO RANK-UP WATCHER ─────────
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
    tpl = await _get_template_bg()
    card = _make_single_card(dp, "AFK MODE ON", user.first_name, f"Reason: {reason}", "Status: Offline", template_bg=tpl)
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

    chat_id = message.chat.id
    MSG_COUNTS[chat_id][user.id] += 1
    USER_NAMES[user.id] = user.first_name
    if message.voice or message.audio:
        VC_POINTS[chat_id][user.id] += 3

    # Auto VIP Rank-Up Banner on Milestone (50 / 150 / 300 Messages)
    new_cnt = MSG_COUNTS[chat_id][user.id]
    if new_cnt in RANK_MILESTONES:
        new_rank = RANK_MILESTONES[new_cnt]
        try:
            dp = await _get_user_dp(client, user.id)
            tpl = await _get_template_bg()
            card = _make_single_card(
                dp,
                "AUTO RANK UP!",
                user.first_name,
                f"New Rank: {new_rank}",
                f"Milestone: {new_cnt} Messages",
                template_bg=tpl,
            )
            cap = (
                f"<blockquote><b>🏆 𝐀𝐔𝐓𝐎 𝐕𝐈𝐏 𝐑𝐀𝐍𝐊-𝐔𝐏!</b></blockquote>\n\n"
                f"👑 <b>Member:</b> <b>{html.escape(user.first_name)}</b>\n"
                f"✨ <b>New Rank:</b> <code>{new_rank}</code> ({new_cnt} Msgs)\n\n{FOOTER}"
            )
            await send_rich_card(client, chat_id, card, cap)
        except Exception:
            pass

    # Auto AFK Return Alert
    if user.id in AFK_USERS and not (message.text and message.text.lower().startswith(("/afk", "!afk", ".afk"))):
        info = AFK_USERS.pop(user.id)
        dur = _fmt_time(time.time() - info["time"])
        await send_colored_msg(
            client,
            chat_id,
            f"<blockquote><b>✨ {html.escape(user.first_name)} वापस आ गए!</b></blockquote>\n"
            f"⏱ <b>Offline Time:</b> <code>{dur}</code>\n\n{FOOTER}",
            _brand_json_kb(),
            reply_to=message.id,
        )

    # Auto AFK Mention / Reply Alert
    if message.reply_to_message and message.reply_to_message.from_user:
        t_id = message.reply_to_message.from_user.id
        if t_id in AFK_USERS:
            info = AFK_USERS[t_id]
            dur = _fmt_time(time.time() - info["time"])
            dp = await _get_user_dp(client, t_id)
            tpl = await _get_template_bg()
            card = _make_single_card(dp, "USER IS AFK", info["name"], f"Since: {dur}", f"Reason: {info['reason']}", template_bg=tpl)
            cap = (
                f"<blockquote><b>💤 {html.escape(info['name'])} अभी Offline हैं!</b></blockquote>\n"
                f"⏱ <b>Since:</b> <code>{dur}</code>\n"
                f"💬 <b>Reason:</b> <code>{html.escape(info['reason'])}</code>\n\n{FOOTER}"
            )
            await send_rich_card(client, chat_id, card, cap)

# ── 2. GROUP MARRIAGE & ROYAL BANNER (1-TIME LOCK) ────────────
@bot.on_message(filters.command(["marry", "propose"], prefixes=["/", "!", "."]))
async def marry_cmd(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await send_colored_msg(
            client, message.chat.id,
            f"<blockquote><b>💍 𝐌𝐆𝐁 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄</b></blockquote>\n\n<b>Kisi member par reply karke <code>/marry</code> likhein!</b>\n\n{FOOTER}",
            _brand_json_kb(), reply_to=message.id,
        )

    u1, u2 = message.from_user, message.reply_to_message.from_user
    if u1.id == u2.id or u2.is_bot:
        return await message.reply_text("😅 <b>Kisi real group member ko propose karein!</b>", parse_mode=enums.ParseMode.HTML)
    if u1.id in MARRIAGES:
        return await message.reply_text(f"💍 <b>Aap pehle se {html.escape(MARRIAGES[u1.id]['partner_name'])} ke saath married hain!</b>", parse_mode=enums.ParseMode.HTML)

    pid = f"{int(time.time()*1000)}{random.randint(10,99)}"
    MARRY_PENDING[pid] = {"u1": u1.id, "u2": u2.id, "done": False}
    rows = [[
        _cbtn("💍 𝐀𝐂𝐂𝐄𝐏𝐓", style="success", callback_data=f"mgb_marry_yes_{pid}"),
        _cbtn("💔 𝐑𝐄𝐉𝐄𝐂𝐓", style="danger", callback_data=f"mgb_marry_no_{pid}"),
    ]]
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>💍 𝐌𝐆𝐁 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄 𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋</b></blockquote>\n\n"
        f"❤️ <b>{html.escape(u1.first_name)}</b> ne <b>{html.escape(u2.first_name)}</b> ko propose kiya hai!\n\n{FOOTER}",
        rows, reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_marry_(yes|no)_(\d+)$"))
async def marry_cb(client, query: CallbackQuery):
    action, pid = query.matches[0].group(1), query.matches[0].group(2)
    state = MARRY_PENDING.get(pid)
    if not state or state.get("done"):
        return await query.answer("🔒 Yeh proposal khatam ho chuka hai!", show_alert=True)
    if query.from_user.id != state["u2"]:
        return await query.answer("❌ Yeh proposal aapke liye nahi hai!", show_alert=True)

    state["done"] = True
    MARRY_PENDING.pop(pid, None)

    id1, id2 = state["u1"], state["u2"]
    u1 = await client.get_users(id1)
    u2 = query.from_user

    if action == "no":
        await query.answer("💔 Proposal Rejected", show_alert=False)
        return await edit_colored_msg(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>💔 𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋 𝐑𝐄𝐉𝐄𝐂𝐓𝐄𝐃</b></blockquote>\n\n"
            f"😢 <b>{html.escape(u2.first_name)}</b> ne reject kar diya!\n\n{FOOTER}",
            [],
        )

    MARRIAGES[id1] = {"partner_id": id2, "partner_name": u2.first_name}
    MARRIAGES[id2] = {"partner_id": id1, "partner_name": u1.first_name}

    await query.answer("💍 Shadi Mubarak Ho!", show_alert=False)
    dp1 = await _get_user_dp(client, id1)
    dp2 = await _get_user_dp(client, id2)
    tpl = await _get_template_bg()
    cert = _make_dual_card(dp1, dp2, u1.first_name, u2.first_name, template_bg=tpl)

    cap = (
        f"<blockquote><b>💍 𝐌𝐆𝐁 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄 𝐂𝐄𝐑𝐓𝐈𝐅𝐈𝐂𝐀𝐓𝐄</b></blockquote>\n\n"
        f"❤️ <b>Couple:</b> <b>{html.escape(u1.first_name)}</b> 💞 <b>{html.escape(u2.first_name)}</b>\n"
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
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>💔 𝐃𝐈𝐕𝐎𝐑𝐂𝐄 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃</b></blockquote>\n\n"
        f"<b>{html.escape(message.from_user.first_name)}</b> aur <b>{html.escape(p['partner_name'])}</b> ab alag ho gaye!\n\n{FOOTER}",
        _brand_json_kb(), reply_to=message.id,
    )

# ── 3. BREAKING NEWS & WANTED ROYAL BANNERS (/news, /wanted) ─
@bot.on_message(filters.command(["news", "wanted"], prefixes=["/", "!", "."]))
async def news_wanted_cmd(client, message: Message):
    target = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else message.from_user
    cmd = message.command[0].lower()
    dp = await _get_user_dp(client, target.id)
    tpl = await _get_template_bg()

    if cmd == "news":
        headline = message.text.split(None, 1)[1] if len(message.command) > 1 else "Group mein bina gaana suney sote hue pakde gaye!"
        card = _make_single_card(dp, "BREAKING NEWS 24x7", target.first_name, headline[:34], "LIVE REPORT : MGB TV", template_bg=tpl)
        cap = (
            f"<blockquote><b>📺 𝐌𝐆𝐁 𝐁𝐑𝐄𝐀𝐊𝐈𝐍𝐆 𝐍𝐄𝐖𝐒</b></blockquote>\n\n"
            f"👤 <b>Target:</b> <b>{html.escape(target.first_name)}</b>\n"
            f"🗞 <b>Headline:</b> <code>{html.escape(headline)}</code>\n\n{FOOTER}"
        )
    else:
        bounty = f"Rs. {random.randint(5, 99)},00,000"
        card = _make_single_card(dp, "WANTED DEAD OR ALIVE", target.first_name, f"Reward: {bounty}", "CRIME : VVIP LEGEND", template_bg=tpl)
        cap = (
            f"<blockquote><b>🚨 𝐌𝐆𝐁 𝐖𝐀𝐍𝐓𝐄𝐃 𝐏𝐎𝐒𝐓𝐄𝐑</b></blockquote>\n\n"
            f"👤 <b>Criminal:</b> <b>{html.escape(target.first_name)}</b>\n"
            f"💰 <b>Bounty:</b> <code>{bounty}</code>\n\n{FOOTER}"
        )
    await send_rich_card(client, message.chat.id, card, cap)

# ── 4. VIP ROYAL PROFILE BANNER (/profile) ────────────────────
@bot.on_message(filters.command(["profile", "vipcard"], prefixes=["/", "!", "."]))
async def profile_cmd(client, message: Message):
    target = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else message.from_user
    msgs = MSG_COUNTS[message.chat.id][target.id] + 1
    partner = MARRIAGES.get(target.id, {}).get("partner_name", "Single")
    rank = "ROYAL KING" if msgs >= 300 else ("VVIP LEGEND" if msgs >= 150 else ("PRO LISTENER" if msgs >= 50 else "RISING STAR"))

    dp = await _get_user_dp(client, target.id)
    tpl = await _get_template_bg()
    card = _make_single_card(dp, f"VIP RANK : {rank}", target.first_name, f"Chat Score: {msgs} Msgs", f"Partner: {partner}", template_bg=tpl)
    cap = (
        f"<blockquote><b>💎 𝐌𝐆𝐁 𝐕𝐈𝐏 𝐏𝐑𝐎𝐅𝐈𝐋𝐄 𝐂𝐀𝐑𝐃</b></blockquote>\n\n"
        f"👤 <b>User:</b> <b>{html.escape(target.first_name)}</b>\n"
        f"🏆 <b>Rank:</b> <code>{rank}</code>\n"
        f"💬 <b>Messages:</b> <code>{msgs}</code>  |  💍 <b>Partner:</b> <code>{html.escape(partner)}</code>\n\n{FOOTER}"
    )
    await send_rich_card(client, message.chat.id, card, cap)

# ── 5. LIVE AUTO-REFRESH LEADERBOARD (/top, /vcstats) ─────────
def _build_lb_text(chat_id: int, is_vc: bool, live: bool = True) -> str:
    data = VC_POINTS[chat_id] if is_vc else MSG_COUNTS[chat_id]
    sorted_u = sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]
    unit = "Pts" if is_vc else "Msgs"
    title = "𝐓𝐎𝐏 𝐕𝐂 𝐀𝐃𝐃𝐈𝐂𝐓𝐒" if is_vc else "𝐆𝐑𝐎𝐔𝐏 𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃"
    now = datetime.now(IST).strftime("%I:%M:%S %p")
    status = f"🟢 <b>LIVE AUTO-REFRESH</b> • <code>{now}</code>" if live else f"⚪ <b>UPDATED</b> • <code>{now}</code>"
    lines = [f"<b>{i}.</b> {html.escape(USER_NAMES.get(uid, 'User'))} — <code>{sc} {unit}</code>" for i, (uid, sc) in enumerate(sorted_u, 1)]
    return f"<blockquote><b>🏆 𝐌𝐆𝐁 {title}</b></blockquote>\n{status}\n\n" + "\n".join(lines) + f"\n\n{FOOTER}"

@bot.on_message(filters.command(["top", "leaderboard", "vcstats"], prefixes=["/", "!", "."]))
async def leaderboard_cmd(client, message: Message):
    chat_id = message.chat.id
    is_vc = message.command[0].lower() == "vcstats"
    data = VC_POINTS[chat_id] if is_vc else MSG_COUNTS[chat_id]
    if not data:
        data[message.from_user.id] += 1
        USER_NAMES[message.from_user.id] = message.from_user.first_name

    top_uid, top_score = sorted(data.items(), key=lambda x: x[1], reverse=True)[0]
    top_name = USER_NAMES.get(top_uid, "VIP Member")
    dp = await _get_user_dp(client, top_uid)
    tpl = await _get_template_bg()
    badge = "TOP VC ADDICTS" if is_vc else "GROUP LEADERBOARD"
    unit = "Pts" if is_vc else "Msgs"
    card = _make_single_card(dp, badge, f"#1 {top_name}", f"Top Score: {top_score} {unit}", f"Active Users: {len(data)}", template_bg=tpl)
    await send_rich_card(client, chat_id, card, _build_lb_text(chat_id, is_vc, live=False))

    key = (chat_id, "vc" if is_vc else "top")
    if key in LIVE_LB_TASKS:
        LIVE_LB_TASKS[key].cancel()

    rows = [[
        _cbtn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", style="success", callback_data=f"mgb_lb_ref_{'vc' if is_vc else 'top'}"),
        _cbtn("⏹ 𝐒𝐓𝐎𝐏 𝐋𝐈𝐕𝐄", style="danger", callback_data=f"mgb_lb_stop_{'vc' if is_vc else 'top'}"),
    ]]
    msg_id = await send_colored_msg(client, chat_id, _build_lb_text(chat_id, is_vc, live=True), rows)

    async def _auto_lb():
        try:
            for _ in range(20):
                await asyncio.sleep(15)
                await edit_colored_msg(client, chat_id, msg_id, _build_lb_text(chat_id, is_vc, live=True), rows)
            await edit_colored_msg(client, chat_id, msg_id, _build_lb_text(chat_id, is_vc, live=False), [[_cbtn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", style="success", callback_data=f"mgb_lb_ref_{'vc' if is_vc else 'top'}")]])
        except asyncio.CancelledError:
            pass
        finally:
            LIVE_LB_TASKS.pop(key, None)

    LIVE_LB_TASKS[key] = asyncio.create_task(_auto_lb())

@bot.on_callback_query(filters.regex(r"^mgb_lb_(ref|stop)_(vc|top)$"))
async def lb_cb(client, query: CallbackQuery):
    act, kind = query.matches[0].group(1), query.matches[0].group(2)
    chat_id = query.message.chat.id
    is_vc = kind == "vc"
    key = (chat_id, kind)
    if act == "stop":
        if key in LIVE_LB_TASKS:
            LIVE_LB_TASKS.pop(key).cancel()
        await query.answer("⏹ Live Refresh Stopped", show_alert=False)
        await edit_colored_msg(client, chat_id, query.message.id, _build_lb_text(chat_id, is_vc, live=False), [[_cbtn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", style="success", callback_data=f"mgb_lb_ref_{kind}")]])
    else:
        await query.answer("🔄 Refreshed!", show_alert=False)
        rows = [[
            _cbtn("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇", style="success", callback_data=f"mgb_lb_ref_{kind}"),
            _cbtn("⏹ 𝐒𝐓𝐎𝐏 𝐋𝐈𝐕𝐄", style="danger", callback_data=f"mgb_lb_stop_{kind}"),
        ]]
        await edit_colored_msg(client, chat_id, query.message.id, _build_lb_text(chat_id, is_vc, live=True), rows)

# ── 6. TRUTH OR DARE (1-TIME PICK LOCK) ───────────────────────
@bot.on_message(filters.command(["truth", "dare", "td"], prefixes=["/", "!", "."]))
async def truth_dare_cmd(client, message: Message):
    cmd = message.command[0].lower()
    gid = f"{int(time.time()*1000)}{random.randint(10,99)}"
    TD_ACTIVE[gid] = {"done": False}

    if cmd == "td":
        rows = [[
            _cbtn("🔥 𝐓𝐑𝐔𝐓𝐇", style="primary", callback_data=f"mgb_td_pick_{gid}_truth"),
            _cbtn("⚡ 𝐃𝐀𝐑𝐄", style="danger", callback_data=f"mgb_td_pick_{gid}_dare"),
        ]]
        return await send_colored_msg(
            client, message.chat.id,
            f"<blockquote><b>🎭 𝐓𝐑𝐔𝐓𝐇 𝐎𝐑 𝐃𝐀𝐑𝐄</b></blockquote>\n\n"
            f"👤 <b>Player:</b> <b>{html.escape(message.from_user.first_name)}</b>\n"
            f"👇 <b>Sirf 1 baar chunein:</b>\n\n{FOOTER}",
            rows, reply_to=message.id,
        )

    is_t = cmd == "truth"
    q = random.choice(TRUTH_LIST if is_t else DARE_LIST)
    tag = "🔥 𝐓𝐑𝐔𝐓𝐇" if is_t else "⚡ 𝐃𝐀𝐑𝐄"
    TD_ACTIVE[gid]["task"] = q
    TD_ACTIVE[gid]["tag"] = tag
    rows = [[
        _cbtn("✅ 𝐃𝐎𝐍𝐄", style="success", callback_data=f"mgb_td_res_{gid}_done"),
        _cbtn("❌ 𝐒𝐊𝐈𝐏", style="danger", callback_data=f"mgb_td_res_{gid}_skip"),
    ]]
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>{tag} 𝐂𝐇𝐀𝐋𝐋𝐄𝐍𝐆𝐄</b></blockquote>\n\n"
        f"👤 <b>Player:</b> <b>{html.escape(message.from_user.first_name)}</b>\n"
        f"💬 <b>Task:</b> <code>{q}</code>\n\n{FOOTER}",
        rows, reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_td_(pick|res)_(\d+)_(truth|dare|done|skip)$"))
async def truth_dare_cb(client, query: CallbackQuery):
    kind, gid, val = query.matches[0].group(1), query.matches[0].group(2), query.matches[0].group(3)
    state = TD_ACTIVE.get(gid)
    if not state or state.get("done"):
        return await query.answer("🔒 Yeh round lock ho chuka hai!", show_alert=True)

    state["done"] = True
    TD_ACTIVE.pop(gid, None)

    if kind == "pick":
        is_t = val == "truth"
        q = random.choice(TRUTH_LIST if is_t else DARE_LIST)
        tag = "🔥 𝐓𝐑𝐔𝐓𝐇" if is_t else "⚡ 𝐃𝐀𝐑𝐄"
        await query.answer("🔒 Challenge Locked!", show_alert=False)
        return await edit_colored_msg(
            client, query.message.chat.id, query.message.id,
            f"<blockquote><b>{tag} 𝐂𝐇𝐀𝐋𝐋𝐄𝐍𝐆𝐄</b></blockquote>\n\n"
            f"👤 <b>Player:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
            f"💬 <b>Task:</b> <code>{q}</code>\n"
            f"🔒 <b>Status:</b> <code>Locked (1-Time Pick)</code>\n\n{FOOTER}",
            [],
        )

    status = "✅ Challenge Completed!" if val == "done" else "❌ Challenge Skipped!"
    await query.answer(status, show_alert=False)
    await edit_colored_msg(
        client, query.message.chat.id, query.message.id,
        f"<blockquote><b>{state.get('tag', '🎭')} 𝐑𝐄𝐒𝐔𝐋𝐓</b></blockquote>\n\n"
        f"👤 <b>Player:</b> <b>{html.escape(query.from_user.first_name)}</b>\n"
        f"💬 <b>Task:</b> <code>{state.get('task', '')}</code>\n"
        f"✨ <b>Result:</b> <b>{status}</b>\n\n{FOOTER}",
        [],
    )

# ── 7. COLORED BUTTON GAME: RPS (1-TIME PICK LOCK) ────────────
@bot.on_message(filters.command(["rps", "game"], prefixes=["/", "!", "."]))
async def rps_cmd(client, message: Message):
    gid = f"{int(time.time()*1000)}{random.randint(10,99)}"
    RPS_ACTIVE[gid] = {"done": False}
    rows = [[
        _cbtn("🪨 𝐑𝐎𝐂𝐊", style="primary", callback_data=f"mgb_rps_{gid}_rock"),
        _cbtn("📄 𝐏𝐀𝐏𝐄𝐑", style="success", callback_data=f"mgb_rps_{gid}_paper"),
        _cbtn("✂️ 𝐒𝐂𝐈𝐒𝐒𝐎𝐑", style="danger", callback_data=f"mgb_rps_{gid}_scissor"),
    ]]
    await send_colored_msg(
        client, message.chat.id,
        f"<blockquote><b>🎮 𝐌𝐆𝐁 𝐑𝐏𝐒 𝐆𝐀𝐌𝐄</b></blockquote>\n\n"
        f"👇 <b>Sirf 1 baar move chunein ({html.escape(message.from_user.first_name)}):</b>\n\n{FOOTER}",
        rows, reply_to=message.id,
    )

@bot.on_callback_query(filters.regex(r"^mgb_rps_(\d+)_(rock|paper|scissor)$"))
async def rps_cb(client, query: CallbackQuery):
    gid, u_move = query.matches[0].group(1), query.matches[0].group(2)
    state = RPS_ACTIVE.get(gid)
    if not state or state.get("done"):
        return await query.answer("🔒 Yeh game khatam ho chuka hai!", show_alert=True)

    state["done"] = True
    RPS_ACTIVE.pop(gid, None)

    b_move = random.choice(["rock", "paper", "scissor"])
    wins = {"rock": "scissor", "paper": "rock", "scissor": "paper"}
    if u_move == b_move:
        res = "🤝 Match Draw!"
    elif wins[u_move] == b_move:
        res = f"🏆 {html.escape(query.from_user.first_name)} Jeet Gaye!"
    else:
        res = "❌ Haar Gaye! MGB Bot Jeet Gaya!"

    await query.answer(res, show_alert=False)
    await edit_colored_msg(
        client, query.message.chat.id, query.message.id,
        f"<blockquote><b>🎮 𝐌𝐆𝐁 𝐆𝐀𝐌𝐄 𝐅𝐈𝐍𝐀𝐋 𝐑𝐄𝐒𝐔𝐋𝐓</b></blockquote>\n\n"
        f"👤 <b>You:</b> <code>{u_move.upper()}</code>  |  🤖 <b>Bot:</b> <code>{b_move.upper()}</code>\n"
        f"✨ <b>Result:</b> <b>{res}</b>\n\n{FOOTER}",
        [],
    )
    
