# ═══════════════════════════════════════════════════════════════
#                  🥀 MGB NOT FREE CODER 💗
#               © 2026 @MGB_NOT_FREE_1 🍓
#   PLUGIN 4: GROUP ADALAT (COURTROOM) & CHOR-POLICE / MAFIA
#   /case | /guilty | /innocent | /verdict
#   /mafia | /join | /startmafia | /suspect | /endmafia
# ═══════════════════════════════════════════════════════════════

import os
import io
import json
import time
import html
import random
import asyncio
import unicodedata
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pyrogram import filters, enums
from pyrogram.types import Message

try:
    from ShizuMusic import bot
except ImportError:
    from ArtistMusic import app as bot

from ArtistMusic.plugins.mgb_viral_cards import (
    OWNER_UNAME,
    CHANNEL_UNAME,
    FOOTER,
    _cbtn,
    _get_user_dp,
    send_rich_card,
    send_colored_msg,
)

# ── STORAGE & LIVE GAME STATE ─────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = "mgb_data"
GAME_DB_FILE = os.path.join(DATA_DIR, "party_games.json")
os.makedirs(DATA_DIR, exist_ok=True)

ACTIVE_CASES = {}   # cid -> {case_no, accused_id, accused_name, judge_id, judge_name, charge, guilty: set, innocent: set, end_ts, task}
ACTIVE_MAFIA = {}   # cid -> {game_no, host_id, host_name, phase, players: {uid: name}, order: [uid], roles: {uid: role}, chor_id, votes: {uid: target_uid}, end_ts, task}

FUNNY_CHARGES = [
    "VC mein aake mic mute karke chup baithna!",
    "Bina party diye group mein VIP ban kar ghumna!",
    "Raat 2 baje tak online rehkar bhi reply na dena!",
    "Group ka sabse bada sticker spammer banna!",
    "Sad gaane baja kar sabka mood emotional karna!",
    "Free mein coins maang kar wapas na lautana!",
]

FUNNY_PUNISHMENTS = [
    "Saza: VC mein 1 Romantic Gaana Sunaana Padega!",
    "Saza: Pure Group Ko Virtual Chai & Samosa Party Do!",
    "Saza: 10 Minute Tak Sabki Tareef Karni Padegi!",
    "Saza: Apna Sabse Funny Dialogue Group Mein Likho!",
    "Saza: Judge Sahab Ko 500 MGB Coins Fine Bharo!",
]

BAIL_REASONS = [
    "VIP Bail Granted! Koi Saboot Nahi Mila!",
    "Adalat Ne Ba-Izzat Bari Kiya! Full VIP Respect!",
    "Case Dismissed! Accused 100% Innocent Nikla!",
]

FANCY_MAP = str.maketrans({
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ꜰ": "F", "ғ": "F",
    "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", "ᴋ": "K", "ʟ": "L", "ᴍ": "M",
    "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "ꜱ": "S", "ᴛ": "T",
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z",
    "Λ": "A", "λ": "A", "ʌ": "A", "Δ": "A", "α": "A", "Σ": "E", "Ω": "O", "β": "B",
    "χ": "X", "Χ": "X", "×": "X", "✗": "X", "✘": "X", "✕": "X", "✖": "X", "⨯": "X", "᙭": "X",
})

def _load_game_db() -> dict:
    base = {"case_count": 0, "mafia_count": 0, "stats": {}}
    if os.path.isfile(GAME_DB_FILE):
        try:
            with open(GAME_DB_FILE, "r", encoding="utf-8") as f:
                base.update(json.load(f))
        except Exception:
            pass
    return base

GDB = _load_game_db()

def _save_game_db():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(GAME_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(GDB, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _bump_stat(uid: int, name: str, key: str):
    rec = GDB["stats"].setdefault(str(uid), {"name": name, "wins": 0, "jailed": 0, "bailed": 0})
    rec["name"] = name
    rec[key] = int(rec.get(key, 0)) + 1
    _save_game_db()

# ── 100% PERMANENT BOTTOM HTML PILL BUTTONS (NO CALLBACKS) ────
def _bottom_html_pills(extra_url: str = None, extra_label: str = None) -> list:
    bottom_row = [
        _cbtn("👑 𝐎𝐖𝐍𝐄𝐑", style="primary", url=f"https://t.me/{OWNER_UNAME}"),
        _cbtn("🚀 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", style="success", url=f"https://t.me/{CHANNEL_UNAME}"),
    ]
    if extra_url and extra_label:
        return [[_cbtn(extra_label, style="primary", url=extra_url)], bottom_row]
    return [bottom_row]

async def _send_pill_msg(client, chat_id: int, text: str, reply_to: int = None, extra_url: str = None, extra_label: str = None):
    await send_colored_msg(client, chat_id, text, _bottom_html_pills(extra_url, extra_label), reply_to=reply_to)

async def _send_game_card(client, chat_id: int, card_io: io.BytesIO, caption: str, rows: list = None):
    use_rows = rows or _bottom_html_pills()
    try:
        await send_rich_card(client, chat_id, card_io, caption, json_rows=use_rows)
    except TypeError:
        card_io.seek(0)
        await send_rich_card(client, chat_id, card_io, caption)

def _profile_url(user) -> str:
    uname = getattr(user, "username", None)
    return f"https://t.me/{uname}" if uname else f"https://t.me/{CHANNEL_UNAME}"

async def _bot_dm_url(client) -> str:
    try:
        uname = getattr(client.me, "username", None) or (await client.get_me()).username
        if uname:
            return f"https://t.me/{uname}?start=mafia"
    except Exception:
        pass
    return f"https://t.me/{CHANNEL_UNAME}"

async def _is_chat_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False

# ── CLEAN TEXT, FONT & STUDIO GRAPHICS HELPERS ────────────────
def _clean_name(val: str, limit: int = 20) -> str:
    s = unicodedata.normalize("NFKC", str(val or "MGB VIP")).translate(FANCY_MAP)
    s = "".join(ch for ch in s if 32 <= ord(ch) <= 126 and ch not in "[](){}")
    s = " ".join(s.split()).strip()
    parts = s.split()
    if len(parts) >= 4 and all(len(p) == 1 for p in parts):
        s = "".join(parts)
    return s[:limit] or "MGB VIP"

def _clean_body(val: str, limit: int = 160) -> str:
    s = unicodedata.normalize("NFKC", str(val or "")).translate(FANCY_MAP)
    s = "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in s)
    return " ".join(s.split()).strip()[:limit] or "Royal Group Trial"

def _font(size: int, bold: bool = True):
    paths = (
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
        if bold else
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    )
    for fp in paths:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _draw_center(draw: ImageDraw.Draw, cx: int, cy: int, text: str, font, fill: tuple):
    try:
        draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")
    except TypeError:
        b = draw.textbbox((0, 0), text, font=font)
        draw.text((int(cx - (b[2] - b[0]) / 2), int(cy - (b[3] - b[1]) / 2 - b[1])), text, font=font, fill=fill)

def _draw_fit_center(draw: ImageDraw.Draw, cx: int, cy: int, text: str, max_w: int, base_size: int, fill: tuple):
    sz = base_size
    f = _font(sz, True)
    while sz > 15:
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            break
        sz -= 2
        f = _font(sz, True)
    _draw_center(draw, cx, cy, text, f, fill)

def _wrap_lines(draw: ImageDraw.Draw, text: str, font, max_w: int, max_lines: int = 3) -> list:
    words = text.split()
    if not words:
        return ["..."]
    out, cur = [], words[0]
    for w in words[1:]:
        test = f"{cur} {w}"
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            out.append(cur)
            cur = w
            if len(out) >= max_lines:
                break
    if len(out) < max_lines:
        out.append(cur)
    if len(out) == max_lines and len(text) > sum(len(x) for x in out) + 5:
        out[-1] = out[-1][:-3].rstrip() + "..."
    return out

def _make_gradient(w: int, h: int, c1: tuple, c2: tuple, horiz: bool = False) -> Image.Image:
    strip = Image.new("RGB", (256, 1) if horiz else (1, 256))
    px = strip.load()
    for i in range(256):
        t = i / 255.0
        col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        if horiz:
            px[i, 0] = col
        else:
            px[0, i] = col
    return strip.resize((w, h), Image.BICUBIC)

def _draw_glow(canvas: Image.Image, cx: int, cy: int, r: int, color: tuple):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(int(r * 0.55))))

