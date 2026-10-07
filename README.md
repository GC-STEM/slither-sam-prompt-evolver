# Slither Sam Prompt Evolver

**An independent educational experiment in evolutionary prompt optimization for Microsoft's Slither Slam activity.**

This project asks: **Can an evolutionary algorithm improve the strategy prompt used to generate a SnakeBot?** It is planned as a supplement to an Hour of AI session in December 2026 and as an independent professional portfolio project.

> [!IMPORTANT]
> **Current status: requirements and design baseline.** The SDLC files describe planned software. Automated tournaments, live-provider integration, isolation, and recorded-session results still require implementation and verification. No experimental improvement or passing test results are claimed.

## Project Goals

- Explore prompt engineering, automated testing, fitness functions, evolutionary algorithms, and optimization.
- Compare a frozen baseline with evolved strategy prompts under equal conditions.
- Investigate generation variation, overfitting, and generalization using independent bot samples and withheld trials.
- Demonstrate requirements, architecture, design, algorithms, construction planning, verification, and honest portfolio evidence.

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

The proposed starting formula is:

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

## Getting Started

Start with the original [Slither Slam activity](https://aka.ms/slither-slam), then read the project overview and requirements. Runtime setup and executable commands will be published after implementation and pilot verification. Command names in the design documents are proposed interfaces, not currently verified instructions.

The December session can use manual observations or genuine recorded results if live automation is unavailable. Those real bundles must be produced and reviewed during construction; synthetic fixtures cannot substitute for claimed experimental findings.

## Questions to Explore

- Does evolution outperform the frozen baseline under withheld conditions?
- Which strategy instructions change, and which changes help consistently?
- How much variation comes from the prompt versus generated implementations?
- Does a shorter strategy work as well as a longer one?
- How do cost, sample count, opponents, and scoring choices affect conclusions?
- Can another person reproduce the saved-bot results and explain the evidence?

## Responsible Use and Contributing

Treat AI-generated code as unverified. Execute it only after the project's isolation, resource-limit, and trusted-outcome checks pass. Keep credentials out of game processes and exports; do not collect participant personal data.

When proposing changes, identify affected requirement/decision/test IDs and preserve **change the prompt, measure the result**. Changes to game rules, API, model, opponents, scoring or schedules require a new versioned comparison. Record individual contributions, reused sources and AI assistance, together with human verification.

## Original Activity and License

- [Slither Slam student activity](https://aka.ms/slither-slam)
- [Slither Slam educator resources](https://aka.ms/slither-slam-educator)

The inspected repository contains a Microsoft MIT [LICENSE](./LICENSE). Preserve applicable notices when copying/adapting that source. Check separate terms for external materials, assets and services before incorporation. This project does not claim that a root notice licenses every externally referenced resource.

## Acknowledgements

Thank you to **Microsoft's Hour of AI and Visual Studio Code for Education teams** for the original Slither Slam learning experience and resources.

Special thanks to **Ben Villalobos**, creator of Slither Slam, for the approachable activity that inspired this experiment.

**Slither Sam Prompt Evolver is an independent educational extension and is not an official Microsoft project.**
