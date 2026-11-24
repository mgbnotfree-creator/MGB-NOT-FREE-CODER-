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
import inspect
import logging
import os
import pyrogram
from typing import Optional

from pyrogram import raw
from pyrogram.session import Auth, Session

from ArtistMusic import config, logger

TARGET_DC = 5


def _build_with_sig(cls, available: dict):
    """Instantiate Auth/Session using exact signature of the installed Pyrogram fork."""
    sig = inspect.signature(cls.__init__)
    kwargs = {}
    for name, param in sig.parameters.items():
        if name == "self" or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if name in available:
            kwargs[name] = available[name]
        elif param.default is inspect.Parameter.empty:
            low = name.lower()
            if "ipv6" in low:
                kwargs[name] = available["ipv6"]
            elif any(k in low for k in ("addr", "ip", "host")):
                kwargs[name] = available["server_address"]
            else:
                raise RuntimeError(
                    f"Unknown required param '{name}' in {cls.__name__}.__init__{sig}"
                )
    return cls(**kwargs)


def _resolve_dc_endpoint(dc_id: int, test_mode: bool, ipv6: bool):
    """Get exact (ip, port) for target Telegram DC."""
    try:
        from pyrogram.session.internals import DataCenter
        try:
            info = DataCenter(dc_id, test_mode, ipv6, False)
        except TypeError:
            info = DataCenter(dc_id, test_mode, ipv6)
        if isinstance(info, (tuple, list)) and len(info) >= 2:
            return str(info[0]), int(info[1])
        return str(info), 443
    except Exception:
        return "91.108.56.130", 443


class MutableUserFilter(pyrogram.filters.Filter, set):
    """A Pyrogram filter that is ALSO a mutable set of user ids."""

    def __init__(self, user_ids=None):
        set.__init__(self, user_ids or [])

    async def __call__(self, _, update):
        user = getattr(update, "from_user", None)
        return bool(user and user.id in self)


class Bot(pyrogram.Client):
    """Main bot client class with true Direct DC 5 auth & BOT_SESSION support."""

    def __init__(self):
        bot_session = (os.getenv("BOT_SESSION") or "").strip() or None
        self._has_bot_session = bool(bot_session)

        client_kwargs = dict(
            name="ArtistMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            in_memory=True,
            ipv6=False,
            sleep_threshold=60,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(
                is_disabled=True
            ),
        )

        if bot_session:
            client_kwargs["session_string"] = bot_session
        else:
            client_kwargs["bot_token"] = config.BOT_TOKEN

        super().__init__(**client_kwargs)

        self.owner: int = config.OWNER_ID
        self.logger: int = config.LOGGER_ID
        self.bl_users: MutableUserFilter = MutableUserFilter()
        self.sudoers: set = {self.owner}
        self.sudo_filter: MutableUserFilter = MutableUserFilter({self.owner})

        self.id: Optional[int] = None
        self.username: Optional[str] = None
        self.mention: Optional[str] = None

    async def _start_on_dc5(self) -> None:
        """Create auth_key directly on DC 5 and connect Session to the exact same DC 5."""
        test_mode = bool(getattr(self, "test_mode", False))
        ipv6 = bool(getattr(self, "ipv6", False))
        dc_ip, dc_port = _resolve_dc_endpoint(TARGET_DC, test_mode, ipv6)

        logger.info(
            f"🌐 Direct DC {TARGET_DC} login ({dc_ip}:{dc_port}) | "
            f"pyrogram v{getattr(pyrogram, '__version__', 'unknown')}"
        )

        await self.storage.open()
        try:
            await self.storage.dc_id(TARGET_DC)
            await self.storage.test_mode(test_mode)
            if hasattr(self.storage, "api_id"):
                try:
                    await self.storage.api_id(self.api_id)
                except Exception:
                    pass

            common_args = {
                "client": self,
                "dc_id": TARGET_DC,
                "server_address": dc_ip,
                "address": dc_ip,
                "ip": dc_ip,
                "ip_address": dc_ip,
                "host": dc_ip,
                "port": dc_port,
                "test_mode": test_mode,
                "ipv6": ipv6,
            }

            logger.info(f"🔐 Generating fresh auth key directly on DC {TARGET_DC}...")
            auth_key = await _build_with_sig(Auth, common_args).create()
            await self.storage.auth_key(auth_key)

            session_args = dict(common_args)
            session_args["auth_key"] = auth_key

            self.session = _build_with_sig(Session, session_args)
            await self.session.start()
            self.is_connected = True
            logger.info(f"📡 Connected cleanly to Telegram DC {TARGET_DC}!")

            await self.sign_in_bot(self.bot_token)
            await self.invoke(raw.functions.updates.GetState())
            self.me = await self.get_me()
            await self.initialize()
            logger.info(f"✅ Bot authorized successfully on DC {await self.storage.dc_id()}!")
        except Exception:
            try:
                if getattr(self, "session", None):
                    await self.session.stop()
            except Exception:
                pass
            self.session = None
            self.is_connected = False
            try:
                await self.storage.close()
            except Exception:
                pass
            raise

    async def boot(self) -> None:
        """Start the bot and verify logger group access."""
        pyro_sess_log = logging.getLogger("pyrogram.session.session")
        old_lvl = pyro_sess_log.level
        pyro_sess_log.setLevel(logging.WARNING)

        try:
            if self._has_bot_session:
                logger.info("🔑 Booting bot using BOT_SESSION (skipping ImportBotAuthorization)...")
                await super().start()
            else:
                await self._start_on_dc5()
        finally:
            pyro_sess_log.setLevel(old_lvl)

        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(self.logger, "🤖 ʙᴏᴛ ꜱᴛᴀʀᴛᴇᴅ")
            member = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(
                f"❌ ʙᴏᴛ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ: {self.logger}\n"
                f"ʀᴇᴀꜱᴏɴ: {ex}\n"
                f"ᴘʟᴇᴀꜱᴇ ᴇɴꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ."
            )

        if member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit(
                f"❌ ʙᴏᴛ ɪꜱ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ ɪɴ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ: {self.logger}\n"
                f"ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴍᴏᴛᴇ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ ᴡɪᴛʜ ɴᴇᴄᴇꜱꜱᴀʀʏ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ."
            )

        logger.info(f"🤖 Bot started successfully as @{self.username}")

    async def exit(self) -> None:
        """Gracefully stop the bot client."""
        await super().stop()
        logger.info("🤖 Bot client stopped.")
        