def _paste_circle_dp(canvas: Image.Image, dp: Image.Image, cx: int, cy: int, r: int, ring_col=None, ring_w: int = 6, glow_col=None):
    if glow_col:
        _draw_glow(canvas, cx, cy, r + 16, glow_col)
    size = r * 2
    av = ImageOps.fit(dp.convert("RGBA"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    canvas.paste(av, (cx - r, cy - r), mask)
    if ring_col and ring_w > 0:
        ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring_col, width=ring_w)

def _save_jpg(img: Image.Image, name: str) -> io.BytesIO:
    out = io.BytesIO()
    out.name = name
    img.convert("RGB").save(out, format="JPEG", quality=95, subsampling=0)
    out.seek(0)
    return out
# ── CARD 1: GROUP ADALAT / FUNNY COURTROOM CARD (/case) ───────
def _render_courtroom_card(
    dp: Image.Image,
    case_no: int,
    accused_name: str,
    judge_name: str,
    charge: str,
    guilty_cnt: int,
    innocent_cnt: int,
    verdict: str = None,
    outcome_line: str = "",
) -> io.BytesIO:
    W, H = 1280, 720
    if verdict == "GUILTY":
        c1, c2, accent = (42, 10, 18), (14, 10, 24), (244, 63, 94)
    elif verdict == "INNOCENT":
        c1, c2, accent = (8, 34, 28), (12, 16, 34), (16, 225, 152)
    else:
        c1, c2, accent = (32, 18, 12), (12, 14, 30), (245, 198, 92)

    bg = _make_gradient(W, H, c1, c2).convert("RGBA")
    _draw_glow(bg, 268, 352, 250, (accent[0], accent[1], accent[2], 95))
    _draw_glow(bg, 1040, 150, 220, (245, 198, 92, 75))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(14, 12, 24, 236), outline=(accent[0], accent[1], accent[2], 242), width=4)
    d.rounded_rectangle((56, 54, W - 56, H - 54), radius=26, outline=(accent[0], accent[1], accent[2], 95), width=2)

    # Top Courtroom Header Bar
    d.rounded_rectangle((74, 70, W - 74, 146), radius=22, fill=(28, 20, 36, 248), outline=(245, 198, 92, 210), width=2)
    d.text((104, 90), f"MGB SUPREME ADALAT  •  CASE #{case_no}", font=_font(30, True), fill=(255, 224, 134))

    badge_txt = (
        "VERDICT: GUILTY!" if verdict == "GUILTY"
        else ("VIP BAIL GRANTED" if verdict == "INNOCENT" else "LIVE COURT TRIAL")
    )
    d.rounded_rectangle((918, 84, 1184, 132), radius=22, fill=(accent[0], accent[1], accent[2], 255))
    _draw_fit_center(d, 1051, 108, badge_txt, 246, 21, (14, 12, 22) if verdict != "GUILTY" else (255, 255, 255))

    # Left: Accused DP + Name Pill + Status Ribbon
    _paste_circle_dp(bg, dp, 268, 336, 132, ring_col=(accent[0], accent[1], accent[2], 255), ring_w=7, glow_col=(accent[0], accent[1], accent[2], 125))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((112, 496, 424, 552), radius=26, fill=(30, 22, 42, 248), outline=(accent[0], accent[1], accent[2], 230), width=3)
    _draw_fit_center(d, 268, 524, _clean_name(accused_name, 18).upper(), 284, 24, (255, 255, 255))

    role_pill = "JAILED!" if verdict == "GUILTY" else ("BA-IZZAT BARI" if verdict == "INNOCENT" else "ACCUSED ON TRIAL")
    d.rounded_rectangle((146, 568, 390, 610), radius=20, fill=(accent[0], accent[1], accent[2], 245))
    _draw_center(d, 268, 589, role_pill, _font(19, True), (14, 12, 22) if verdict != "GUILTY" else (255, 255, 255))

    # Right: Judge + Charge Box + Jury Meter + Verdict/Commands
    rx1, rx2, rcx = 472, 1184, 828
    d.text((rx1 + 8, 174), f"JUDGE SAHAB: {_clean_name(judge_name, 22).upper()}", font=_font(22, True), fill=(245, 198, 92))

    # Charge Box
    d.rounded_rectangle((rx1, 212, rx2, 368), radius=24, fill=(22, 18, 36, 245), outline=(148, 124, 92, 190), width=2)
    d.text((rx1 + 24, 228), "OFFICIAL ILZAAM / CHARGE:", font=_font(18, True), fill=(245, 198, 92))
    f_chg = _font(27, True)
    cy = 264
    for ln in _wrap_lines(d, _clean_body(charge, 140), f_chg, (rx2 - rx1) - 48, max_lines=3):
        d.text((rx1 + 24, cy), ln, font=f_chg, fill=(252, 248, 255))
        cy += 34

    # Live Jury Voting Meter (Guilty Red vs Innocent Green)
    total = guilty_cnt + innocent_cnt
    g_pct = int(round((guilty_cnt / total) * 100)) if total > 0 else 50
    i_pct = 100 - g_pct if total > 0 else 50

    d.rounded_rectangle((rx1, 390, rx2, 518), radius=24, fill=(18, 16, 32, 245), outline=(92, 102, 144, 190), width=2)
    d.text((rx1 + 24, 408), f"GUILTY: {guilty_cnt} ({g_pct}%)", font=_font(23, True), fill=(255, 96, 122))
    inn_lbl = f"INNOCENT: {innocent_cnt} ({i_pct}%)"
    iw = d.textbbox((0, 0), inn_lbl, font=_font(23, True))[2]
    d.text((rx2 - 24 - iw, 408), inn_lbl, font=_font(23, True), fill=(52, 232, 168))

    bx1, by1, bx2, by2 = rx1 + 24, 456, rx2 - 24, 492
    bar_w = bx2 - bx1
    split_x = bx1 + max(24, min(bar_w - 24, int(bar_w * (g_pct / 100.0))))
    d.rounded_rectangle((bx1, by1, bx2, by2), radius=16, fill=(16, 185, 129, 255))
    d.rounded_rectangle((bx1, by1, split_x, by2), radius=16, fill=(225, 29, 72, 255))
    d.line((split_x, by1 - 4, split_x, by2 + 4), fill=(255, 255, 255, 240), width=3)

    # Bottom Outcome / Instruction Box
    foot_line = _clean_body(outcome_line, 58).upper() if outcome_line else "JURY VOTE: /guilty OR /innocent  •  /verdict TO END"
    d.rounded_rectangle((rx1, 540, rx2, 612), radius=22, fill=(26, 20, 40, 245), outline=(accent[0], accent[1], accent[2], 210), width=2)
    _draw_fit_center(d, rcx, 576, foot_line, (rx2 - rx1) - 36, 21, (255, 232, 164) if verdict else (228, 236, 252))

    _draw_center(d, W // 2, 654, "ORDER! ORDER!  •  MGB NOT CODER COURTROOM", _font(20, True), (210, 198, 228))
    return _save_jpg(bg, "mgb_court.jpg")

# ── CARD 2: CHOR-POLICE / MAFIA LOBBY & SUSPECT ROSTER CARD ───
def _render_mafia_lobby_card(
    dp: Image.Image,
    game_no: int,
    host_name: str,
    players: list,
    phase: str,
    status_line: str,
) -> io.BytesIO:
    W, H = 1280, 780
    is_vote = phase == "VOTING"
    accent = (244, 63, 94) if is_vote else (245, 198, 92)
    bg = _make_gradient(W, H, (28, 8, 18), (10, 10, 26)).convert("RGBA")
    _draw_glow(bg, 220, 140, 250, (225, 29, 72, 95))
    _draw_glow(bg, 1060, 640, 250, (245, 198, 92, 80))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((36, 34, W - 36, H - 34), radius=34, fill=(14, 10, 22, 238), outline=(accent[0], accent[1], accent[2], 240), width=4)

    # Top Noir Header Bar
    d.rounded_rectangle((68, 60, W - 68, 152), radius=24, fill=(28, 16, 32, 248), outline=(accent[0], accent[1], accent[2], 210), width=2)
    _paste_circle_dp(bg, dp, 124, 106, 34, ring_col=(accent[0], accent[1], accent[2], 255), ring_w=3)
    d = ImageDraw.Draw(bg)

    hdr = f"CHOR-POLICE / MAFIA  •  GAME #{game_no}"
    d.text((178, 76), hdr, font=_font(30, True), fill=(255, 224, 134))
    d.text((178, 116), f"HOST: {_clean_name(host_name, 18).upper()}   •   PLAYERS: {len(players)}/10", font=_font(20, False), fill=(208, 214, 234))

    pill_txt = "CHOR HUNT LIVE" if is_vote else "LOBBY OPEN"
    d.rounded_rectangle((952, 80, 1184, 132), radius=24, fill=(accent[0], accent[1], accent[2], 255))
    _draw_center(d, 1068, 106, pill_txt, _font(21, True), (255, 255, 255) if is_vote else (14, 12, 22))

    # 2-Column Numbered Player Roster (Up to 10 Players)
    col_w, row_h = 548, 76
    start_x, start_y = 68, 182
    gap_x, gap_y = 48, 18

    for idx in range(10):
        col = idx % 2
        row = idx // 2
        x1 = start_x + col * (col_w + gap_x)
        y1 = start_y + row * (row_h + gap_y)
        x2, y2 = x1 + col_w, y1 + row_h

        if idx < len(players):
            p_num, p_name, votes_on = players[idx]
            d.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=(26, 18, 38, 245), outline=(accent[0], accent[1], accent[2], 210), width=2)
            d.ellipse((x1 + 16, y1 + 14, x1 + 64, y1 + 62), fill=(accent[0], accent[1], accent[2], 255))
            _draw_center(d, x1 + 40, y1 + 38, f"#{p_num}", _font(22, True), (255, 255, 255) if is_vote else (14, 12, 22))
            d.text((x1 + 82, y1 + 22), _clean_name(p_name, 18).upper(), font=_font(25, True), fill=(255, 255, 255))

            if is_vote:
                d.rounded_rectangle((x2 - 156, y1 + 16, x2 - 16, y2 - 16), radius=16, fill=(44, 16, 28, 250), outline=(244, 63, 94, 210), width=2)
                _draw_center(d, x2 - 86, y1 + 38, f"{votes_on} SUS", _font(19, True), (255, 174, 188))
            else:
                d.rounded_rectangle((x2 - 134, y1 + 16, x2 - 16, y2 - 16), radius=16, fill=(16, 42, 34, 245), outline=(16, 225, 152, 200), width=2)
                _draw_center(d, x2 - 75, y1 + 38, "READY", _font(18, True), (120, 248, 198))
        else:
            d.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=(18, 14, 28, 170), outline=(66, 56, 86, 150), width=2)
            _draw_center(d, (x1 + x2) // 2, (y1 + y2) // 2, f"SLOT #{idx + 1}  —  WAITING (/join)", _font(19, False), (128, 124, 152))

    # Bottom Command Strip
    d.rounded_rectangle((68, 660, W - 68, 720), radius=22, fill=(24, 14, 34, 248), outline=(accent[0], accent[1], accent[2], 210), width=2)
    _draw_fit_center(d, W // 2, 690, _clean_body(status_line, 66).upper(), W - 180, 22, (255, 228, 154))
    return _save_jpg(bg, "mgb_mafia_lobby.jpg")

# ── CARD 3: DM SECRET ROLE CARD (CHOR / POLICE / DOCTOR / CITIZEN)
def _render_mafia_role_card(dp: Image.Image, player_name: str, role_name: str, game_no: int, group_name: str) -> io.BytesIO:
    W, H = 1200, 640
    role_styles = {
        "CHOR": ((46, 8, 18), (14, 8, 22), (244, 63, 94), "CHORI CHHUPAO! KISI KO SHAK NA HONE DO!"),
        "POLICE": ((10, 22, 54), (10, 12, 28), (56, 189, 248), "ASLI CHOR KO PAKDO! /suspect <num> USE KARO!"),
        "DOCTOR": ((8, 38, 28), (10, 14, 26), (16, 225, 152), "INNOCENTS KO BACHAO AUR CHOR KO VOTE KARO!"),
        "CITIZEN": ((30, 16, 48), (12, 12, 28), (245, 198, 92), "GROUP KE SAATH MILKAR ASLI CHOR DHOONDHO!"),
    }
    c1, c2, accent, mission = role_styles.get(role_name, role_styles["CITIZEN"])
    bg = _make_gradient(W, H, c1, c2).convert("RGBA")
    _draw_glow(bg, 250, 320, 230, (accent[0], accent[1], accent[2], 100))
    _draw_glow(bg, 980, 140, 200, (accent[0], accent[1], accent[2], 70))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((36, 34, W - 36, H - 34), radius=34, fill=(12, 12, 24, 238), outline=(accent[0], accent[1], accent[2], 245), width=4)

    _paste_circle_dp(bg, dp, 248, 294, 122, ring_col=(accent[0], accent[1], accent[2], 255), ring_w=7, glow_col=(accent[0], accent[1], accent[2], 125))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((106, 444, 390, 498), radius=24, fill=(24, 22, 42, 248), outline=(accent[0], accent[1], accent[2], 225), width=3)
    _draw_fit_center(d, 248, 471, _clean_name(player_name, 18).upper(), 258, 23, (255, 255, 255))
    _draw_center(d, 248, 534, f"GAME #{game_no}", _font(20, True), accent)

    rx1, rx2, rcx = 442, 1118, 780
    d.rounded_rectangle((rx1, 84, rx2, 142), radius=24, fill=(accent[0], accent[1], accent[2], 250))
    _draw_center(d, rcx, 113, "TOP SECRET MAFIA ROLE FILE", _font(24, True), (12, 14, 24) if role_name != "CHOR" else (255, 255, 255))

    _draw_center(d, rcx, 236, role_name, _font(86, True), (255, 255, 255))

    d.rounded_rectangle((rx1, 314, rx2, 466), radius=24, fill=(20, 18, 36, 245), outline=(accent[0], accent[1], accent[2], 190), width=2)
    d.text((rx1 + 26, 332), "YOUR SECRET MISSION:", font=_font(19, True), fill=accent)
    cy = 370
    for ln in _wrap_lines(d, mission, _font(26, True), (rx2 - rx1) - 52, max_lines=2):
        d.text((rx1 + 26, cy), ln, font=_font(26, True), fill=(248, 248, 255))
        cy += 38

    _draw_fit_center(d, rcx, 524, f"GROUP: {_clean_name(group_name, 26).upper()}  •  DO NOT SHARE!", 640, 21, (255, 220, 146))
    _draw_center(d, rcx, 566, "MGB NOT CODER  •  CONFIDENTIAL", _font(19, True), (180, 194, 220))
    return _save_jpg(bg, "mgb_mafia_role.jpg")

# ── CARD 4: CHOR CAUGHT / ESCAPED FINAL VERDICT CARD ──────────
def _render_mafia_verdict_card(
    chor_dp: Image.Image,
    chor_name: str,
    game_no: int,
    caught: bool,
    suspected_name: str,
    total_votes: int,
    police_names: str,
) -> io.BytesIO:
    W, H = 1280, 720
    if caught:
        c1, c2, accent = (8, 34, 46), (12, 16, 34), (16, 225, 152)
        banner_txt = "POLICE & CITIZENS WIN!"
        sub_tag = "CHOR ARRESTED!"
    else:
        c1, c2, accent = (48, 8, 18), (16, 10, 24), (244, 63, 94)
        banner_txt = "CHOR ESCAPED — MAFIA WINS!"
        sub_tag = "MASTERMIND CHOR"

    bg = _make_gradient(W, H, c1, c2).convert("RGBA")
    _draw_glow(bg, 268, 348, 250, (accent[0], accent[1], accent[2], 105))
    _draw_glow(bg, 1040, 160, 230, (245, 198, 92, 85))

    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((38, 36, W - 38, H - 36), radius=34, fill=(12, 12, 24, 238), outline=(accent[0], accent[1], accent[2], 245), width=4)

    # Top Result Banner
    d.rounded_rectangle((176, 66, W - 176, 134), radius=32, fill=(accent[0], accent[1], accent[2], 255))
    _draw_fit_center(d, W // 2, 100, f"{banner_txt}  •  GAME #{game_no}", 860, 30, (12, 14, 24) if caught else (255, 255, 255))

    # Left: Real Chor DP Revealed
    _paste_circle_dp(bg, chor_dp, 268, 352, 136, ring_col=(accent[0], accent[1], accent[2], 255), ring_w=7, glow_col=(accent[0], accent[1], accent[2], 130))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((112, 514, 424, 570), radius=26, fill=(28, 18, 36, 248), outline=(accent[0], accent[1], accent[2], 235), width=3)
    _draw_fit_center(d, 268, 542, _clean_name(chor_name, 18).upper(), 284, 24, (255, 255, 255))
    d.rounded_rectangle((138, 586, 398, 628), radius=20, fill=(245, 198, 92, 250))
    _draw_center(d, 268, 607, sub_tag, _font(19, True), (14, 12, 22))

    # Right: Case Summary Box
    rx1, rx2, rcx = 472, 1184, 828
    d.rounded_rectangle((rx1, 180, rx2, 536), radius=28, fill=(20, 18, 36, 245), outline=(245, 198, 92, 200), width=2)
    rows = [
        ("REAL CHOR REVEALED", _clean_name(chor_name, 22).upper(), (255, 128, 148)),
        ("MOST VOTED SUSPECT", _clean_name(suspected_name, 22).upper(), (255, 226, 138)),
        ("POLICE TEAM", _clean_name(police_names, 28).upper(), (112, 214, 255)),
        ("TOTAL JURY VOTES", f"{total_votes} VOTES CAST", (236, 244, 255)),
    ]
    ry = 204
    for lbl, val, col in rows:
        d.text((rx1 + 30, ry), lbl, font=_font(18, True), fill=(184, 196, 224))
        d.text((rx1 + 30, ry + 24), val, font=_font(28, True), fill=col)
        ry += 80

    d.rounded_rectangle((rx1, 560, rx2, 626), radius=22, fill=(26, 20, 42, 248), outline=(accent[0], accent[1], accent[2], 210), width=2)
    _draw_center(d, rcx, 593, "PLAY AGAIN: /mafia   •   MGB NOT CODER", _font(21, True), (255, 228, 154))
    return _save_jpg(bg, "mgb_mafia_verdict.jpg")
  # ── 1. GROUP ADALAT / FUNNY COURTROOM (/case, /guilty, /innocent, /verdict)
async def _conclude_court_case(client, cid: int):
    case = ACTIVE_CASES.pop(cid, None)
    if not case:
        return

    g_cnt = len(case["guilty"])
    i_cnt = len(case["innocent"])
    if g_cnt > i_cnt:
        verdict = "GUILTY"
        outcome = random.choice(FUNNY_PUNISHMENTS)
        _bump_stat(case["accused_id"], case["accused_name"], "jailed")
        emoji_hdr = "⚖️ 𝐀𝐃𝐀𝐋𝐀𝐓 𝐅𝐀𝐈𝐒𝐋𝐀 — 𝐆𝐔𝐈𝐋𝐓𝐘!"
    else:
        verdict = "INNOCENT"
        outcome = random.choice(BAIL_REASONS)
        _bump_stat(case["accused_id"], case["accused_name"], "bailed")
        emoji_hdr = "🎉 𝐀𝐃𝐀𝐋𝐀𝐓 𝐅𝐀𝐈𝐒𝐋𝐀 — 𝐕𝐈𝐏 𝐁𝐀𝐈𝐋 𝐆𝐑𝐀𝐍𝐓𝐄𝐃!"

    dp = await _get_user_dp(client, case["accused_id"])
    card = await asyncio.to_thread(
        _render_courtroom_card,
        dp,
        case["case_no"],
        case["accused_name"],
        case["judge_name"],
        case["charge"],
        g_cnt,
        i_cnt,
        verdict,
        outcome,
    )
    cap = (
        f"<blockquote><b>{emoji_hdr}</b></blockquote>\n\n"
        f"👤 <b>Accused:</b> <b>{html.escape(case['accused_name'])}</b>\n"
        f"📊 <b>Final Votes:</b> <code>Guilty: {g_cnt}</code> | <code>Innocent: {i_cnt}</code>\n"
        f"📜 <b>Order:</b> <code>{html.escape(outcome)}</code>\n\n{FOOTER}"
    )
    await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills())

async def _court_case_timer(client, cid: int, delay_sec: int):
    try:
        await asyncio.sleep(delay_sec)
        cur = ACTIVE_CASES.get(cid)
        if not cur or cur.get("task") is not asyncio.current_task():
            return
        await _conclude_court_case(client, cid)
    except asyncio.CancelledError:
        return
    except Exception:
        ACTIVE_CASES.pop(cid, None)

@bot.on_message(filters.group & filters.command(["case", "adalat", "court"], prefixes=["/", "!", "."]))
async def open_court_case_cmd(client, message: Message):
    cid = message.chat.id
    judge = message.from_user
    if not judge:
        return

    # If a trial is already active, display its live courtroom card
    if cid in ACTIVE_CASES:
        c = ACTIVE_CASES[cid]
        rem = max(1, int(c["end_ts"] - time.time()))
        dp = await _get_user_dp(client, c["accused_id"])
        card = await asyncio.to_thread(
            _render_courtroom_card,
            dp, c["case_no"], c["accused_name"], c["judge_name"], c["charge"],
            len(c["guilty"]), len(c["innocent"]), None, f"VOTING ENDS IN {rem}s • /guilty OR /innocent",
        )
        cap = (
            f"<blockquote><b>⚖️ 𝐂𝐀𝐒𝐄 #{c['case_no']} 𝐋𝐈𝐕𝐄 𝐈𝐍 𝐂𝐎𝐔𝐑𝐓!</b></blockquote>\n\n"
            f"👤 <b>Accused:</b> <b>{html.escape(c['accused_name'])}</b>\n"
            f"⏳ <b>Time Left:</b> <code>{rem}s</code>\n"
            f"🗳 <b>Vote:</b> <code>/guilty</code> | <code>/innocent</code> | <b>End:</b> <code>/verdict</code>\n\n{FOOTER}"
        )
        return await _send_game_card(client, cid, card, cap)

    reply = message.reply_to_message
    if not reply or not reply.from_user or reply.from_user.is_bot:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>⚖️ 𝐌𝐆𝐁 𝐒𝐔𝐏𝐑𝐄𝐌𝐄 𝐀𝐃𝐀𝐋𝐀𝐓</b></blockquote>\n\n"
            f"⚡ <b>Use:</b> Kisi dost ke message par reply karke likhein:\n"
            f"• <code>/case VC mein aake chup rehna</code>\n"
            f"• <code>/case</code> <i>(Auto Funny Ilzaam)</i>\n\n{FOOTER}",
            reply_to=message.id,
        )

    accused = reply.from_user
    raw_charge = message.text.split(None, 1)[1].strip() if (message.text and len(message.text.split(None, 1)) > 1) else ""
    charge = raw_charge[:140] if raw_charge else random.choice(FUNNY_CHARGES)

    GDB["case_count"] = int(GDB.get("case_count", 0)) + 1
    case_no = GDB["case_count"]
    _save_game_db()

    duration_sec = 60
    task = asyncio.create_task(_court_case_timer(client, cid, duration_sec))
    ACTIVE_CASES[cid] = {
        "case_no": case_no,
        "accused_id": accused.id,
        "accused_name": accused.first_name,
        "judge_id": judge.id,
        "judge_name": judge.first_name,
        "charge": charge,
        "guilty": set(),
        "innocent": set(),
        "end_ts": time.time() + duration_sec,
        "task": task,
    }

    dp = await _get_user_dp(client, accused.id)
    card = await asyncio.to_thread(
        _render_courtroom_card,
        dp, case_no, accused.first_name, judge.first_name, charge, 0, 0, None, "",
    )
    cap = (
        f"<blockquote><b>⚖️ 𝐎𝐑𝐃𝐄𝐑! 𝐎𝐑𝐃𝐄𝐑! — 𝐂𝐀𝐒𝐄 #{case_no} 𝐎𝐏𝐄𝐍!</b></blockquote>\n\n"
        f"👨‍⚖️ <b>Judge:</b> <b>{html.escape(judge.first_name)}</b>\n"
        f"🎯 <b>Accused:</b> <b>{html.escape(accused.first_name)}</b>\n"
        f"📜 <b>Ilzaam:</b> <code>{html.escape(charge)}</code>\n\n"
        f"🗳 <b>Jury Vote (60s):</b> <code>/guilty</code> (Saza) | <code>/innocent</code> (Bail)\n"
        f"🔨 <b>Instant Faisla:</b> <code>/verdict</code>\n\n{FOOTER}"
    )
    await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills(_profile_url(accused), "⚖️ 𝐀𝐂𝐂𝐔𝐒𝐄𝐃"))

