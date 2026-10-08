# Slither Sam Prompt Evolver

**An independent educational experiment in evolutionary prompt optimization for Microsoft's Slither Slam activity.**

This project asks: **Can an evolutionary algorithm improve the strategy prompt used to generate a SnakeBot?** It is planned as a supplement to an Hour of AI session in December 2026 and as an independent professional portfolio project.

> [!IMPORTANT]
> **Current status: requirements/design baseline plus implemented configuration validation, local run storage, and offline scoring.** The remaining SDLC capabilities describe planned software. Automated tournaments, live-provider integration, isolation, and recorded-session results still require implementation and verification. The offline increments have verified tests; no experimental improvement or passing system acceptance is claimed.

## Project Goals

* Explore prompt engineering, automated testing, fitness functions, evolutionary algorithms, and optimization.
* Compare a frozen baseline with evolved strategy prompts under equal conditions.
* Investigate generation variation, overfitting, and generalization using independent bot samples and withheld trials.
* Demonstrate requirements, architecture, design, algorithms, construction planning, verification, and honest portfolio evidence.

A repeatable experiment with a well-supported negative or inconclusive finding can still be a successful project.

## Initial Delivery Paths

| Path | Intended Use | Model Credentials |
| --- | --- | --- |
| Automated prototype | Local Python command line coordinates generation, JavaScript matches, scoring and evolution; browser displays game behavior. | Supplied by whoever runs the experiment. |
| Guided experiment | Participants revise prompts, observe trials, and compare documented results. | Not required for importing manual observations. |
| Recorded replay | Facilitator displays real saved outcomes and trusted state events. | Not required; replay does not execute stored bot source. |

The first interface is a **local command line plus browser game**. A browser dashboard may be added later.

## How the Experiment Works

1. Run a small pilot and choose provider/model, workload, and finite spending/request limits.
2. Freeze the baseline strategy, generation context, game/API profile, model settings, and scoring version.
3. Generate multiple independent bot implementations for each strategy prompt.
4. Validate outputs, evaluate equal opponent/seed schedules, and preserve failures and raw records.
5. Score prompts, select parents, and create new strategies through mutation and crossover.
6. Freeze the selected prompt and compare fresh generated samples with the baseline on withheld seeds.
7. Export the actual evidence, costs, lineage, and limitations.

The **strategy prompt** evolves. Generated bot source is evaluated and preserved; it is not directly evolved or silently repaired. This is evolutionary search, not GAN training.

## Fitness Function

The implemented scoring-version-1 starting formula is:

```text
fitness = 0.70 × overall_effective_win_rate
        + 0.30 × worst_opponent_effective_win_rate
```

Effective rates use a complete scheduled-trial denominator. Invalid generated samples receive explicit zero-credit synthetic trial records. These records are distinguished from played games. Draws score zero; bot-caused failures and infrastructure faults are handled separately.

