# Data Quality Framework: What "Migrated Correctly" Means

A migration that produces a report which opens without error but shows
the wrong number is worse than one that fails to open at all -- the
first one looks fine and gets shipped. This framework is built around
checking both halves explicitly, because they catch different failure
modes and neither implies the other.

## Two independent checks, two different failure modes

**Schema conformance** (`schema_conformance_check.py`) answers: "will
every visual actually render against the new schema?" It catches a
mapping that points to a field which doesn't exist -- a typo in the
mapping file, a column that was renamed in the canonical schema after
the mapping was built, a legacy table that was never given a mapping at
all. This is checked independently of the rebind engine itself: the
rebind engine trusts the mapping file and applies it faithfully; this
check trusts nothing and verifies the result against the real schema. A
rebind tool that validated its own output against its own input mapping
would never catch a wrong mapping -- it would just apply the wrong
mapping consistently. That's why this is a separate module, not a flag
inside the rebind engine.

**Value conformance** (`value_spot_check.py`) answers a different
question entirely: "even where the schema resolves cleanly, is the
business number still correct?" A binding can resolve to a real column
and still produce a wrong total, if the consolidation logic
double-counted a region, dropped rows during a join, or summed a
currency-converted column against a local-currency one. Schema
conformance has no way to catch this, because nothing about it is
structurally wrong -- it's wrong at the value level.

## What this actually caught in this repo's sample data

Running `schema_conformance_check.py` against this repo's sample data
surfaces two issues, not one:

1. A mapping that points `NA_SalesFact.RepName` to
   `fact_sales.SalesRepName`, when the canonical schema actually has
   `SalesRepFullName`. This is exactly the kind of issue that happens
   when a canonical schema evolves after a mapping file is built -- it's
   invisible by eye in a CSV with hundreds of rows, but immediate once
   checked programmatically. The checker's fuzzy-match suggestion
   (`did you mean 'SalesRepFullName'?`) is what makes this fixable in
   seconds rather than a search-the-schema exercise.

2. The binding that `rebind_visuals.py` already flagged as unmapped --
   `SGP_SalesFact.ProductLine` -- shows up again here, from a different
   angle. The rebind engine flags it because no mapping exists for it.
   The conformance check flags it independently because the table it's
   still sitting on, `SGP_SalesFact`, doesn't exist in the canonical
   schema at all. Two tools, two different reasons, same underlying
   problem -- which is itself a useful property: a real issue surfacing
   from more than one direction is a stronger signal than catching it
   once.

## Why this runs as code, not as a manual review checklist

Both checks here are deliberately re-runnable, not a one-time manual
sign-off. The actual production version of this pattern ran as part of
the migration pipeline itself, not as a separate QA pass at the end --
which matters because a mapping file gets edited more than once during
a real migration, and re-validating by hand each time doesn't scale
past the first edit.