@bot.on_message(filters.group & filters.command(["guilty", "saza", "innocent", "bail"], prefixes=["/", "!", "."]))
async def court_jury_vote_cmd(client, message: Message):
    cid = message.chat.id
    voter = message.from_user
    if not voter:
        return

    case = ACTIVE_CASES.get(cid)
    if not case:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>⚖️ 𝐍𝐎 𝐀𝐂𝐓𝐈𝐕𝐄 𝐂𝐎𝐔𝐑𝐓 𝐂𝐀𝐒𝐄</b></blockquote>\n\n"
            f"⚡ <b>Naya case kholne ke liye kisi par reply karke <code>/case</code> likhein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    cmd = message.command[0].lower()
    if cmd in ("guilty", "saza"):
        case["innocent"].discard(voter.id)
        case["guilty"].add(voter.id)
        choice_lbl = "GUILTY (SAZA) 🔨"
    else:
        case["guilty"].discard(voter.id)
        case["innocent"].add(voter.id)
        choice_lbl = "INNOCENT (VIP BAIL) 🕊"

    rem = max(1, int(case["end_ts"] - time.time()))
    await _send_pill_msg(
        client, cid,
        f"<blockquote><b>🗳 𝐉𝐔𝐑𝐘 𝐕𝐎𝐓𝐄 𝐑𝐄𝐂𝐎𝐑𝐃𝐄𝐃 — 𝐂𝐀𝐒𝐄 #{case['case_no']}</b></blockquote>\n\n"
        f"👤 <b>Juror:</b> <b>{html.escape(voter.first_name)}</b> ➔ <code>{choice_lbl}</code>\n"
        f"📊 <b>Live Score:</b> <code>Guilty: {len(case['guilty'])}</code> | <code>Innocent: {len(case['innocent'])}</code>\n"
        f"⏳ <b>Faisla In:</b> <code>{rem}s</code> | <b>Live Card:</b> <code>/case</code>\n\n{FOOTER}",
        reply_to=message.id,
    )

