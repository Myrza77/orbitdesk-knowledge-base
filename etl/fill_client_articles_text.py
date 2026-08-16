"""
fill_client_articles_text.py

Backfills real article body text from the source dataset's response
examples. Kept as a separate pass from 07_knowledge_articles_map.sql on
purpose, because this step gets re-run repeatedly as content improves --
and a naive plain INSERT here is exactly what caused a real crash
(Postgres error 42P07 / unique-violation-style failure) the first time
this kind of script was re-run against already-seeded rows in the
original project.

Fix: ON CONFLICT DO UPDATE makes the fill idempotent -- safe to run as
many times as needed as source content changes, never crashes on a
second pass.
"""
import csv
import re

import psycopg2

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")
SRC = "/home/claude/bitext-data/data/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"

BAD_WORD_PAT = re.compile(r'\b(fuck\w*|shit\w*|damn\w*|ass|asshole\w*|bitch\w*|crap\w*|bastard\w*)\b', re.I)


def is_clean(row):
    return not (BAD_WORD_PAT.search(row['instruction']) or BAD_WORD_PAT.search(row['response']))


def clean_text(t):
    t = re.sub(r'\{\{Order Number\}\}', 'ORD-48213', t)
    t = re.sub(r'\{\{Invoice Number\}\}', 'INV-77042', t)
    t = re.sub(r'\{\{[^}]+\}\}', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def fill(conn):
    rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
    by_intent = {}
    for r in rows:
        if is_clean(r):
            by_intent.setdefault(r['intent'], r)  # first clean example wins

    updated = 0
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        for intent, row in by_intent.items():
            cur.execute(
                """INSERT INTO articles (category_id, title, body, updated_by, updated_at)
                   VALUES (%s, %s, %s, 'fill_client_articles_text', now())
                   ON CONFLICT (category_id) DO UPDATE
                     SET body = EXCLUDED.body, updated_at = now(), updated_by = EXCLUDED.updated_by""",
                (intent, intent.replace('_', ' ').capitalize(), clean_text(row['response'])),
            )
            updated += 1
    conn.commit()
    return updated


if __name__ == "__main__":
    conn = psycopg2.connect(**DB)

    n1 = fill(conn)
    print(f"Run 1: filled {n1} article bodies")

    n2 = fill(conn)  # re-run against already-filled rows -- this is what used to crash with 42P07
    print(f"Run 2 (re-run against already-filled rows): filled {n2} "
          f"({'OK, no crash, safe upsert' if n2 == n1 else 'unexpected'})")

    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("SELECT COUNT(*) FROM articles WHERE body != '(pending content)';")
        print(f"\nArticles with real content: {cur.fetchone()[0]} / 27")

    conn.close()
