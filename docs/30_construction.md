# Slither Sam Prompt Evolver | Software Construction Plan

**Document status:** Baseline revision 0.1.4. Configuration validation, local run storage, offline scoring, and declared-evidence report exports have implementation/test evidence; other capabilities and full system acceptance remain unverified.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Construction Approach](#construction-approach)
* [Development Environment](#development-environment)
* [Source-Code Organization](#source-code-organization)
* [Work Breakdown and Construction Order](#work-breakdown-and-construction-order)
* [Integration Strategy](#integration-strategy)
* [Version Control and Change Management](#version-control-and-change-management)
* [Dependency and Supply-Chain Management](#dependency-and-supply-chain-management)
* [Build and Packaging](#build-and-packaging)
* [Construction Testing](#construction-testing)
* [Code Review and Static Verification](#code-review-and-static-verification)
* [Security During Construction](#security-during-construction)
* [Construction Quality Gates](#construction-quality-gates)
* [Automation and Continuous Integration](#automation-and-continuous-integration)
* [Roles and Responsibilities](#roles-and-responsibilities)
* [Milestones and Schedule](#milestones-and-schedule)
* [Construction Measures and Progress Tracking](#construction-measures-and-progress-tracking)
* [Construction Risks and Mitigations](#construction-risks-and-mitigations)
* [Construction Deliverables](#construction-deliverables)
* [Traceability and Handoff](#traceability-and-handoff)
* [Open Issues](#open-issues)
* [References](#references)

## Purpose and Scope

### Purpose

Guide incremental implementation, integration, and evidence collection for the independent portfolio project. This is a construction plan. The [configuration validator](./11_configuration.md) and [local evidence store](./12_local_storage.md) are implemented parts of W-02; [122 passing tests](./44_report_validation.md) cover configuration, storage, scoring, and [declared-evidence reporting](./14_reports.md). The offline fixture report slice of W-02 is verified. Integrated slot journals, checkpoints, and full recovery remain pending, so W-02 is not fully complete. The optimizer and runner remain planned.

### Construction Scope

Initial automated prototype and guided/replay session increment. Dashboard, distributed jobs, and additional providers are deferred.

### Construction Inputs

[Requirements](./10_requirements.md), [Architecture](./21_architecture.md), [Design](./20_design.md), [Pseudocode](./26_pseudocode.txt), [PDL](./29_pdl.md), editable diagrams, the pinned game bundle, and confirmed project decisions. Review feasibility findings before treating the architecture as ready for live generated-code execution.

## Construction Approach

### Development Method

Use small vertical slices, beginning with offline evidence/scoring and guided mode. Run an early game/isolation spike before investing in a full evolution loop. Integrate a fake provider and runner first, then the verified game adapter and selected live provider. Keep a usable guided demonstration throughout.

### Construction Principles

Prefer readable functions, explicit records and errors, limited dependencies, immutable experiment context, and traceable work items. Preserve raw evidence. Use AI assistance with human review and cite reused sources. Do not evolve source code, silently repair bot outputs, or adjust evaluation conditions mid-run.

### Definition of Construction Complete

A component is complete when its contract, failure behavior, meaningful tests, and documentation agree; its changes have been reviewed; and its traceability is updated. Overall acceptance additionally requires the executed tests, genuine experiment bundle, and release recommendation in the test plan.

## Development Environment

### Languages and Runtimes

Python coordinator and JavaScript game. Propose Python 3.12 and Ubuntu as the first reference environment. Record exact browser, supporting Node/tooling, and package versions after the feasibility spike. Windows and macOS remain unverified until smoke-tested. This baseline does not require students to adopt the project's runtime stack as a course requirement.

### Development Tools

VS Code, Git, Bash as primary shell, Python virtual environment, diagram editor supporting draw.io, Python test runner, and browser developer tools. Select browser automation, JavaScript test tooling, formatting, and linting packages only after verifying the smallest workable dependency set.

### Environment Setup

During implementation, provide a tested setup document that creates an isolated Python environment, installs pinned dependencies, prepares read-only game assets, verifies the disposable browser boundary, and executes an offline smoke run. Credentials are optional until live pilot mode and are supplied through operator-named environment variables. Record the exact successful setup commands; do not publish speculative install commands as verified instructions.

### Coding and Documentation Standards

Use descriptive snake_case Python names, consistent JavaScript names, small single-purpose functions, clear module docstrings, and type hints for contracts. Explain non-obvious scoring and recovery decisions in comments. Use UTF-8 and consistent newline/formatting rules. Keep requirement IDs stable. Replace assignment-only language in implementation templates with project-specific documentation; the source template's course submission and AI prohibitions are not project requirements under the user's independent-project scope.

## Source-Code Organization

| Planned Path | Purpose |
| --- | --- |
| `src/slither_evolver/cli.py`, `config.py`, `orchestrator.py` | Command routing, input validation, run state and scheduling. |
| `src/slither_evolver/providers/`, `budget.py` | Provider protocol/implementation and request reservation ledger. |
| `src/slither_evolver/prompts.py`, `evolution.py`, `scoring.py` | Strategy fragments, lineage, seeded search and pure scoring. |
| `src/slither_evolver/validation.py`, `evaluation.py` | Bot contract checks, equal schedules and holdout boundary. |
| `src/slither_evolver/runner/` | Trusted JavaScript controller, restricted worker and helper facade. |
| `src/slither_evolver/storage.py`, `reports.py`, `guided.py`, `replay.py` | Durable evidence, exports, manual import and inert presentation. |
| `tests/` | Unit, contract, integration, misuse and recovery tests. |
| `configs/`, `schemas/`, `prompts/` | Versioned operator examples, schemas and seed strategy bank. |
| `game/` | Original/adapted game assets, original notices and profile manifests. |
| `examples/` | Clearly labeled synthetic fixtures and reviewed genuine recorded-session bundles. |
| `runs/` | Local generated artifacts and credentials-free evidence; raw runs excluded from ordinary commits. |
| `docs/` | SDLC baseline, decisions, setup and final evidence summary. |

Configuration, storage, scoring, reporting, and offline command dispatch now exist with component tests. Other paths are targets. The unused program/test templates have been removed.

## Work Breakdown and Construction Order

| Work Item | Increment / Prerequisites | Deliverable / Gate |
| --- | --- | --- |
| W-01 | Baseline review | Requirements/design decisions and unresolved pilot settings recorded. |
| W-02 | Domain schemas, config, store, scorer | Offline component slice verified: config, prompt/sample store, scorer, fixture report export/recalculation. Integrated slot journals and full recovery pending. |
| W-03 | Guided import and inert replay after W-02 | No-credentials demonstration with labeled fixtures; real data still pending. |
| W-04 | Early game/API/clock/randomness spike | Original/adapted parity findings, profile version and known rule quirks. |
| W-05 | Isolation and limits after W-04 | Capability/deadline tests pass before accepting generated source. |
| W-06 | Provider protocol and budget gate after W-02 | Fake adapter, reservation/retry/recovery tests. |
| W-07 | Small live pilot after W-05/W-06 | Operator-selected model/caps/scale with actual cost/time and validity measurements. |
| W-08 | Seeded search and coordinator | Complete fake-adapter loop, then bounded live evolution. |
| W-09 | Freeze, fresh holdout comparison | Real evidence bundle; conclusion may be positive, negative, or inconclusive. |
| W-10 | Session rehearsal and portfolio release | Usable guided/replay path, clean exports, executed test report and limitations. |

## Integration Strategy

### Integration Order

Schemas/store/scorer → CLI/guided/replay → fake provider and fake runner → verified real runner → bounded live provider → evolution → holdout → session/portfolio package. Game and security feasibility work proceeds early but joins live execution only after its gates pass.

### Integration Verification

At each slice, run the relevant contract/integration tests from [Testing](./40_testing.md). Keep a small deterministic fixture bundle for regression. Record actual results; do not count fixture execution as a real model/tournament finding.

## Version Control and Change Management

### Branching and Commit Practices

Use short feature branches and descriptive commits linked to work items. Review diffs before merging to main. A solo developer may record a structured self-review; a second reviewer is useful for security/scoring, but is not presumed available. Tag a demonstrated release only after its evidence is complete.

### Change Control

A change request states the problem, affected requirement/decision/test IDs, and evidence. Update requirements before implementing material scope changes. Engine/API/model/scoring changes create a new experiment manifest/profile and require a new baseline comparison. Preserve previous records.

### Configuration Items

Version source, schemas, sanitized examples, game source/adaptations/notices, profile manifests, search operators, tests, SDLC documents, setup instructions, and dependency locks. Exclude secrets, operator browser profiles, virtual environments, transient caches, and unreviewed run artifacts.

## Dependency and Supply-Chain Management

| Dependency | Version / Constraint | Purpose | License | Security / Maintenance Notes |
| --- | --- | --- | --- | --- |
| Python | 3.12 proposed; exact patch verified in pilot | Coordinator | Verify distribution notices | Record interpreter and lock environment. |
| Slither Slam source | Pinned inspected commit/profile | Game/API/opponents | Applicable Microsoft MIT notice in repo | Preserve notice; document adaptations and source hashes. |
| p5.js | Original HTML references 1.9.2 | Original browser rendering | Verify package notices before vendoring | Offline asset/source check required; not evidence of current security status. |
| Browser automation / runtime | Select and pin in feasibility spike | Controlled browser and worker lifecycle | Verify selected package terms | No operator browser profile or provider credentials. |
| Provider SDK or HTTP client | Select after provider pilot | Generation adapter | Verify selected package terms | Provider confined to trusted process; minimize dependencies. |
| Test/lint tooling | Select and pin during W-02 | Verification | Verify selected package terms | Offline tests by default; no paid CI calls. |

## Build and Packaging

Package a runnable Python module and versioned JavaScript assets when constructed. Produce a credentials-free example bundle and documented smoke command. Record source commit, dependency locks, game/profile hashes, schemas, and build/test results. A document ZIP is a planning deliverable; it is not the executable release. Clean packaging excludes local keys, raw operator data, browser profiles, and unreviewed generated source.

## Construction Testing

### Unit Testing

Test config boundaries, schedule completeness, 70/30 scoring, lineage, duplicate handling, reservations, and report projections with meaningful independent expected values. Avoid tests that simply reproduce implementation statements. Use synthetic fixtures without real credentials.

### Integration Testing

Test provider/runner contracts, complete fake loops, stored evidence/reports, guided import, replay, controlled game traces, interruption/resume and budget boundaries. Add bounded live smoke tests only after operator configuration and isolation gates pass.

### Test-First / Test-Driven Practices

Write tests before or alongside implementation for scoring, budget, failure classification, and recovery, where wrong behavior can produce misleading results or spending. Formal test-driven development is a suggested practice, not a required ritual for every reversible formatting change.

## Code Review and Static Verification

Review inputs, generated-code boundary, cost ledger, score denominator, holdout leakage, source notices, and exported evidence. Run selected format/lint/type checks and dependency/security checks appropriate to the dependency set. Record results and unresolved findings rather than claiming a blanket security certification.

## Security During Construction

Do not execute generated source until isolation misuse tests pass. Never pass keys to game processes or export them. Treat all model responses and imported files as untrusted. Escape viewer content; verify hashes and bounded messages; enforce deadlines and process/resource limits. Preserve raw responses locally for diagnostics. Follow applicable provider/service terms during the pilot.

## Construction Quality Gates

| Gate | Required Evidence | Failure Response |
| --- | --- | --- |
| QG-01 — Domain | Config, scoring, schedule, provenance and fake-contract tests | Fix before integrating live dependencies. |
| QG-02 — Game | Original/adapted helper/state/outcome parity and deterministic trace checks | Block competitive claims; characterize/version differences. |
| QG-03 — Isolation | No network/files/secrets; enforced deadlines/resource limits | Block generated-code execution. |
| QG-04 — Paid pilot | Finite caps, reservations, selected service metadata, real measurements | Remain in offline/guided mode. |
| QG-05 — Experiment | Complete records, baseline, frozen holdout, recalculable report | Report partial/blocked; do not claim improvement. |
| QG-06 — Release | Executed Must tests, safe reviewed bundle, attribution and rehearsal | Delay full acceptance; publish explicit prototype limitations if appropriate. |

## Automation and Continuous Integration

Plan CI for offline unit/contract tests, schema/doc/link checks and selected linting. Integration tests requiring a browser run only in a controlled documented environment. CI never holds personal provider credentials or starts paid requests by default. A manual bounded live pilot is separate evidence. Workflow files and checks must be implemented and tested before being described as active.

## Roles and Responsibilities

The project developer owns implementation, evidence, integration, and self-review. The operator owns provider credentials, budgets and run decisions; the same person may fill both roles. Instructor Mike facilitates the December session and reviews scope. Portfolio reviewers evaluate evidence, not grades. AI assistance is recorded and independently verified; it does not replace developer responsibility.

## Milestones and Schedule

| Milestone | Target Relative to Session | Exit Evidence |
| --- | --- | --- |
| Baseline and feasibility | By six weeks before | Decisions and game/isolation spike findings. |
| Offline guided slice | By four weeks before | Import/replay/report smoke demonstration. |
| Bounded live pilot and prototype | By three weeks before | Service/scale selected; real small-run records. |
| Holdout and recorded evidence | By two weeks before | Reviewed genuine result bundle and limitations. |
| Rehearsal and freeze | By one week before | Credential-free fallback and session walkthrough. |

These are proposed offsets, not confirmed dates. The facilitator must confirm the exact December 2026 session date. If feasibility slips, deliver a guided/manual experiment with actual recorded evidence and explicitly describe the automated path as incomplete.

## Construction Measures and Progress Tracking

Track verified work-item completion, Must tests executed/passed/blocked, bot validity, record completeness, time/cost per pilot, unresolved parity/isolation issues, and session readiness. Lines of code and prompt length alone are not progress measures.

## Construction Risks and Mitigations

| Risk | Likelihood / Impact | Mitigation | Trigger / Contingency |
| --- | --- | --- | --- |
| Browser/game adapter changes semantics | Medium / high | Early original/adapted parity tests | Suspend comparisons; revise profile and baseline. |
| Isolated execution cannot meet contract | Medium / high | Prove smallest viable boundary before live bots | Use manual/guided path; no unsafe shortcut. |
| Model validity/cost worse than expected | Unknown until pilot / high | Small bounded pilot and replaceable adapter | Change model/settings in new manifest; reduce scale. |
| Schedule exceeds available time | Medium / medium | Vertical slices and recorded fallback | Reduce demonstration scope with honest status. |
| Missing or ambiguous run evidence | Medium / high | Append-only records and checkpoint tests | Block verified report; recover/re-run bounded work. |

## Construction Deliverables

Implemented package and JavaScript adapter; schemas/config examples; dependency locks/notices; automated tests; validated setup; genuine sanitized experiment/replay bundle; guided exercise; executed test/completion report; updated SDLC and portfolio reflection identifying personal contributions and AI assistance.

## Traceability and Handoff

Link each work item to requirement, design, source and test IDs. At test handoff supply exact commit/environment/profile, compatible fixture bundle, known defects, raw outcome/usage records and construction gate status. The requirement table lists planned module paths; replace them with implemented references once source exists.

## Open Issues

Select exact packages/runtimes, provider/model/caps, pilot scale, and December date. Verify game behavior/isolation and resolve desired rule changes through a recorded profile decision. The existing copied Microsoft SECURITY.md is upstream guidance; before public release, establish accurate project-specific reporting contacts rather than implying Microsoft supports this independent extension.

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Construction Plan"
description: "Initial project baseline for software construction plan."
document_type: "Software Construction Plan (SCP)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.4"
updated: "2026-10-08T07:10:16-04:00"
toc: true
tags: ["construction", "implementation", "portfolio"]
-->
