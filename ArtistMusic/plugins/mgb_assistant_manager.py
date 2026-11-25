# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Module       : Dynamic Assistant Manager (Live + MongoDB)
# UI Style     : Permanent Colored HTML Buttons (Uniform 2x)
# Powered By   : ❖ MGB NOT FREE ❖
# Commands     : /addass, /loginass, /otp, /pass, /cancelass,
#                /asslist, /delass
# ==========================================================
import inspect
import os
import time
from typing import Any, Dict, List, Optional

from pymongo import AsyncMongoClient as AsyncIOMotorClient
from pyrogram import Client, enums, filters
from pyrogram.errors import (
    FloodWait,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import ArtistMusic
from ArtistMusic import app, config, logger

try:
    from pytgcalls import PyTgCalls
except Exception:
    PyTgCalls = None

try:
    import httpx
except Exception:
    httpx = None

try:
    import aiohttp
except Exception:
    aiohttp = None

# ----------------------------------------------------------
# Branding (Auto-Synced Live By mgb_brand_manager.py)
# ----------------------------------------------------------
OWNER_URL = "https://t.me/MGB_NOT_FREE_1"
UPDATES_URL = "https://t.me/mgb_not_free_coder"
SUPPORT_URL = "https://t.me/mgb_not_free_coder"
POWERED_TEXT = "🍓 <b>Powered By :</b> @MGB_NOT_FREE_1"

_MONGO_COL = None
_DYNAMIC_CLIENTS: Dict[int, Dict[str, Any]] = {}
_PENDING_LOGINS: Dict[int, Dict[str, Any]] = {}

_BTN_SUPPORTS_STYLE = (
    "style" in inspect.signature(InlineKeyboardButton.__init__).parameters
)


# ----------------------------------------------------------
# Permissions, MongoDB & ArtistMusic Runtime Helpers
# ----------------------------------------------------------
def _is_owner_or_sudo(user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    owner_id = int(getattr(config, "OWNER_ID", 0) or os.getenv("OWNER_ID", "0") or 0)
    app_owner = int(getattr(app, "owner", 0) or 0)
    sudoers = getattr(app, "sudoers", set()) or set()
    return user_id in (owner_id, app_owner) or user_id in sudoers


def _get_collection():
    global _MONGO_COL
    if _MONGO_COL is not None:
        return _MONGO_COL
    mongo_uri = (
        getattr(config, "MONGO_URL", None)
        or getattr(config, "MONGO_DB_URI", None)
        or os.getenv("MONGO_URL")
        or os.getenv("MONGO_DB_URI")
    )
    if not mongo_uri:
        raise RuntimeError("MONGO_URL / MONGO_DB_URI nahi mila!")
    client = AsyncIOMotorClient(mongo_uri)
    _MONGO_COL = client["MGB_ASSISTANT_MGR"]["extra_assistants"]
    return _MONGO_COL


def _get_userbot_manager():
    return getattr(ArtistMusic, "userbot", None) or getattr(ArtistMusic, "user", None)


def _get_call_manager():
    return (
        getattr(ArtistMusic, "tune", None)
        or getattr(ArtistMusic, "anon", None)
        or getattr(ArtistMusic, "calls", None)
        or getattr(ArtistMusic, "call", None)
    )


async def _safe_delete(msg: Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


def _get_existing_ids() -> set:
    ids = set(_DYNAMIC_CLIENTS.keys())
    ub = _get_userbot_manager()
    if ub and hasattr(ub, "clients") and isinstance(ub.clients, list):
        for c in ub.clients:
            cid = getattr(c, "id", None)
            if cid:
                ids.add(cid)
    return ids


# ----------------------------------------------------------
# Permanent Colored HTML Button Engine (Uniform 2x Bottom)
# ----------------------------------------------------------
def _hbtn(
    text: str,
    url: Optional[str] = None,
    callback_data: Optional[str] = None,
    style: str = "primary",
) -> Dict[str, Any]:
    btn: Dict[str, Any] = {"text": text, "style": style}
    if url:
        btn["url"] = url
    if callback_data:
        btn["callback_data"] = callback_data
    return btn


def _default_bottom_rows(
    top_rows: Optional[List[List[Dict[str, Any]]]] = None,
) -> List[List[Dict[str, Any]]]:
    rows: List[List[Dict[str, Any]]] = list(top_rows or [])
    rows.append(
        [
            _hbtn("👑 OWNER", url=OWNER_URL, style="primary"),
            _hbtn("🚀 UPDATES", url=UPDATES_URL, style="success"),
        ]
    )
    rows.append(
        [
            _hbtn("💬 SUPPORT", url=SUPPORT_URL, style="primary"),
            _hbtn("📋 ASSISTANTS", callback_data="mgb_ass_refresh", style="success"),
        ]
    )
    return rows


def _rows_to_pyro_markup(rows: List[List[Dict[str, Any]]]) -> InlineKeyboardMarkup:
    pyro_rows = []
    for row in rows:
        pyro_row = []
        for item in row:
            kw: Dict[str, Any] = {"text": item["text"]}
            if "url" in item:
                kw["url"] = item["url"]
            if "callback_data" in item:
                kw["callback_data"] = item["callback_data"]
            if _BTN_SUPPORTS_STYLE and item.get("style"):
                kw["style"] = item["style"]
            pyro_row.append(InlineKeyboardButton(**kw))
        pyro_rows.append(pyro_row)
    return InlineKeyboardMarkup(pyro_rows)


async def _bot_api_post(method: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bot_token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not bot_token:
        return None
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(url, json=payload)
                data = r.json()
                return data.get("result") if (r.status_code == 200 and data.get("ok")) else None
        if aiohttp is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=12) as r:
                    data = await r.json()
                    return data.get("result") if (r.status == 200 and data.get("ok")) else None
    except Exception:
        return None
    return None


async def _send_html_card(
    chat_id: int,
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
    reply_to_id: Optional[int] = None,
) -> Optional[int]:
    btn_rows = rows if rows is not None else _default_bottom_rows()

    if _BTN_SUPPORTS_STYLE:
        msg = await app.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=_rows_to_pyro_markup(btn_rows),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_to_message_id=reply_to_id,
        )
        return msg.id if msg else None

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": btn_rows},
    }
    if reply_to_id:
        payload["reply_parameters"] = {
            "message_id": reply_to_id,
            "allow_sending_without_reply": True,
        }

    res = await _bot_api_post("sendMessage", payload)
    if isinstance(res, dict) and res.get("message_id"):
        return int(res["message_id"])

    msg = await app.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=_rows_to_pyro_markup(btn_rows),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )
    return msg.id if msg else None


