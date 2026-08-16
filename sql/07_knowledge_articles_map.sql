-- 07_knowledge_articles_map.sql
-- Creates one article slot per category -- the mapping between the fixed
-- category list and the editable instruction text that will fill it.
-- Body is intentionally left as a placeholder here; a separate step
-- (08_fill_client_articles_text.sql) fills real content, because in the
-- real project those were two genuinely separate passes (slots created
-- once, content backfilled/edited repeatedly afterward) -- collapsing
-- them into one script would hide exactly the kind of idempotency bug
-- the next step exists to guard against.

SET search_path TO orbitdesk;

INSERT INTO articles (category_id, title, body, updated_by)
SELECT category_id, category_name, '(pending content)', 'seed'
FROM categories
ON CONFLICT (category_id) DO NOTHING;

SELECT COUNT(*) AS article_slots FROM articles;
