"""
seed_categories.py

Populates the fixed category list from the source dataset's own taxonomy.
Mirrors a real product decision from the original project: categories are
NOT invented freely by an LLM at classification time -- they're a closed,
pre-agreed list. Here the list comes from the Bitext dataset's own
category/intent structure (11 categories, 27 intents) instead of an
internal knowledge base export, but the principle -- classify against a
fixed set, never free text -- is the same.
"""
import csv
import os
import psycopg2

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bitext_customer_support.csv")

CLASS_NAMES = {
    'ACCOUNT': 'Account', 'CANCEL': 'Cancellations', 'CONTACT': 'Contact & Escalation',
    'DELIVERY': 'Delivery', 'FEEDBACK': 'Feedback', 'INVOICE': 'Invoicing',
    'ORDER': 'Orders', 'PAYMENT': 'Payment', 'REFUND': 'Refunds',
    'SHIPPING': 'Shipping', 'SUBSCRIPTION': 'Subscriptions',
}


def humanize(intent: str) -> str:
    return intent.replace('_', ' ').capitalize()


def main():
    rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
    seen = {}
    for r in rows:
        seen[r['intent']] = r['category']

    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("TRUNCATE categories CASCADE;")
        for intent, cat in sorted(seen.items()):
            cur.execute(
                """INSERT INTO categories (category_id, class_id, class_name, category_name)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (category_id) DO UPDATE SET category_name = EXCLUDED.category_name""",
                (intent, cat.lower(), CLASS_NAMES[cat], humanize(intent)),
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT class_name, COUNT(*) FROM categories GROUP BY class_name ORDER BY class_name;")
        print("Seeded categories by class:")
        for class_name, count in cur.fetchall():
            print(f"  {class_name}: {count}")
    conn.close()


if __name__ == "__main__":
    main()