async def _edit_html_msg(
    chat_id: int,
    msg_id: Optional[int],
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
) -> None:
    btn_rows = rows if rows is not None else _default_bottom_rows()
    if not msg_id:
        await _send_html_card(chat_id, text, rows=btn_rows)
        return

    if _BTN_SUPPORTS_STYLE:
        try:
            await app.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
        return

    payload = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": btn_rows},
    }
    res = await _bot_api_post("editMessageText", payload)
    if res is None:
        try:
            await app.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass


# ----------------------------------------------------------
# Live Assistant Engine (Pyrogram + PyTgCalls + MongoDB)
# ----------------------------------------------------------
async def _attach_assistant(
    session_string: str,
    added_by: int = 0,
    save_db: bool = True,
) -> Dict[str, Any]:
    """Start Pyrogram + PyTgCalls client live and inject into ArtistMusic runtime."""
    session_string = session_string.strip()
    cli = Client(
        name=f"mgb_dyn_ass_{int(time.time() * 1000)}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session_string,
        in_memory=True,
        ipv6=False,
    )

    await cli.start()
    try:
        me = await cli.get_me()
        if me.is_bot:
            await cli.stop()
            raise ValueError("Ye bot session hai! Assistant ke liye User Account ka session dein.")

        if me.id in _get_existing_ids():
            await cli.stop()
            raise ValueError(f"Assistant {me.first_name} ({me.id}) pehle se bot mein active hai.")

        cli.id = me.id
        cli.name = me.first_name
        cli.username = me.username
        cli.mention = me.mention

        ptg = None
        if PyTgCalls is not None:
            try:
                ptg = PyTgCalls(cli, cache_duration=100)
            except TypeError:
                ptg = PyTgCalls(cli)
            await ptg.start()

        ub = _get_userbot_manager()
        if ub is not None:
            if hasattr(ub, "clients") and isinstance(ub.clients, list):
                ub.clients.append(cli)
            if hasattr(ub, "ids") and isinstance(ub.ids, list) and me.id not in ub.ids:
                ub.ids.append(me.id)

        call_mgr = _get_call_manager()
        if call_mgr is not None and ptg is not None:
            if hasattr(call_mgr, "clients") and isinstance(call_mgr.clients, list):
                call_mgr.clients.append(ptg)

        _DYNAMIC_CLIENTS[me.id] = {
            "client": cli,
            "call": ptg,
            "me": me,
            "session": session_string,
        }

        if save_db:
            col = _get_collection()
            await col.update_one(
                {"user_id": me.id},
                {
                    "$set": {
                        "user_id": me.id,
                        "name": me.first_name,
                        "username": me.username,
                        "session": session_string,
                        "added_by": added_by,
                        "added_at": int(time.time()),
                    }
                },
                upsert=True,
            )

        logger_id = getattr(config, "LOGGER_ID", None)
        if logger_id:
            try:
                await cli.send_message(
                    logger_id,
                    f"👤 <b>New Assistant Connected</b>\n"
                    f"• <b>Name:</b> {me.mention}\n"
                    f"• <b>ID:</b> <code>{me.id}</code>\n"
                    f"• <b>Username:</b> @{me.username if me.username else 'None'}",
                )
            except Exception:
                pass

        logger.info(
            f"👤 Dynamic Assistant started: {me.first_name} (@{me.username}) [{me.id}]"
        )
        return {
            "id": me.id,
            "name": me.first_name,
            "username": me.username,
            "mention": me.mention,
            "vc_ready": bool(ptg),
        }
    except Exception:
        try:
            if getattr(cli, "is_connected", False):
                await cli.stop()
        except Exception:
            pass
        raise


