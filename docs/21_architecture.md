# Slither Sam Prompt Evolver | Software Architecture Description

**Document status:** Baseline revision 0.1.4. Configuration validation, local run storage, offline scoring, and declared-evidence report exports have implementation/test evidence; other capabilities and full system acceptance remain unverified.

The configuration, evidence-store, pure offline scorer, and declared-evidence reporter portions now exist. [Local storage](./12_local_storage.md) preserves frozen context and supplied artifacts without instantiating the planned provider, runner, or coordinator. The [scorer](./13_offline_scoring.md) separately validates declared result snapshots and computes complete-schedule fitness; it does not produce trusted outcomes. [Report exports](./14_reports.md) recompute these declarations, publish consistent Markdown/JSON/CSV, and check archived integrity; they are separate from the prompt/sample RunStore and do not authenticate a game or enforce holdout freeze. The architectural trust boundaries and game isolation still need implementation and verification.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Architecture Context](#architecture-context)
* [Architecture Overview](#architecture-overview)
* [Architecture Views](#architecture-views)
* [Interfaces and Integration](#interfaces-and-integration)
* [Quality Attribute Strategies](#quality-attribute-strategies)
* [Technology Stack and Platform Decisions](#technology-stack-and-platform-decisions)
* [Dependencies and Supply-Chain Considerations](#dependencies-and-supply-chain-considerations)
* [Architectural Decisions and Rationale](#architectural-decisions-and-rationale)
* [Architecture Risks and Technical Debt](#architecture-risks-and-technical-debt)
* [Architecture Evaluation](#architecture-evaluation)
* [Traceability to Detailed Design and Testing](#traceability-to-detailed-design-and-testing)
* [Open Issues](#open-issues)
* [References](#references)

## Purpose and Scope

### Purpose

Record the organization and trade-offs that constrain implementation of the initial experiment. This is a proposed architecture awaiting game, isolation, and pilot verification.

### Architecture Scope

Python experiment tooling, JavaScript game adapter, isolated bot execution, local storage/reports, manual import, and inert replay. External model services and VS Code for Education remain outside this system.

### Intended Audience

Developer, operator, facilitator, future maintainers, and portfolio reviewers.

### Definitions, Acronyms, and Abbreviations

An **adapter** translates one external interface into a stable project contract. A **trusted controller** owns real game state and outcomes. A **worker** executes generated decisions using copies of game state. An **experiment profile** versions engine behavior, APIs, timing, seeds, opponents, and limits.

## Architecture Context

### Requirements and Architectural Drivers

| Driver / ASR | Source | Architectural Significance |
| --- | --- | --- |
| FR-005, FR-018, NFR-001 | [Requirements](./10_requirements.md) | Replaceable provider and central cost gate. |
| FR-007, FR-020, NFR-003, NFR-008 | [Requirements](./10_requirements.md) | Trusted outcomes, isolated decisions, deterministic-profile proof. |
| FR-014, FR-021, NFR-002 | [Requirements](./10_requirements.md) | File-based evidence and resumable work. |
| FR-015–FR-016, NFR-005 | [Requirements](./10_requirements.md) | Independent manual/replay path and text-first presentation. |
| FR-017, FR-022 | [Requirements](./10_requirements.md) | Holdout boundary independent of search. |

### Stakeholders and Concerns

| Stakeholder | Architectural Concerns | Relevant View(s) |
| --- | --- | --- |
| Operator | Costs, secrets, stop/restart, repeatability | Runtime, deployment, data |
| Developer / maintainer | Small testable units and replaceable dependencies | Module, logical |
| Facilitator / participants | Reliable offline material and readable results | Scenario, logical |
| Reviewer | Traceability, boundaries, genuine evidence | Data, scenario |

### System Context

The operator invokes a local Python command. Only the provider adapter communicates with an external LLM. The coordinator launches a JavaScript match controller in a disposable browser environment. Generated code runs in a restricted worker that receives state copies and returns direction decisions. Trusted code validates decisions, updates game state, and writes outcome evidence. Local reports and replay consume stored data.

The system-boundary page of [23_diagram.drawio](./23_diagram.drawio) shows these relationships. Reports use stored evidence; replay does not run generated code.

### Assumptions and Constraints

Single operator and sequential jobs initially. Python/JavaScript and a command line/browser interface are confirmed. Reference Ubuntu and Python 3.12 are proposed defaults, not certified compatibility. Provider/model/budget and resource limits are operator configuration after a pilot. The execution boundary must be verified before accepting generated code.

## Architecture Overview

### Architectural Style or Pattern

A modular local pipeline with ports/adapters for model generation and game evaluation. A small coordinator controls workflow; pure functions score and evolve prompts. JSON contracts and a local evidence store connect components. Microservices and a database would add unnecessary initial deployment and administration work.

### Major Architectural Elements

| Element | Responsibility | Interfaces / Dependencies | Related Requirements |
| --- | --- | --- | --- |
| CLI/configuration | Validate mode, inputs, limits, and command intent | JSON config; coordinator | FR-001–FR-002 |
| Coordinator/scheduler | Own run state, equal schedules, stop conditions | Store, provider, runner, scorer | FR-008–FR-009, FR-012, FR-019 |
| Provider/budget adapter | Make bounded requests and preserve raw responses | Configured HTTPS API; operator secret | FR-005, FR-018, NFR-001 |
| Validation/runner | Check interface; isolate decisions; own true outcomes | Browser controller and restricted worker | FR-006–FR-007, FR-020 |
| Scoring/evolution | Rank evidence and construct new strategy prompts | Pure domain records and seeded search RNG | FR-003–FR-004, FR-010–FR-011 |
| Store/reporting | Preserve immutable evidence, resume, export | Local JSON/JSONL/CSV/Markdown | FR-013–FR-014, FR-021–FR-022 |
| Guided/replay | Import manual records and display recorded events | Same schemas with explicit provenance | FR-015–FR-016 |
| Holdout evaluator | Evaluate frozen prompt and baseline outside selection | Disjoint seeds, fresh generated samples | FR-017, FR-022 |

### Key Interactions

The coordinator reserves request cost before generation, validates each response, schedules equal evaluations, and records completed work before scoring. Infrastructure faults suspend the affected work; they do not lower prompt fitness. Only optimization evidence enters selection. Final holdout evaluation is reported after the selected prompt is frozen.

## Architecture Views

### Logical / Capability View

The capabilities are planning, generation, validation, evaluation, scoring, evolution, persistence, comparison, and presentation. Manual import bypasses generation; replay bypasses both generation and bot execution. Scoring is shared between eligible automated and manual bundles, while provenance prevents pooling incomparable data.

### Module / Development View

Planned package `src/slither_evolver/` contains `cli`, `config`, `orchestrator`, `budget`, `prompts`, `validation`, `evaluation`, `scoring`, `evolution`, `storage`, `reports`, `guided`, `replay`, `providers/`, and `runner/`. Domain logic depends on contracts, not provider SDKs. The configuration, storage, scoring, and reporting modules plus offline dispatch in `__main__.py` are implemented. The remaining modules are targets; the unused program template has been removed.

### Component-and-Connector / Runtime View

Python passes bounded JSON requests to the JavaScript adapter and consumes bounded JSON results. A trusted browser controller holds authoritative state. A disposable worker receives a compatible helper facade over copied state and can return only an action. No provider key is passed to the browser, worker, or game directory. The operator may open the separate trusted viewer for visualization.

### Information / Data View

Run ID owns configuration and profile hashes. Prompt IDs own strategy text and lineage. Sample IDs link prompt, raw generation response, and source hash. Slot IDs link sample/opponent/seed/profile to a result. Reports derive from records and do not overwrite them. See the detailed records in [Design](./20_design.md#data-design).

### Process / Concurrency View

One coordinator and one scheduled job at a time initially. A bot worker is the isolation unit, not a mechanism for unbounded parallelism. The controller waits for a valid decision with a deadline; no state advance depends on arrival speed. Provider and match deadlines are separate. Only the coordinator writes the evidence store.

### Deployment / Physical View

Trusted Python runs locally with the operator's credential environment. A separate disposable, least-privilege browser process has no inherited credential environment or user profile and only read-only game assets; generated workers have network restrictions and enforceable deadlines. The local viewer binds to loopback. This is a proposed isolation arrangement: worker syntax filtering or Python subprocess separation alone is insufficient, and live bot execution remains blocked until the environment passes misuse tests.

### Scenario / Use-Case View

**Provider interruption:** A timed-out request keeps its conservative cost reservation and becomes uncertain. The operator resumes after reconciling or retaining that charge bound. Completed samples and slots are reused. Guided/replay mode remains available.

**Game-profile change:** A helper or collision-rule change creates a new profile. The coordinator rejects resume into the previous experiment. Baseline and candidates must be evaluated again under the new profile.

## Interfaces and Integration

### External Interfaces

Provider HTTPS generation API; versioned Slither Slam JavaScript helper contract; local browser visualization; file-based manual import. The project does not presume access to a hosted activity's private generation service.

### Internal Architectural Interfaces

`GenerationRequest → GenerationResult`, `MatchRequest → MatchResult`, `SlotRecords → FitnessResult`, and `RankedPrompts → NextPopulation`. Every message carries schema/run identifiers and bounded values. Errors distinguish configuration, bot, provider, engine, storage, and operator interruption.

### Interoperability

UTF-8 JSON/JSONL for contracts, CSV for tabular exchange, Markdown for reports, JavaScript source for generated bots, and draw.io XML for diagrams. Compatibility follows recorded schemas and hashes; unknown schema versions fail clearly.

## Quality Attribute Strategies

### Performance and Scalability

Sequential execution simplifies cost and resource accounting. Pilot records time per request and match before selecting scale. Skip completed work and deduplicate prompts; cache only with complete context hashes. Do not convert saved elites into extra model requests by default. Parallel execution is deferred.

### Reliability, Availability, and Recoverability

Persist cost reservations before requests; persist completed events before checkpoints. Use atomic manifest/checkpoint replacement. A slot has one terminal record. Uncertain external requests require explicit handling; retries create separate request IDs and reservations. Replay is an operational fallback independent of provider availability.

### Security and Privacy

Separate provider secrets from game execution. The trusted controller determines outcomes; workers receive copied state and cannot modify the real engine. Disable worker network/import capabilities and enforce process/resource boundaries. Escape report/replay content and treat source as inert text. Do not collect participant personal data.

### Maintainability, Modifiability, and Testability

Pure scoring/evolution functions and fake provider/runner adapters permit offline testing. Stable contracts localize service changes. Explicit profile versions expose engine changes. Requirements/test IDs and immutable evidence support investigation and review.

### Usability and Accessibility

Keep command help, progress, errors, and primary results textual. The browser canvas and animation supplement reports and recorded state tables. A future dashboard needs its own accessibility requirements and verification; this baseline makes no WCAG compliance claim.

## Technology Stack and Platform Decisions

Python coordinator; JavaScript game/controller; browser visualization; local files instead of a database. A Python browser-automation adapter and JavaScript workers are candidates for the feasibility spike, not selected dependencies yet. Python 3.12 is proposed; exact browser and supporting runtime/package versions are selected and pinned after pilot testing. The inspected original HTML references p5.js 1.9.2; preserve and verify any vendored dependency before relying on offline display.

## Dependencies and Supply-Chain Considerations

Retain the Microsoft MIT notice for applicable source. Record original and adapted hashes, opponent files, and system instructions from `index.yml`. Confirm terms for each selected provider and package during construction. Pin dependencies after verification; avoid loading arbitrary remote scripts in bot workers. The project cannot claim a completed security review from a dependency list.

## Architectural Decisions and Rationale

| ID | Decision | Alternatives Considered | Rationale / Trade-offs | Consequences |
| --- | --- | --- | --- | --- |
| ADR-001 | Python coordinates; JavaScript preserves game language | JavaScript throughout | User-confirmed curriculum connection and reuse | Requires a tested cross-language contract. |
| ADR-002 | CLI + browser first | Hosted dashboard | User-confirmed smaller initial scope | Dashboard is deferred. |
| ADR-003 | Replaceable provider with operator credentials | One hard-coded model / participant keys | User-confirmed flexibility | Model/cost metadata and adapter tests required. |
| ADR-004 | Automated path plus guided/replay path | Live-only demonstration | User-confirmed session resilience | Real recorded bundles must be produced. |
| ADR-005 | Trusted game controller; untrusted bot decisions isolated | Execute generated source beside coordinator | Protect credentials and result integrity | Isolation proof is a release gate. |
| ADR-006 | File store and sequential execution | Database/distributed jobs | Simpler independent-project operation | Concurrency growth needs redesign. |
| ADR-007 | Freeze optimization context and reserve holdout | Tune against every available result | Honest comparison and reduced leakage | Holdout cannot be used to revise this experiment's winner. |

## Architecture Risks and Technical Debt

Clock/randomness adaptation, helper parity, and isolation are the largest feasibility risks. Original collision checks are sequential and can behave unexpectedly; preserve characterized behavior rather than silently changing it. A learned prompt can exploit a known profile; holdout seeds improve evidence but cannot prove transfer to different games or opponents. Replay data may be large; bounded event capture is configurable. Platform portability and dashboard implementation remain deferred or unverified.

## Architecture Evaluation

Before live evolution, complete a feasibility spike that exercises API/helper parity, deterministic traces, malformed generated responses, isolation, budget reservations, and restart. Review results against FR-007/FR-020 and NFR-001/NFR-003/NFR-008. No architectural quality is reported as verified until its test evidence exists.

## Traceability to Detailed Design and Testing

| Architectural Element / Decision | Detailed Design | Verification |
| --- | --- | --- |
| ADR-001–ADR-004 | CLI, provider, coordinator, guided/replay contracts | TC-001–TC-005, TC-015–TC-018, TC-029 |
| ADR-005 | Validation, game controller, decision worker | TC-006–TC-007, TC-019–TC-020, TC-025, TC-030–TC-031 |
| ADR-006 | Evidence store, reservation ledger, recovery | TC-009, TC-012–TC-014, TC-023–TC-024 |
| ADR-007 | Score, evolution, holdout protocol | TC-008, TC-010–TC-011, TC-017, TC-021–TC-022, TC-032 |

## Open Issues

Operator selects provider/model/budget after pilot. Developer selects and verifies browser automation/isolation packages and exact runtimes. Facilitator confirms the December date. Engine/profile behavior changes require a recorded decision before implementation. Browser dashboard remains a later increment.

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Architecture Description"
description: "Initial project baseline for software architecture description."
document_type: "Software Architecture Description (SAD)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.4"
updated: "2026-10-08T07:10:16-04:00"
toc: true
tags: ["architecture", "sad", "portfolio"]
-->
