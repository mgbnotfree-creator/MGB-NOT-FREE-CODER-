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

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ArtistMusic import app, config, lang

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
        self.ikm = InlineKeyboardMarkup
        self.ikb = InlineKeyboardButton

    def cancel_dl(self, text) -> InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=f"❌  {text}", callback_data="cancel_dl")]])

    def controls(self, chat_id: int, status: str = None, timer: str = None, remove: bool = False) -> InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append([self.ikb(text=f"{status}", callback_data=f"controls status {chat_id}")])
        elif timer:
            keyboard.append([self.ikb(text=f"{timer}", callback_data=f"controls status {chat_id}")])

        if not remove:
            keyboard.append([
                self.ikb(text="⏸️ ᴘᴀᴜꜱᴇ", callback_data=f"controls pause {chat_id}"),
                self.ikb(text="▶️ ʀᴇꜱᴜᴍᴇ", callback_data=f"controls resume {chat_id}"),
                self.ikb(text="🔁 ʟᴏᴏᴘ", callback_data=f"controls replay {chat_id}"),
                self.ikb(text="⏭️ ꜱᴋɪᴘ", callback_data=f"controls skip {chat_id}"),
                self.ikb(text="⏹️ ꜱᴛᴏᴘ", callback_data=f"controls stop {chat_id}"),
            ])
            from ArtistMusic import db
            ap_on = chat_id in db.autoplay_on
            keyboard.append([
                self.ikb(text="🟢 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏɴ" if ap_on else "🔴 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏꜰꜰ", callback_data=f"controls autoplay {chat_id}"),
                self.ikb(text="🚨 ᴄʟᴏꜱᴇ 🚨", callback_data=f"controls close {chat_id}")
            ])
        return self.ikm(keyboard)

    def help_markup(self, _lang: dict, back: bool = False) -> InlineKeyboardMarkup:
        if back:
            return self.ikm([[self.ikb(text="« ʙᴀᴄᴋ", callback_data="help_main")]])
        else:
            _btns = [self.ikb(text=_label, callback_data=f"help_{_key}") for _key, _label, _ in HELP_GROUPS]
            rows = [_btns[n:n + 3] for n in range(0, len(_btns), 3)]
            rows.append([self.ikb(text="❌ ᴄʟᴏꜱᴇ", callback_data="start")])
            return self.ikm(rows)

    def help_text(self, _lang: dict, category: str):
        for _key, _label, _srcs in HELP_GROUPS:
            if _key == category:
                parts = [_lang.get(f"help_{k}") for k in _srcs]
                parts = [p for p in parts if p]
                return "\n\n".join(parts) if parts else None
        return None

    def langs_markup(self) -> InlineKeyboardMarkup:
        langs = [
            ("🇺🇸 English",    "en"), ("🇮🇳 Hindi",      "hi"), ("🇮🇳 Telugu",     "te"),
            ("🇰🇷 Korean",     "ko"), ("🇲🇲 Myanmar",    "my"), ("🇮🇩 Indonesian", "id"),
        ]
        rows = []
        for i in range(0, len(langs), 2):
            row = [self.ikb(text=langs[i][0], callback_data=f"setlang_{langs[i][1]}")]
            if i + 1 < len(langs):
                row.append(self.ikb(text=langs[i+1][0], callback_data=f"setlang_{langs[i+1][1]}"))
            rows.append(row)
        rows.append([self.ikb(text="« ʙᴀᴄᴋ", callback_data="start")])
        return self.ikm(rows)

    def ping_markup(self, text: str) -> InlineKeyboardMarkup:
        return self.ikm([
            [self.ikb(text=f"{text}", callback_data="ping_refresh")],
            [
                self.ikb(text="💠 ꜱᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT),
                self.ikb(text="🌐 ᴜᴘᴅᴀᴛᴇꜱ", url=config.SUPPORT_CHANNEL)
            ],
            [self.ikb(text="⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", url=f"https://t.me/{app.username}?startgroup=true")]
        ])

    def play_queued(self, chat_id: int, item_id: str, _text: str) -> InlineKeyboardMarkup:
        return self.ikm([[
            self.ikb(text="▶️", callback_data=f"controls resume {chat_id} {item_id}"),
            self.ikb(text="⏸️", callback_data=f"controls pause {chat_id} {item_id}"),
            self.ikb(text="🔁", callback_data=f"controls replay {chat_id} {item_id}"),
            self.ikb(text="⏭️", callback_data=f"controls skip {chat_id} {item_id}"),
            self.ikb(text="⏹️", callback_data=f"controls stop {chat_id} {item_id}"),
        ]])

    def queue_markup(self, chat_id: int, _text: str, playing: bool) -> InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm([[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]])

    def settings_markup(self, _lang: dict, admin_only: bool, force_admin: bool, language: str, chat_id: int) -> InlineKeyboardMarkup:
        return self.ikm([
            [self.ikb(text="  " + _lang["play_mode"], callback_data=f"controls status {chat_id}")],
            [self.ikb(text="" + language.upper(), callback_data="help_langs")]
        ])

    # 🔥 MGB Start Menu - BLUE THEME DESIGN 🔵 🔥
    def start_key(self, _lang: dict, private: bool = False) -> InlineKeyboardMarkup:
        return self.ikm([
            [self.ikb(text="⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", url=f"https://t.me/{app.username}?startgroup=true")],
            [
                self.ikb(text="💠 ꜱᴜᴘᴘᴏʀᴛ 💠", url=config.SUPPORT_CHAT),
                self.ikb(text="🌐 ᴜᴘᴅᴀᴛᴇꜱ 🌐", url=config.SUPPORT_CHANNEL)
            ],
            [self.ikb(text="📘 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ 📘", callback_data="help")],
            [
                self.ikb(text="🫂 ᴏᴡɴᴇʀ 🫂", url=f"tg://user?id={config.OWNER_ID}"),
                self.ikb(text="💻 ᴘᴀʏᴍᴇɴᴛ Qʀ ↗", url="https://github.com/user-attachments/assets/52db898f-cd48-402b-863b-4226ec462f1c")
            ],
            [self.ikb(text="🔵 ʀɪʏᴀ ᴍᴜꜱɪᴄ ʙᴏᴛ 🔵", url="https://t.me/RIYA_MUSIC_BOT_786")],
            [self.ikb(text="🟦 ꜱʜɪᴢᴜ ᴍᴜꜱɪᴄ 🟦", url="https://t.me/MGB_NOT_FREE_BOSS_BOT")],
            [self.ikb(text="🌍 ʟᴀɴɢᴜᴀɢᴇ", callback_data="help_langs")]
        ])

    def yt_key(self, link: str) -> InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="👀 ᴡᴀᴛᴄʜ", url=link),
                self.ikb(text="📥 ᴅᴏᴡɴʟᴏᴀᴅ", url=link)
            ]
        ])