async def boot_saved_assistants() -> int:
    """Auto-boot all MongoDB-saved extra assistants on Render/VPS startup."""
    started = 0
    try:
        col = _get_collection()
        docs = await col.find({}).to_list(length=100)
    except Exception as ex:
        logger.warning(f"⚠️ Could not load saved assistants from MongoDB: {ex}")
        return 0

    for doc in docs:
        sess = (doc.get("session") or "").strip()
        uid = doc.get("user_id")
        if not sess:
            continue
        try:
            await _attach_assistant(sess, added_by=doc.get("added_by", 0), save_db=False)
            started += 1
        except Exception as ex:
            logger.warning(f"⚠️ Saved assistant {uid} failed to start: {ex}")

    if started:
        logger.info(f"✅ Loaded {started} extra assistant(s) from MongoDB.")
    return started


def _build_asslist_text() -> str:
    ub = _get_userbot_manager()
    lines = ["<blockquote>👥 <b>MGB ASSISTANT MANAGER</b></blockquote>\n"]
    shown_ids = set()
    idx = 0

    if ub and hasattr(ub, "clients") and isinstance(ub.clients, list):
        for c in ub.clients:
            cid = getattr(c, "id", None)
            if not cid or cid in shown_ids:
                continue
            shown_ids.add(cid)
            idx += 1
            cname = getattr(c, "name", "Assistant")
            uname = getattr(c, "username", None)
            tag = "BOT-DB" if cid in _DYNAMIC_CLIENTS else "ENV"
            lines.append(
                f"<b>{idx}. {cname}</b> [<code>{tag}</code>]\n"
                f"   • <b>ID:</b> <code>{cid}</code>\n"
                f"   • <b>User:</b> @{uname if uname else 'Not Set'}\n"
            )

    for cid, info in _DYNAMIC_CLIENTS.items():
        if cid in shown_ids:
            continue
        idx += 1
        me = info["me"]
        lines.append(
            f"<b>{idx}. {me.first_name}</b> [<code>BOT-DB</code>]\n"
            f"   • <b>ID:</b> <code>{cid}</code>\n"
            f"   • <b>User:</b> @{me.username if me.username else 'Not Set'}\n"
        )

    if idx == 0:
        lines.append("<i>Abhi koi active assistant nahi mila.</i>\n")

    lines.append(
        "<b>Commands:</b>\n"
        "• <code>/addass &lt;string_session&gt;</code>\n"
        "• <code>/loginass +91XXXXXXXXXX</code> (DM only)\n"
        "• <code>/delass &lt;user_id&gt;</code>\n\n"
        f"{POWERED_TEXT}"
    )
    return "\n".join(lines)
