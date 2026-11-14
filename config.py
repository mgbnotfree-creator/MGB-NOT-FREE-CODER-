# ========================================================== 
# Copyright (c) 2026 MGB Coder
# All Rights Reserved.
#
# Project      : MGB Coder Telegram Music Bot
# Powered By   : MGB NOT FREE CODER 
# Type         : API Based Telegram Music Bot
#
# Channel      : https://t.me/MGB_CODER
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
from os import getenv
from typing import List
from dotenv import load_dotenv

load_dotenv()

# आपकी सारी Start Images का कलेक्शन
MGB_START_IMAGES = " ".join([
    "https://i.ibb.co/8nyBbj1G/uploaded-image.jpg", "https://i.ibb.co/Q7DqP4r1/uploaded-image.jpg",
    "https://i.ibb.co/kgn1FNnB/uploaded-image.jpg", "https://i.ibb.co/jvTydJjy/uploaded-image.jpg",
    "https://i.ibb.co/rGBPnMxB/uploaded-image.jpg", "https://i.ibb.co/spzdNgV1/uploaded-image.jpg",
    "https://i.ibb.co/LXMH418p/uploaded-image.jpg", "https://i.ibb.co/Cp5NVjvx/uploaded-image.jpg",
    "https://i.ibb.co/9Hp2dHMs/uploaded-image.jpg", "https://i.ibb.co/WNbHdS37/uploaded-image.jpg",
    "https://i.ibb.co/mVnMtcHZ/uploaded-image.jpg", "https://i.ibb.co/xtp0rdwq/uploaded-image.jpg",
    "https://i.ibb.co/20f9sJXw/uploaded-image.jpg", "https://i.ibb.co/N6hR3YH6/uploaded-image.jpg",
    "https://i.ibb.co/ks4BnCZZ/uploaded-image.jpg", "https://i.ibb.co/PG4hQpHm/uploaded-image.jpg",
    "https://i.ibb.co/SDmsMMRF/uploaded-image.jpg", "https://i.ibb.co/hRPMstGv/uploaded-image.jpg",
    "https://i.ibb.co/VckR9GtL/uploaded-image.jpg", "https://i.ibb.co/MDGLVKD2/uploaded-image.jpg",
    "https://i.ibb.co/JRvwr1qS/uploaded-image.jpg", "https://i.ibb.co/qYnk8Sj2/uploaded-image.jpg",
    "https://i.ibb.co/TB53mWhx/uploaded-image.jpg", "https://i.ibb.co/zh1wP11d/uploaded-image.jpg",
    "https://i.ibb.co/232czyTT/uploaded-image.jpg", "https://i.ibb.co/DgVYqjKH/uploaded-image.jpg",
    "https://i.ibb.co/Vpcfb8M7/uploaded-image.jpg", "https://i.ibb.co/F4gQLn27/uploaded-image.jpg",
    "https://i.ibb.co/YT0vWzZs/uploaded-image.jpg", "https://i.ibb.co/6R9mXRsb/uploaded-image.jpg",
    "https://i.ibb.co/jPCfz0Y6/uploaded-image.jpg", "https://i.ibb.co/bjz5gCw8/uploaded-image.jpg",
    "https://i.ibb.co/B5VxJSnp/uploaded-image.jpg", "https://i.ibb.co/bRgqfgCV/uploaded-image.jpg",
    "https://i.ibb.co/JRzRR2TK/uploaded-image.jpg", "https://i.ibb.co/7JHdyvDg/uploaded-image.jpg",
    "https://i.ibb.co/xK9xsWfL/uploaded-image.jpg", "https://i.ibb.co/HLcBvkWb/uploaded-image.jpg",
    "https://i.ibb.co/YnX0yps/uploaded-image.jpg", "https://i.ibb.co/VYWVrVk1/uploaded-image.jpg",
    "https://i.ibb.co/8LxXQHnS/uploaded-image.jpg", "https://i.ibb.co/XfqLmYqs/uploaded-image.jpg",
    "https://i.ibb.co/ych4j7SN/uploaded-image.jpg", "https://i.ibb.co/YB111tzh/uploaded-image.jpg",
    "https://i.ibb.co/Sg3qzDH/uploaded-image.jpg", "https://i.ibb.co/rGr0XMkW/uploaded-image.jpg",
    "https://i.ibb.co/mVJnMhm1/uploaded-image.jpg", "https://i.ibb.co/9HPfjy1K/uploaded-image.jpg",
    "https://i.ibb.co/PzbpzjGD/uploaded-image.jpg", "https://i.ibb.co/mVQDqVGg/uploaded-image.jpg",
    "https://i.ibb.co/fGGxDLJH/uploaded-image.jpg", "https://i.ibb.co/DgTgNRVt/uploaded-image.jpg",
    "https://i.ibb.co/ZzGp75Q9/uploaded-image.jpg", "https://i.ibb.co/mVKSdsZ6/uploaded-image.jpg",
    "https://i.ibb.co/VpJ0VRHH/uploaded-image.jpg", "https://i.ibb.co/tT20j75p/uploaded-image.jpg",
    "https://i.ibb.co/TxpVRkBM/uploaded-image.jpg", "https://i.ibb.co/Pn7KzYd/uploaded-image.jpg",
    "https://i.ibb.co/MrH3z5C/uploaded-image.jpg", "https://i.ibb.co/6JH4LZ0k/uploaded-image.jpg",
    "https://i.ibb.co/bgNkVW9s/uploaded-image.jpg", "https://i.ibb.co/DHmJL1xN/uploaded-image.jpg",
    "https://i.ibb.co/VYxgH104/uploaded-image.jpg", "https://i.ibb.co/9HGfGS6p/uploaded-image.jpg",
    "https://i.ibb.co/kszkYNkC/uploaded-image.jpg", "https://i.ibb.co/fGHxQXCg/uploaded-image.jpg",
    "https://i.ibb.co/PGcmJXw4/uploaded-image.jpg", "https://i.ibb.co/chb6YRn8/uploaded-image.jpg",
    "https://i.ibb.co/CKZDvQ0S/uploaded-image.jpg", "https://i.ibb.co/Xx4Hvw5s/uploaded-image.jpg",
    "https://i.ibb.co/4nMqsdy4/uploaded-image.jpg", "https://i.ibb.co/q3wzw41k/uploaded-image.jpg",
    "https://i.ibb.co/kvdh9bP/uploaded-image.jpg", "https://i.ibb.co/fY9WMDVz/uploaded-image.jpg",
    "https://i.ibb.co/KxDRsdNs/uploaded-image.jpg", "https://i.ibb.co/93H3nvfb/uploaded-image.jpg",
    "https://i.ibb.co/7t9Hbfxq/uploaded-image.jpg", "https://i.ibb.co/4gwkDGxm/uploaded-image.jpg",
    "https://i.ibb.co/cS1g750T/uploaded-image.jpg", "https://i.ibb.co/HpnM7k0C/uploaded-image.jpg",
    "https://i.ibb.co/FLshfPwm/uploaded-image.jpg", "https://i.ibb.co/1GzQ5jDp/uploaded-image.jpg",
    "https://i.ibb.co/Y7qQRxd4/uploaded-image.jpg", "https://i.ibb.co/zTJ9fWmD/uploaded-image.jpg",
    "https://i.ibb.co/XxWV4WTG/uploaded-image.jpg", "https://i.ibb.co/9kVbs4LS/uploaded-image.jpg",
    "https://i.ibb.co/RkDkPDk6/uploaded-image.jpg", "https://i.ibb.co/f3r0p3q/uploaded-image.jpg",
    "https://i.ibb.co/9mFbdpj0/uploaded-image.jpg", "https://i.ibb.co/k6WWGcQX/uploaded-image.jpg",
    "https://i.ibb.co/yFXBRxQb/uploaded-image.jpg", "https://i.ibb.co/Y4CnRwfV/uploaded-image.jpg",
    "https://i.ibb.co/HfdhzG5F/uploaded-image.jpg", "https://i.ibb.co/5WQ1bty3/uploaded-image.jpg",
    "https://i.ibb.co/20xqjmYh/uploaded-image.jpg", "https://i.ibb.co/N2rww039/uploaded-image.jpg",
    "https://i.ibb.co/GfMsCgH0/uploaded-image.jpg", "https://i.ibb.co/tMyBmNTj/uploaded-image.jpg",
    "https://i.ibb.co/wFH4GhLr/uploaded-image.jpg", "https://i.ibb.co/9RKdj23/uploaded-image.jpg",
    "https://i.ibb.co/jPB7xsyB/uploaded-image.jpg", "https://i.ibb.co/67bqbYzT/uploaded-image.jpg",
    "https://i.ibb.co/kgVf2F5B/uploaded-image.jpg", "https://i.ibb.co/zhdk9pcZ/uploaded-image.jpg",
    "https://i.ibb.co/B1Zxcy5/uploaded-image.jpg", "https://i.ibb.co/zMzhGyM/uploaded-image.jpg",
    "https://i.ibb.co/ds45Tgrf/uploaded-image.jpg", "https://i.ibb.co/mCgthCCx/uploaded-image.jpg",
    "https://i.ibb.co/pB6B9qHM/uploaded-image.jpg"
])

