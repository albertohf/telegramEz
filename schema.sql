-- ============================================================
-- Supabase SQL Schema for TelegramEz SaaS
-- Run this in the Supabase SQL Editor
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────── telegram_accounts ────────────────────

CREATE TABLE IF NOT EXISTS telegram_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_id INTEGER NOT NULL,
    api_hash TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    session_name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'disconnected'
        CHECK (status IN ('connected', 'disconnected', 'banned')),
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────── flows ────────────────────────────

CREATE TABLE IF NOT EXISTS flows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL
        CHECK (trigger_type IN ('first_message', 'keyword', 'manual')),
    trigger_content TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────── flow_steps ───────────────────────────

CREATE TABLE IF NOT EXISTS flow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id UUID NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    type TEXT NOT NULL
        CHECK (type IN ('send_text', 'send_image', 'send_audio', 'send_file',
                        'wait_message', 'wait_time', 'end')),
    payload JSONB DEFAULT '{}',
    UNIQUE (flow_id, step_order)
);

-- ──────────────────── conversations ───────────────────────

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    user_telegram_id BIGINT NOT NULL,
    flow_id UUID NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
    current_step_order INTEGER NOT NULL DEFAULT 1,
    state TEXT NOT NULL DEFAULT 'running'
        CHECK (state IN ('running', 'waiting_input', 'completed')),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────── indexes ─────────────────────────────

CREATE INDEX IF NOT EXISTS idx_conversations_account_user
    ON conversations (account_id, user_telegram_id);

CREATE INDEX IF NOT EXISTS idx_flows_account
    ON flows (account_id);

CREATE INDEX IF NOT EXISTS idx_flow_steps_flow
    ON flow_steps (flow_id, step_order);
