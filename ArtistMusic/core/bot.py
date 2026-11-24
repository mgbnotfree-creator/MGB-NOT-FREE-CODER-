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
import logging
import os
import pyrogram
from typing import Optional

from pyrogram import raw
from pyrogram.errors import UserMigrate
from pyrogram.session import Auth, Session

from ArtistMusic import config, logger


class MutableUserFilter(pyrogram.filters.Filter, set):
    """A Pyrogram filter that is ALSO a mutable set of user ids."""

    def __init__(self, user_ids=None):
        set.__init__(self, user_ids or [])

    async def __call__(self, _, update):
        user = getattr(update, "from_user", None)
        return bool(user and user.id in self)


class Bot(pyrogram.Client):
    """Main bot client class with Direct Multi-DC login & BOT_SESSION support."""

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

    async def _switch_dc(self, dc_id: int) -> None:
        """Switch active MTProto session directly to target DC."""
        if getattr(self, "session", None):
            try:
                await self.session.stop()
            except Exception:
                pass
        test_mode = await self.storage.test_mode()
        await self.storage.dc_id(dc_id)
        auth_key = await Auth(self, dc_id, test_mode).create()
        await self.storage.auth_key(auth_key)
        self.session = Session(self, dc_id, auth_key, test_mode)
        await self.session.start()

    async def _start_with_direct_dc(self) -> None:
        """Bypass broken DC 2 routing by trying DC 5 -> 4 -> 1 -> 2 directly."""
        is_authorized = await self.connect()
        try:
            if not is_authorized:
                last_err = None
                authorized_user = None
                for dc in (5, 4, 1, 2):
                    try:
                        logger.info(f"🌐 Trying direct bot login on DC {dc}...")
                        await self._switch_dc(dc)
                        while True:
                            try:
                                r = await self.invoke(
                                    raw.functions.auth.ImportBotAuthorization(
                                        flags=0,
                                        api_id=self.api_id,
                                        api_hash=self.api_hash,
                                        bot_auth_token=self.bot_token,
                                    ),
                                    retries=2,
                                )
                                await self.storage.user_id(r.user.id)
                                await self.storage.is_bot(True)
                                authorized_user = r.user
                                logger.info(f"✅ Bot authorized directly on DC {await self.storage.dc_id()}!")
                                break
                            except UserMigrate as e:
                                logger.info(f"🔀 Migrating bot login to DC {e.value}...")
                                await self._switch_dc(e.value)
                        if authorized_user:
                            break
                    except Exception as err:
                        last_err = err
                        logger.warning(f"⚠️ Direct login on DC {dc} failed: {err}")

                if not authorized_user:
                    raise last_err or RuntimeError("All Telegram DCs failed for ImportBotAuthorization")

            await self.invoke(raw.functions.updates.GetState())
        except Exception:
            if getattr(self, "is_connected", False):
                try:
                    await self.disconnect()
                except Exception:
                    pass
            raise
        else:
            self.me = await self.get_me()
            await self.initialize()

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
                await self._start_with_direct_dc()
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
        
