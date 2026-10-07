# Slither Sam Prompt Evolver | Software Solution Overview

**Document status:** Initial design baseline, version 0.1.0. Describes planned software; implementation and execution evidence are not claimed.

<!-- omit from toc -->
## Table of Contents

- [Problem or Need](#problem-or-need)
- [Solution Purpose](#solution-purpose)
- [Users and Stakeholders](#users-and-stakeholders)
- [Solution Overview](#solution-overview)
- [Inputs](#inputs)
- [Processing](#processing)
- [Outputs](#outputs)
- [Major Workflow](#major-workflow)
- [Assumptions and Constraints](#assumptions-and-constraints)
- [Success Criteria](#success-criteria)
- [Related Documents](#related-documents)
- [References](#references)

## Problem or Need

Manual prompt improvement can be difficult to evaluate. One lucky game or one unusually strong generated program can make a prompt appear better than it is. Learners and portfolio reviewers need a clear way to see what changed, how it was tested, and what the evidence supports.

The project also needs a dependable December 2026 Hour of AI extension. Live model requests may be slow, costly, or unavailable during a session, so the learning experience must also work with guided trials and recorded evidence.

## Solution Purpose

Slither Sam Prompt Evolver will compare prompts that ask an LLM to generate a SnakeBot for Microsoft's Slither Slam game. An evolutionary search will select and change strategy instructions, generate bots, and measure their performance against a fixed evaluation schedule.

The project will also demonstrate the SDLC through a professional portfolio: requirements, design decisions, algorithms, planned tests, and eventually genuine execution evidence. A functioning experiment is useful even if evolution does not improve the prompt.

## Users and Stakeholders

| User or Stakeholder | Role or Need |
| --- | --- |
| Independent project developer | Builds and maintains the experiment and explains technical decisions. |
| Experiment operator | Supplies credentials, selects limits, runs the pilot, and reviews costs and results. |
| Instructor Mike / session facilitator | Uses a guided exercise or recorded demonstration during Hour of AI. |
| Participants | Explore the relationship between prompts, generated code, tests, and performance. |
| Portfolio reviewer | Examines traceability, reproducibility, honest findings, and the developer's contribution. |
| Microsoft and original creator Ben Villalobos | Receive attribution and preservation of applicable source notices. |

## Solution Overview

### Major Capabilities

- Run a small pilot before selecting provider, model, and spending settings.
- Run automated prompt generations from a local command line and view game behavior in a browser.
- Collect manual trials or replay recorded results without model credentials.
- Compare a frozen baseline with evolved prompts and export readable evidence.
- Preserve decisions, lineage, failures, and limitations for portfolio review.

## Inputs

| Input | Source | Purpose |
| --- | --- | --- |
| Baseline and candidate strategy prompts | Project files or operator | Define the instructions being compared. |
| Frozen game/API and system instructions | Versioned Slither Slam source | Keep generation and evaluation contracts consistent. |
| Provider, model, and budget configuration | Experiment operator after pilot | Select services and bound work and spending. |
| Opponents, seeds, and match settings | Versioned experiment profile | Create equal test conditions. |
| Manual observations or recorded bundles | Guided participants / previous real runs | Support the session without live generation. |

## Processing

1. Validate configuration and record the experiment's fixed conditions.
2. Generate several independent bots from each prompt and validate their interface.
3. Run equal scheduled trials and record outcomes and failures.
4. Score prompts, retain selected strategies, and produce new prompts through mutation and crossover.
5. Freeze the selected prompt and compare fresh bot samples with the baseline on withheld conditions.
6. Export the evidence and its limitations; display existing records when live work is unsuitable.

## Outputs

| Output | Destination | Purpose |
| --- | --- | --- |
| Prompt population and lineage | Local experiment bundle | Explain how strategies changed. |
| Generated bot samples and provenance | Local experiment bundle | Preserve what was actually evaluated. |
| Slot-level outcomes and diagnostics | JSON/CSV records | Support correct scoring and investigation. |
| Baseline, generation, and holdout summaries | Markdown/JSON/CSV reports | Communicate measured findings. |
| Replay events and guided worksheets | Session material | Provide a usable December fallback. |

## Major Workflow

The operator starts with a pilot, chooses limits, and launches a bounded experiment. The software iterates on prompts using optimization matches, then evaluates a frozen selection on a separate holdout schedule. The facilitator can instead import manual observations or review a recorded bundle.

See the two editable pages in [23_diagram.drawio](./23_diagram.drawio): experiment control flow and system boundaries.

## Assumptions and Constraints

### Assumptions

Python will coordinate experiments; JavaScript will run the existing game. The first interface is a local command line plus browser game. A dashboard may follow later. Provider/model/budget and trial counts remain configurable and are selected after a small pilot.

### Constraints

Only the strategy prompt evolves. The generation context, game profile, scoring version, and comparison schedule remain fixed within an experiment. Generated code requires a verified isolated execution environment. Real recorded results must be collected during construction; this document package contains no invented tournament evidence.

## Success Criteria

- The automated prototype completes a bounded run or clearly explains a recoverable interruption.
- A reader can recalculate scores from complete exported records and inspect the baseline comparison.
- The guided session works without participant API keys using manual observations or actual recorded results.
- The portfolio separates decisions, proposed work, tested behavior, and unresolved limitations.
- Improvement is measured honestly; a negative or inconclusive finding does not make the engineering project unsuccessful.

## Related Documents

- [Requirements](./10_requirements.md)
- [Design](./20_design.md)
- [Architecture](./21_architecture.md)
- [Diagram](./23_diagram.drawio)
- [Pseudocode](./26_pseudocode.txt)
- [Program Design Language](./29_pdl.md)
- [Construction](./30_construction.md)
- [Testing](./40_testing.md)

## References

- [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
- [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
- [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
- [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Solution Overview"
description: "Initial project baseline for software solution overview."
document_type: "Software Solution Overview"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.0"
updated: "2026-10-07T16:12:51-04:00"
toc: true
tags: ["overview", "software-development", "portfolio"]
-->
