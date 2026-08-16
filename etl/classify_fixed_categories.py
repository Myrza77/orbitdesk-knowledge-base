"""
classify_fixed_categories.py

Classifies inquiries against the FIXED category list only (never free
text) -- category_hint from the source is used here as a stand-in for
what would be a real LLM call in production, closed to the same 27
allowed labels either way.

The actual fix this script demonstrates: incremental classification via
NOT EXISTS, so re-running the job never touches an inquiry that's
already classified. Without this, re-classifying everything on every run
lets natural LLM output variance silently flip an inquiry's category
between runs with no underlying data change -- that instability is what
this guards against, not just "slowness."
"""
import psycopg2

DB = dict(host="localhost", dbname="orbitdesk", user="postgres", password="postgres")


def classify_new_inquiries(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("""
            SELECT i.inquiry_id, r.category_hint
            FROM inquiries i
            JOIN raw_inquiry_snapshots r ON r.inquiry_id = i.inquiry_id
            WHERE NOT EXISTS (
                SELECT 1 FROM classifications c WHERE c.inquiry_id = i.inquiry_id
            )
            GROUP BY i.inquiry_id, r.category_hint
        """)
        pending = cur.fetchall()

        valid_categories = set()
        cur.execute("SELECT category_id FROM categories;")
        valid_categories = {row[0] for row in cur.fetchall()}

        classified = 0
        for inquiry_id, category_hint in pending:
            # closed-set guard: never write a category outside the fixed list,
            # same constraint a real LLM call would be prompted with
            if category_hint not in valid_categories:
                continue
            cur.execute(
                "INSERT INTO classifications (inquiry_id, category_id) VALUES (%s, %s) "
                "ON CONFLICT (inquiry_id) DO NOTHING",
                (inquiry_id, category_hint),
            )
            classified += 1
    conn.commit()
    return classified


if __name__ == "__main__":
    conn = psycopg2.connect(**DB)

    n1 = classify_new_inquiries(conn)
    print(f"Run 1: classified {n1} inquiries")

    n2 = classify_new_inquiries(conn)
    print(f"Run 2 (same data): classified {n2} inquiries "
          f"({'OK, idempotent' if n2 == 0 else 'BUG: reclassified existing rows'})")

    with conn.cursor() as cur:
        cur.execute("SET search_path TO orbitdesk;")
        cur.execute("""
            SELECT cat.class_name, COUNT(*)
            FROM classifications c
            JOIN categories cat ON cat.category_id = c.category_id
            GROUP BY cat.class_name ORDER BY cat.class_name
        """)
        print("\nClassified inquiries by class:")
        for class_name, count in cur.fetchall():
            print(f"  {class_name}: {count}")

    conn.close()
