-- Additional tables on top of LiteLLM's schema
-- LiteLLM creates its own tables (LiteLLM_SpendLogs, LiteLLM_TeamTable, etc.) on startup
-- This migration adds PierceGate-specific tables for AI Act compliance

CREATE TABLE IF NOT EXISTS teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    budget_eur  NUMERIC(10,4) DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- AI Act compliance fields extending LiteLLM spend logs
-- request_id references LiteLLM_SpendLogs.request_id
CREATE TABLE IF NOT EXISTS log_extensions (
    request_id      TEXT PRIMARY KEY,
    team_id         UUID REFERENCES teams(id),
    use_case        TEXT,
    data_residency  TEXT DEFAULT 'EU',
    integrity_hash  TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_log_ext_team    ON log_extensions(team_id);
CREATE INDEX IF NOT EXISTS idx_log_ext_created ON log_extensions(created_at DESC);
