"""
export_for_thomas.py

Final pipeline step: exports the state of the warehouse into flat CSVs --
the same handoff format the real project used to pass data from the
analyst side to the developer side. Three files, same shape as the real
export: articles (category reference text), classification (inquiry ->
category mapping, no message text), agent_category_scores (n-weighted
scoring inputs).

These are what the two demo HTML files' embedded data is built from
(via build_demo_data.py) -- the demos are downstream of this export,
not a separate hand-authored dataset.
"""
import csv

import psycopg2

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "export")

import os
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    conn = psycopg2.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")

        cur.execute("""
            SELECT cat.class_id, cat.class_name, a.category_id, cat.category_name, a.title, a.body
            FROM articles a JOIN categories cat ON cat.category_id = a.category_id
            ORDER BY cat.class_name, cat.category_name
        """)
        with open(f"{OUT_DIR}/articles.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["class_id", "class_name", "category_id", "category_name", "title", "body"])
            w.writerows(cur.fetchall())

        cur.execute("SELECT inquiry_id, category_id FROM classifications ORDER BY inquiry_id")
        with open(f"{OUT_DIR}/classification.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["inquiry_id", "category_id"])
            w.writerows(cur.fetchall())

        cur.execute("""
            SELECT agent_id, category_id, accuracy_pct, n, autofail
            FROM agent_category_scores ORDER BY agent_id, category_id
        """)
        with open(f"{OUT_DIR}/agent_category_scores.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["agent_id", "category_id", "accuracy_pct", "n", "autofail"])
            w.writerows(cur.fetchall())

        cur.execute("SELECT client_name, total_inquiries, top_categories, last_contact FROM client_profile")
        with open(f"{OUT_DIR}/client_profile.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["client_name", "total_inquiries", "top_categories", "last_contact"])
            w.writerows(cur.fetchall())

        # example tickets per category, for the "show real examples" UI panels --
        # topic text + metadata only, same constraint as the real export (no full transcript)
        cur.execute("""
            SELECT i.inquiry_id, cl.category_id, i.client_name, i.topic_text, i.agent_id, i.opened_at
            FROM inquiries i
            JOIN classifications cl ON cl.inquiry_id = i.inquiry_id
            ORDER BY cl.category_id, i.opened_at DESC
        """)
        with open(f"{OUT_DIR}/example_tickets.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["inquiry_id", "category_id", "client_name", "topic_text", "agent_id", "opened_at"])
            w.writerows(cur.fetchall())

    print("Exported to", OUT_DIR)
    for fname in ["articles.csv", "classification.csv", "agent_category_scores.csv",
                  "client_profile.csv", "example_tickets.csv"]:
        with open(f"{OUT_DIR}/{fname}") as f:
            print(f"  {fname}: {sum(1 for _ in f) - 1} rows")
    conn.close()


if __name__ == "__main__":
    main()