@bot.on_message(filters.group & filters.command(["verdict", "endcase", "faisla"], prefixes=["/", "!", "."]))
async def end_court_case_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    case = ACTIVE_CASES.get(cid)
    if not case:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>⚖️ 𝐍𝐎 𝐀𝐂𝐓𝐈𝐕𝐄 𝐂𝐀𝐒𝐄</b></blockquote>\n\n"
            f"⚠️ <b>Abhi Adalat mein koi mukadma nahi chal raha!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if user.id != case["judge_id"] and not await _is_chat_admin(client, cid, user.id):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐉𝐔𝐃𝐆𝐄 / 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Judge Sahab ya Admin hi faisla jaldi suna sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if case.get("task") and not case["task"].done():
        case["task"].cancel()
    await _conclude_court_case(client, cid)

# ── 2. CHOR-POLICE / MAFIA PARTY GAME (/mafia, /join, /startmafia, /suspect, /endmafia)
def _build_mafia_roster(game: dict) -> list:
    tally = {}
    for target_uid in game["votes"].values():
        tally[target_uid] = tally.get(target_uid, 0) + 1
    out = []
    for idx, uid in enumerate(game["order"], start=1):
        out.append((idx, game["players"].get(uid, "Player"), tally.get(uid, 0)))
    return out

