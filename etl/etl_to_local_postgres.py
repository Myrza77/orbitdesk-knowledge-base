"""
etl_to_local_postgres.py

Loads inquiries from the source dataset into the raw staging table. Each
inquiry is captured 1-3 times to realistically reproduce how an
incremental ETL job re-snapshots a ticket every time it's touched
(status change, reassignment, etc.) -- the exact shape of pattern that
caused a real x12 count inflation bug downstream (see 04_dedup_and_load.sql
for the fix). This step deliberately does NOT deduplicate -- that's the
next script's job, kept separate on purpose so the bug and its fix are
both visible as their own steps, same as they were in the real project.
"""
import csv
import random
import re
from datetime import datetime, timedelta

import psycopg2

random.seed(7)

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")
SRC = "/home/claude/bitext-data/data/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"

BAD_WORD_PAT = re.compile(r'\b(fuck\w*|shit\w*|damn\w*|ass|asshole\w*|bitch\w*|crap\w*|bastard\w*)\b', re.I)


def is_clean(row):
    """Hard filter, applied at ingestion -- not a preference applied
    later. A colloquial-register tag in the source dataset can carry
    profanity; this is checked before a row ever reaches the warehouse,
    not patched afterward at export time. (An earlier pass skipped this
    at the ETL step and let 20 matches slip through downstream into the
    generated demo data -- fixed here at the actual entry point.)"""
    return not (BAD_WORD_PAT.search(row['instruction']) or BAD_WORD_PAT.search(row['response']))

AGENTS = ["aigerim", "bermet", "cholpon", "svetlana77", "sokolov"]
AGENT_WEIGHTS = [0.40, 0.20, 0.18, 0.05, 0.17]  # mirrors real coverage skew

FIRST_NAMES = ['Daniel', 'Priya', 'Marco', 'Elena', 'Chidi', 'Sofia', 'Liam', 'Noor', 'Hiro', 'Grace',
               'Omar', 'Ines', 'Tariq', 'Freya', 'Bilal', 'Nadia', 'Victor', 'Amara', 'Jonas', 'Wei']
LAST_NAMES = ['Reyes', 'Kapoor', 'Bianchi', 'Novak', 'Okafor', 'Alves', 'Byrne', 'Haddad', 'Sato', 'Murphy',
              'Farouk', 'Costa', 'Rahman', 'Larsen', 'Khoury', 'Ahmadi', 'Petrov', 'Diallo', 'Kowalski', 'Zhang']


def fake_client():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def load_source_rows(limit_per_intent=200):
    """Sample a manageable, realistic-scale subset per intent instead of
    all ~1000 rows/intent -- a demo warehouse, not a full 27k-row dump.
    (Raised from an initial 45 -> 200 after the first pass showed most
    agents averaging well under the MIN_SAMPLE=15 threshold per category --
    not enough volume to demonstrate real per-category scores broadly.)"""
    rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
    rows = [r for r in rows if is_clean(r)]
    by_intent = {}
    for r in rows:
        by_intent.setdefault(r['intent'], []).append(r)
    sampled = []
    for intent, group in by_intent.items():
        sampled.extend(random.sample(group, min(limit_per_intent, len(group))))
    return sampled


def main():
    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("TRUNCATE raw_inquiry_snapshots RESTART IDENTITY;")

    sampled = load_source_rows()
    base_time = datetime(2026, 8, 1, 8, 0)
    inserted_snapshots = 0

    with conn.cursor() as cur:
        for i, row in enumerate(sampled):
            inquiry_id = f"INQ-{i+1:05d}"
            client = fake_client()
            agent = random.choices(AGENTS, weights=AGENT_WEIGHTS)[0]
            opened_at = base_time + timedelta(minutes=random.randint(0, 60 * 24 * 10))

            # 1-3 snapshots per inquiry -- the realistic re-capture pattern
            n_snapshots = random.choices([1, 2, 3], weights=[0.55, 0.30, 0.15])[0]
            for s in range(n_snapshots):
                cur.execute(
                    """INSERT INTO raw_inquiry_snapshots
                       (inquiry_id, client_name, topic_text, category_hint, agent_id, captured_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (inquiry_id, client, row['instruction'], row['intent'], agent,
                     opened_at + timedelta(minutes=s * 20)),
                )
                inserted_snapshots += 1
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM raw_inquiry_snapshots;")
        total_snapshots = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT inquiry_id) FROM raw_inquiry_snapshots;")
        total_inquiries = cur.fetchone()[0]

    print(f"Loaded {total_snapshots} raw snapshots for {total_inquiries} real inquiries")
    print(f"(inflation ratio if not deduped: {total_snapshots/total_inquiries:.2f}x)")
    conn.close()


if __name__ == "__main__":
    main()
