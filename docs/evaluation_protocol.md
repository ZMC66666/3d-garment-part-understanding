# Alignment Evaluation Protocol

The downstream garment-to-body alignment experiment is evaluated on controlled subsets of the held-out test set.

- **Attraction metrics:** 120 region-specific runs
  - 40 neckline runs
  - 40 waistline runs
  - 40 cuff runs
- **Hem violation:** 40 hem-specific runs
- **Penetration:** evaluated on all 160 alignment runs

The 160 runs correspond to **104 unique garments**, because some garments participate in multiple region-specific evaluations.

For each run, a metric is first averaged over its eligible garment vertices. Reported results are then obtained by equally averaging the run-level values. Garment categories are not macro-averaged.

## Metrics

- **Struct.** — garment-body structural-coordinate mismatch in attraction regions
- **Gap** — unsigned point-to-surface attraction distance
- **Hem** — minimum-clearance violation
- **Pen.** — percentage of garment vertices with negative signed gap

Lower values indicate better alignment for all four metrics.
