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
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
import logging
import os
import pyrogram
from typing import Optional

from ArtistMusic import config, logger


class MutableUserFilter(pyrogram.filters.Filter, set):
    """
    A Pyrogram filter that is ALSO a mutable set of user ids.
    """

    def __init__(self, user_ids=None):
        set.__init__(self, user_ids or [])

    async def __call__(self, _, update):
        user = getattr(update, "from_user", None)
        return bool(user and user.id in self)


class Bot(pyrogram.Client):
    """
    Main bot client class extending Pyrogram's Client.
    """

    def __init__(self):
        """Initialize the bot client with Render-safe settings."""
        bot_session = (os.getenv("BOT_SESSION") or "").strip() or None

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

        # Keep Pyrogram's client name intact until boot() sets Telegram first_name
        self.id: Optional[int] = None
        self.username: Optional[str] = None
        self.mention: Optional[str] = None

    async def boot(self) -> None:
        """
        Start the bot and perform initial setup.
        """
        # Temporarily show Pyrogram's real MTProto/DC warning during login
        pyro_sess_log = logging.getLogger("pyrogram.session.session")
        pyro_conn_log = logging.getLogger("pyrogram.connection.connection")
        old_sess_lvl = pyro_sess_log.level
        old_conn_lvl = pyro_conn_log.level
        pyro_sess_log.setLevel(logging.WARNING)
        pyro_conn_log.setLevel(logging.WARNING)

        try:
            await super().start()
        finally:
            pyro_sess_log.setLevel(old_sess_lvl)
            pyro_conn_log.setLevel(old_conn_lvl)

        # Set bot information
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        # Verify logger group access
        try:
            await self.send_message(self.logger, "🤖 ʙᴏᴛ ꜱᴛᴀʀᴛᴇᴅ")
            member = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(
                f"❌ ʙᴏᴛ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ: {self.logger}\n"
                f"ʀᴇᴀꜱᴏɴ: {ex}\n"
                f"ᴘʟᴇᴀꜱᴇ ᴇɴꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ."
            )

        # Verify admin status
        if member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit(
                f"❌ ʙᴏᴛ ɪꜱ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ ɪɴ ʟᴏɢɢᴇʀ ɢʀᴏᴜᴘ: {self.logger}\n"
                f"ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴍᴏᴛᴇ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ ᴡɪᴛʜ ɴᴇᴄᴇꜱꜱᴀʀʏ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ."
            )

        logger.info(f"🤖 Bot started successfully as @{self.username}")

    async def exit(self) -> None:
        """
        Gracefully stop the bot client.
        """
        await super().stop()
        logger.info("🤖 Bot client stopped.")
