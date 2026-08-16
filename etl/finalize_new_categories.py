"""
finalize_new_categories.py

Reviews the uncategorized backlog for recurring, nameable patterns and
promotes them into new fixed categories -- the same shape of work as the
real project's Uncategorized-bucket reclassification (which split off 3
new categories and deliberately left the remaining long tail
uncategorized rather than forcing it somewhere).

Only promotes what has a genuinely clear, defensible pattern (keyword
match against two nameable clusters found in the backlog). Everything
else stays uncategorized on purpose -- not every ticket needs a home,
and inventing a category for a single one-off ticket would just move the
long-tail problem instead of solving it.
"""
import re

import psycopg2

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")

NEW_CATEGORIES = [
    {
        'category_id': 'support_hours_inquiry',
        'class_id': 'contact',
        'class_name': 'Contact & Escalation',
        'category_name': 'Support hours inquiry',
        'pattern': re.compile(r'\b(hours?|time)\b.{0,25}\b(call|reach|contact|speak)\b', re.I),
    },
    {
        'category_id': 'formal_complaint_filing',
        'class_id': 'feedback',
        'class_name': 'Feedback',
        'category_name': 'Formal complaint filing',
        'pattern': re.compile(r'\b(lodge|file|filing)\b.{0,20}\b(complaint|claim|reclamation)\b', re.I),
    },
]


def main():
    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("""
            SELECT i.inquiry_id, i.topic_text
            FROM inquiries i
            WHERE NOT EXISTS (SELECT 1 FROM classifications c WHERE c.inquiry_id = i.inquiry_id)
        """)
        backlog = cur.fetchall()

    promoted_counts = {c['category_id']: 0 for c in NEW_CATEGORIES}
    still_uncategorized = 0

    conn2 = psycopg2.connect(**DB)
    with conn2.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        for cat in NEW_CATEGORIES:
            cur.execute(
                """INSERT INTO categories (category_id, class_id, class_name, category_name)
                   VALUES (%s,%s,%s,%s) ON CONFLICT (category_id) DO NOTHING""",
                (cat['category_id'], cat['class_id'], cat['class_name'], cat['category_name']),
            )
            cur.execute(
                """INSERT INTO category_prompt_map (category_id, prompt_key, copilot_only)
                   VALUES (%s, %s, true) ON CONFLICT (category_id) DO NOTHING""",
                (cat['category_id'], 'draft_' + cat['category_id']),
            )
            cur.execute(
                """INSERT INTO articles (category_id, title, body, updated_by)
                   VALUES (%s, %s, '(pending content -- newly promoted, not yet written)', 'finalize_new_categories')
                   ON CONFLICT (category_id) DO NOTHING""",
                (cat['category_id'], cat['category_name']),
            )

        for inquiry_id, topic_text in backlog:
            matched = None
            for cat in NEW_CATEGORIES:
                if cat['pattern'].search(topic_text):
                    matched = cat['category_id']
                    break
            if matched:
                cur.execute(
                    "INSERT INTO classifications (inquiry_id, category_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                    (inquiry_id, matched),
                )
                promoted_counts[matched] += 1
            else:
                still_uncategorized += 1
    conn2.commit()

    print("Promoted from backlog into new categories:")
    for cat_id, count in promoted_counts.items():
        print(f"  {cat_id}: {count}")
    print(f"Still genuinely uncategorized (left as-is, not forced): {still_uncategorized}")
    print(f"Category count: 27 -> {27 + len(NEW_CATEGORIES)}")

    conn.close()
    conn2.close()


if __name__ == "__main__":
    main()
