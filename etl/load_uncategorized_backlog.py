"""
load_uncategorized_backlog.py

Simulates inquiries arriving after the initial category list was fixed --
real tickets that don't cleanly match any of the 27 known categories.
They get loaded with category_hint = 'uncategorized', which the closed-set
classifier (classify_fixed_categories.py) correctly refuses to force into
an existing category. This is the same "long tail with no home" pattern
the real project's Uncategorized bucket had -- ~26% of real volume there,
deliberately not force-fit into existing categories.
"""
import csv
import os
import random
import re

import psycopg2

random.seed(11)

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bitext_customer_support.csv")

BAD_WORD_PAT = re.compile(r'(fuck|shit|damn|\bass\b|asshole|bitch|crap|bastard)', re.I)  # no \b before the root -- catches compounds like 'goddamn' that a leading boundary misses


def is_clean(row):
    return not (BAD_WORD_PAT.search(row['instruction']) or BAD_WORD_PAT.search(row['response']))

FIRST_NAMES = ['Daniel', 'Priya', 'Marco', 'Elena', 'Chidi', 'Sofia', 'Liam', 'Noor', 'Hiro', 'Grace']
LAST_NAMES = ['Reyes', 'Kapoor', 'Bianchi', 'Novak', 'Okafor', 'Alves', 'Byrne', 'Haddad', 'Sato', 'Murphy']


def fake_client():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def main():
    rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
    rows = [r for r in rows if is_clean(r)]
    # pull from the two broadest, most miscellaneous-sounding intents --
    # a reasonable stand-in for "tickets that don't fit a narrow category"
    candidates = [r for r in rows if r['intent'] in ('complaint', 'contact_customer_service')]
    sample = random.sample(candidates, 90)

    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        for i, row in enumerate(sample):
            inquiry_id = f"INQ-UNCAT-{i+1:04d}"
            cur.execute(
                """INSERT INTO raw_inquiry_snapshots
                   (inquiry_id, client_name, topic_text, category_hint, agent_id)
                   VALUES (%s, %s, %s, 'uncategorized', %s)""",
                (inquiry_id, fake_client(), row['instruction'],
                 random.choice(['aigerim', 'bermet', 'cholpon', 'sokolov'])),
            )
            cur.execute(
                """INSERT INTO inquiries (inquiry_id, client_name, topic_text, agent_id, opened_at)
                   VALUES (%s, %s, %s, %s, now())
                   ON CONFLICT (inquiry_id) DO NOTHING""",
                (inquiry_id, fake_client(), row['instruction'],
                 random.choice(['aigerim', 'bermet', 'cholpon', 'sokolov'])),
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM inquiries i
            WHERE NOT EXISTS (SELECT 1 FROM classifications c WHERE c.inquiry_id = i.inquiry_id)
        """)
        print(f"Inquiries with no category yet: {cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()
