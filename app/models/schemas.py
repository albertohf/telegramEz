"""Pydantic schemas for API requests/responses and DB row representations."""

from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


# ──────────────────────── Enums ────────────────────────

class AccountStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    BANNED = "banned"


class TriggerType(str, Enum):
    FIRST_MESSAGE = "first_message"
    KEYWORD = "keyword"
    MANUAL = "manual"


class StepType(str, Enum):
    SEND_TEXT = "send_text"
    SEND_IMAGE = "send_image"
    SEND_AUDIO = "send_audio"
    SEND_FILE = "send_file"
    WAIT_MESSAGE = "wait_message"
    WAIT_TIME = "wait_time"
    END = "end"


class ConversationState(str, Enum):
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"


# ──────────────────── Telegram Accounts ────────────────────

class AccountCreate(BaseModel):
    api_id: int
    api_hash: str
    phone_number: str
    session_name: str


class AccountResponse(BaseModel):
    id: str
    api_id: int
    phone_number: str
    session_name: str
    status: AccountStatus
    last_seen: Optional[str] = None


# ──────────────────────── Flows ────────────────────────

class FlowStepCreate(BaseModel):
    order: int
    type: StepType
    payload: dict


class FlowCreate(BaseModel):
    account_id: str
    name: str
    trigger_type: TriggerType
    trigger_content: Optional[str] = None
    steps: List[FlowStepCreate]


class FlowStepResponse(BaseModel):
    id: str
    flow_id: str
    order: int
    type: StepType
    payload: dict


class FlowResponse(BaseModel):
    id: str
    account_id: str
    name: str
    trigger_type: TriggerType
    trigger_content: Optional[str] = None
    is_active: bool
    steps: Optional[List[FlowStepResponse]] = None


# ──────────────────── Conversations ────────────────────

class ConversationResponse(BaseModel):
    id: str
    account_id: str
    user_telegram_id: int
    flow_id: str
    current_step_order: int
    state: ConversationState
    context: dict


# ──────────────────── Send Requests ────────────────────

class SendTextRequest(BaseModel):
    account_id: str
    chat_id: int
    text: str


class SendFileRequest(BaseModel):
    account_id: str
    chat_id: int
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    caption: Optional[str] = None
    voice_note: bool = False
    video_note: bool = False
    force_document: bool = False
