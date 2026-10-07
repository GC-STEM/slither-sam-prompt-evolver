# Slither Sam Prompt Evolver | Software Requirements Specification

**Document status:** Baseline revision 0.1.1. Configuration validation has implementation/test evidence; other planned capabilities remain unverified.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Product Context](#product-context)
* [Functional Requirements](#functional-requirements)
* [Data Requirements](#data-requirements)
* [External Interface Requirements](#external-interface-requirements)
* [Nonfunctional Requirements](#nonfunctional-requirements)
* [Technology and Implementation Constraints](#technology-and-implementation-constraints)
* [Legal, Regulatory, Policy, and Ethical Constraints](#legal-regulatory-policy-and-ethical-constraints)
* [Acceptance Criteria](#acceptance-criteria)
* [Requirements Traceability](#requirements-traceability)
* [Requirement Priorities and Release Allocation](#requirement-priorities-and-release-allocation)
* [Risks, Conflicts, and Open Issues](#risks-conflicts-and-open-issues)
* [References](#references)

## Purpose and Scope

### Purpose

Define the initial product baseline and the evidence needed to decide whether the automated prototype and guided-session materials are usable. Requirements guide construction and verification; they do not certify an implementation.

### Product Scope

A local educational experiment for evolutionary optimization of Slither Slam strategy prompts, with manual-result import and recorded-result replay. The project is an independent portfolio artifact, not a graded course assignment.

### Intended Audience

Developer, experiment operator, facilitator, testers, maintainers, and portfolio reviewers.

### Definitions, Acronyms, and Abbreviations

| Term | Meaning |
| --- | --- |
| LLM | Large language model used to generate bot source. |
| Prompt / genotype | Strategy instructions changed by evolutionary search. |
| Bot sample / phenotype | One independent generated JavaScript implementation. |
| Fitness | Versioned numerical measure used to select prompts. |
| Evaluation slot | One scheduled bot-sample/opponent/seed/configuration trial. |
| Optimization set | Trials that can influence prompt selection. |
| Holdout set | Withheld trials used only after selection is frozen. |
| Replay | Display of recorded events, without re-running stored generated code. |

## Product Context

### Problem Statement

The project needs comparable evidence about prompt quality and a dependable learning demonstration. Single games and single generated programs cannot establish that a prompt improved.

### Product Perspective

New experiment tooling around existing Slither Slam source. The bundled `index.yml` contains game, opponent, helper, system-prompt, and browser resources. Configuration validation is now implemented; see [its contract](./11_configuration.md) and [execution evidence](./41_configuration_validation.md). The original placeholder files remain templates, and the optimizer/game pipeline is not yet implemented.

### Stakeholders and User Classes

| Stakeholder or User Class | Goals / Needs | Relevant Characteristics |
| --- | --- | --- |
| Developer / operator | Traceable implementation, bounded costs, repeatable experiments | Comfortable with Python, terminal, and local setup. |
| Facilitator / participants | Understand results and continue despite unavailable live APIs | Participants need not have credentials or development environments. |
| Reviewer / maintainer | Inspect evidence and identify individual contributions | Must distinguish plans and fixtures from genuine run results. |

### Operating Environment

Local Python coordinator and JavaScript browser game on an operator-controlled computer. Ubuntu is the proposed reference environment; Windows and macOS are portability targets to verify during the pilot. Python 3.12 is a proposed baseline consistent with the introductory course; exact browser, Node/tooling, and package versions must be selected, tested, and recorded before claiming support.

### Assumptions and Dependencies

An operator supplies provider credentials for live generation. Provider/model and spending cap are selected after a pilot. The game adapter, deterministic execution profile, isolation, and API parity require proof of concept. No public hosting or participant sign-in is required for the initial version.

### Scope Boundaries

#### In Scope

Pilot planning, provider adapter, prompt population and lineage, multiple generated samples, validated/isolated game evaluation, scoring, evolution, holdout comparison, checkpoints, local reports, guided import, and inert replay.

#### Out of Scope

Model training, GAN training, direct source-code evolution, arbitrary generated-code execution on the host, multi-user hosting, browser dashboard, cloud deployment, institutional policy approval, and guaranteed competitive improvement. A later dashboard needs a new requirements increment.

## Functional Requirements

| ID | Requirement | Rationale / Source | Priority | Acceptance Evidence |
| --- | --- | --- | --- | --- |
| `FR-001` | The system shall validate an experiment configuration before any model request or generated-code execution. | Operator-controlled experiment | Must | `TC-001` |
| `FR-002` | The command line shall provide distinct pilot, evolve, guided, replay, report, and resume workflows. | Confirmed local interface and dual delivery paths | Must | `TC-002` |
| `FR-003` | The system shall preserve an unchanged baseline prompt and fixed generation context for each experiment. | Baseline comparison and prompt-only optimization | Must | `TC-003` |
| `FR-004` | The system shall create a configured population of distinct strategy prompts with stable identifiers and parent/operator lineage. | Evolutionary search and portfolio evidence | Must | `TC-004` |
| `FR-005` | The system shall obtain a configured number of independent bot samples per prompt through a replaceable provider adapter, reusing compatible saved optimization samples when available. | Confirmed provider flexibility and sampling variation | Must | `TC-005` |
| `FR-006` | The system shall validate each returned bot against the frozen playerAI interface before accepting it for evaluation. | Bundled game API and unverified generated code | Must | `TC-006` |
| `FR-007` | The JavaScript runner shall evaluate accepted bots under a versioned game profile with recorded seed, clock policy, and match limits. | Controlled game evaluation | Must | `TC-007` |
| `FR-008` | The scheduler shall assign every prompt the same opponent, seed, configuration, and sample-count schedule within a comparison. | Fair comparisons | Must | `TC-008` |
| `FR-009` | The system shall record a terminal result or explicit interruption for each scheduled evaluation slot. | Complete denominators and diagnostic evidence | Must | `TC-009` |
| `FR-010` | The scorer shall compute prompt fitness using the versioned formula and failure policies specified in the design. | Existing README 70/30 starting formula | Must | `TC-010` |
| `FR-011` | The evolution engine shall construct each next population using recorded selection, mutation, crossover, and elite-retention rules. | Evolutionary algorithm | Must | `TC-011` |
| `FR-012` | The system shall stop scheduling work covered by a configured generation, request, spending, or elapsed-time limit when that limit is reached. | Bounded experiment | Must | `TC-012` |
| `FR-013` | The reporter shall export human-readable Markdown and machine-readable JSON/CSV results with baseline comparisons and limitations. | Session and portfolio evidence | Must | `TC-013` |
| `FR-014` | The system shall checkpoint completed work and resume only when the experiment manifest remains compatible. | Recoverability and cost control | Must | `TC-014` |
| `FR-015` | Guided mode shall import manually collected results with provenance and validation without issuing model requests. | Confirmed guided-session path | Must | `TC-015` |
| `FR-016` | Replay mode shall display an existing result bundle without model requests or executing stored generated source. | Recorded-session fallback | Must | `TC-016` |
| `FR-017` | The system shall reserve a disjoint holdout seed set and evaluate the selected prompt and baseline once selection is frozen. | Generalization check | Must | `TC-017` |
| `FR-018` | Pilot mode shall estimate workload and enforce operator-supplied request and spending bounds before live requests. | Confirmed pilot before selecting provider/model/budget | Must | `TC-018` |
| `FR-019` | The system shall distinguish bot-caused failures from provider, runner, and storage failures in scoring and reporting. | Avoid biased fitness from infrastructure faults | Must | `TC-019` |
| `FR-020` | The runner shall accept only validated direction decisions from generated-code execution and calculate outcomes in trusted game code. | Protect evaluation integrity | Must | `TC-020` |
| `FR-021` | The manifest shall identify source commit, game/API/system-prompt hashes, model settings, experiment configuration, and artifact hashes. | Reproducibility and audit trail | Must | `TC-021` |
| `FR-022` | The final report shall include optimization and holdout results for the baseline and selected prompt using the same sample and match schedule. | Honest evidence of prompt performance | Must | `TC-022` |

### Use Cases or User Stories

* **UC-01 — Pilot:** An operator validates a small configuration, reviews workload/cost bounds, and collects enough evidence to choose provider/model/run settings (FR-001, FR-002, FR-018).
* **UC-02 — Evolve:** An operator completes an optimization run and freezes a selected prompt for holdout comparison (FR-003–FR-014, FR-017, FR-019–FR-022).
* **UC-03 — Guide/replay:** A facilitator imports manual records or displays an existing bundle without provider access (FR-015–FR-016).
* **UC-04 — Resume:** An interrupted experiment resumes only compatible completed work, retaining ambiguous request costs (FR-012, FR-014, FR-018–FR-019).

## Data Requirements

### Inputs

| Input | Source | Type / Format | Validation / Constraints | Related Requirements |
| --- | --- | --- | --- | --- |
| Experiment config | Operator | Versioned UTF-8 JSON | Positive finite limits; known schema; disjoint seed sets; live provider and cost bound required | FR-001, FR-018 |
| Strategy population | Project/operator | UTF-8 text + JSON metadata | Nonempty; configured length limit; distinct hashes; fixed API context | FR-003–FR-004 |
| Model response | Provider adapter | Raw text + metadata | Bounded size; single supported code block or plain code; playerAI contract; retain original | FR-005–FR-006 |
| Match request | Scheduler | Versioned JSON | Known sample, opponent, seed, profile and resource limits | FR-007–FR-008 |
| Manual results | Facilitator | CSV + provenance manifest | Unique IDs; allowed statuses; explicit opponent/configuration; unknown seed remains unknown | FR-015 |
| Replay bundle | Existing experiment | JSON/events + manifest | Hashes, schemas and provenance; render strings as inert text | FR-016, FR-021 |

### Outputs

| Output | Destination | Type / Format | Required Characteristics | Related Requirements |
| --- | --- | --- | --- | --- |
| Manifest / checkpoints | Local run directory | JSON | Source/settings hashes; schema/scoring versions; atomic checkpoints | FR-014, FR-021 |
| Generation and match records | Local run directory | JSONL / CSV | Full schedule; raw and aggregate values; status and reason | FR-009–FR-010 |
| Comparison report | Local run directory | Markdown/JSON/CSV | Baseline and selected prompt; sample counts, failures, limitations; no fabricated results | FR-013, FR-022 |
| Replay events | Local run directory | JSONL | Trusted state events only; no executable viewer content | FR-016 |

### Persistent Data

Keep immutable source responses, extracted source, prompts, lineage, manifests, request reservations, outcomes, and report versions. Hash artifacts; checkpoint by atomic replacement. Raw bot artifacts stay local by default. Publish only reviewed, credential-free portfolio evidence. Retention and deletion are operator-controlled; no participant personal information is needed.

### Data Privacy and Sensitivity

Credentials are transient operator secrets, read only by the trusted provider adapter. They do not enter game workers, manifests, or exports. Prompts sent to an external provider are disclosed in the run manifest; use project/game data without student names, grades, or other personal information.

## External Interface Requirements

### User Interfaces

Terminal commands with explicit offline/live modes, help, progress, and error recovery. Browser visualization is supplemental; readable reports explain all outcomes. Proposed commands and exit statuses are specified in the design and are not yet runnable.

### Software Interfaces and APIs

A provider adapter accepts a generation request and returns raw content, provider/model identifiers, request identifiers when available, settings, usage, and charge status. A JavaScript runner accepts a versioned match request and returns trusted direction/state/outcome records. Generated source implements the frozen `playerAI(player)` contract and supported game helpers. The current source defines Direction values as strings; the activity's prose description is not a substitute for inspected code.

### Hardware and Device Interfaces

No dedicated devices or sensors. Ordinary local computer, terminal, and browser only.

### Communication Interfaces

Configured provider HTTPS requests occur in the trusted coordinator. Any local viewer binds to loopback only. Generated-code workers have no network access. No unattended live requests occur in CI.

## Nonfunctional Requirements

### Performance and Efficiency

* **NFR-001:** No paid request may start without a finite request cap and a conservative cost reservation that fits the remaining spending cap. Evidence: `TC-023`.
* **NFR-009:** The runner shall enforce configured source-size, message-size, per-decision time, per-match frame, memory, and run-time limits. Evidence: `TC-031`.

### Reliability, Availability, and Recoverability

* **NFR-002:** After forced interruption, every completed evaluation shall be recovered once, with no duplicate terminal records or automatic reissue of ambiguous paid requests. Evidence: `TC-024`.
* **NFR-008:** Rerunning a saved bot on an identical supported runner profile and seed shall reproduce the recorded direction trace and terminal result. Evidence: `TC-030`.

### Security

* **NFR-003:** Generated-code execution shall have no access to provider credentials, host files, or network services, and shall be terminable within the configured deadline. Evidence: `TC-025`.

### Privacy

* **NFR-004:** Result bundles shall contain no credentials or participant personal data; export validation shall reject known secret markers. Evidence: `TC-026`.

### Usability and Accessibility

* **NFR-005:** Every command shall provide help and actionable errors; reports shall remain readable with keyboard access and without color, diagrams, or animation. Evidence: `TC-027`.

### Maintainability and Supportability

* **NFR-006:** Scoring, configuration, evolution, storage, and provider contracts shall be testable without live APIs or generated-code execution. Evidence: `TC-028`.
* **NFR-010:** Every reported fitness value shall be recalculable from an exported configuration and complete slot-level evidence. Evidence: `TC-032`.

### Portability, Compatibility, and Interoperability

* **NFR-007:** The pilot shall reproduce a local smoke run on the reference Ubuntu environment and document Windows/macOS results as tested or unverified. Evidence: `TC-029`.


### Scalability

Initial execution is sequential and bounded. Distributed processing and concurrent live requests are deferred. Scale values are experiment configuration, not promised capacity.

## Technology and Implementation Constraints

Confirmed: Python coordinator, JavaScript game, local command line/browser interface, replaceable LLM provider adapter, operator-owned credentials, configurable pilot-selected settings. Preserve source notices and distinguish strategy edits from engine/profile edits. Do not automate a signed-in consumer chat interface as a substitute for a provider adapter.

## Legal, Regulatory, Policy, and Ethical Constraints

The inspected root LICENSE contains the Microsoft MIT notice. Preserve applicable notices in copied or adapted source and document provenance; the presence of a license file does not establish terms for every external asset or service. This extension is independent and not an official Microsoft product. Record AI assistance and human verification in portfolio evidence. Do not represent synthetic fixtures as experimental findings or a win rate as proof of correctness.

## Acceptance Criteria

* **AC-01:** Automated path completes a small configured run with full schedule evidence, correct fitness, lineage, and a compatible restart demonstration.
* **AC-02:** Pilot establishes game-profile parity and execution isolation before generated bots run in live experiments.
* **AC-03:** Guided/manual import and replay work without credentials, provider requests, or stored-bot execution during replay.
* **AC-04:** Baseline and frozen selected prompt receive equal fresh holdout evaluation; conclusions reflect actual evidence, including no improvement.
* **AC-05:** All Must requirements and associated tests pass for the declared release environment; blocked/unexecuted tests remain explicitly recorded.
* **AC-06:** Publishable evidence contains attribution, source/configuration provenance, and no credentials or participant data.

## Requirements Traceability

Implementation paths below are planned, not evidence that files exist. The same test IDs appear in the test plan.

| Requirement ID | Source | Architecture / Design | Implementation | Verification |
| --- | --- | --- | --- | --- |
| `FR-001` | Operator-controlled experiment | SAD components / SDD contracts and algorithms | `src/slither_evolver/config.py` | `TC-001` |
| `FR-002` | Confirmed local interface and dual delivery paths | SAD components / SDD contracts and algorithms | `src/slither_evolver/cli.py` | `TC-002` |
| `FR-003` | Baseline comparison and prompt-only optimization | SAD components / SDD contracts and algorithms | `src/slither_evolver/prompts.py` | `TC-003` |
| `FR-004` | Evolutionary search and portfolio evidence | SAD components / SDD contracts and algorithms | `src/slither_evolver/evolution.py` | `TC-004` |
| `FR-005` | Confirmed provider flexibility and sampling variation | SAD components / SDD contracts and algorithms | `src/slither_evolver/providers/base.py` | `TC-005` |
| `FR-006` | Bundled game API and unverified generated code | SAD components / SDD contracts and algorithms | `src/slither_evolver/validation.py` | `TC-006` |
| `FR-007` | Controlled game evaluation | SAD components / SDD contracts and algorithms | `src/slither_evolver/runner/controller.js` | `TC-007` |
| `FR-008` | Fair comparisons | SAD components / SDD contracts and algorithms | `src/slither_evolver/evaluation.py` | `TC-008` |
| `FR-009` | Complete denominators and diagnostic evidence | SAD components / SDD contracts and algorithms | `src/slither_evolver/storage.py` | `TC-009` |
| `FR-010` | Existing README 70/30 starting formula | SAD components / SDD contracts and algorithms | `src/slither_evolver/scoring.py` | `TC-010` |
| `FR-011` | Evolutionary algorithm | SAD components / SDD contracts and algorithms | `src/slither_evolver/evolution.py` | `TC-011` |
| `FR-012` | Bounded experiment | SAD components / SDD contracts and algorithms | `src/slither_evolver/orchestrator.py` | `TC-012` |
| `FR-013` | Session and portfolio evidence | SAD components / SDD contracts and algorithms | `src/slither_evolver/reports.py` | `TC-013` |
| `FR-014` | Recoverability and cost control | SAD components / SDD contracts and algorithms | `src/slither_evolver/storage.py` | `TC-014` |
| `FR-015` | Confirmed guided-session path | SAD components / SDD contracts and algorithms | `src/slither_evolver/guided.py` | `TC-015` |
| `FR-016` | Recorded-session fallback | SAD components / SDD contracts and algorithms | `src/slither_evolver/replay.py` | `TC-016` |
| `FR-017` | Generalization check | SAD components / SDD contracts and algorithms | `src/slither_evolver/evaluation.py` | `TC-017` |
| `FR-018` | Confirmed pilot before selecting provider/model/budget | SAD components / SDD contracts and algorithms | `src/slither_evolver/budget.py` | `TC-018` |
| `FR-019` | Avoid biased fitness from infrastructure faults | SAD components / SDD contracts and algorithms | `src/slither_evolver/orchestrator.py` | `TC-019` |
| `FR-020` | Protect evaluation integrity | SAD components / SDD contracts and algorithms | `src/slither_evolver/runner/worker.js` | `TC-020` |
| `FR-021` | Reproducibility and audit trail | SAD components / SDD contracts and algorithms | `src/slither_evolver/storage.py` | `TC-021` |
| `FR-022` | Honest evidence of prompt performance | SAD components / SDD contracts and algorithms | `src/slither_evolver/reports.py` | `TC-022` |
| `NFR-001` | Performance and Efficiency | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/budget.py` | `TC-023` |
| `NFR-002` | Reliability, Availability, and Recoverability | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/storage.py` | `TC-024` |
| `NFR-003` | Security | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/runner/worker.js` | `TC-025` |
| `NFR-004` | Privacy | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/reports.py` | `TC-026` |
| `NFR-005` | Usability and Accessibility | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/cli.py` | `TC-027` |
| `NFR-006` | Maintainability and Supportability | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/providers/base.py` | `TC-028` |
| `NFR-007` | Portability, Compatibility, and Interoperability | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/cli.py` | `TC-029` |
| `NFR-008` | Reliability, Availability, and Recoverability | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/runner/controller.js` | `TC-030` |
| `NFR-009` | Performance and Efficiency | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/runner/controller.js` | `TC-031` |
| `NFR-010` | Maintainability and Supportability | SAD quality strategies / SDD limits and recovery | `src/slither_evolver/scoring.py` | `TC-032` |

## Requirement Priorities and Release Allocation

All listed requirements are Must for the combined initial prototype/session increment. Build them in vertical slices; guided delivery can be demonstrated earlier than live evolution. Browser dashboard, distributed runs, additional providers, and statistical power studies are deferred increments. A release may document a partial prototype, but cannot claim full acceptance while Must evidence is missing.

## Risks, Conflicts, and Open Issues

| ID | Issue / Risk | Impact | Owner | Status / Resolution |
| --- | --- | --- | --- | --- |
| REQ-ISSUE-001 | Provider/model, prices, budget, and sample/trial counts not selected | Final workload cannot be promised | Operator | Select after pilot; live mode requires explicit finite caps. |
| REQ-ISSUE-002 | Game depends on browser frames and uncontrolled randomness | Repeatability not established | Developer | Prototype seeded/clock-controlled adapter and verify against reference source. |
| REQ-ISSUE-003 | Source collision checks and helper return types may have order/contract surprises | Silent fixes can change comparisons | Developer / operator | Characterize in parity tests; changes require a new profile and baseline. |
| REQ-ISSUE-004 | Exact session date and supported versions unknown | Calendar and portability claims remain provisional | Facilitator / developer | Confirm before release; use milestone offsets and tested-version manifest. |
| REQ-ISSUE-005 | Safe worker execution not yet verified | Generated-source evaluation blocked | Developer | Complete isolation proof and resource-bound tests first. |

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Requirements Specification"
description: "Initial project baseline for software requirements specification."
document_type: "Software Requirements Specification (SRS)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.1"
updated: "2026-10-07T19:05:27-04:00"
toc: true
tags: ["requirements", "srs", "portfolio"]
-->