class Config:
    def __init__(self):
        # Telegram API
        self.API_ID: int = int(getenv("API_ID", "29308061"))
        self.API_HASH: str = getenv("API_HASH", "462de3dfc98fd938ef9c6ee31a72d099")
        self.BOT_TOKEN: str = getenv("BOT_TOKEN", "")
        self.LOGGER_ID: int = int(getenv("LOGGER_ID", "0"))
        self.OWNER_ID: int = int(getenv("OWNER_ID", "0"))

        # Database
        self.MONGO_URL: str = getenv("MONGO_DB_URI", "mongodb+srv://Elevenyts:Elevenyts@cluster0.vuyc1u2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

        # Limits
        self.DURATION_LIMIT: int = int(getenv("DURATION_LIMIT", "300")) * 60
        self.QUEUE_LIMIT: int = int(getenv("QUEUE_LIMIT", "30"))
        self.PLAYLIST_LIMIT: int = int(getenv("PLAYLIST_LIMIT", "20"))

        # Assistant Sessions @stringenbot
        self.SESSION1: str = getenv("STRING_SESSION", "")
        self.SESSION2: str = getenv("STRING_SESSION2", "")
        self.SESSION3: str = getenv("STRING_SESSION3", "")

        # Support Links
        self.SUPPORT_CHANNEL: str = getenv("SUPPORT_CHANNEL", "https://t.me/MGB_CODER")
        self.SUPPORT_CHAT: str = getenv("SUPPORT_CHAT", "https://t.me/RIYA_MUSIC_BOT_786")

        # Excluded Chats
        self.EXCLUDED_CHATS: List[int] = self._parse_excluded_chats()

        # Feature Flags
        self.AUTO_END: bool = self._str_to_bool(getenv("AUTO_END", "False"))
        self.AUTO_LEAVE: bool = self._str_to_bool(getenv("AUTO_LEAVE", "False"))
        self.THUMB_GEN: bool = self._str_to_bool(getenv("THUMB_GEN", "True"))
        self.VIDEO_PLAY: bool = self._str_to_bool(getenv("VIDEO_PLAY", "True"))
        self.VIDEO_MAX_HEIGHT: int = self._parse_video_height()

        # Zefron API (Updated from ShrutiBots)
        self.ARTISTBOTS_API_URL: str = getenv("ARTISTBOTS_API_URL", "https://3.25.100.233.sslip.io")
        self.ARTISTBOTS_KEY: str = getenv("ARTISTBOTS_KEY", "YOUR_ZEFRON_API_KEY")
        self.ENABLE_API: bool = self._str_to_bool(getenv("ENABLE_API", "True"))
        self.ENABLE_COOKIES_FALLBACK: bool = self._str_to_bool(getenv("ENABLE_COOKIES_FALLBACK", "True"))
        self.API_TIMEOUT: int = int(getenv("API_TIMEOUT", "60"))
        self.API_STREAM_TIMEOUT: int = int(getenv("API_STREAM_TIMEOUT", "300"))

        # YouTube Cookies
        self.COOKIES_URL: List[str] = self._parse_cookies()

        # Multiple Start Images Applied Here 👇
        self.START_IMG: str = getenv("START_IMG", MGB_START_IMAGES)
        
        self.DEFAULT_THUMB: str = getenv("DEFAULT_THUMB", "https://graph.org/file/8e084972eb12cfbca9608-b2fbb5c052543b3a1f.jpg")
        self.PING_IMG: str = getenv("PING_IMG", "https://graph.org/file/8e084972eb12cfbca9608-b2fbb5c052543b3a1f.jpg")
        self.RADIO_IMG: str = getenv("RADIO_IMG", "https://graph.org/file/8e084972eb12cfbca9608-b2fbb5c052543b3a1f.jpg")
        
        # Moderation
        self.EXCLUDED_USERNAMES: List[str] = getenv("EXCLUDED_USERNAMES", "").split()

    def _parse_video_height(self) -> int:
        default_height = 1080
        raw_value = getenv("VIDEO_MAX_HEIGHT", str(default_height))
        try:
            height = int(raw_value)
        except (TypeError, ValueError):
            return default_height
        if height <= 0:
            return 0
        return max(480, min(height, 2160))

    def _parse_excluded_chats(self) -> List[int]:
        excluded = getenv("EXCLUDED_CHATS", "")
        if not excluded:
            return []
        chat_ids = []
        for chat_id in excluded.split(","):
            chat_id = chat_id.strip()
            if chat_id.lstrip('-').isdigit():
                chat_ids.append(int(chat_id))
        return chat_ids

    def _parse_cookies(self) -> List[str]:
        cookie_str = getenv("COOKIE_URL", "")
        if not cookie_str:
            return []
        valid_sources = ["batbin.me", "pastebin.com", "paste.ee", "rentry.co"]
        return [url.strip() for url in cookie_str.split() if url.strip() and any(source in url for source in valid_sources)]

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes", "y", "on")

    def check(self) -> None:
        required_vars = {
            "API_ID": self.API_ID,
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "MONGO_DB_URI": self.MONGO_URL,
            "LOGGER_ID": self.LOGGER_ID,
            "OWNER_ID": self.OWNER_ID,
            "STRING_SESSION": self.SESSION1,
        }
        missing = [name for name, value in required_vars.items() if not value or (isinstance(value, int) and value == 0)]
        if missing:
            raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
        
        if self.ENABLE_API and not self.ARTISTBOTS_KEY:
            print("Warning: ENABLE_API is True but ARTISTBOTS_KEY is not set")


config = Config()