async def _conclude_mafia_game(client, cid: int):
    game = ACTIVE_MAFIA.pop(cid, None)
    if not game:
        return

    chor_id = game.get("chor_id")
    chor_name = game["players"].get(chor_id, "Unknown")
    tally = {}
    for target_uid in game["votes"].values():
        tally[target_uid] = tally.get(target_uid, 0) + 1

    total_votes = len(game["votes"])
    if tally:
        max_v = max(tally.values())
        top_suspects = [uid for uid, cnt in tally.items() if cnt == max_v]
        if len(top_suspects) == 1:
            sus_uid = top_suspects[0]
            sus_name = game["players"].get(sus_uid, "Unknown")
            caught = sus_uid == chor_id
        else:
            sus_name = "TIE VOTE (CONFUSION!)"
            caught = False
    else:
        sus_name = "NO VOTES CAST"
        caught = False

    police_list = [game["players"][u] for u, r in game["roles"].items() if r == "POLICE"]
    police_names = ", ".join(police_list) if police_list else "CITY PATROL"

    if caught:
        for uid, role in game["roles"].items():
            if role != "CHOR":
                _bump_stat(uid, game["players"].get(uid, "Player"), "wins")
    elif chor_id:
        _bump_stat(chor_id, chor_name, "wins")

    chor_dp = await _get_user_dp(client, chor_id or game["host_id"])
    card = await asyncio.to_thread(
        _render_mafia_verdict_card,
        chor_dp, chor_name, game["game_no"], caught, sus_name, total_votes, police_names,
    )

    role_reveal = "\n".join(
        f"• <b>{html.escape(game['players'][u])}</b> — <code>{game['roles'].get(u, 'CITIZEN')}</code>"
        for u in game["order"]
    )
    res_hdr = "🚔 𝐂𝐇𝐎𝐑 𝐏𝐀𝐊𝐃𝐀 𝐆𝐀𝐘𝐀 — 𝐏𝐎𝐋𝐈𝐂𝐄 𝐖𝐈𝐍𝐒!" if caught else "🕵️ 𝐂𝐇𝐎𝐑 𝐁𝐇𝐀𝐀𝐆 𝐆𝐀𝐘𝐀 — 𝐌𝐀𝐅𝐈𝐀 𝐖𝐈𝐍𝐒!"
    cap = (
        f"<blockquote><b>{res_hdr}</b></blockquote>\n\n"
        f"🎭 <b>Real Chor:</b> <b>{html.escape(chor_name)}</b>\n"
        f"🎯 <b>Most Suspected:</b> <code>{html.escape(sus_name)}</code> (<code>{total_votes} Votes</code>)\n\n"
        f"<blockquote><b>📜 𝐀𝐋𝐋 𝐑𝐎𝐋𝐄𝐒 𝐑𝐄𝐕𝐄𝐀𝐋𝐄𝐃</b>\n{role_reveal}</blockquote>\n\n{FOOTER}"
    )
    await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills())