# ----------------------------------------------------------
# 1. /addass — Direct String Session se Assistant Add Karein
# ----------------------------------------------------------
@app.on_message(filters.command(["addass", "addassistant"]))
async def add_assistant_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    session_str = ""
    deleted_cmd = False
    if len(message.command) >= 2:
        session_str = message.text.split(None, 1)[1].strip()
        await _safe_delete(message)
        deleted_cmd = True
    elif message.reply_to_message and message.reply_to_message.text:
        session_str = message.reply_to_message.text.strip()

    if not session_str or len(session_str) < 50:
        return await _send_html_card(
            message.chat.id,
            "<blockquote>👤 <b>ADD NEW ASSISTANT</b></blockquote>\n\n"
            "<b>Tarika 1 (String Session):</b>\n"
            "<code>/addass YOUR_PYROGRAM_STRING_SESSION</code>\n"
            "<i>(Ya string session message par reply karke <code>/addass</code> bhejein)</i>\n\n"
            "<b>Tarika 2 (Phone + OTP — DM mein):</b>\n"
            "<code>/loginass +91XXXXXXXXXX</code>\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=None if deleted_cmd else message.id,
        )

    status_id = await _send_html_card(
        message.chat.id,
        "<blockquote>⏳ <b>CONNECTING ASSISTANT...</b></blockquote>\n\n"
        "Session verify aur Voice Chat client start ho raha hai...\n\n"
        f"{POWERED_TEXT}",
    )

    try:
        info = await _attach_assistant(
            session_str,
            added_by=message.from_user.id,
            save_db=True,
        )
        warn_uname = (
            ""
            if info["username"]
            else "\n⚠️ <b>Tip:</b> Is account par Telegram @username zaroor set kar lein."
        )
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>✅ <b>ASSISTANT ADDED LIVE!</b></blockquote>\n\n"
            f"• <b>Name:</b> {info['mention']}\n"
            f"• <b>User ID:</b> <code>{info['id']}</code>\n"
            f"• <b>Username:</b> @{info['username'] if info['username'] else 'Not Set'}\n"
            f"• <b>VC Engine:</b> {'Active ✅' if info['vc_ready'] else 'Client Only ⚠️'}\n"
            f"• <b>Saved in MongoDB:</b> Yes ✅{warn_uname}\n\n"
            f"{POWERED_TEXT}",
        )
    except Exception as ex:
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>❌ <b>ASSISTANT ADD FAILED</b></blockquote>\n\n"
            f"<b>Reason:</b> <code>{ex}</code>\n\n"
            f"{POWERED_TEXT}",
        )