For example, equal-schedule rates of 92%, 88%, 90%, and 20% produce a fitness of **0.5675**. This is an arithmetic example, not an experiment result. The complete versioned policy is in [Design](./docs/20_design.md#main-processing-flow).

## Avoiding Misleading Results

Use equal schedules, multiple generated samples, preserved source/configuration hashes, and a disjoint holdout set. Only optimization results influence selection. Fresh holdout generations help assess the prompt rather than only a saved winning bot.

Saved-source replay can be reproducible even when the provider cannot reproduce identical generated source. Small pilots, reused elite samples, shared seeds, known opponents, and game-engine quirks limit what conclusions we can draw. A tournament score is evidence under the tested profile, not proof of correctness or optimal play.

## Software Development Lifecycle

| Artifact | Purpose |
| --- | --- |
| [Overview](./docs/00_overview.md) | Problem, stakeholders, capabilities and observable success. |
| [Requirements](./docs/10_requirements.md) | Stable requirements, acceptance criteria and traceability. |
| [Design](./docs/20_design.md) | Contracts, records, algorithms, failures and configuration. |
| [Architecture](./docs/21_architecture.md) | Components, trust boundaries and architectural decisions. |
| [Editable diagrams](./docs/23_diagram.drawio) | Experiment flow and system boundaries. |
| [Pseudocode](./docs/26_pseudocode.txt) | Language-independent control flow using LET. |
| [Program Design Language](./docs/29_pdl.md) | Implementation-oriented refinement and invariants. |
| [Construction plan](./docs/30_construction.md) | Incremental work, integration and quality gates. |
| [Test plan](./docs/40_testing.md) | Planned procedures and required execution evidence. |

Diagram previews: [experiment flow](./docs/23_diagram_flow.svg) and [system boundaries](./docs/23_diagram_architecture.svg). Text explanations remain available in the overview, architecture, design and pseudocode.

## Configuration Validation

The first construction increment validates experiment settings locally. From the repository root in Bash, using Python 3.12 or later:

```bash
PYTHONPATH=src python -m slither_evolver validate --config configs/offline.example.json
```

The supplied configuration uses synthetic opponents, hashes, and limits. It is an offline validation example, not a recommended pilot configuration. Add `--live` to check the fields required for future live requests; the supplied example intentionally fails because provider/budget decisions are still open. Neither check makes model requests, reads credentials, or runs bots.

[Configuration contract and commands](./docs/11_configuration.md) · [Actual validation evidence](./docs/41_configuration_validation.md)

Run the standard-library tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

All 87 tests (26 configuration, 35 storage, and 26 scoring) passed on Ubuntu 24.04.3 with Python 3.12.14. Tournaments, the report workflow, and the experiment coordinator remain planned. Full scheduler recovery is not implemented.

## Local Run Storage

Create an empty synthetic evidence store from the example:

```bash
PYTHONPATH=src python -m slither_evolver init \
  --config configs/offline.example.json \
  --provenance synthetic \
  --description "Synthetic configuration fixture; no played games."
```

Inspect it with `PYTHONPATH=src python -m slither_evolver inspect --run runs/synthetic-config-check`. Existing run IDs are never overwritten. Initialization preserves configuration and declared source/model context; it does not execute an experiment.

For a save/reload demonstration with handwritten prompts and source text, run `PYTHONPATH=src python examples/storage_demo.py`. It stores two prompts and two samples, labels them synthetic, and never runs the bot text.

[Storage contract and recovery limits](./docs/12_local_storage.md) · [Actual storage evidence](./docs/42_storage_validation.md)

## Offline Scoring

Run the independently checked arithmetic example:

```bash
PYTHONPATH=src python examples/scoring_demo.py
```

Expected synthetic fitness: **0.5675**, exactly **227/400**. No actual games or provider requests occur. For the complete JSON summary:

```bash
PYTHONPATH=src python -m slither_evolver score \
  --config fixtures/scoring/design_example.config.json \
  --results fixtures/scoring/design_example.results.json
```

Scoring requires every configured sample/opponent/seed slot exactly once. Invalid-generation exposures count as synthetic zero-credit slots; missing results, infrastructure faults, and interruptions block final fitness. Provenance labels stay in the summary.

[Scoring/result contract](./docs/13_offline_scoring.md) · [Actual scoring evidence](./docs/43_scoring_validation.md)

## Offline Scoring

Run the independently checked arithmetic example:

```bash
PYTHONPATH=src python examples/scoring_demo.py
```

Expected synthetic fitness: **0.5675**, exactly **227/400**. No actual games or provider requests occur. For the complete JSON summary:

```bash
PYTHONPATH=src python -m slither_evolver score \
  --config fixtures/scoring/design_example.config.json \
  --results fixtures/scoring/design_example.results.json
```

Scoring requires every configured sample/opponent/seed slot exactly once. Invalid-generation exposures count as synthetic zero-credit slots; missing results, infrastructure faults, and interruptions block final fitness. Provenance labels stay in the summary.

[Scoring/result contract](./docs/13_offline_scoring.md) · [Actual scoring evidence](./docs/43_scoring_validation.md)

## Getting Started

Start with the original [Slither Slam activity](https://aka.ms/slither-slam), then read the project overview and requirements. The validation, initialization, inspection, and scoring commands above are implemented. Experiment runtime setup and the other command names in the design documents remain proposed until their implementation and pilot verification.

The December session can use manual observations or genuine recorded results if live automation is unavailable. Those real bundles must be produced and reviewed during construction; synthetic fixtures cannot substitute for claimed experimental findings.

## Questions to Explore

* Does evolution outperform the frozen baseline under withheld conditions?
* Which strategy instructions change, and which changes help consistently?
* How much variation comes from the prompt versus generated implementations?
* Does a shorter strategy work as well as a longer one?
* How do cost, sample count, opponents, and scoring choices affect conclusions?
* Can another person reproduce the saved-bot results and explain the evidence?

## Responsible Use and Contributing

Treat AI-generated code as unverified. Execute it only after the project's isolation, resource-limit, and trusted-outcome checks pass. Keep credentials out of game processes and exports; do not collect participant personal data.

When proposing changes, identify affected requirement/decision/test IDs and preserve **change the prompt, measure the result**. Changes to game rules, API, model, opponents, scoring or schedules require a new versioned comparison. Record individual contributions, reused sources and AI assistance, together with human verification.

## Original Activity and License

* [Slither Slam student activity](https://aka.ms/slither-slam)
* [Slither Slam educator resources](https://aka.ms/slither-slam-educator)

The inspected repository contains a Microsoft MIT [LICENSE](./LICENSE). Preserve applicable notices when copying/adapting that source. Check separate terms for external materials, assets and services before incorporation. This project does not claim that a root notice licenses every externally referenced resource.

## Acknowledgements

Thank you to **Microsoft's Hour of AI and Visual Studio Code for Education teams** for the original Slither Slam learning experience and resources.

Special thanks to **Ben Villalobos**, creator of Slither Slam, for the approachable activity that inspired this experiment.

**Slither Sam Prompt Evolver is an independent educational extension and is not an official Microsoft project.**