async def _mafia_vote_timer(client, cid: int, delay_sec: int):
    try:
        await asyncio.sleep(delay_sec)
        cur = ACTIVE_MAFIA.get(cid)
        if not cur or cur.get("task") is not asyncio.current_task():
            return
        await _conclude_mafia_game(client, cid)
    except asyncio.CancelledError:
        return
    except Exception:
        ACTIVE_MAFIA.pop(cid, None)

@bot.on_message(filters.group & filters.command(["mafia", "chorpolice", "cp"], prefixes=["/", "!", "."]))
async def mafia_lobby_cmd(client, message: Message):
    cid = message.chat.id
    host = message.from_user
    if not host:
        return

    dm_url = await _bot_dm_url(client)

    # Show current lobby or voting board if game already running
    if cid in ACTIVE_MAFIA:
        g = ACTIVE_MAFIA[cid]
        dp = await _get_user_dp(client, g["host_id"])
        roster = _build_mafia_roster(g)
        if g["phase"] == "VOTING":
            rem = max(1, int(g["end_ts"] - time.time()))
            st_line = f"{rem}s LEFT • VOTE CHOR WITH /suspect <num> • /endmafia"
        else:
            st_line = "TYPE /join TO ENTER • HOST: /startmafia (MIN 3 PLAYERS)"
        card = await asyncio.to_thread(_render_mafia_lobby_card, dp, g["game_no"], g["host_name"], roster, g["phase"], st_line)
        cap = (
            f"<blockquote><b>🕵️ 𝐂𝐇𝐎𝐑-𝐏𝐎𝐋𝐈𝐂𝐄 / 𝐌𝐀𝐅𝐈𝐀 #{g['game_no']} ({g['phase']})</b></blockquote>\n\n"
            f"👥 <b>Players:</b> <code>{len(g['order'])}/10</code>\n"
            f"⚡ <b>Commands:</b> <code>/join</code> | <code>/startmafia</code> | <code>/suspect 1</code>\n\n{FOOTER}"
        )
        return await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills(dm_url, "🕵️ 𝐎𝐏𝐄𝐍 𝐁𝐎𝐓 𝐃𝐌"))

    GDB["mafia_count"] = int(GDB.get("mafia_count", 0)) + 1
    game_no = GDB["mafia_count"]
    _save_game_db()

    game = {
        "game_no": game_no,
        "host_id": host.id,
        "host_name": host.first_name,
        "phase": "LOBBY",
        "players": {host.id: host.first_name},
        "order": [host.id],
        "roles": {},
        "chor_id": None,
        "votes": {},
        "end_ts": 0.0,
        "task": None,
    }
    ACTIVE_MAFIA[cid] = game

    dp = await _get_user_dp(client, host.id)
    card = await asyncio.to_thread(
        _render_mafia_lobby_card,
        dp, game_no, host.first_name, _build_mafia_roster(game), "LOBBY",
        "TYPE /join TO PLAY • START BOT DM FOR SECRET ROLE • /startmafia",
    )
    cap = (
        f"<blockquote><b>🕵️ 𝐂𝐇𝐎𝐑-𝐏𝐎𝐋𝐈𝐂𝐄 / 𝐌𝐀𝐅𝐈𝐀 𝐆𝐀𝐌𝐄 #{game_no} 𝐎𝐏𝐄𝐍!</b></blockquote>\n\n"
        f"👑 <b>Host:</b> <b>{html.escape(host.first_name)}</b> (Auto-Joined)\n"
        f"🎮 <b>Join Game:</b> <code>/join</code> <i>(3–10 Players)</i>\n"
        f"🚀 <b>Start Round:</b> <code>/startmafia</code>\n"
        f"📩 <b>Tip:</b> Secret role card ke liye niche button se Bot DM start kar lein!\n\n{FOOTER}"
    )
    await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills(dm_url, "🕵️ 𝐒𝐓𝐀𝐑𝐓 𝐁𝐎𝐓 𝐃𝐌"))