# ----------------------------------------------------------
# 2. /loginass, /otp, /pass, /cancelass — Phone + OTP Login
# ----------------------------------------------------------
@app.on_message(filters.command(["loginass", "newass"]))
async def login_assistant_start(_, message: Message):
    uid = getattr(message.from_user, "id", None)
    if not _is_owner_or_sudo(uid):
        return

    if message.chat.type != enums.ChatType.PRIVATE:
        return await _send_html_card(
            message.chat.id,
            "<blockquote>🔒 <b>PRIVATE CHAT ONLY</b></blockquote>\n\n"
            "Security ke liye <code>/loginass</code> sirf bot ke <b>DM (Private Chat)</b> mein use karein.\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    if len(message.command) < 2:
        return await _send_html_card(
            message.chat.id,
            "<blockquote>📱 <b>PHONE SE ASSISTANT ADD KAREIN</b></blockquote>\n\n"
            "Country code ke saath number bhejein:\n"
            "<code>/loginass +919876543210</code>\n\n"
            "<i>Cancel karne ke liye:</i> <code>/cancelass</code>\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    phone = message.text.split(None, 1)[1].strip().replace(" ", "")
    await _safe_delete(message)

    old = _PENDING_LOGINS.pop(uid, None)
    if old:
        try:
            await old["client"].disconnect()
        except Exception:
            pass

    status_id = await _send_html_card(
        message.chat.id,
        "<blockquote>📡 <b>SENDING TELEGRAM OTP...</b></blockquote>\n\n"
        "Thoda wait karein, Telegram par login code bheja ja raha hai...\n\n"
        f"{POWERED_TEXT}",
    )

    temp_cli = Client(
        name=f"mgb_login_{uid}_{int(time.time())}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        in_memory=True,
        ipv6=False,
    )

    try:
        await temp_cli.connect()
        sent = await temp_cli.send_code(phone)
        _PENDING_LOGINS[uid] = {
            "client": temp_cli,
            "phone": phone,
            "phone_code_hash": sent.phone_code_hash,
            "step": "otp",
            "ts": time.time(),
        }
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>📩 <b>OTP SENT SUCCESSFULLY</b></blockquote>\n\n"
            "Telegram par aaya hua 5-digit OTP <b>space ke saath</b> bhejein (taaki Telegram expire na kare):\n\n"
            "<b>Example:</b> <code>/otp 1 2 3 4 5</code>\n"
            "<i>Cancel karne ke liye:</i> <code>/cancelass</code>\n\n"
            f"{POWERED_TEXT}",
        )
    except PhoneNumberInvalid:
        await temp_cli.disconnect()
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>❌ <b>INVALID PHONE NUMBER</b></blockquote>\n\n"
            "Sahi country code ke saath dobara try karein (e.g. <code>+919876543210</code>).\n\n"
            f"{POWERED_TEXT}",
        )
    except FloodWait as fw:
        await temp_cli.disconnect()
        await _edit_html_msg(
            message.chat.id,
            status_id,
            f"<blockquote>⏳ <b>FLOODWAIT</b></blockquote>\n\n"
            f"{fw.value} seconds baad try karein.\n\n{POWERED_TEXT}",
        )
    except Exception as ex:
        try:
            await temp_cli.disconnect()
        except Exception:
            pass
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>❌ <b>OTP SEND FAILED</b></blockquote>\n\n"
            f"<b>Reason:</b> <code>{ex}</code>\n\n"
            f"{POWERED_TEXT}",
        )


@app.on_message(filters.command("otp") & filters.private)
async def login_assistant_otp(_, message: Message):
    uid = getattr(message.from_user, "id", None)
    if not _is_owner_or_sudo(uid) or uid not in _PENDING_LOGINS:
        return

    state = _PENDING_LOGINS[uid]
    if state["step"] != "otp":
        return await _send_html_card(
            message.chat.id,
            "<blockquote>🔐 <b>2FA PASSWORD REQUIRED</b></blockquote>\n\n"
            f"Password bhejein: <code>/pass YOUR_PASSWORD</code>\n\n{POWERED_TEXT}",
        )

    if len(message.command) < 2:
        return await _send_html_card(
            message.chat.id,
            f"OTP aise bhejein: <code>/otp 1 2 3 4 5</code>\n\n{POWERED_TEXT}",
        )

    raw_code = message.text.split(None, 1)[1]
    code = "".join(ch for ch in raw_code if ch.isdigit())
    await _safe_delete(message)

    status_id = await _send_html_card(
        message.chat.id,
        f"<blockquote>⏳ <b>VERIFYING OTP...</b></blockquote>\n\n{POWERED_TEXT}",
    )
    cli: Client = state["client"]

    try:
        await cli.sign_in(state["phone"], state["phone_code_hash"], code)
        session_str = await cli.export_session_string()
        await cli.disconnect()
        _PENDING_LOGINS.pop(uid, None)

        info = await _attach_assistant(session_str, added_by=uid, save_db=True)
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>✅ <b>NEW ASSISTANT LOGGED IN &amp; ACTIVE!</b></blockquote>\n\n"
            f"• <b>Name:</b> {info['mention']}\n"
            f"• <b>User ID:</b> <code>{info['id']}</code>\n"
            f"• <b>Username:</b> @{info['username'] if info['username'] else 'Not Set'}\n"
            f"• <b>Saved in MongoDB:</b> Yes ✅\n\n"
            f"{POWERED_TEXT}",
        )
    except SessionPasswordNeeded:
        state["step"] = "2fa"
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>🔐 <b>2FA PASSWORD REQUIRED</b></blockquote>\n\n"
            "Is account par Two-Step Verification ON hai.\n"
            "Password bhejein (send hote hi auto-delete ho jayega):\n"
            "<code>/pass YOUR_2FA_PASSWORD</code>\n\n"
            f"{POWERED_TEXT}",
        )
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>❌ <b>INVALID OR EXPIRED OTP</b></blockquote>\n\n"
            "Sahi OTP <code>/otp 1 2 3 4 5</code> bhejein ya <code>/cancelass</code> karein.\n\n"
            f"{POWERED_TEXT}",
        )
    except Exception as ex:
        try:
            await cli.disconnect()
        except Exception:
            pass
        _PENDING_LOGINS.pop(uid, None)
        await _edit_html_msg(
            message.chat.id,
            status_id,
            f"<blockquote>❌ <b>LOGIN FAILED</b></blockquote>\n\n"
            f"<code>{ex}</code>\n\n{POWERED_TEXT}",
        )


