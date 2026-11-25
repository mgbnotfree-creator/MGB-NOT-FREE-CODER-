# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Module       : Global Live Brand Manager & Owner Recovery
# UI Style     : Permanent Colored HTML Buttons (Uniform 2x)
# Powered By   : ❖ MGB NOT FREE ❖
# Commands     : /brand, /setall, /setchannel, /setgroup,
#                /setownerlink, /replace, /delreplace,
#                /claimowner
# ==========================================================
import asyncio
import contextvars
import copy
import hmac
import inspect
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from pymongo import AsyncMongoClient as AsyncIOMotorClient
from pyrogram import enums, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ArtistMusic import app, config, logger

try:
    import httpx
except Exception:
    httpx = None

try:
    import aiohttp
except Exception:
    aiohttp = None

# ----------------------------------------------------------
# Defaults & Runtime Cache (Zero DB Latency Per Message)
# ----------------------------------------------------------
DEFAULT_OWNER_HANDLE = "@MGB_NOT_FREE_1"
DEFAULT_OWNER_URL = "https://t.me/MGB_NOT_FREE_1"

DEFAULT_UPDATES_HANDLE = "@mgb_not_free_coder"
DEFAULT_UPDATES_URL = "https://t.me/mgb_not_free_coder"

DEFAULT_SUPPORT_HANDLE = "@mgb_not_free_coder"
DEFAULT_SUPPORT_URL = "https://t.me/mgb_not_free_coder"

_MONGO_COL = None
_LOADED = False
_PATCHED = False
_SKIP_REPLACE = contextvars.ContextVar("_mgb_skip_brand_replace", default=False)

_BTN_SUPPORTS_STYLE = (
    "style" in inspect.signature(InlineKeyboardButton.__init__).parameters
)

_STATE: Dict[str, Any] = {
    "enabled": True,
    "active_owner_id": 0,
    "owner_handle": DEFAULT_OWNER_HANDLE,
    "owner_url": DEFAULT_OWNER_URL,
    "updates_handle": DEFAULT_UPDATES_HANDLE,
    "updates_url": DEFAULT_UPDATES_URL,
    "support_handle": DEFAULT_SUPPORT_HANDLE,
    "support_url": DEFAULT_SUPPORT_URL,
    "old_owner_slugs": ["MGB_NOT_FREE", "MGB_NOT_FREE_1"],
    "old_updates_slugs": ["MGB_CODER", "mgb_not_free_coder"],
    "old_support_slugs": ["MGB_CODER", "mgb_not_free_coder"],
    "custom_rules": {},
}

_URL_PATTERNS: List[Tuple[re.Pattern, str]] = []
_TEXT_PATTERNS: List[Tuple[re.Pattern, str]] = []


# ----------------------------------------------------------
# MongoDB, URL Parser & Auth Helpers
# ----------------------------------------------------------
def _get_col():
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
        raise RuntimeError("MONGO_URL / MONGO_DB_URI missing!")
    client = AsyncIOMotorClient(mongo_uri)
    _MONGO_COL = client["MGB_BRAND_MGR"]["settings"]
    return _MONGO_COL


def _parse_tg_target(raw: str) -> Tuple[str, str, Optional[str]]:
    val = (raw or "").strip()
    if not val:
        raise ValueError("Link ya username khali hai!")

    if "+" in val or "joinchat/" in val.lower():
        if not val.startswith(("http://", "https://")):
            val = "https://" + val.lstrip("/")
        return val, val, None

    slug = re.sub(r"^https?://(?:www\.)?(?:t\.me|telegram\.me)/", "", val, flags=re.I)
    slug = slug.lstrip("@").split("?")[0].split("/")[0].strip()

    if not slug or not re.fullmatch(r"[A-Za-z0-9_]{3,64}", slug):
        raise ValueError(
            "Valid @username, https://t.me/username, ya https://t.me/+invite_link dein."
        )
    return f"@{slug}", f"https://t.me/{slug}", slug