@bot.on_message(filters.group & filters.command(["join", "joinmafia"], prefixes=["/", "!", "."]))
async def mafia_join_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    game = ACTIVE_MAFIA.get(cid)
    if not game:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🕵️ 𝐍𝐎 𝐌𝐀𝐅𝐈𝐀 𝐋𝐎𝐁𝐁𝐘 𝐎𝐏𝐄𝐍</b></blockquote>\n\n"
            f"🎮 <b>Naya game shuru karein:</b> <code>/mafia</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if game["phase"] != "LOBBY":
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐆𝐀𝐌𝐄 𝐀𝐋𝐑𝐄𝐀𝐃𝐘 𝐒𝐓𝐀𝐑𝐓𝐄𝐃</b></blockquote>\n\n"
            f"⏳ <b>Agle round mein join karein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if user.id in game["players"]:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>✅ 𝐀𝐋𝐑𝐄𝐀𝐃𝐘 𝐈𝐍 𝐋𝐎𝐁𝐁𝐘</b></blockquote>\n\n"
            f"👤 <b>{html.escape(user.first_name)}</b> pehle se join hain! (<code>{len(game['order'])}/10</code>)\n\n{FOOTER}",
            reply_to=message.id,
        )

    if len(game["order"]) >= 10:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🚫 𝐋𝐎𝐁𝐁𝐘 𝐅𝐔𝐋𝐋 (10/10)</b></blockquote>\n\n"
            f"🚀 <b>Host ab <code>/startmafia</code> chala sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    game["players"][user.id] = user.first_name
    game["order"].append(user.id)
    dm_url = await _bot_dm_url(client)
    plist = ", ".join(f"<b>{html.escape(game['players'][u])}</b>" for u in game["order"])
    await _send_pill_msg(
        client, cid,
        f"<blockquote><b>🎮 𝐏𝐋𝐀𝐘𝐄𝐑 𝐉𝐎𝐈𝐍𝐄𝐃 𝐌𝐀𝐅𝐈𝐀 #{game['game_no']}!</b></blockquote>\n\n"
        f"👤 <b>Joined:</b> <b>{html.escape(user.first_name)}</b> (<code>{len(game['order'])}/10</code>)\n"
        f"👥 <b>Squad:</b> {plist}\n"
        f"🚀 <b>Ready?</b> Host likhein <code>/startmafia</code> (Min 3 Players)\n\n{FOOTER}",
        reply_to=message.id,
        extra_url=dm_url,
        extra_label="🕵️ 𝐒𝐓𝐀𝐑𝐓 𝐁𝐎𝐓 𝐃𝐌",
    )