@app.on_message(filters.command("pass") & filters.private)
async def login_assistant_2fa(_, message: Message):
    uid = getattr(message.from_user, "id", None)
    if not _is_owner_or_sudo(uid) or uid not in _PENDING_LOGINS:
        return

    state = _PENDING_LOGINS[uid]
    if state["step"] != "2fa":
        return

    if len(message.command) < 2:
        return await _send_html_card(
            message.chat.id,
            f"Password aise bhejein: <code>/pass YOUR_PASSWORD</code>\n\n{POWERED_TEXT}",
        )

    password = message.text.split(None, 1)[1].strip()
    await _safe_delete(message)

    status_id = await _send_html_card(
        message.chat.id,
        f"<blockquote>🔐 <b>VERIFYING 2FA PASSWORD...</b></blockquote>\n\n{POWERED_TEXT}",
    )
    cli: Client = state["client"]

    try:
        await cli.check_password(password)
        session_str = await cli.export_session_string()
        await cli.disconnect()
        _PENDING_LOGINS.pop(uid, None)

        info = await _attach_assistant(session_str, added_by=uid, save_db=True)
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>✅ <b>NEW ASSISTANT LOGGED IN &amp; ACTIVE!</b></blockquote>\n\n"
            f"• <b>Name:</b> {info['mention']}\n"
            f"• <b>User ID:</b> <code>{info['id']}</code>\n"
            f"• <b>Username:</b> @{info['username'] if info['username'] else 'Not Set'}\n"
            f"• <b>Saved in MongoDB:</b> Yes ✅\n\n"
            f"{POWERED_TEXT}",
        )
    except PasswordHashInvalid:
        await _edit_html_msg(
            message.chat.id,
            status_id,
            "<blockquote>❌ <b>WRONG 2FA PASSWORD</b></blockquote>\n\n"
            "Dobara <code>/pass YOUR_PASSWORD</code> bhejein ya <code>/cancelass</code> karein.\n\n"
            f"{POWERED_TEXT}",
        )
    except Exception as ex:
        try:
            await cli.disconnect()
        except Exception:
            pass
        _PENDING_LOGINS.pop(uid, None)
        await _edit_html_msg(
            message.chat.id,
            status_id,
            f"<blockquote>❌ <b>2FA FAILED</b></blockquote>\n\n"
            f"<code>{ex}</code>\n\n{POWERED_TEXT}",
        )


