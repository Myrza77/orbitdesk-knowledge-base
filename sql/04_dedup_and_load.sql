-- 04_dedup_and_load.sql
-- Fix for a real bug class: aggregating directly against raw_inquiry_snapshots
-- counts snapshots, not inquiries (see etl_to_local_postgres.py -- the ratio
-- printed there is the same inflation the real project hit once, at 12x
-- instead of ~1.6x, before it was caught).
--
-- DISTINCT ON keeps only the latest snapshot per inquiry_id before it's
-- promoted into the canonical `inquiries` table -- everything downstream
-- of this step counts real inquiries, never staging rows.

SET search_path TO orbitdesk;

-- what the bug looked like: counting the staging table directly
SELECT 'BUGGY: raw snapshot count' AS label, COUNT(*) AS n FROM raw_inquiry_snapshots;

-- the fix
INSERT INTO inquiries (inquiry_id, client_name, topic_text, agent_id, opened_at)
SELECT DISTINCT ON (inquiry_id)
    inquiry_id, client_name, topic_text, agent_id, captured_at
FROM raw_inquiry_snapshots
ORDER BY inquiry_id, captured_at DESC
ON CONFLICT (inquiry_id) DO NOTHING;

SELECT 'FIXED: real inquiry count' AS label, COUNT(*) AS n FROM inquiries;
