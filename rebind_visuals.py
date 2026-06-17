"""
rebind_visuals.py

Core rebind engine: walks every visual's field bindings in a report layout
and rewrites legacy (table, field) references to their canonical
equivalents, using a mapping built from the consolidated semantic model.

This operates on a JSON structure that mirrors the shape of a real Power BI
Report/Layout definition's field-binding sections (table/column/measure
references per visual), simplified for portability and to avoid depending
on any real client report file. A production version reads the actual
Report/Layout part directly from inside the .pbix archive (a .pbix file is
a zip archive; Report/Layout is UTF-16-encoded JSON inside it) -- the
logic below is unchanged, only the I/O layer differs. See README.md for
more on that distinction.

Run:
    python rebind_visuals.py
"""

import copy
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
LAYOUT_IN = BASE_DIR / "sample_report_layout.json"
MAPPING_FILE = BASE_DIR / "mapping_config.csv"
LAYOUT_OUT = BASE_DIR / "_rebound_report_layout.json"


def load_mapping(path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """
    Build a lookup: (legacy_table, legacy_field) -> (canonical_table, canonical_field).
    field_kind (column vs measure) isn't used as part of the key -- a visual binds to a
    field by name regardless of kind, and the mapping CSV is the single source of truth
    either way. field_kind stays in the CSV purely for human readability during review.
    """
    mapping = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["legacy_table"], row["legacy_field"])
            mapping[key] = (row["canonical_table"], row["canonical_field"])
    return mapping


def rebind_layout(layout: dict, mapping: dict) -> tuple[dict, dict]:
    """Mutates a deep-copied structure; the caller's input layout is left untouched."""
    stats = {"visuals_touched": 0, "bindings_rewritten": 0, "unmapped": []}

    for page in layout["pages"]:
        for visual in page["visuals"]:
            visual_touched = False
            for binding in visual["field_bindings"]:
                field_name = binding.get("column") or binding.get("measure")
                key = (binding["table"], field_name)

                if key in mapping:
                    new_table, new_field = mapping[key]
                    binding["table"] = new_table
                    if "column" in binding:
                        binding["column"] = new_field
                    else:
                        binding["measure"] = new_field
                    stats["bindings_rewritten"] += 1
                    visual_touched = True
                else:
                    stats["unmapped"].append({
                        "page": page["page_name"],
                        "visual_id": visual["visual_id"],
                        "table": binding["table"],
                        "field": field_name,
                    })

            if visual_touched:
                stats["visuals_touched"] += 1

    return layout, stats


def run() -> None:
    with open(LAYOUT_IN) as f:
        layout = json.load(f)

    mapping = load_mapping(MAPPING_FILE)
    rebound, stats = rebind_layout(copy.deepcopy(layout), mapping)

    with open(LAYOUT_OUT, "w") as f:
        json.dump(rebound, f, indent=2)

    total_visuals = sum(len(p["visuals"]) for p in layout["pages"])
    total_bindings = sum(len(v["field_bindings"]) for p in layout["pages"] for v in p["visuals"])

    print(f"Visuals processed:  {total_visuals}")
    print(f"Visuals touched:    {stats['visuals_touched']}")
    print(f"Bindings rewritten: {stats['bindings_rewritten']} / {total_bindings}")

    if stats["unmapped"]:
        print(f"\nUnmapped bindings (left unchanged, needs manual review): {len(stats['unmapped'])}")
        for u in stats["unmapped"]:
            print(f"  - page '{u['page']}', visual {u['visual_id']}: {u['table']}.{u['field']}")
    else:
        print("\nAll bindings mapped.")

    print(f"\nRebound layout written to: {LAYOUT_OUT}")


if __name__ == "__main__":
    run()
