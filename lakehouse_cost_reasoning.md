<!--
  Once both repos are pushed to GitHub, replace the plain-text repo name
  references below with direct links, e.g.
  https://github.com/<your-username>/enterprise-lakehouse-platform
-->

# FinOps: Lakehouse Storage and Compute Cost Reasoning

This applies FinOps thinking to the lakehouse architecture in the
companion repository, `enterprise-lakehouse-platform` -- the same
discipline of quantifying cost and trade-offs, applied here to storage
tiering and compute optimization instead of engineering time.

## Storage tiering by access pattern, not by default

Bronze data is written once and rarely read directly -- its main value
is as a replay source if a silver transformation needs correcting. Gold
data is read constantly by BI tools and dashboards. Treating both
identically from a storage-cost standpoint wastes money: bronze is a
strong candidate for cooler, cheaper storage tiers and more aggressive
lifecycle policies (archive or delete after N days, once silver has
successfully reprocessed it), while gold needs to stay on
performance-optimized storage because query latency there is
user-facing.

The cost lever here is simple to state and easy to skip if nobody owns
it explicitly: storage that's provisioned once and never revisited
tends to default to the most expensive tier, because that's the path of
least resistance when a pipeline is first built under deadline pressure.

## The Z-ordering trade-off, stated as a cost decision

Z-ordering and file compaction (Delta Lake's OPTIMIZE) trade compute
cost now for query cost later: running OPTIMIZE consumes compute and
isn't free, but unoptimized small files mean every downstream query
scans more files than necessary, which shows up as both slower
dashboards and higher compute spend on every single query that hits
that table.

The FinOps framing of this isn't "always optimize" or "never optimize"
-- it's: optimize the tables that are queried often enough that the
per-query savings, multiplied across query volume, exceeds the one-time
compute cost of running OPTIMIZE. A table queried twice a month doesn't
justify the same optimization schedule as a table behind an executive
dashboard refreshed every few minutes.

## Why this belongs next to the architecture decisions, not separate from them

Every storage and compute choice already documented in that companion
repository's `architecture/decisions.md` has a cost dimension that
wasn't spelled out there. This document is that missing dimension: the
same decisions, read through a cost lens instead of a reliability lens.
