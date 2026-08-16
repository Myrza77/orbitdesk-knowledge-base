-- 03_category_prompt_map.sql
-- Maps each category to a drafting-assistant prompt template.
--
-- Encodes a real product decision from the original project: knowledge
-- base instructions are wired to the AGENT-FACING drafting assistant
-- (copilot) only -- never to a direct customer-facing auto-reply. The
-- `copilot_only` flag defaults to true and is never flipped by this
-- script; it's a deliberate one-way door, not a per-category toggle.

SET search_path TO orbitdesk;

INSERT INTO category_prompt_map (category_id, prompt_key, copilot_only)
SELECT category_id, 'draft_' || category_id, true
FROM categories
ON CONFLICT (category_id) DO NOTHING;

SELECT COUNT(*) AS mapped_categories FROM category_prompt_map WHERE copilot_only = true;