def _is_authorized(user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    env_owner = int(getattr(config, "OWNER_ID", 0) or os.getenv("OWNER_ID", "0") or 0)
    active_owner = int(_STATE.get("active_owner_id") or 0)
    sudoers = getattr(app, "sudoers", set()) or set()

    if active_owner:
        if user_id == active_owner:
            return True
    elif user_id == env_owner:
        return True
    return user_id in sudoers


async def _safe_delete(msg: Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


# ----------------------------------------------------------
# Permanent Colored HTML Button Engine (Uniform Bottom Grid)
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


def _default_bottom_rows() -> List[List[Dict[str, Any]]]:
    bot_uname = getattr(app, "username", None) or "Yasmeen_api_bot"
    return [
        [
            _hbtn("👑 OWNER", url=_STATE["owner_url"], style="primary"),
            _hbtn("🚀 UPDATES", url=_STATE["updates_url"], style="success"),
        ],
        [
            _hbtn("💬 SUPPORT", url=_STATE["support_url"], style="primary"),
            _hbtn(
                "➕ ADD BOT",
                url=f"https://t.me/{bot_uname}?startgroup=true",
                style="success",
            ),
        ],
    ]


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


async def _bot_api_post(method: str, payload: Dict[str, Any]) -> bool:
    bot_token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not bot_token:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(url, json=payload)
                return r.status_code == 200 and r.json().get("ok", False)
        if aiohttp is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=12) as r:
                    data = await r.json()
                    return r.status == 200 and data.get("ok", False)
    except Exception:
        return False
    return False


async def _send_html_card(
    message: Message,
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
    reply: bool = True,
) -> None:
    btn_rows = rows if rows is not None else _default_bottom_rows()
    token = _SKIP_REPLACE.set(True)
    try:
        if _BTN_SUPPORTS_STYLE:
            markup = _rows_to_pyro_markup(btn_rows)
            if reply:
                await message.reply_text(
                    text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            else:
                await app.send_message(
                    message.chat.id,
                    text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            return

        payload: Dict[str, Any] = {
            "chat_id": message.chat.id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
            "reply_markup": {"inline_keyboard": btn_rows},
        }
        if reply:
            payload["reply_parameters"] = {
                "message_id": message.id,
                "allow_sending_without_reply": True,
            }

        ok = await _bot_api_post("sendMessage", payload)
        if not ok:
            markup = _rows_to_pyro_markup(btn_rows)
            await app.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
    finally:
        _SKIP_REPLACE.reset(token)


async def _edit_html_card(
    cq: CallbackQuery,
    text: str,
    rows: Optional[List[List[Dict[str, Any]]]] = None,
) -> None:
    btn_rows = rows if rows is not None else _default_bottom_rows()
    token = _SKIP_REPLACE.set(True)
    try:
        if _BTN_SUPPORTS_STYLE:
            await cq.message.edit_text(
                text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return

        payload = {
            "chat_id": cq.message.chat.id,
            "message_id": cq.message.id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
            "reply_markup": {"inline_keyboard": btn_rows},
        }
        ok = await _bot_api_post("editMessageText", payload)
        if not ok:
            await cq.message.edit_text(
                text,
                reply_markup=_rows_to_pyro_markup(btn_rows),
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
    except Exception:
        pass
    finally:
        _SKIP_REPLACE.reset(token)
# ----------------------------------------------------------
# Compile Fast Replacement Rules & Sync Runtime Modules
# ----------------------------------------------------------
def _rebuild_patterns() -> None:
    global _URL_PATTERNS, _TEXT_PATTERNS
    url_rules: List[Tuple[int, re.Pattern, str]] = []
    text_rules: List[Tuple[int, re.Pattern, str]] = []

    active_slugs = set()
    for key in ("owner_handle", "updates_handle", "support_handle"):
        h = str(_STATE.get(key) or "")
        if h.startswith("@"):
            active_slugs.add(h[1:].lower())

    slot_map = [
        ("old_owner_slugs", _STATE["owner_handle"], _STATE["owner_url"]),
        ("old_updates_slugs", _STATE["updates_handle"], _STATE["updates_url"]),
        ("old_support_slugs", _STATE["support_handle"], _STATE["support_url"]),
    ]

    seen_slugs = set()
    for alias_key, new_handle, new_url in slot_map:
        for slug in _STATE.get(alias_key, []):
            s = str(slug or "").strip().lstrip("@")
            low = s.lower()
            if not s or low in active_slugs or low in seen_slugs:
                continue
            seen_slugs.add(low)

            url_pat = re.compile(
                rf"(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/{re.escape(s)}(?![A-Za-z0-9_])",
                re.IGNORECASE,
            )
            handle_pat = re.compile(
                rf"@{re.escape(s)}(?![A-Za-z0-9_])",
                re.IGNORECASE,
            )

            url_rules.append((len(s), url_pat, new_url))
            text_rules.append((len(s) + 10, url_pat, new_url))
            text_rules.append((len(s), handle_pat, new_handle))

    for old_str, new_str in (_STATE.get("custom_rules") or {}).items():
        old_s = str(old_str or "").strip()
        new_s = str(new_str or "").strip()
        if not old_s or old_s == new_s:
            continue
        pat = re.compile(re.escape(old_s), re.IGNORECASE)
        url_rules.append((len(old_s) + 50, pat, new_s))
        text_rules.append((len(old_s) + 50, pat, new_s))

    url_rules.sort(key=lambda x: x[0], reverse=True)
    text_rules.sort(key=lambda x: x[0], reverse=True)

    _URL_PATTERNS = [(p, rep) for _, p, rep in url_rules]
    _TEXT_PATTERNS = [(p, rep) for _, p, rep in text_rules]


def _sync_live_modules() -> None:
    owner_url = _STATE["owner_url"]
    owner_handle = _STATE["owner_handle"]
    updates_url = _STATE["updates_url"]
    updates_handle = _STATE["updates_handle"]
    support_url = _STATE["support_url"]
    active_owner = int(_STATE.get("active_owner_id") or 0)

    if active_owner:
        old_owner = getattr(app, "owner", None)
        app.owner = active_owner
        if hasattr(config, "OWNER_ID"):
            config.OWNER_ID = active_owner
        if hasattr(app, "sudoers") and isinstance(app.sudoers, set):
            if old_owner and old_owner != active_owner:
                app.sudoers.discard(old_owner)
            app.sudoers.add(active_owner)
        if hasattr(app, "sudo_filter") and isinstance(app.sudo_filter, set):
            if old_owner and old_owner != active_owner:
                app.sudo_filter.discard(old_owner)
            app.sudo_filter.add(active_owner)

    for attr in ("SUPPORT_CHANNEL", "UPDATES_CHANNEL", "CHANNEL_URL"):
        if hasattr(config, attr):
            setattr(config, attr, updates_url)
    for attr in ("SUPPORT_CHAT", "SUPPORT_GROUP", "GROUP_URL"):
        if hasattr(config, attr):
            setattr(config, attr, support_url)
    for attr in ("OWNER_USERNAME", "OWNER_LINK"):
        if hasattr(config, attr):
            setattr(
                config,
                attr,
                owner_url if "LINK" in attr else owner_handle.lstrip("@"),
            )

    powered = f"🍓 <b>Powered By :</b> {owner_handle}"
    for mod_name, mod in list(sys.modules.items()):
        if not mod or "ArtistMusic.plugins." not in mod_name:
            continue
        if hasattr(mod, "OWNER_URL"):
            setattr(mod, "OWNER_URL", owner_url)
        if hasattr(mod, "UPDATES_URL"):
            setattr(mod, "UPDATES_URL", updates_url)
        if hasattr(mod, "SUPPORT_URL"):
            setattr(mod, "SUPPORT_URL", support_url)
        if hasattr(mod, "CHANNEL_HANDLE"):
            setattr(mod, "CHANNEL_HANDLE", updates_handle)
        if hasattr(mod, "POWERED_TEXT"):
            setattr(mod, "POWERED_TEXT", powered)


async def _load_state() -> None:
    global _LOADED
    try:
        doc = await _get_col().find_one({"_id": "brand_config"})
        if not doc:
            to_save = dict(_STATE)
            to_save["_id"] = "brand_config"
            await _get_col().insert_one(to_save)
        else:
            for k in list(_STATE.keys()):
                if k in doc and doc[k] is not None:
                    _STATE[k] = doc[k]
        _rebuild_patterns()
        _sync_live_modules()
        _LOADED = True
        logger.info("🛡️ MGB Live Brand Manager & Owner Recovery loaded.")
    except Exception as ex:
        logger.warning(f"⚠️ Brand Manager MongoDB load failed: {ex}")


async def _save_state() -> None:
    _rebuild_patterns()
    _sync_live_modules()
    to_save = dict(_STATE)
    to_save["updated_at"] = int(time.time())
    await _get_col().update_one(
        {"_id": "brand_config"},
        {"$set": to_save},
        upsert=True,
    )


# ----------------------------------------------------------
# Global Safe Outgoing Message & Button Replacer Hook
# ----------------------------------------------------------
def _apply_text_replace(text: Any) -> Any:
    if not _STATE.get("enabled", True) or not isinstance(text, str) or not text:
        return text
    out = text
    for pat, rep in _TEXT_PATTERNS:
        out = pat.sub(rep, out)
    return out


def _apply_url_replace(url: str, btn_label: str) -> str:
    if not url or not isinstance(url, str):
        return url

    label_up = (btn_label or "").upper()
    url_low = url.lower()

    if "startgroup=" in url_low or "start=" in url_low:
        return url

    if "OWNER" in label_up or "DEV" in label_up:
        return _STATE["owner_url"]
    if "UPDATE" in label_up or "CHANNEL" in label_up:
        return _STATE["updates_url"]
    if "SUPPORT" in label_up or ("GROUP" in label_up and "ADD" not in label_up):
        return _STATE["support_url"]

    out = url
    for pat, rep in _URL_PATTERNS:
        out = pat.sub(rep, out)
    return out


def _apply_markup_replace(markup: Any) -> Any:
    if not _STATE.get("enabled", True) or not isinstance(markup, InlineKeyboardMarkup):
        return markup
    try:
        new_rows = []
        changed = False
        for row in markup.inline_keyboard:
            new_row = []
            for btn in row:
                b_url = getattr(btn, "url", None)
                if b_url:
                    replaced_url = _apply_url_replace(b_url, getattr(btn, "text", ""))
                    if replaced_url != b_url:
                        cloned = copy.copy(btn)
                        cloned.url = replaced_url
                        new_row.append(cloned)
                        changed = True
                        continue
                new_row.append(btn)
            new_rows.append(new_row)
        return InlineKeyboardMarkup(new_rows) if changed else markup
    except Exception:
        return markup


def _install_global_hooks() -> None:
    global _PATCHED
    if _PATCHED or getattr(app, "_mgb_brand_patched", False):
        return

    target_methods = (
        "send_message",
        "send_photo",
        "send_video",
        "send_animation",
        "send_document",
        "send_audio",
        "edit_message_text",
        "edit_message_caption",
        "edit_message_reply_markup",
    )

    for m_name in target_methods:
        orig_fn = getattr(app, m_name, None)
        if not callable(orig_fn):
            continue
        sig = inspect.signature(orig_fn)

        def _make_wrapper(_orig=orig_fn, _sig=sig):
            async def _wrapped(*args, **kwargs):
                if _SKIP_REPLACE.get() or not _STATE.get("enabled", True):
                    return await _orig(*args, **kwargs)
                try:
                    bound = _sig.bind_partial(*args, **kwargs)
                    if "text" in bound.arguments and bound.arguments["text"]:
                        bound.arguments["text"] = _apply_text_replace(bound.arguments["text"])
                    if "caption" in bound.arguments and bound.arguments["caption"]:
                        bound.arguments["caption"] = _apply_text_replace(bound.arguments["caption"])
                    if "reply_markup" in bound.arguments and bound.arguments["reply_markup"]:
                        bound.arguments["reply_markup"] = _apply_markup_replace(
                            bound.arguments["reply_markup"]
                        )
                    return await _orig(*bound.args, **bound.kwargs)
                except Exception:
                    return await _orig(*args, **kwargs)

            return _wrapped

        setattr(app, m_name, _make_wrapper())

    app._mgb_brand_patched = True
    _PATCHED = True


_rebuild_patterns()
_install_global_hooks()


async def boot_brand_manager() -> None:
    _install_global_hooks()
    await _load_state()


try:
    asyncio.get_running_loop().call_soon(lambda: asyncio.create_task(_load_state()))
except RuntimeError:
    pass


@app.on_message(filters.all, group=-100)
async def _ensure_brand_loaded(_, __):
    if not _LOADED:
        await _load_state()


# ----------------------------------------------------------
# Panel Builder (Uniform 2x3 Colored HTML Buttons)
# ----------------------------------------------------------
def _build_brand_panel() -> Tuple[str, List[List[Dict[str, Any]]]]:
    enabled = bool(_STATE.get("enabled", True))
    active_owner = int(_STATE.get("active_owner_id") or getattr(config, "OWNER_ID", 0) or 0)
    custom_rules = _STATE.get("custom_rules") or {}
    has_recovery = bool((os.getenv("RECOVERY_KEY") or "").strip())

    rules_preview = ""
    if custom_rules:
        items = [
            f"   • <code>{k}</code> ➔ <code>{v}</code>"
            for k, v in list(custom_rules.items())[:8]
        ]
        rules_preview = "\n<b>Custom Replacements:</b>\n" + "\n".join(items) + "\n"

    text = (
        "<blockquote>🛡️ <b>MGB GLOBAL BRAND &amp; RECOVERY MANAGER</b></blockquote>\n\n"
        f"• <b>Global Auto-Replace:</b> {'🟢 ON' if enabled else '🔴 OFF'}\n"
        f"• <b>Active Owner ID:</b> <code>{active_owner}</code>\n"
        f"• <b>Emergency Key:</b> {'✅ SET' if has_recovery else '⚠️ Add RECOVERY_KEY in Render'}\n\n"
        "<b>Live Active Links (Poore Bot Mein):</b>\n"
        f"• <b>Owner:</b> <code>{_STATE['owner_handle']}</code>\n"
        f"• <b>Updates Channel:</b> <code>{_STATE['updates_handle']}</code>\n"
        f"• <b>Support Group:</b> <code>{_STATE['support_handle']}</code>\n"
        f"{rules_preview}\n"
        "<b>One-Command Updates:</b>\n"
        "• <code>/setall @owner @channel @group</code> — Sab 1 saath update\n"
        "• <code>/setchannel @newchannel</code> — Channel update\n"
        "• <code>/setgroup @newgroup</code> — Support group update\n"
        "• <code>/setownerlink @newowner</code> — Owner handle update\n"
        "• <code>/replace old | new</code> — Custom text/link replace\n"
        "• <code>/claimowner SECRET_KEY</code> — Ban recovery (DM)\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}"
    )

    rows = [
        [
            _hbtn(
                "⏸ STOP REPLACE" if enabled else "▶️ START REPLACE",
                callback_data="mgb_brand_toggle",
                style="danger" if enabled else "success",
            ),
            _hbtn("🔄 REFRESH", callback_data="mgb_brand_refresh", style="primary"),
        ],
        *_default_bottom_rows(),
    ]
    return text, rows
# ----------------------------------------------------------
# 1. /brand — Control Panel
# ----------------------------------------------------------
@app.on_message(filters.command(["brand", "brandpanel", "setlinks"]))
async def brand_panel_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return
    text, rows = _build_brand_panel()
    await _send_html_card(message, text, rows=rows)


@app.on_callback_query(filters.regex("^mgb_brand_(toggle|refresh)$"))
async def brand_panel_cb(_, cq: CallbackQuery):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(cq.from_user, "id", None)):
        return await cq.answer("Sirf Owner / Sudo users ke liye!", show_alert=True)

    action = cq.data.split("_")[-1]
    if action == "toggle":
        _STATE["enabled"] = not bool(_STATE.get("enabled", True))
        await _save_state()
        await cq.answer(
            "Global Brand Replace ON 🟢"
            if _STATE["enabled"]
            else "Global Brand Replace OFF 🔴",
            show_alert=True,
        )
    else:
        await _load_state()
        await cq.answer("Refreshed ✅")

    text, rows = _build_brand_panel()
    await _edit_html_card(cq, text, rows=rows)


# ----------------------------------------------------------
# 2. /setall — Ek Hi Command Se Owner + Channel + Group Update
# ----------------------------------------------------------
@app.on_message(filters.command("setall"))
async def set_all_links_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 4:
        return await _send_html_card(
            message,
            "<blockquote>⚡ <b>ALL-IN-ONE INSTANT UPDATE</b></blockquote>\n\n"
            "Ek hi command mein Owner, Updates Channel aur Support Group teeno badlein:\n"
            "<code>/setall @new_owner @new_channel @new_group</code>\n\n"
            "<i>(Private invite link <code>https://t.me/+xxxx</code> bhi chalega)</i>\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    try:
        o_handle, o_url, o_slug = _parse_tg_target(message.command[1])
        u_handle, u_url, u_slug = _parse_tg_target(message.command[2])
        s_handle, s_url, s_slug = _parse_tg_target(message.command[3])
    except ValueError as err:
        return await _send_html_card(
            message,
            f"<blockquote>❌ <b>INVALID LINK</b></blockquote>\n\n{err}\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    for key, old_val in (
        ("old_owner_slugs", _STATE["owner_handle"]),
        ("old_updates_slugs", _STATE["updates_handle"]),
        ("old_support_slugs", _STATE["support_handle"]),
    ):
        if old_val.startswith("@"):
            sl = old_val[1:]
            if sl not in _STATE[key]:
                _STATE[key].append(sl)

    _STATE["owner_handle"], _STATE["owner_url"] = o_handle, o_url
    _STATE["updates_handle"], _STATE["updates_url"] = u_handle, u_url
    _STATE["support_handle"], _STATE["support_url"] = s_handle, s_url

    for key, sl in (
        ("old_owner_slugs", o_slug),
        ("old_updates_slugs", u_slug),
        ("old_support_slugs", s_slug),
    ):
        if sl and sl not in _STATE[key]:
            _STATE[key].append(sl)

    await _save_state()
    text, rows = _build_brand_panel()
    await _send_html_card(
        message,
        "✅ <b>Owner, Updates Channel aur Support Group poore bot mein live update ho gaye!</b>\n\n"
        + text,
        rows=rows,
    )


# ----------------------------------------------------------
# 3. Quick Commands: /setchannel, /setgroup, /setownerlink
# ----------------------------------------------------------
@app.on_message(filters.command(["setchannel", "setupdate", "setupdates"]))
async def set_channel_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2:
        return await _send_html_card(
            message,
            "<blockquote>🚀 <b>UPDATE CHANNEL</b></blockquote>\n\n"
            "Use karein: <code>/setchannel @new_channel</code>\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    try:
        u_handle, u_url, u_slug = _parse_tg_target(message.command[1])
    except ValueError as err:
        return await _send_html_card(message, f"❌ {err}")

    old_val = _STATE["updates_handle"]
    if old_val.startswith("@") and old_val[1:] not in _STATE["old_updates_slugs"]:
        _STATE["old_updates_slugs"].append(old_val[1:])

    _STATE["updates_handle"], _STATE["updates_url"] = u_handle, u_url
    if u_slug and u_slug not in _STATE["old_updates_slugs"]:
        _STATE["old_updates_slugs"].append(u_slug)

    await _save_state()
    await _send_html_card(
        message,
        "<blockquote>✅ <b>UPDATES CHANNEL UPDATED</b></blockquote>\n\n"
        f"• <b>New Channel:</b> <code>{u_handle}</code>\n"
        f"• <b>URL:</b> <code>{u_url}</code>\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
    )


@app.on_message(filters.command(["setgroup", "setsupport"]))
async def set_group_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2:
        return await _send_html_card(
            message,
            "<blockquote>💬 <b>UPDATE SUPPORT GROUP</b></blockquote>\n\n"
            "Use karein: <code>/setgroup @new_group</code> ya <code>/setgroup https://t.me/+invite</code>\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    try:
        s_handle, s_url, s_slug = _parse_tg_target(message.command[1])
    except ValueError as err:
        return await _send_html_card(message, f"❌ {err}")

    old_val = _STATE["support_handle"]
    if old_val.startswith("@") and old_val[1:] not in _STATE["old_support_slugs"]:
        _STATE["old_support_slugs"].append(old_val[1:])

    _STATE["support_handle"], _STATE["support_url"] = s_handle, s_url
    if s_slug and s_slug not in _STATE["old_support_slugs"]:
        _STATE["old_support_slugs"].append(s_slug)

    await _save_state()
    await _send_html_card(
        message,
        "<blockquote>✅ <b>SUPPORT GROUP UPDATED</b></blockquote>\n\n"
        f"• <b>New Group:</b> <code>{s_handle}</code>\n"
        f"• <b>URL:</b> <code>{s_url}</code>\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
    )


@app.on_message(filters.command(["setownerlink", "setowneruser"]))
async def set_owner_link_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2:
        return await _send_html_card(
            message,
            "<blockquote>👑 <b>UPDATE OWNER LINK</b></blockquote>\n\n"
            "Use karein: <code>/setownerlink @new_owner_username</code>\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    try:
        o_handle, o_url, o_slug = _parse_tg_target(message.command[1])
    except ValueError as err:
        return await _send_html_card(message, f"❌ {err}")

    old_val = _STATE["owner_handle"]
    if old_val.startswith("@") and old_val[1:] not in _STATE["old_owner_slugs"]:
        _STATE["old_owner_slugs"].append(old_val[1:])

    _STATE["owner_handle"], _STATE["owner_url"] = o_handle, o_url
    if o_slug and o_slug not in _STATE["old_owner_slugs"]:
        _STATE["old_owner_slugs"].append(o_slug)

    await _save_state()
    await _send_html_card(
        message,
        "<blockquote>✅ <b>OWNER HANDLE UPDATED</b></blockquote>\n\n"
        f"• <b>New Owner:</b> <code>{o_handle}</code>\n"
        f"• <b>URL:</b> <code>{o_url}</code>\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
    )


# ----------------------------------------------------------
# 4. /replace & /delreplace — Custom Global Text/Link Replace
# ----------------------------------------------------------
@app.on_message(filters.command("replace"))
async def add_custom_replace_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    raw = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    if "|" not in raw:
        return await _send_html_card(
            message,
            "<blockquote>🔁 <b>CUSTOM GLOBAL REPLACE</b></blockquote>\n\n"
            "Kisi bhi purane text ya link ko poore bot mein badlein:\n"
            "<code>/replace purana_link | naya_link</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/replace @MGB_CODER | @NEW_MGB_CHANNEL</code>\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )

    old_s, new_s = [p.strip() for p in raw.split("|", 1)]
    if not old_s or not new_s:
        return await _send_html_card(message, "❌ Purana aur naya dono text dena zaroori hai.")

    _STATE.setdefault("custom_rules", {})[old_s] = new_s
    await _save_state()
    await _send_html_card(
        message,
        "<blockquote>✅ <b>GLOBAL REPLACE RULE SAVED</b></blockquote>\n\n"
        f"• <b>Old:</b> <code>{old_s}</code>\n"
        f"• <b>New:</b> <code>{new_s}</code>\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
    )


@app.on_message(filters.command("delreplace"))
async def del_custom_replace_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()
    if not _is_authorized(getattr(message.from_user, "id", None)):
        return

    if len(message.command) < 2:
        return await _send_html_card(
            message,
            "Use karein: <code>/delreplace purana_text</code>",
        )

    key = message.text.split(None, 1)[1].strip()
    rules = _STATE.get("custom_rules") or {}
    if key in rules:
        rules.pop(key)
        await _save_state()
        await _send_html_card(
            message,
            f"<blockquote>🗑 <b>RULE DELETED</b></blockquote>\n\n"
            f"Rule <code>{key}</code> remove kar diya gaya ✅\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        )
    else:
        await _send_html_card(message, f"⚠️ Rule <code>{key}</code> nahi mila.")


# ----------------------------------------------------------
# 5. /claimowner — Emergency Owner Takeover (Ban/Freeze Safe)
# ----------------------------------------------------------
@app.on_message(filters.command("claimowner"))
async def claim_owner_cmd(_, message: Message):
    if not _LOADED:
        await _load_state()

    await _safe_delete(message)

    if message.chat.type != enums.ChatType.PRIVATE:
        return await _send_html_card(
            message,
            "<blockquote>🔒 <b>PRIVATE DM ONLY</b></blockquote>\n\n"
            "Security ke liye <code>/claimowner</code> sirf bot ke <b>Private DM</b> mein bhejein!\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
            reply=False,
        )

    master_key = (os.getenv("RECOVERY_KEY") or "").strip()
    if not master_key:
        return await _send_html_card(
            message,
            "<blockquote>⚠️ <b>RECOVERY_KEY NOT SET</b></blockquote>\n\n"
            "Render Dashboard ➔ Environment mein <code>RECOVERY_KEY</code> add karein.\n\n"
            f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
            reply=False,
        )

    if len(message.command) < 2:
        return await _send_html_card(
            message,
            "Use karein: <code>/claimowner APNA_SECRET_KEY</code>",
            reply=False,
        )

    provided_key = message.text.split(None, 1)[1].strip()
    if not hmac.compare_digest(provided_key, master_key):
        return await _send_html_card(
            message,
            "<blockquote>❌ <b>ACCESS DENIED</b></blockquote>\n\n"
            "Galat Recovery Key!",
            reply=False,
        )

    new_owner = message.from_user
    _STATE["active_owner_id"] = new_owner.id

    if new_owner.username:
        old_val = _STATE["owner_handle"]
        if old_val.startswith("@") and old_val[1:] not in _STATE["old_owner_slugs"]:
            _STATE["old_owner_slugs"].append(old_val[1:])
        _STATE["owner_handle"] = f"@{new_owner.username}"
        _STATE["owner_url"] = f"https://t.me/{new_owner.username}"
        if new_owner.username not in _STATE["old_owner_slugs"]:
            _STATE["old_owner_slugs"].append(new_owner.username)

    await _save_state()
    await _send_html_card(
        message,
        "<blockquote>🚨 <b>EMERGENCY OWNER RECOVERY SUCCESSFUL</b></blockquote>\n\n"
        f"• <b>New Active Owner:</b> {new_owner.mention} (<code>{new_owner.id}</code>)\n"
        f"• <b>New Owner Link:</b> <code>{_STATE['owner_handle']}</code>\n"
        "• <b>Old Banned Account Access:</b> Removed ✅\n"
        "• <b>MongoDB Saved:</b> Yes (Restart-Safe ✅)\n\n"
        "<b>Ab turant saare links update karein:</b>\n"
        "<code>/setall @new_owner @new_channel @new_group</code>\n\n"
        f"🍓 <b>Powered By :</b> {_STATE['owner_handle']}",
        reply=False,
    )