@bot.on_message(filters.group & filters.command(["startmafia", "deal"], prefixes=["/", "!", "."]))
async def mafia_start_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    game = ACTIVE_MAFIA.get(cid)
    if not game or game["phase"] != "LOBBY":
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🕵️ 𝐍𝐎 𝐋𝐎𝐁𝐁𝐘 𝐓𝐎 𝐒𝐓𝐀𝐑𝐓</b></blockquote>\n\n"
            f"🎮 <b>Pehle <code>/mafia</code> se lobby banayein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if user.id != game["host_id"] and not await _is_chat_admin(client, cid, user.id):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐇𝐎𝐒𝐓 / 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Host ya Admin hi Mafia round start kar sakta hai!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if len(game["order"]) < 3:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>⚠️ 𝐌𝐈𝐍𝐈𝐌𝐔𝐌 3 𝐏𝐋𝐀𝐘𝐄𝐑𝐒 𝐍𝐄𝐄𝐃𝐄𝐃</b></blockquote>\n\n"
            f"👥 <b>Abhi Players:</b> <code>{len(game['order'])}/3</code> — doston ko <code>/join</code> bolen!\n\n{FOOTER}",
            reply_to=message.id,
        )

    # Shuffle & assign secret roles
    uids = list(game["order"])
    random.shuffle(uids)
    roles = {}
    roles[uids[0]] = "CHOR"
    roles[uids[1]] = "POLICE"
    if len(uids) >= 4:
        roles[uids[2]] = "DOCTOR"
        for u in uids[3:]:
            roles[u] = "CITIZEN"
    else:
        for u in uids[2:]:
            roles[u] = "CITIZEN"

    game["roles"] = roles
    game["chor_id"] = uids[0]
    game["phase"] = "VOTING"
    duration_sec = 75
    game["end_ts"] = time.time() + duration_sec
    game["task"] = asyncio.create_task(_mafia_vote_timer(client, cid, duration_sec))

    # Deliver Private Secret Role Card to every player's DM
    group_title = message.chat.title or "MGB GROUP"
    dm_sent = 0
    for uid in game["order"]:
        role = roles[uid]
        pname = game["players"][uid]
        try:
            p_dp = await _get_user_dp(client, uid)
            rcard = await asyncio.to_thread(_render_mafia_role_card, p_dp, pname, role, game["game_no"], group_title)
            rcap = (
                f"<blockquote><b>🤫 𝐒𝐄𝐂𝐑𝐄𝐓 𝐌𝐀𝐅𝐈𝐀 𝐑𝐎𝐋𝐄 — 𝐆𝐀𝐌𝐄 #{game['game_no']}</b></blockquote>\n\n"
                f"🎭 <b>Your Role:</b> <code>{role}</code>\n"
                f"👥 <b>Group:</b> <b>{html.escape(group_title)}</b>\n"
                f"⚠️ <b>Apna role kisi ko mat batana! Group mein <code>/suspect &lt;num&gt;</code> se vote karo!</b>\n\n{FOOTER}"
            )
            await _send_game_card(client, uid, rcard, rcap)
            dm_sent += 1
        except Exception:
            pass

    dm_url = await _bot_dm_url(client)
    host_dp = await _get_user_dp(client, game["host_id"])
    roster = _build_mafia_roster(game)
    card = await asyncio.to_thread(
        _render_mafia_lobby_card,
        host_dp, game["game_no"], game["host_name"], roster, "VOTING",
        "75s CHOR HUNT LIVE • VOTE WITH /suspect <num> • /endmafia",
    )
    roster_lines = "\n".join(f"• <code>/suspect {num}</code> — <b>{html.escape(nm)}</b>" for num, nm, _ in roster)
    cap = (
        f"<blockquote><b>🚨 𝐑𝐎𝐋𝐄𝐒 𝐃𝐄𝐀𝐋𝐓! 𝐂𝐇𝐎𝐑 𝐇𝐔𝐍𝐓 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!</b></blockquote>\n\n"
        f"📩 <b>Secret Role DMs Sent:</b> <code>{dm_sent}/{len(game['order'])}</code>\n"
        f"🕵️ <b>Group mein 1 CHOR chhupa hai! 75s mein pakdo:</b>\n\n"
        f"{roster_lines}\n\n"
        f"⚡ <b>Early Reveal:</b> <code>/endmafia</code>\n\n{FOOTER}"
    )
    await _send_game_card(client, cid, card, cap, rows=_bottom_html_pills(dm_url, "📩 𝐂𝐇𝐄𝐂𝐊 𝐒𝐄𝐂𝐑𝐄𝐓 𝐃𝐌"))

@bot.on_message(filters.group & filters.command(["suspect", "catch", "accuse"], prefixes=["/", "!", "."]))
async def mafia_suspect_vote_cmd(client, message: Message):
    cid = message.chat.id
    voter = message.from_user
    if not voter:
        return
    game = ACTIVE_MAFIA.get(cid)
    if not game or game["phase"] != "VOTING":
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🕵️ 𝐍𝐎 𝐀𝐂𝐓𝐈𝐕𝐄 𝐂𝐇𝐎𝐑 𝐇𝐔𝐍𝐓</b></blockquote>\n\n"
            f"🎮 <b>Naya game shuru karein:</b> <code>/mafia</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if voter.id not in game["players"]:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>👀 𝐒𝐏𝐄𝐂𝐓𝐀𝐓𝐎𝐑 𝐌𝐎𝐃𝐄</b></blockquote>\n\n"
            f"⚠️ <b>Sirf joined players hi is round mein suspect vote kar sakte hain!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🎯 𝐇𝐎𝐖 𝐓𝐎 𝐒𝐔𝐒𝐏𝐄𝐂𝐓</b></blockquote>\n\n"
            f"⚡ <b>Player number likhein:</b> <code>/suspect 1</code> se <code>/suspect {len(game['order'])}</code>\n\n{FOOTER}",
            reply_to=message.id,
        )

    idx = int(message.command[1]) - 1
    if not (0 <= idx < len(game["order"])):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>❌ 𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐏𝐋𝐀𝐘𝐄𝐑 𝐍𝐔𝐌𝐁𝐄𝐑</b></blockquote>\n\n"
            f"🎯 <b>1 se {len(game['order'])} ke beech choose karein!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    target_uid = game["order"][idx]
    game["votes"][voter.id] = target_uid
    target_name = game["players"][target_uid]
    rem = max(1, int(game["end_ts"] - time.time()))

    await _send_pill_msg(
        client, cid,
        f"<blockquote><b>🎯 𝐒𝐔𝐒𝐏𝐄𝐂𝐓 𝐕𝐎𝐓𝐄 𝐋𝐎𝐂𝐊𝐄𝐃!</b></blockquote>\n\n"
        f"👤 <b>{html.escape(voter.first_name)}</b> ne shak kiya ➔ <b>#{idx + 1} {html.escape(target_name)}</b> par!\n"
        f"🗳 <b>Votes Cast:</b> <code>{len(game['votes'])}/{len(game['order'])}</code> | ⏳ <code>{rem}s</code>\n\n{FOOTER}",
        reply_to=message.id,
    )

    # Auto-conclude immediately if every player has voted
    if len(game["votes"]) >= len(game["order"]):
        if game.get("task") and not game["task"].done():
            game["task"].cancel()
        await _conclude_mafia_game(client, cid)

@bot.on_message(filters.group & filters.command(["endmafia", "stopmafia"], prefixes=["/", "!", "."]))
async def mafia_end_cmd(client, message: Message):
    cid = message.chat.id
    user = message.from_user
    if not user:
        return

    game = ACTIVE_MAFIA.get(cid)
    if not game:
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🕵️ 𝐍𝐎 𝐀𝐂𝐓𝐈𝐕𝐄 𝐌𝐀𝐅𝐈𝐀 𝐆𝐀𝐌𝐄</b></blockquote>\n\n"
            f"⚠️ <b>Abhi koi Chor-Police / Mafia game nahi chal raha!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if user.id != game["host_id"] and not await _is_chat_admin(client, cid, user.id):
        return await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🔒 𝐇𝐎𝐒𝐓 / 𝐀𝐃𝐌𝐈𝐍 𝐎𝐍𝐋𝐘</b></blockquote>\n\n"
            f"⚠️ <b>Sirf Host ya Admin hi game khatam kar sakta hai!</b>\n\n{FOOTER}",
            reply_to=message.id,
        )

    if game.get("task") and not game["task"].done():
        game["task"].cancel()

    if game["phase"] == "VOTING":
        await _conclude_mafia_game(client, cid)
    else:
        ACTIVE_MAFIA.pop(cid, None)
        await _send_pill_msg(
            client, cid,
            f"<blockquote><b>🛑 𝐌𝐀𝐅𝐈𝐀 𝐋𝐎𝐁𝐁𝐘 𝐂𝐀𝐍𝐂𝐄𝐋𝐋𝐄𝐃</b></blockquote>\n\n"
            f"✅ <b>Game #{game['game_no']} band kar diya gaya hai!</b>\n\n{FOOTER}",
            reply_to=message.id,
  )
