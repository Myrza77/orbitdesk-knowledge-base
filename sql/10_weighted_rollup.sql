-- 10_weighted_rollup.sql
-- Same rollup rule as the manager scorecard demo's JS logic
-- (computeClassRollup / computeTopRollup), now as SQL views against the
-- real schema: n-weighted average, never a plain average of averages;
-- autofail blocks the score only where it happened, not the parent
-- level; MIN_SAMPLE gates whether a score is shown at all.

SET search_path TO orbitdesk;

CREATE OR REPLACE VIEW class_score_rollup AS
WITH scored AS (
    SELECT
        cat.class_id, cat.class_name,
        s.agent_id, s.category_id, s.n, s.autofail,
        CASE WHEN s.n >= 15 AND NOT s.autofail THEN s.accuracy_pct ELSE NULL END AS usable_score
    FROM agent_category_scores s
    JOIN categories cat ON cat.category_id = s.category_id
)
SELECT
    agent_id,
    class_id, class_name,
    COUNT(*) AS category_count,
    COUNT(*) FILTER (WHERE autofail) AS autofail_count,
    SUM(n) FILTER (WHERE usable_score IS NOT NULL) AS scored_n,
    ROUND(
        SUM(usable_score * n) FILTER (WHERE usable_score IS NOT NULL)
        / NULLIF(SUM(n) FILTER (WHERE usable_score IS NOT NULL), 0)
    , 1) AS class_score
FROM scored
GROUP BY agent_id, class_id, class_name;

CREATE OR REPLACE VIEW overall_score_rollup AS
SELECT
    agent_id,
    ROUND(SUM(class_score * scored_n) FILTER (WHERE class_score IS NOT NULL)
        / NULLIF(SUM(scored_n) FILTER (WHERE class_score IS NOT NULL), 0), 1) AS overall_score,
    SUM(autofail_count) AS total_autofails,
    SUM(scored_n) AS total_scored_n
FROM class_score_rollup
GROUP BY agent_id;

SELECT * FROM overall_score_rollup ORDER BY agent_id;
