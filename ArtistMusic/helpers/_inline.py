import time
from pyrogram import types
from pyrogram.enums import ButtonStyle

from ArtistMusic import app, config, lang

# ---------------------------------------------------------
# 🎨 SMART DYNAMIC COLORS & TIMER (VelocityBots Style)
# ---------------------------------------------------------

def _time_format(sec: int, duration: int) -> str:
    sec = max(0, int(sec or 0))
    return time.strftime("%H:%M:%S" if duration >= 3600 else "%M:%S", time.gmtime(sec))

def progress_text(played_sec: int, duration_sec: int) -> str:
    """लाइव टाइमर और लोडिंग बार बनाता है (जैसे 01:20 ━━●━━━ 04:30)"""
    if duration_sec <= 0:
        return "LIVE"
    played = max(0, min(played_sec, duration_sec))
    n = 14
    filled = int(round(n * played / duration_sec))
    bar = "━" * filled + "●" + "━" * (n - filled)
    return f"{_time_format(played, duration_sec)} {bar} {_time_format(duration_sec, duration_sec)}"

def _styles(playing: bool):
    """हर 5 सेकंड में बटन्स का रंग घुमाता है!"""
    phase = int(time.time() // 5) % 4 if playing else 0
    palettes = (
        ("success", "primary", "danger", "success"),
        ("primary", "success", "success", "danger"),
        ("danger", "primary", "success", "primary"),
        ("success", "danger", "primary", "success"),
    )
    return palettes[phase]


# ---------------------------------------------------------
# HELP MENU: 21 buttons with custom style symbols & emojis
# ---------------------------------------------------------
HELP_GROUPS = [
    ("play",        "𓇼 Play",           ["play"]),
    ("playback",    "🐚 Playback",       ["pause", "resume", "skip", "stop"]),
    ("seek",        "𖤍 Seek/Loop",      ["seek", "loop", "shuffle"]),
    ("queue",       "×̷̷͜×̷ Queue",        ["queue", "autoplay"]),
    ("playmode",    "𓆩♛𓆪 Playmode",     ["playmode", "link", "autoleave"]),
    ("ban",         "𝄞 Ban",            ["ban", "gban"]),
    ("mute",        "🦋 Mute",           ["mute", "mass"]),
    ("promote",     "🕷 Promote",       ["promote", "auth"]),
    ("group",       "✿ Group",          ["group", "welcome"]),
    ("clean",       "𖤓 Clean",          ["purge", "zombies"]),
    ("tag",         "𓇼 Tag All",        ["tag"]),
    ("sticker",     "🐚 Stickers",      ["sticker"]),
    ("info",        "𖤍 Info",           ["info", "bots"]),
    ("sudo",        "×̷̷͜×̷ Sudo",         ["sudo"]),
    ("broadcast",   "𓆩♛𓆪 Broadcast",    ["broadcast"]),
    ("blacklist",   "𝄞 Blacklist",      ["blchat", "bluser"]),
    ("maintenance", "🦋 Maintenance",   ["maintenance"]),
    ("active",      "🕷 Active VCs",    ["active", "logs"]),
    ("restart",     "✿ Restart",        ["restart", "leave"]),
    ("eval",        "𖤓 Eval",           ["eval"]),
    ("ping",        "𓇼 Ping",           ["ping", "stats"]),
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

    # 🚀 1. NEW SMART HTML PLAYER CONTROLS (कलरफुल टाइमर और HTML वाले बटन)
    def controls_html(
        self, chat_id: int, played_sec: int = 0, duration_sec: int = 0, playing: bool = True
    ) -> str:
        """यह आपका नया HTML प्लेयर कंट्रोल है!"""
        time_style, replay_style, state_style, queue_style = _styles(playing)
        state = "pause" if playing else "resume"
        label = "II Pause" if playing else "▷ Resume"
        p = progress_text(played_sec, duration_sec)
        
        from ArtistMusic import db
        ap_on = chat_id in db.autoplay_on
        ap_label = "AUTOPLAY : ON" if ap_on else "AUTOPLAY : OFF"
        ap_style = "success" if ap_on else "primary"
        
        return (
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="{time_style}" data="controls status {chat_id}">{p}</tg-button>'
            f'</tg-button-row>'
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="{state_style}" data="controls {state} {chat_id}">{label}</tg-button>'
            f'<tg-button type="callback_data" style="{time_style}" data="controls replay {chat_id}">↻ Replay</tg-button>'
            f'<tg-button type="callback_data" style="{replay_style}" data="controls skip {chat_id}">⚠︎ Skip</tg-button>'
            f'<tg-button type="callback_data" style="{queue_style}" data="controls stop {chat_id}">▢ Stop</tg-button>'
            f'</tg-button-row>'
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="{ap_style}" data="controls autoplay {chat_id}">{ap_label}</tg-button>'
            f'<tg-button type="callback_data" style="danger" data="controls close {chat_id}">• CLOSE •</tg-button>'
            f'</tg-button-row>'
        )

    # 🛑 2. OLD NORMAL CONTROLS (बॉट को क्रैश होने से बचाने के लिए बैकअप)
    def controls(
        self, chat_id: int, status: str = None, timer: str = None, remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        """यह पुराना नॉर्मल प्लेयर कंट्रोल है जो बॉट को क्रैश होने से बचाएगा।"""
        keyboard = []
        if status:
            keyboard.append([self.ikb(text=f"{status}", callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY)])
        elif timer:
            keyboard.append([self.ikb(text=f"{timer}", callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY)])
        if not remove:
            keyboard.append([
                self.ikb(text="II", callback_data=f"controls pause {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="▷", callback_data=f"controls resume {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="↻", callback_data=f"controls replay {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="⚠︎", callback_data=f"controls skip {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="▢", callback_data=f"controls stop {chat_id}", style=ButtonStyle.PRIMARY),
            ])
            from ArtistMusic import db
            ap_on = chat_id in db.autoplay_on
            keyboard.append([
                self.ikb(text="AUTOPLAY : ON" if ap_on else "AUTOPLAY : OFF", callback_data=f"controls autoplay {chat_id}", style=ButtonStyle.SUCCESS),
                self.ikb(text="• CLOSE •", callback_data=f"controls close {chat_id}", style=ButtonStyle.DANGER),
            ])
        return self.ikm(keyboard)


    # 🎨 3. COLORFUL HTML HELP MENU (VelocityBots Style HTML Buttons)
    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> str:
        """हेल्प मेन्यू के लिए कलरफुल HTML बटन्स (3-3 के ग्रिड में)"""
        if back:
            return (
                f'<tg-button-row align="center">'
                f'<tg-button type="callback_data" style="success" data="help_main">« ʙᴀᴄᴋ</tg-button>'
                f'</tg-button-row>'
            )
        
        rows_html = ""
        batch_size = 3
        for i in range(0, len(HELP_GROUPS), batch_size):
            chunk = HELP_GROUPS[i:i + batch_size]
            row_buttons = ""
            for idx, (_key, _label, _) in enumerate(chunk):
                style = "success" if (i + idx) % 3 == 1 else ("danger" if (i + idx) % 3 == 2 else "primary")
                row_buttons += f'<tg-button type="callback_data" style="{style}" data="help_{_key}">{_label}</tg-button>'
            rows_html += f'<tg-button-row align="center">{row_buttons}</tg-button-row>'
        
        rows_html += (
            f'<tg-button-row align="center">'
            f'<tg-button type="callback_data" style="danger" data="start">❌ ᴄʟᴏꜱᴇ</tg-button>'
            f'</tg-button-row>'
        )
        return rows_html

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
                self.ikb(text="🍹 ᴜᴘᴅᴧᴛᴇꜱ",  url=config.SUPPORT_CHAT,    style=ButtonStyle.PRIMARY),
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
                self.ikb(text="▷",   callback_data=f"controls resume {chat_id} {item_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="II",  callback_data=f"controls pause {chat_id} {item_id}",  style=ButtonStyle.PRIMARY),
                self.ikb(text="↻",   callback_data=f"controls replay {chat_id} {item_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text="⏯",   callback_data=f"controls skip {chat_id} {item_id}",   style=ButtonStyle.PRIMARY),
                self.ikb(text="▢",   callback_data=f"controls stop {chat_id} {item_id}",   style=ButtonStyle.PRIMARY),
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
    
