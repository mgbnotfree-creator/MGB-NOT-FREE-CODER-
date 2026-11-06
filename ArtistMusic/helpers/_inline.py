# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : MGB API Telegram Music Bot
# Powered By   : ❖ MGB NOT FREE ❖
# Type         : API Based Telegram Music Bot
#
# Bot          : @Yasmeen_api_bot
# Channel      : https://t.me/MGB_CODER
# ==========================================================

import random
from typing import Optional
from ArtistMusic import app, config, lang

def _tg_btn(text: str, callback_data: str, style: Optional[str] = None) -> str:
    style_attr = f' style="{style}"' if style else ""
    return f'<tg-button type="callback_data"{style_attr} data="{callback_data}">{text}</tg-button>'

def _url_btn(text: str, url: str, style: Optional[str] = None) -> str:
    style_attr = f' style="{style}"' if style else ""
    return f'<tg-button type="url"{style_attr} url="{url}">{text}</tg-button>'

def _row(*buttons: str) -> str:
    return "<tg-button-row>" + "".join(buttons) + "</tg-button-row>"

def random_style() -> str:
    return random.choice(["success", "danger", "primary"])

# ---------------------------------------------------------
# HELP MENU GROUPS
# ---------------------------------------------------------
HELP_GROUPS = [
    ("play",        "▶️ Play",           ["play"]),
    ("playback",    "⏸️ Playback",        ["pause", "resume", "skip", "stop"]),
    ("seek",        "⏩ Seek/Loop",      ["seek", "loop", "shuffle"]),
    ("queue",       "📋 Queue",          ["queue", "autoplay"]),
    ("playmode",    "⚙️ Playmode",       ["playmode", "link", "autoleave"]),
    ("ban",         "🚫 Ban",            ["ban", "gban"]), 
    ("mute",        "🔇 Mute",           ["mute", "mass"]),
    ("promote",     "⭐ Promote",        ["promote", "auth"]), 
    ("group",       "👥 Group",          ["group", "welcome"]), 
    ("clean",       "🧹 Clean",          ["purge", "zombies"]),
    ("tag",         "🏷️ Tag All",        ["tag"]),
    ("sticker",     "🎨 Stickers",       ["sticker"]),
    ("info",        "ℹ️ Info",           ["info", "bots"]),
    ("sudo",        "👑 Sudo",           ["sudo"]),
    ("broadcast",   "📢 Broadcast",      ["broadcast"]),
    ("blacklist",   "⛔ Blacklist",      ["blchat", "bluser"]),
    ("maintenance", "🛠️ Maintenance",    ["maintenance"]),
    ("active",      "📊 Active VCs",     ["active", "logs"]),
    ("restart",     "🔄 Restart",        ["restart", "leave"]),
    ("eval",        "💻 Eval",           ["eval"]),
    ("ping",        "🏓 Ping",           ["ping", "stats"]),
]

