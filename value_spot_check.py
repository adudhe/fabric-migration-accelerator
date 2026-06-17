"""
value_spot_check.py

Compares a business metric computed the "old way" (summed across the
fragmented regional sources independently) against the same metric
computed from the new consolidated source, on a small synthetic dataset.
This is the spot-check a migration actually needs: structural conformance
(schema_conformance_check.py) proves the visuals will render; this proves
the numbers they render are still right.

Run:
    python value_spot_check.py
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
LEGACY_REGIONAL_DATA = BASE_DIR / "sample_legacy_regional_revenue.csv"
CONSOLIDATED_DATA = BASE_DIR / "sample_consolidated_revenue.csv"

TOLERANCE = 0.01  # acceptable rounding/FX-timing variance, expressed as a fraction


def sum_column(path: Path, column: str) -> float:
    with open(path, newline="") as f:
        return sum(float(row[column]) for row in csv.DictReader(f))


def run() -> None:
    legacy_total = sum_column(LEGACY_REGIONAL_DATA, "revenue")
    consolidated_total = sum_column(CONSOLIDATED_DATA, "revenue")

    diff = abs(legacy_total - consolidated_total)
    diff_pct = diff / legacy_total if legacy_total else 0

    print(f"Legacy (4 regional sources, summed independently): {legacy_total:,.2f}")
    print(f"Consolidated (single fact_sales source):            {consolidated_total:,.2f}")
    print(f"Difference: {diff:,.2f} ({diff_pct:.4%})")

    if diff_pct <= TOLERANCE:
        print(f"\n[PASS] Within {TOLERANCE:.0%} tolerance -- consolidation preserved the total.")
    else:
        print(f"\n[FAIL] Exceeds {TOLERANCE:.0%} tolerance -- investigate before shipping.")


if __name__ == "__main__":
    run()
