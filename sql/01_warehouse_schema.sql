-- warehouse_schema.sql
-- Core schema for the OrbitDesk knowledge base warehouse.
-- Mirrors the real project's local Postgres warehouse structure:
-- a raw staging layer (append-only, as-received from source), a
-- canonical layer (deduplicated, one row per real entity), and derived
-- scoring/profile tables built on top of the canonical layer.

CREATE SCHEMA IF NOT EXISTS orbitdesk;
SET search_path TO orbitdesk;

-- ===== Staging layer: raw, append-only, may contain duplicates =====
CREATE TABLE IF NOT EXISTS raw_inquiry_snapshots (
    snapshot_id   SERIAL PRIMARY KEY,
    inquiry_id    TEXT NOT NULL,
    client_name   TEXT NOT NULL,
    topic_text    TEXT NOT NULL,
    category_hint TEXT,              -- source-provided category, may be absent
    agent_id      TEXT,
    captured_at   TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_snapshots_inquiry ON raw_inquiry_snapshots(inquiry_id);

-- ===== Canonical layer =====
CREATE TABLE IF NOT EXISTS categories (
    category_id    TEXT PRIMARY KEY,
    class_id       TEXT NOT NULL,
    class_name     TEXT NOT NULL,
    category_name  TEXT NOT NULL,
    active         BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS category_prompt_map (
    category_id   TEXT PRIMARY KEY REFERENCES categories(category_id),
    prompt_key    TEXT NOT NULL,        -- which drafting-assistant prompt template applies
    copilot_only  BOOLEAN NOT NULL DEFAULT true  -- never wired to direct auto-reply, agent-facing only
);

CREATE TABLE IF NOT EXISTS articles (
    category_id  TEXT PRIMARY KEY REFERENCES categories(category_id),
    title        TEXT NOT NULL,
    body         TEXT NOT NULL,
    updated_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_by   TEXT NOT NULL DEFAULT 'seed'
);

CREATE TABLE IF NOT EXISTS inquiries (
    inquiry_id   TEXT PRIMARY KEY,
    client_name  TEXT NOT NULL,
    topic_text   TEXT NOT NULL,
    agent_id     TEXT,
    opened_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    inquiry_id     TEXT PRIMARY KEY REFERENCES inquiries(inquiry_id),
    category_id    TEXT NOT NULL REFERENCES categories(category_id),
    classified_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_category_scores (
    agent_id       TEXT NOT NULL,
    category_id    TEXT NOT NULL REFERENCES categories(category_id),
    accuracy_pct   NUMERIC,
    n              INTEGER NOT NULL,
    autofail       BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (agent_id, category_id)
);

CREATE TABLE IF NOT EXISTS client_profile (
    client_name     TEXT PRIMARY KEY,
    total_inquiries INTEGER NOT NULL,
    top_categories  TEXT[],
    last_contact    TIMESTAMP
);
