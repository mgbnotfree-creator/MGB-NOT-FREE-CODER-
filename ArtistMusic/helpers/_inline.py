# ==========================================================
# Copyright (c) 2026 MGB NOT FREE CODER
# All Rights Reserved.
#
# Project      : MGB API Telegram Music Bot
# Powered By   : ❖ MGB NOT FREE ❖
# Type         : API Based Telegram Music Bot
#
# Bot          : @Yasmeen_api_bot
# Channel      : https://t.me/MGB_CODER
# ==========================================================
from pyrogram import types
from pyrogram.enums import ButtonStyle

from ArtistMusic import app, config, lang

# ---------------------------------------------------------
# HELP MENU: 21 buttons (merged groups)
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
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[
            self.ikb(
                text=f"❌  {text}",
                callback_data="cancel_dl",
                style=ButtonStyle.DANGER,
            )
        ]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []

        if status:
            keyboard.append(
                [self.ikb(
                    text=f"{status}",
                    callback_data=f"controls status {chat_id}",
                    style=ButtonStyle.PRIMARY,
                )]
            )
        elif timer:
            keyboard.append(
                [self.ikb(
                    text=f"{timer}",
                    callback_data=f"controls status {chat_id}",
                    style=ButtonStyle.PRIMARY,
                )]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="⏸️",  callback_data=f"controls pause {chat_id}",  style=ButtonStyle.PRIMARY),
                    self.ikb(text="▶️",   callback_data=f"controls resume {chat_id}", style=ButtonStyle.PRIMARY),
                    self.ikb(text="🔁",   callback_data=f"controls replay {chat_id}", style=ButtonStyle.PRIMARY),
                    self.ikb(text="⏭️", callback_data=f"controls skip {chat_id}",   style=ButtonStyle.PRIMARY),
                    self.ikb(text="⏹️",   callback_data=f"controls stop {chat_id}",   style=ButtonStyle.PRIMARY),
                ]
            )
            from ArtistMusic import db
            ap_on = chat_id in db.autoplay_on
            keyboard.append(
                [
                    self.ikb(
                        text="🟢 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏɴ" if ap_on else "🔴 ᴀᴜᴛᴏᴘʟᴀʏ : ᴏꜰꜰ",
                        callback_data=f"controls autoplay {chat_id}",
                        style=ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="🚨 ᴄʟᴏꜱᴇ 🚨",
                        callback_data=f"controls close {chat_id}",
                        style=ButtonStyle.DANGER,
                    ),
                ]
            )

        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [self.ikb(
                    text="« ʙᴀᴄᴋ",
                    callback_data="help_main",
                    style=ButtonStyle.SUCCESS,
                )]
            ]
        else:
            _btns = [
                self.ikb(
                    text=_label,
                    callback_data=f"help_{_key}",
                    style=ButtonStyle.PRIMARY,
                )
                for _key, _label, _ in HELP_GROUPS
            ]
            rows = [_btns[n:n + 3] for n in range(0, len(_btns), 3)]
            rows.append([
                self.ikb(
                    text="❌ ᴄʟᴏꜱᴇ",
                    callback_data="start",
                    style=ButtonStyle.SUCCESS,
                )
            ])
        return self.ikm(rows)

    def help_text(self, _lang: dict, category: str):
        for _key, _label, _srcs in HELP_GROUPS:
            if _key == category:
                parts = [_lang.get(f"help_{k}") for k in _srcs]
                parts = [p for p in parts if p]
                return "\n\n".join(parts) if parts else None
        return None

    def langs_markup(self) -> types.InlineKeyboardMarkup:
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
        rows = []
        for i in range(0, len(langs), 2):
            row = [self.ikb(text=langs[i][0], callback_data=f"setlang_{langs[i][1]}", style=ButtonStyle.PRIMARY)]
            if i + 1 < len(langs):
                row.append(self.ikb(text=langs[i + 1][0], callback_data=f"setlang_{langs[i + 1][1]}", style=ButtonStyle.PRIMARY))
            rows.append(row)
        rows.append([self.ikb(
            text="« ʙᴀᴄᴋ",
            callback_data="start",
            style=ButtonStyle.SUCCESS,
        )])
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(
                    text=f"{text}",
                    callback_data="ping_refresh",
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                self.ikb(text="🌸 ꜱᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHANNEL, style=ButtonStyle.PRIMARY),
                self.ikb(text="🍹 ᴜᴘᴅᴀᴛᴇꜱ",  url=config.SUPPORT_CHAT,    style=ButtonStyle.PRIMARY),
            ],
            [
                self.ikb(
                    text="⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.SUCCESS,
                ),
            ],
        ])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="▶️",   callback_data=f"controls resume {chat_id} {item_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="⏸️",  callback_data=f"controls pause {chat_id} {item_id}",  style=ButtonStyle.PRIMARY),
                self.ikb(text="🔁",   callback_data=f"controls replay {chat_id} {item_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="⏭️", callback_data=f"controls skip {chat_id} {item_id}",   style=ButtonStyle.PRIMARY),
                self.ikb(text="⏹️",   callback_data=f"controls stop {chat_id} {item_id}",   style=ButtonStyle.PRIMARY),
            ],
        ])

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(
                text=_text,
                callback_data=f"controls {_action} {chat_id} q",
                style=ButtonStyle.SUCCESS,
            )]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, force_admin: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        play_mode_txt  = lang["admin_only_txt"] if admin_only  else lang["everyone"]
        force_mode_txt = lang["admin_only_txt"] if force_admin else lang["everyone"]
        return self.ikm([
            [
                self.ikb(text="  " + lang["play_mode"],  callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text=play_mode_txt,              callback_data="playmode",                   style=ButtonStyle.SUCCESS),
            ],
            [
                self.ikb(text="  " + lang["force_mode"], callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text=force_mode_txt,             callback_data="forcemode",                  style=ButtonStyle.SUCCESS),
            ],
            [
                self.ikb(text="" + language.upper(),  callback_data="help_langs", style=ButtonStyle.PRIMARY),
            ],
        ])

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text="" + lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.PRIMARY,
                )
            ],
            [
                self.ikb(text="  " + lang["help"],  callback_data="help"),
            ],
            [
                self.ikb(text="  " + lang["support"], url=config.SUPPORT_CHAT),
                self.ikb(text=" " + lang["channel"], url=config.SUPPORT_CHANNEL),
            ],
            [
                self.ikb(text="👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/MGB_NOT_FREE"),
                self.ikb(text="🎵 ꜱʜɪᴢᴜ ᴍᴜꜱɪᴄ", url="https://t.me/MGB_NOT_FREE_BOSS_BOT"),
            ],
            [
                self.ikb(text="🌐 LANGUAGE",  callback_data="help_langs"),
            ],
        ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="👀 ᴡᴀᴛᴄʜ",     copy_text=link, style=ButtonStyle.PRIMARY),
                self.ikb(text="📥 ᴅᴏᴡɴʟᴏᴀᴅ", url=link,       style=ButtonStyle.DANGER),
            ],
        ])
