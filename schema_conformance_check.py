"""
schema_conformance_check.py

Independent verification: does every field binding in the rebound report
layout actually resolve against the real canonical schema?

This is deliberately separate from rebind_visuals.py and trusts nothing it
produced. The rebind engine's job is to faithfully apply a mapping; this
module's job is to verify the mapping itself was correct against the
schema that actually exists -- which is exactly the kind of check that
catches a stale or hand-edited mapping file before it ships, rather than
after a report goes live with a broken visual.

Run:
    python ../rebind/rebind_visuals.py    # produces _rebound_report_layout.json
    python schema_conformance_check.py
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
REBOUND_LAYOUT = BASE_DIR.parent / "rebind" / "_rebound_report_layout.json"
CANONICAL_SCHEMA = BASE_DIR.parent / "sample_data" / "canonical_schema.json"


def closest_match(field: str, candidates: list[str]) -> str | None:
    """Simple suggestion for a likely-renamed field: shares a long common prefix."""
    best, best_len = None, 0
    for c in candidates:
        common = 0
        for a, b in zip(field, c):
            if a != b:
                break
            common += 1
        if common > best_len and common >= len(field) * 0.6:
            best, best_len = c, common
    return best


def run() -> None:
    with open(REBOUND_LAYOUT) as f:
        layout = json.load(f)
    with open(CANONICAL_SCHEMA) as f:
        schema = json.load(f)

    issues = []
    checked = 0

    for page in layout["pages"]:
        for visual in page["visuals"]:
            for binding in visual["field_bindings"]:
                checked += 1
                table = binding["table"]
                field = binding.get("column") or binding.get("measure")

                if table not in schema:
                    issues.append(
                        f"page '{page['page_name']}', visual {visual['visual_id']}: "
                        f"table '{table}' does not exist in canonical schema"
                    )
                elif field not in schema[table]:
                    suggestion = closest_match(field, schema[table])
                    hint = f" (did you mean '{suggestion}'?)" if suggestion else ""
                    issues.append(
                        f"page '{page['page_name']}', visual {visual['visual_id']}: "
                        f"'{table}.{field}' does not exist in canonical schema{hint}"
                    )

    print(f"Bindings checked: {checked}")
    if issues:
        print(f"Conformance issues found: {len(issues)}\n")
        for issue in issues:
            print(f"  [FAIL] {issue}")
        print("\nThese bindings will resolve to a broken visual if shipped as-is.")
    else:
        print("All bindings conform to the canonical schema.")


if __name__ == "__main__":
    run()
