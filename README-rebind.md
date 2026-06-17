# Rebind Engine

## What this actually does

A real Power BI report (.pbix file) is a zip archive. Inside it,
`Report/Layout` is a UTF-16-encoded JSON document describing every page,
every visual, and every field that visual is bound to (a bar chart's
category axis bound to `Table.Column`, a card's value bound to a measure,
and so on). Migrating a report to a new semantic model means every one of
those bindings has to point at the new model's table and column names
instead of the old one's -- across potentially thousands of visuals, if
done by hand, one click at a time in Power BI Desktop.

This repo illustrates that rebind logic using `sample_report_layout.json`,
a JSON structure that mirrors the *shape* of a real Report/Layout's
field-binding sections, simplified for portability and to avoid depending
on any real client report file. The transformation logic in
`rebind_visuals.py` -- look up each binding's (table, field) in a mapping,
rewrite it if found, flag it if not -- is the actual hard part of the
problem, and is unchanged whether the input is this synthetic JSON or a
real Report/Layout extracted from a .pbix archive.

A production version of this tool adds one more layer underneath: reading
`Report/Layout` directly out of the .pbix zip archive (Python's built-in
`zipfile` module opens it, since .pbix is just a zip; the layout part
needs UTF-16 decoding), and writing the rebound version back into a new
.pbix archive. That I/O layer is mechanical. The logic this repo
demonstrates -- the mapping lookup, the rewrite, the explicit flagging of
anything that doesn't map -- is the part that actually matters and the
part that's identical either way.

## Running it

```bash
python rebind_visuals.py
```

Reads `sample_report_layout.json` and `mapping_config.csv`, writes
`_rebound_report_layout.json` (gitignored), and prints a summary.

## What to expect

5 visuals, 10 total field bindings, across 4 legacy regional tables. One
binding (`SGP_SalesFact.ProductLine`) has no entry in `mapping_config.csv`
-- this is deliberate, to demonstrate that the engine flags unmapped
fields explicitly rather than guessing or silently dropping them. You'll
see it called out in the run output as needing manual review.

The other 9 bindings rewrite cleanly. One of them -- `NA_SalesFact.RepName`
mapping to `fact_sales.SalesRepName` -- looks fine here, but doesn't
actually exist in the canonical schema once you check it against
`../sample_data/canonical_schema.json`. The rebind engine has no way to
know that; it just applies the mapping it was given. Catching it is
exactly what `../data_quality/schema_conformance_check.py` is for -- run
that next to see it surface, along with a second, related issue.
