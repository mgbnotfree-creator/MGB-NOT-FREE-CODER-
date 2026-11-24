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
import sys
import pyrogram
from typing import Optional

from pyrogram import raw

from ArtistMusic import config, logger

TARGET_DC = 5


def _wrap_dc(cls, target_dc: int = TARGET_DC):
    """Wrap Pyrogram Auth/Session to force target DC without breaking version-specific args."""
    def _factory(*args, **kwargs):
        if "dc_id" in kwargs:
            kwargs["dc_id"] = target_dc
        elif len(args) >= 2 and isinstance(args[1], int):
            args = (args[0], target_dc, *args[2:])
        return cls(*args, **kwargs)
    return _factory


class MutableUserFilter(pyrogram.filters.Filter, set):
    """A Pyrogram filter that is ALSO a mutable set of user ids."""

    def __init__(self, user_ids=None):
        set.__init__(self, user_ids or [])

    async def __call__(self, _, update):
        user = getattr(update, "from_user", None)
        return bool(user and user.id in self)


class Bot(pyrogram.Client):
    """Main bot client class with Direct DC 5 login & BOT_SESSION support."""

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

        # Pass dc_id natively if installed Pyrogram/Pyrofork/Kurigram supports it
        init_params = inspect.signature(pyrogram.Client.__init__).parameters
        if "dc_id" in init_params and not bot_session:
            client_kwargs["dc_id"] = TARGET_DC

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
        """Force initial Telegram connection & bot login directly on DC 5."""
        logger.info(
            f"🌐 Booting bot directly on Telegram DC {TARGET_DC} "
            f"(pyrogram v{getattr(pyrogram, '__version__', 'unknown')})..."
        )

        orig_open = self.storage.open
        orig_dc_id = self.storage.dc_id

        async def _open_dc5():
            await orig_open()
            await orig_dc_id(TARGET_DC)

        async def _forced_dc5(*args, **kwargs):
            if (not args and not kwargs) or (len(args) == 1 and args[0] is object):
                return await orig_dc_id()
            return await orig_dc_id(TARGET_DC)

        # Patch Auth & Session temporarily during initial connect so DC 2 is never used
        patched = []
        for mod_name in ("pyrogram.client", "pyrogram.methods.auth.connect"):
            mod = sys.modules.get(mod_name)
            if not mod:
                continue
            for attr in ("Auth", "Session"):
                if hasattr(mod, attr):
                    orig_obj = getattr(mod, attr)
                    patched.append((mod, attr, orig_obj))
                    setattr(mod, attr, _wrap_dc(orig_obj, TARGET_DC))

        self.storage.open = _open_dc5
        self.storage.dc_id = _forced_dc5

        try:
            is_authorized = await self.connect()
        finally:
            self.storage.open = orig_open
            self.storage.dc_id = orig_dc_id
            for mod, attr, orig_obj in patched:
                setattr(mod, attr, orig_obj)

        try:
            sess_dc = getattr(self.session, "dc_id", None)
            store_dc = await self.storage.dc_id()
            logger.info(f"📡 Connected to Telegram DC {sess_dc} (storage DC {store_dc})")

            if not is_authorized:
                await self.sign_in_bot(self.bot_token)

            await self.invoke(raw.functions.updates.GetState())
            self.me = await self.get_me()
            await self.initialize()
            logger.info(f"✅ Bot authorized successfully on DC {await self.storage.dc_id()}!")
        except Exception:
            try:
                if getattr(self, "is_connected", False):
                    await self.disconnect()
                else:
                    if getattr(self, "session", None):
                        await self.session.stop()
                    await self.storage.close()
            except Exception:
                pass
            self.session = None
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
        