@app.on_message(filters.command("cancelass") & filters.private)
async def cancel_assistant_login(_, message: Message):
    uid = getattr(message.from_user, "id", None)
    if not _is_owner_or_sudo(uid):
        return

    state = _PENDING_LOGINS.pop(uid, None)
    if not state:
        return await _send_html_card(
            message.chat.id,
            f"<blockquote>ℹ️ <b>NO ACTIVE LOGIN</b></blockquote>\n\n"
            f"Koi active login process chal nahi raha hai.\n\n{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    try:
        await state["client"].disconnect()
    except Exception:
        pass
    await _send_html_card(
        message.chat.id,
        f"<blockquote>✅ <b>LOGIN CANCELLED</b></blockquote>\n\n"
        f"Assistant login process cancel kar diya gaya hai.\n\n{POWERED_TEXT}",
        reply_to_id=message.id,
    )


# ----------------------------------------------------------
# 3. /asslist & Refresh Button — Saare Assistants Dekhein
# ----------------------------------------------------------
@app.on_message(filters.command(["asslist", "assistants"]))
async def list_assistants_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    await _send_html_card(
        message.chat.id,
        _build_asslist_text(),
        reply_to_id=message.id,
    )


@app.on_callback_query(filters.regex("^mgb_ass_refresh$"))
async def refresh_assistants_cb(_, cq: CallbackQuery):
    if not _is_owner_or_sudo(getattr(cq.from_user, "id", None)):
        return await cq.answer("Sirf Owner / Sudo users ke liye!", show_alert=True)

    await _edit_html_msg(
        cq.message.chat.id,
        cq.message.id,
        _build_asslist_text(),
    )
    await cq.answer("Assistant list refreshed ✅")


# ----------------------------------------------------------
# 4. /delass <user_id> — Dynamic Assistant Remove Karein
# ----------------------------------------------------------
@app.on_message(filters.command(["delass", "rmass", "removeassistant"]))
async def delete_assistant_cmd(_, message: Message):
    if not _is_owner_or_sudo(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await _send_html_card(
            message.chat.id,
            "<blockquote>🗑 <b>REMOVE ASSISTANT</b></blockquote>\n\n"
            "Pehle <code>/asslist</code> se <code>BOT-DB</code> wale assistant ki ID dekhein, phir bhejein:\n"
            "<code>/delass USER_ID</code>\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    target_id = int(message.command[1])
    if target_id not in _DYNAMIC_CLIENTS:
        try:
            res = await _get_collection().delete_one({"user_id": target_id})
            if res.deleted_count:
                return await _send_html_card(
                    message.chat.id,
                    "<blockquote>🗑 <b>ASSISTANT REMOVED</b></blockquote>\n\n"
                    f"Assistant <code>{target_id}</code> MongoDB se remove kar diya gaya ✅\n\n"
                    f"{POWERED_TEXT}",
                    reply_to_id=message.id,
                )
        except Exception:
            pass
        return await _send_html_card(
            message.chat.id,
            "<blockquote>⚠️ <b>REMOVE NOT ALLOWED</b></blockquote>\n\n"
            f"ID <code>{target_id}</code> dynamic list mein nahi mila.\n"
            "<i>Note: Render Environment (<code>ENV</code>) wale default assistant ko yahan se delete nahi kar sakte.</i>\n\n"
            f"{POWERED_TEXT}",
            reply_to_id=message.id,
        )

    entry = _DYNAMIC_CLIENTS.pop(target_id)
    cli: Client = entry["client"]
    ptg = entry.get("call")

    ub = _get_userbot_manager()
    if ub:
        if hasattr(ub, "clients") and isinstance(ub.clients, list) and cli in ub.clients:
            ub.clients.remove(cli)
        if hasattr(ub, "ids") and isinstance(ub.ids, list) and target_id in ub.ids:
            ub.ids.remove(target_id)

    call_mgr = _get_call_manager()
    if call_mgr and ptg and hasattr(call_mgr, "clients") and ptg in call_mgr.clients:
        call_mgr.clients.remove(ptg)

    if ptg:
        try:
            await ptg.stop()
        except Exception:
            pass
    try:
        await cli.stop()
    except Exception:
        pass

    try:
        await _get_collection().delete_one({"user_id": target_id})
    except Exception:
        pass

    await _send_html_card(
        message.chat.id,
        "<blockquote>🗑 <b>ASSISTANT REMOVED</b></blockquote>\n\n"
        f"Assistant <code>{target_id}</code> ko live runtime aur MongoDB dono se hata diya gaya hai ✅\n\n"
        f"{POWERED_TEXT}",
        reply_to_id=message.id,
      )
  