class Inline:
    def __init__(self):
        pass

    def cancel_dl(self, text) -> str:
        return _row(_tg_btn(f"❌  {text}", "cancel_dl", "danger"))

    # प्लेयर कंट्रोल्स
    def controls(self, chat_id: int, status: str = None, timer: str = None, remove: bool = False) -> str:
        html = ""
        if status:
            html += _row(_tg_btn(f"{status}", f"controls status {chat_id}", "primary"))
        elif timer:
            html += _row(_tg_btn(f"{timer}", f"controls status {chat_id}", "primary"))

        if not remove:
            html += _row(
                _tg_btn("⏸️ ᴘᴀᴜꜱᴇ", f"controls pause {chat_id}", random_style()),
                _tg_btn("▶️ ʀᴇꜱᴜᴍᴇ", f"controls resume {chat_id}", random_style()),
                _tg_btn("🔁 ʟᴏᴏᴘ", f"controls replay {chat_id}", random_style()),
                _tg_btn("⏭️ ꜱᴋɪᴘ", f"controls skip {chat_id}", random_style()),
                _tg_btn("⏹️ ꜱᴛᴏᴘ", f"controls stop {chat_id}", random_style()),
            )
            from ArtistMusic import db
            ap_on = chat_id in db.autoplay_on
            html += _row(
                _tg_btn("🟢 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏɴ" if ap_on else "🔴 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏꜰꜰ", f"controls autoplay {chat_id}", "success"),
                _tg_btn("🚨 ᴄʟᴏꜱᴇ 🚨", f"controls close {chat_id}", "danger")
            )
        return html

    def help_markup(self, _lang: dict, back: bool = False) -> str:
        if back:
            return _row(_tg_btn("« ʙᴀᴄᴋ", "help_main", "success"))
        else:
            _btns = [_tg_btn(_label, f"help_{_key}", "primary") for _key, _label, _ in HELP_GROUPS]
            rows = [_row(*_btns[n:n + 3]) for n in range(0, len(_btns), 3)]
            rows.append(_row(_tg_btn("❌ ᴄʟᴏꜱᴇ", "start", "danger")))
            return "".join(rows)

    def help_text(self, _lang: dict, category: str):
        for _key, _label, _srcs in HELP_GROUPS:
            if _key == category:
                parts = [_lang.get(f"help_{k}") for k in _srcs]
                parts = [p for p in parts if p]
                return "\n\n".join(parts) if parts else None
        return None

    def langs_markup(self) -> str:
        langs = [
            ("🇺🇸 English",    "en"), ("🇮🇳 Hindi",      "hi"),
            ("🇮🇳 Telugu",     "te"), ("🇰🇷 Korean",     "ko"),
            ("🇲🇲 Myanmar",    "my"), ("🇮🇩 Indonesian", "id"),
            ("🇵🇹 Portuguese", "pt"), ("🇸🇦 Arabic",     "ar"),
            ("🇪🇸 Spanish",    "es"), ("🇫🇷 French",     "fr"),
            ("🇷🇺 Russian",    "ru"), ("🇩🇪 German",     "de"),
            ("🇹🇷 Turkish",    "tr"), ("🇧🇩 Bengali",    "bn"),
            ("🇹🇭 Thai",       "th"), ("🇻🇳 Vietnamese", "vi"),
            ("🇯🇵 Japanese",   "ja"), ("🇨🇳 Chinese",    "zh"),
            ("🇵🇰 Urdu",       "ur"), ("🇮🇷 Persian",    "fa"),
            ("🇮🇳 Bhojpuri",   "bho"), ("🇳🇵 Nepali",     "ne"),
        ]
        html = ""
        for i in range(0, len(langs), 2):
            if i + 1 < len(langs):
                html += _row(
                    _tg_btn(langs[i][0], f"setlang_{langs[i][1]}", "primary"),
                    _tg_btn(langs[i+1][0], f"setlang_{langs[i+1][1]}", "primary")
                )
            else:
                html += _row(_tg_btn(langs[i][0], f"setlang_{langs[i][1]}", "primary"))
        html += _row(_tg_btn("« ʙᴀᴄᴋ", "start", "success"))
        return html

    def ping_markup(self, text: str) -> str:
        return (
            _row(_tg_btn(f"{text}", "ping_refresh", "primary"))
            + _row(
                _url_btn("🌸 ꜱᴜᴘᴘᴏʀᴛ", config.SUPPORT_CHAT, random_style()),
                _url_btn("🍹 ᴜᴘᴅᴀᴛᴇꜱ", config.SUPPORT_CHANNEL, random_style())
            )
            + _row(_url_btn("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", f"https://t.me/{app.username}?startgroup=true", "success"))
        )

    def play_queued(self, chat_id: int, item_id: str, _text: str) -> str:
        return _row(
            _tg_btn("▶️", f"controls resume {chat_id} {item_id}", "primary"),
            _tg_btn("⏸️", f"controls pause {chat_id} {item_id}", "primary"),
            _tg_btn("🔁", f"controls replay {chat_id} {item_id}", "primary"),
            _tg_btn("⏭️", f"controls skip {chat_id} {item_id}", "primary"),
            _tg_btn("⏹️", f"controls stop {chat_id} {item_id}", "primary"),
        )

    def queue_markup(self, chat_id: int, _text: str, playing: bool) -> str:
        _action = "pause" if playing else "resume"
        return _row(_tg_btn(_text, f"controls {_action} {chat_id} q", "success"))

    def settings_markup(self, _lang: dict, admin_only: bool, force_admin: bool, language: str, chat_id: int) -> str:
        play_mode_txt  = _lang["admin_only_txt"] if admin_only  else _lang["everyone"]
        force_mode_txt = _lang["admin_only_txt"] if force_admin else _lang["everyone"]
        return (
            _row(
                _tg_btn("  " + _lang["play_mode"], f"controls status {chat_id}", "primary"),
                _tg_btn(play_mode_txt, "playmode", "success")
            )
            + _row(
                _tg_btn("  " + _lang["force_mode"], f"controls status {chat_id}", "primary"),
                _tg_btn(force_mode_txt, "forcemode", "success")
            )
            + _row(_tg_btn("" + language.upper(), "help_langs", "primary"))
        )

    # MGB Start Menu
    def start_key(self, _lang: dict, private: bool = False) -> str:
        return (
            _row(_url_btn("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", f"https://t.me/{app.username}?startgroup=true", random_style()))
            + _row(
                _url_btn("🌸 ꜱᴜᴘᴘᴏʀᴛ 🌸", config.SUPPORT_CHAT, random_style()),
                _url_btn("🍹 ᴜᴘᴅᴀᴛᴇꜱ 🍹", config.SUPPORT_CHANNEL, random_style())
            )
            + _row(_tg_btn("🏨 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ 🏨", "help", random_style()))
            + _row(
                _url_btn("🫂 ᴏᴡɴᴇʀ 🫂", f"tg://user?id={config.OWNER_ID}", random_style()),
                _url_btn("💻 ᴘᴀʏᴍᴇɴᴛ Qʀ ↗", "https://github.com/user-attachments/assets/52db898f-cd48-402b-863b-4226ec462f1c", random_style())
            )
            + _row(_url_btn("💖 ʀɪʏᴀ ᴍᴜꜱɪᴄ ʙᴏᴛ", "https://t.me/RIYA_MUSIC_BOT_786", random_style()))
            + _row(_url_btn("🎵 ꜱʜɪᴢᴜ ᴍᴜꜱɪᴄ 🎵", "https://t.me/MGB_NOT_FREE_BOSS_BOT", random_style()))
            + _row(_tg_btn("🌐 ʟᴀɴɢᴜᴀɢᴇ", "help_langs", random_style()))
        )

    def yt_key(self, link: str) -> str:
        return _row(
            _url_btn("👀 ᴡᴀᴛᴄʜ", link, "primary"),
            _url_btn("📥 ᴅᴏᴡɴʟᴏᴀᴅ", link, "danger")
  )
