#!/usr/bin/env python3
"""
Communication interfaces - Telegram and Discord
"""

import os
import json
import requests
import logging
from pathlib import Path
import discord
from typing import Optional, Callable
from discord.ext import commands
import asyncio

logger = logging.getLogger(__name__)

class DiscordBot:
    """Discord bot interface for agent communication"""
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.callback = None
        self.ready = False
        self.setup_handlers()

    def setup_handlers(self):
        """Register Discord event handlers"""
        @self.bot.event
        async def on_ready():
            logger.info(f"✓ Discord bot connected as {self.bot.user}")
            self.ready = True

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            if self.channel_id == 0 or message.channel.id == self.channel_id:
                if self.callback:
                    response = self.callback(message.content)
                    try:
                        await message.reply(response)
                    except Exception as e:
                        logger.error(f"Failed to reply to message: {e}")

    def set_callback(self, callback: Callable[[str], str]):
        """Register message handler callback"""
        self.callback = callback

    async def start_bot(self):
        """Start Discord bot in background"""
        if not self.token:
            logger.warning("Discord token not configured")
            return False

        if self.channel_id == 0:
            logger.warning("Discord channel ID not configured")
            return False

        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
            return False

    def send_message_sync(self, text: str):
        """Synchronously send message to Discord channel (non-blocking)"""
        if not self.token or self.channel_id == 0:
            return False

        if not self.bot.is_closed():
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                try:
                    # Schedule the coroutine on the bot's event loop
                    asyncio.create_task(channel.send(text))
                    return True
                except Exception as e:
                    logger.error(f"Failed to send Discord message: {e}")
                    return False
        return False

    async def send_message(self, text: str):
        """Asynchronously send message to channel"""
        if self.channel_id > 0 and not self.bot.is_closed():
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                try:
                    await channel.send(text)
                    return True
                except Exception as e:
                    logger.error(f"Failed to send Discord message: {e}")
        return False

class TelegramBot:
    """Telegram bot interface - sends/receives messages via the Bot API"""
    def __init__(self, token: Optional[str] = None):
        import threading
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_base = f"https://api.telegram.org/bot{self.token}" if self.token else None
        self._poll_lock = threading.Lock()  # prevent concurrent getUpdates (409 conflict)
        self.callback = None
        self.offset_file = Path(__file__).parent / ".freeWill_telegram_offset.json"
        self.update_offset = self._load_offset()

    def _load_offset(self):
        """Restore the update offset across process restarts (agent.py runs once per iteration)"""
        try:
            if self.offset_file.exists():
                return json.loads(self.offset_file.read_text()).get("offset")
        except Exception:
            pass
        return None

    def _save_offset(self):
        try:
            self.offset_file.write_text(json.dumps({"offset": self.update_offset}))
        except Exception as e:
            logger.error(f"Failed to persist Telegram offset: {e}")

    def set_callback(self, callback: Callable[[str], str]):
        """Register message handler callback"""
        self.callback = callback

    def send_message_sync(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Send a message to the configured chat via the Telegram Bot API"""
        if not self.token or not self.api_base:
            logger.debug("Telegram not configured")
            return False
        target = chat_id or self.chat_id
        if not target:
            logger.warning("Telegram chat ID not configured")
            return False
        # Clean Discord markdown for Telegram plain text
        plain = (text
            .replace("**", "")
            .replace("__", "")
            .replace("*", "")
            .replace("`", "")
        )[:4096]
        try:
            resp = requests.post(
                f"{self.api_base}/sendMessage",
                json={"chat_id": target, "text": plain},
                timeout=15
            )
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram send error: {resp.status_code} - {resp.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Telegram send exception: {e}")
            return False

    async def send_message(self, text: str):
        """Async wrapper around the sync send for interface parity with DiscordBot"""
        return self.send_message_sync(text)

    def get_updates(self):
        """Fetch new incoming messages since the last processed offset"""
        if not self.token or not self.api_base:
            return []
        if not self._poll_lock.acquire(blocking=False):
            return []  # Another thread is already polling — skip this call
        try:
            params = {"timeout": 0}
            if self.update_offset is not None:
                params["offset"] = self.update_offset
            resp = requests.get(f"{self.api_base}/getUpdates", params=params, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Telegram getUpdates error: {resp.status_code} - {resp.text[:200]}")
                return []
            updates = resp.json().get("result", [])
            if updates:
                self.update_offset = updates[-1]["update_id"] + 1
                self._save_offset()
            return updates
        except Exception as e:
            logger.error(f"Telegram getUpdates exception: {e}")
            return []
        finally:
            self._poll_lock.release()

    def handle_updates(self):
        """Poll for new messages and dispatch them to the registered callback"""
        if not self.callback:
            return
        for update in self.get_updates():
            message = update.get("message") or update.get("edited_message")
            if not message:
                continue
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            if not text or chat_id is None:
                continue
            try:
                response = self.callback(text)
                if response:
                    self.send_message_sync(response, chat_id=chat_id)
            except Exception as e:
                logger.error(f"Telegram callback error: {e}")
