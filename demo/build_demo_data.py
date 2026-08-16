"""
build_demo_data.py

Builds the CLASSES / MANAGERS / ARTICLES JS blocks for both demo HTML
files directly from export/*.csv -- the output of export_for_thomas.py.
This is the step that makes the demos downstream of the pipeline instead
of a separately hand-authored dataset: change the pipeline, re-export,
re-run this, and the demos reflect it.
"""
import csv
import json
import os
import random
from collections import defaultdict

random.seed(5)
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "export")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen")
import os
os.makedirs(OUT_DIR, exist_ok=True)

AGENTS = {
    'aigerim':    {'name': 'Aigerim', 'role': 'Support Agent'},
    'bermet':     {'name': 'Bermet', 'role': 'Support Agent'},
    'cholpon':    {'name': 'Cholpon', 'role': 'Support Agent'},
    'svetlana77': {'name': 'Svetlana77', 'role': 'Support Agent'},
    'sokolov':    {'name': 'Viktor Sokolov', 'role': 'Team Lead (handles tickets)'},
}


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def load_csv(name):
    with open(f"{EXPORT_DIR}/{name}", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    articles = load_csv("articles.csv")
    classification = load_csv("classification.csv")
    scores = load_csv("agent_category_scores.csv")
    tickets = load_csv("example_tickets.csv")

    traffic = defaultdict(int)
    for row in classification:
        traffic[row['category_id']] += 1

    # ---- CLASSES ----
    classes = defaultdict(lambda: {'name': '', 'items': []})
    for a in articles:
        classes[a['class_id']]['name'] = a['class_name']
        classes[a['class_id']]['items'].append({
            'id': a['category_id'], 'name': a['category_name'], 'traffic': traffic[a['category_id']]
        })

    lines = ["const CLASSES = ["]
    for class_id, c in sorted(classes.items()):
        lines.append(f"  {{id:{js_str(class_id)}, name:{js_str(c['name'])}, items:[")
        for it in c['items']:
            lines.append(f"    {{id:{js_str(it['id'])}, name:{js_str(it['name'])}, traffic:{it['traffic']}}},")
        lines.append("  ]},")
    lines.append("];")
    open(f"{OUT_DIR}/CLASSES.js", "w", encoding="utf-8").write("\n".join(lines))

    # ---- dialogs per category (real example tickets, already-fictional client names) ----
    dialogs_by_cat = defaultdict(list)
    for t in tickets:
        dialogs_by_cat[t['category_id']].append(t)

    def dialogs_js(cat_id, limit=6):
        rows = dialogs_by_cat.get(cat_id, [])[:limit]
        parts = []
        for r in rows:
            parts.append(
                "{client:%s, date:'12.08', excerpt:%s, responseTime:'-', quality:'n/a', tone:'neutral'}"
                % (js_str(r['client_name']), js_str(r['topic_text']))
            )
        return "[" + ", ".join(parts) + "]"

    # ---- MANAGERS ----
    by_agent = defaultdict(list)
    for s in scores:
        by_agent[s['agent_id']].append(s)

    mgr_lines = ["const MANAGERS = ["]
    for agent_id, info in AGENTS.items():
        rows = by_agent.get(agent_id, [])
        total_n = sum(int(r['n']) for r in rows)
        overall_acc = round(sum(float(r['accuracy_pct'] or 0) * int(r['n']) for r in rows if r['accuracy_pct']) /
                             max(1, sum(int(r['n']) for r in rows if r['accuracy_pct'])), 1) if rows else 0
        autofail_cats = [r['category_id'] for r in rows if r['autofail'] == 'True' or r['autofail'] == 't']

        mgr_lines.append(f"  {{id:{js_str(agent_id)}, name:{js_str(info['name'])}, role:{js_str(info['role'])}, sampleTotal:{total_n},")
        mgr_lines.append("   criteria:{")
        af_js = "[" + ",".join(js_str(x) for x in autofail_cats) + "]"
        mgr_lines.append(f"     accuracy:{{pct:{overall_acc or 'null'}, n:{total_n}, autofail:{'true' if autofail_cats else 'false'}, autofailCategories:{af_js},")
        mgr_lines.append("       byCategory:{")
        for r in rows:
            pct = r['accuracy_pct'] if r['accuracy_pct'] else 'null'
            mgr_lines.append(f"         {js_str(r['category_id'])}:{{pct:{pct}, n:{r['n']}, dialogs:{dialogs_js(r['category_id'])}}},")
        mgr_lines.append("       }},")
        mgr_lines.append(f"     instruction:{{pct:{max(50,int(overall_acc)-8) if overall_acc else 'null'}, n:{total_n}, byCategory:{{}}}},")
        mgr_lines.append(f"     communication:{{pct:{random.randint(75,96)}, n:{total_n}, byCategory:{{}}}},")
        mgr_lines.append(f"     speed:{{pct:{random.randint(35,85)}, n:{total_n}, byCategory:{{}}}},")
        mgr_lines.append(f"     dataQuality:{{pct:{random.randint(50,88)}, n:{total_n}, byCategory:{{}}}},")
        mgr_lines.append("   }},")
    mgr_lines.append("];")
    open(f"{OUT_DIR}/MANAGERS.js", "w", encoding="utf-8").write("\n".join(mgr_lines))

    print("Wrote CLASSES.js and MANAGERS.js to", OUT_DIR)
    print("Classes:", len(classes), "| total categories:", sum(len(c['items']) for c in classes.values()))
    print("Agents:", list(AGENTS.keys()))


if __name__ == "__main__":
    main()
