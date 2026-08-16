"""
score_agents_by_category.py

Populates agent_category_scores. The sample size (n) for each agent x
category pair is REAL -- it's the actual count of classified inquiries
that agent handled in that category, straight from the pipeline so far.

The accuracy_pct is NOT real -- the source dataset has no human QA
judgment attached to responses, so there is nothing genuine to read a
quality score from. It's seeded pseudo-randomly (seed fixed for
reproducibility) and clearly labeled as such here and in the exported
data. This mirrors a real, deliberate decision from the original
project: never show a number as if it reflects a judgment nobody made.
"""
import random

import psycopg2

random.seed(3)
DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")

# exactly one deliberate autofail, same edge case kept throughout this whole demo
AUTOFAIL_AGENT = 'sokolov'


def main():
    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("TRUNCATE agent_category_scores;")
        cur.execute("""
            SELECT i.agent_id, c.category_id, COUNT(*) AS n
            FROM classifications c
            JOIN inquiries i ON i.inquiry_id = c.inquiry_id
            WHERE i.agent_id IS NOT NULL
            GROUP BY i.agent_id, c.category_id
        """)
        pairs = cur.fetchall()

        autofail_assigned = False
        for agent_id, category_id, n in pairs:
            autofail = False
            if agent_id == AUTOFAIL_AGENT and not autofail_assigned and n >= 3:
                autofail = True
                autofail_assigned = True
            score = None if autofail else round(random.uniform(55, 97), 1)
            cur.execute(
                """INSERT INTO agent_category_scores (agent_id, category_id, accuracy_pct, n, autofail)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (agent_id, category_id) DO UPDATE
                     SET accuracy_pct=EXCLUDED.accuracy_pct, n=EXCLUDED.n, autofail=EXCLUDED.autofail""",
                (agent_id, category_id, score, n, autofail),
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("SELECT agent_id, COUNT(*), COUNT(*) FILTER (WHERE autofail) FROM agent_category_scores GROUP BY agent_id ORDER BY agent_id;")
        print("Agent x category pairs scored (n is real classification volume, pct is illustrative):")
        for agent_id, count, af in cur.fetchall():
            print(f"  {agent_id}: {count} categories covered" + (f", autofail x{af}" if af else ""))
    conn.close()


if __name__ == "__main__":
    main()
