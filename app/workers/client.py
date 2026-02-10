"""
TelegramWorker — Isolated Telethon client for a single Telegram account.

Each worker runs in its own process and handles:
- Connecting to Telegram
- Listening for incoming messages
- Executing actions from the FlowEngine
- Sending heartbeats to the database
"""

import asyncio
import logging
import os
import requests
from datetime import datetime, timezone
from typing import Optional

from telethon import TelegramClient, events

from app.core.config import settings
from app.core.database import get_supabase
from app.services.flow_engine import FlowEngine

logger = logging.getLogger(__name__)


class TelegramWorker:
    """Wraps a Telethon client for one account."""

    def __init__(self, account: dict):
        self.account = account
        self.account_id = account["id"]
        self.api_id = account["api_id"]
        self.api_hash = account["api_hash"]
        self.session_name = account["session_name"]

        # Session file path
        session_dir = settings.SESSIONS_DIR
        os.makedirs(session_dir, exist_ok=True)
        session_path = os.path.join(session_dir, self.session_name)

        self.client = TelegramClient(session_path, self.api_id, self.api_hash)
        self.flow_engine = FlowEngine()
        self.db = get_supabase()
        self._running = False

    async def start(self):
        """Connect and start listening."""
        await self.client.start()
        self._running = True

        self._update_status("connected")
        logger.info(f"Worker {self.session_name} connected.")

        # Register message handler
        self.client.add_event_handler(self._on_message, events.NewMessage(incoming=True))

        # Start heartbeat loop
        asyncio.create_task(self._heartbeat_loop())

        # Run until disconnected
        await self.client.run_until_disconnected()

    async def stop(self):
        """Disconnect gracefully."""
        self._running = False
        await self.client.disconnect()
        self._update_status("disconnected")
        logger.info(f"Worker {self.session_name} disconnected.")

    # ── Message Handler ─────────────────────────────────────

    async def _on_message(self, event):
        """Handle incoming private messages."""
        if not event.is_private:
            return

        sender_id = event.sender_id
        text = event.raw_text or ""

        try:
            # 1. Check if there's an active conversation waiting for input
            active_conv = self._get_active_conversation(sender_id)

            if active_conv and active_conv["state"] == "waiting_input":
                # Resume the flow with user's message
                result = await self.flow_engine.process(active_conv, user_message=text)
                await self._execute_actions(sender_id, result["actions"])
            else:
                # 2. Check triggers
                matched_flow = await self.flow_engine.check_triggers(
                    self.account_id, sender_id, text
                )
                if matched_flow:
                    result = await self.flow_engine.start_flow(
                        self.account_id, sender_id, matched_flow["id"]
                    )
                    await self._execute_actions(sender_id, result["actions"])
                else:
                    # 3. Forward to webhook if configured
                    await self._forward_to_webhook(event)

        except Exception as e:
            logger.error(f"Error processing message from {sender_id}: {e}", exc_info=True)

    # ── Action Executor ─────────────────────────────────────

    async def _execute_actions(self, chat_id: int, actions: list):
        """Execute a list of actions returned by the FlowEngine."""
        for action in actions:
            action_type = action["type"]
            payload = action["payload"]

            try:
                if action_type == "send_text":
                    await self.client.send_message(chat_id, payload["text"])

                elif action_type == "send_image":
                    await self.client.send_file(
                        chat_id,
                        file=payload.get("url") or payload.get("file_path"),
                        caption=payload.get("caption", ""),
                        force_document=False,
                    )

                elif action_type == "send_audio":
                    await self.client.send_file(
                        chat_id,
                        file=payload.get("url") or payload.get("file_path"),
                        voice_note=payload.get("voice_note", False),
                    )

                elif action_type == "send_file":
                    await self.client.send_file(
                        chat_id,
                        file=payload.get("url") or payload.get("file_path"),
                        caption=payload.get("caption", ""),
                        force_document=True,
                    )

                elif action_type == "wait_time":
                    seconds = payload.get("seconds", 1)
                    await asyncio.sleep(seconds)

            except Exception as e:
                logger.error(f"Error executing action {action_type}: {e}", exc_info=True)

    # ── Webhook Forward ─────────────────────────────────────

    async def _forward_to_webhook(self, event):
        """Forward unhandled messages to the configured webhook."""
        if not settings.WEBHOOK_URL:
            return

        sender = await event.get_sender()
        first_name = getattr(sender, "first_name", "") or ""
        last_name = getattr(sender, "last_name", "") or ""

        msg = {
            "account_id": self.account_id,
            "sender_id": event.sender_id,
            "sender_username": getattr(sender, "username", None),
            "sender_name": f"{first_name} {last_name}".strip(),
            "chat_id": event.chat_id,
            "text": event.raw_text,
            "date": str(event.message.date),
            "message_id": event.message.id,
            "has_media": bool(event.message.media),
        }

        try:
            requests.post(settings.WEBHOOK_URL, json=msg, timeout=10)
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    # ── Helpers ──────────────────────────────────────────────

    def _get_active_conversation(self, sender_id: int) -> Optional[dict]:
        result = (
            self.db.table("conversations")
            .select("*")
            .eq("account_id", self.account_id)
            .eq("user_telegram_id", sender_id)
            .neq("state", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def _update_status(self, status: str):
        self.db.table("telegram_accounts").update({
            "status": status,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }).eq("id", self.account_id).execute()

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to the database."""
        while self._running:
            try:
                self._update_status("connected")
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(30)
