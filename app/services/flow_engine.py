"""
FlowEngine — State machine that processes conversation flows.

Stateless service: receives a conversation state + optional user message,
executes steps, and returns actions for the worker to perform.
"""

import asyncio
import logging
from typing import Optional, List
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class FlowEngine:
    """Processes flow steps for a given conversation."""

    def __init__(self):
        self.db = get_supabase()

    # ── public ──────────────────────────────────────────────

    async def check_triggers(self, account_id: str, sender_id: int, text: str) -> Optional[dict]:
        """Check if an incoming message matches any active flow trigger.
        Returns the flow dict if matched, None otherwise.
        """
        flows = (
            self.db.table("flows")
            .select("*")
            .eq("account_id", account_id)
            .eq("is_active", True)
            .execute()
        )

        for flow in flows.data:
            if flow["trigger_type"] == "first_message":
                # Check if user already has an active conversation for this flow
                existing = (
                    self.db.table("conversations")
                    .select("id")
                    .eq("account_id", account_id)
                    .eq("user_telegram_id", sender_id)
                    .eq("flow_id", flow["id"])
                    .neq("state", "completed")
                    .execute()
                )
                if not existing.data:
                    return flow

            elif flow["trigger_type"] == "keyword":
                keyword = (flow.get("trigger_content") or "").lower()
                if keyword and keyword in text.lower():
                    return flow

        return None

    async def start_flow(self, account_id: str, sender_id: int, flow_id: str) -> dict:
        """Create a new conversation and return the first actions to execute."""
        conversation = (
            self.db.table("conversations")
            .insert({
                "account_id": account_id,
                "user_telegram_id": sender_id,
                "flow_id": flow_id,
                "current_step_order": 1,
                "state": "running",
                "context": {},
            })
            .execute()
        )
        conv = conversation.data[0]
        return await self.process(conv)

    async def process(self, conversation: dict, user_message: Optional[str] = None) -> dict:
        """Process the current step of a conversation.

        Returns a dict with:
            actions: list of dicts {type, payload} for the worker
            conversation: updated conversation state
        """
        actions: List[dict] = []
        conv = conversation.copy()

        while True:
            step = self._get_step(conv["flow_id"], conv["current_step_order"])

            if step is None:
                # No more steps — flow finished
                conv["state"] = "completed"
                self._update_conversation(conv)
                break

            step_type = step["type"]

            if step_type == "send_text":
                actions.append({
                    "type": "send_text",
                    "payload": step["payload"],
                })
                conv["current_step_order"] += 1

            elif step_type == "send_image":
                actions.append({
                    "type": "send_image",
                    "payload": step["payload"],
                })
                conv["current_step_order"] += 1

            elif step_type == "send_audio":
                actions.append({
                    "type": "send_audio",
                    "payload": step["payload"],
                })
                conv["current_step_order"] += 1

            elif step_type == "send_file":
                actions.append({
                    "type": "send_file",
                    "payload": step["payload"],
                })
                conv["current_step_order"] += 1

            elif step_type == "wait_message":
                if user_message is not None:
                    # Store the user's answer in context
                    var_name = step["payload"].get("variable", "last_input")
                    ctx = conv.get("context", {})
                    ctx[var_name] = user_message
                    conv["context"] = ctx
                    conv["current_step_order"] += 1
                    user_message = None  # consumed
                else:
                    conv["state"] = "waiting_input"
                    self._update_conversation(conv)
                    break

            elif step_type == "wait_time":
                seconds = step["payload"].get("seconds", 1)
                actions.append({
                    "type": "wait_time",
                    "payload": {"seconds": seconds},
                })
                conv["current_step_order"] += 1

            elif step_type == "end":
                conv["state"] = "completed"
                self._update_conversation(conv)
                break

            else:
                logger.warning(f"Unknown step type: {step_type}")
                conv["current_step_order"] += 1

        # Persist updated step position
        if conv["state"] != "completed":
            self._update_conversation(conv)

        return {"actions": actions, "conversation": conv}

    # ── private ─────────────────────────────────────────────

    def _get_step(self, flow_id: str, order: int) -> Optional[dict]:
        result = (
            self.db.table("flow_steps")
            .select("*")
            .eq("flow_id", flow_id)
            .eq("step_order", order)
            .execute()
        )
        return result.data[0] if result.data else None

    def _update_conversation(self, conv: dict):
        self.db.table("conversations").update({
            "current_step_order": conv["current_step_order"],
            "state": conv["state"],
            "context": conv["context"],
        }).eq("id", conv["id"]).execute()
