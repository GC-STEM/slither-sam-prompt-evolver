# Slither Sam Experiment Report

**Provenance:** SYNTHETIC
**Status:** partial declared evidence

Run: synthetic-report-example
Configuration SHA-256: d2aed42fd4a89f24cc5a0df3de554f700bed6f3e9ed99224da049f69928b285e
Baseline: baseline; selected: selected

**SYNTHETIC FIXTURE — no actual games or experiment findings.**

## Baseline Comparison

Deltas are selected minus baseline within each declared phase.

| Phase | Comparison | Fitness delta | Exact delta |
| --- | --- | --- | --- |
| optimization | unavailable | Not available | Not available |
| holdout | unavailable | Not available | Not available |

## Prompt and Phase Results

Counts are outcome categories in the supplied evidence. Synthetic failures are never played matches.

| Phase | Role | Prompt | Status | Scheduled | Recorded | Played category | Wins | Losses | Draws | Synthetic failures | Fitness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| optimization | baseline | baseline | partial | 12 | 11 | 11 | 6 | 5 | 0 | 0 | Not available |

### optimization: baseline

Provenance note: Handwritten arithmetic fixture; no models, generated bots, or played games.
Declared samples: 2; accepted: 2; invalid: 0.
Blockers: missing samples = 0; missing slots = 1; blocked samples = 0; infrastructure faults = 0; interrupted slots = 0.

| Opponent | Scheduled | Recorded | Wins | Played category | Synthetic failures | Effective rate |
| --- | --- | --- | --- | --- | --- | --- |
| synthetic-opponent-a | 6 | 6 | 4 | 6 | 0 | Not available |
| synthetic-opponent-b | 6 | 5 | 2 | 5 | 0 | Not available |

| Sample | Index | Generation declaration | Scheduled | Recorded | Wins | Missing slots |
| --- | --- | --- | --- | --- | --- | --- |
| sample-0 | 0 | accepted | 6 | 6 | 5 | 0 |
| sample-1 | 1 | accepted | 6 | 5 | 1 | 1 |

## Missing Evidence

* optimization: selected
* holdout: baseline
* holdout: selected

## Limits and Interpretation

* SYNTHETIC: these are arithmetic fixtures, not actual played games or experiment findings.
* Completion means the declared coordinate schedules are complete; it is not system acceptance.
* Provenance, accepted generation, and outcomes are declarations; no source or game is executed by this exporter.
* Independent model sampling, selection freeze, fresh holdout generation, and trusted runner outcomes are not established here.
* Shared source samples/seeds and small workloads limit statistical interpretation; no confidence intervals or significance claims are made.
* Provider usage/cost, elapsed time, lineage search, and parity/isolation evidence are unavailable in this result schema.
* Raw text still needs human review; automated export checks cover known patterns only.

## Recalculation

The export includes normalized config.json, canonical evidence snapshots, exact score ratios, and file hashes.
Use the verify-report command to check files and rebuild every derived format. Hashes are integrity checks, not signatures.
