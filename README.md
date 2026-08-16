# OrbitDesk Knowledge Base — support classification & agent scoring pipeline

A data pipeline that ingests raw support tickets, classifies them against a
fixed category taxonomy, and scores agent performance against that
taxonomy with an honest, n-weighted methodology — plus a scorecard UI that
consumes its output.

Built as a demonstration of a real, similarly-shaped project (an AI
knowledge base + agent scoring system for an accounting/tax consultancy):
same architecture and same methodology, rebuilt end-to-end on the public
[Bitext Customer Support dataset](https://github.com/bitext/customer-support-llm-chatbot-training-dataset)
(CDLA-Sharing-1.0) instead of any real client's data.

## What's actually here

```
sql/    -- warehouse schema, category seeding, dedup, article content, rollup views
etl/    -- Python: loading, classification, scoring, export
demo/   -- the agent scorecard UI, wired to the pipeline's own export
```

Run `git log --oneline` — the commit history *is* the project narrative:
schema → seed data → load → **fix a snapshot-inflation bug** → classify →
**fix a rerun-crash bug** → discover an uncategorized backlog → promote new
categories from it → score agents on real volume → **fix a profanity-filter
gap caught after the fact** → wire the demo to real pipeline output. Nothing
here shipped in one commit.

## Pipeline, step by step

| Step | File | What it does |
|---|---|---|
| 1 | `sql/01_warehouse_schema.sql` | Staging + canonical schema |
| 2 | `etl/seed_categories.py` | Fixed category list (29, from source taxonomy — never invented freely at classification time) |
| 3 | `sql/03_category_prompt_map.sql` | Routes categories to a drafting-assistant prompt, agent-facing only, never a direct auto-reply |
| 4 | `etl/etl_to_local_postgres.py` | Loads raw tickets, realistic multi-snapshot capture pattern |
| 5 | `sql/04_dedup_and_load.sql` | **Bug fix**: `DISTINCT ON` before canonical load — a naive count here is exactly what caused a real 12x inflation once |
| 6 | `etl/classify_fixed_categories.py` | Incremental classification, `NOT EXISTS` guard against re-classification instability between runs |
| 7-8 | `sql/07_knowledge_articles_map.sql`, `etl/fill_client_articles_text.py` | Article content, idempotent upsert fill — **bug fix**: a plain `INSERT` here used to crash on rerun |
| 9-10 | `etl/load_uncategorized_backlog.py`, `etl/finalize_new_categories.py` | New tickets that don't fit → reviewed → 2 new categories promoted, the rest honestly left uncategorized |
| 11 | `etl/score_agents_by_category.py`, `sql/09_client_profile.sql`, `sql/10_weighted_rollup.sql`, `etl/export_for_thomas.py` | Agent scoring (**n is real classification volume, not invented**), client profile, n-weighted rollup, final CSV export |

## The scoring methodology (`demo/manager-scorecard-demo.html`)

- **n-weighted, never a plain average of averages.** A category with 3
  observations doesn't weigh the same as one with 50.
- **A minimum-sample threshold** below which a score isn't shown as a
  number at all — "insufficient data" instead of false precision.
- **A critical failure (autofail) blocks the score only where it
  happened** — the parent level stays visible with a warning badge, not
  hidden behind it.
- **A caught methodology bug**: an earlier version showed sample size
  even for categories with no category-specific data — it silently used
  the agent's overall figure, which looked like real per-category volume
  but wasn't. Fixed by tracking which numbers are real vs. inherited and
  labeling both honestly. See the `isReal` flag in `computeClassRollup`.

## Run it yourself

```bash
createdb orbitdesk
psql -d orbitdesk -f sql/01_warehouse_schema.sql
python3 etl/seed_categories.py
psql -d orbitdesk -f sql/03_category_prompt_map.sql
python3 etl/etl_to_local_postgres.py
psql -d orbitdesk -f sql/04_dedup_and_load.sql
python3 etl/classify_fixed_categories.py
psql -d orbitdesk -f sql/07_knowledge_articles_map.sql
python3 etl/fill_client_articles_text.py
python3 etl/load_uncategorized_backlog.py
python3 etl/finalize_new_categories.py
python3 etl/score_agents_by_category.py
psql -d orbitdesk -f sql/09_client_profile.sql
psql -d orbitdesk -f sql/10_weighted_rollup.sql
python3 etl/export_for_thomas.py
python3 demo/build_demo_data.py   # regenerates demo/gen/*.js from the export
```

Then open `demo/manager-scorecard-demo.html` directly in a browser.

## What I decided vs. what Claude generated

I defined the scoring methodology, the pipeline shape, which bugs were
worth reproducing and fixing as their own steps, and caught two real
issues during the build (a profanity-filter gap that let 20 matches
through on the first pass, and the sample-size honesty bug above) by
checking actual output, not just that code ran. Claude generated the
SQL/Python/JS implementing those decisions, iterated against my feedback.
Every script's output above was actually run against a live PostgreSQL
16 instance while building this, not just written.
