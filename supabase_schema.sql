-- supabase_schema.sql
-- Run this in Supabase Dashboard → SQL Editor to create the required tables
-- This schema matches the existing SQLite schema used by the application

-- ─── Jobs table (main jobs data) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    salary_raw TEXT,
    salary_currency TEXT,
    salary_annual NUMERIC,
    url TEXT,
    category TEXT,
    score INTEGER DEFAULT 0,
    matched TEXT,  -- comma-separated skills from CV matching
    posted TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs (score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (source);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs (category);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs (posted);

-- ─── Applications tracking table ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applications (
    job_id TEXT PRIMARY KEY,
    title TEXT,
    company TEXT,
    url TEXT,
    status TEXT DEFAULT 'applied',
    notes TEXT DEFAULT '',
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Enable Row Level Security (optional - for future auth) ─────────────
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

-- Policy: allow all operations for now (adjust when adding auth)
CREATE POLICY "Allow all for anon" ON jobs FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON applications FOR ALL USING (true);

-- ─── Verify tables created ───────────────────────────────────────────────
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('jobs', 'applications');