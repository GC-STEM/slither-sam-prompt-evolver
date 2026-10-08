# Slither Sam Prompt Evolver | Software Test Plan

**Document status:** Baseline revision 0.1.2. Configuration validation and local run storage have implementation/test evidence; other capabilities and full system acceptance remain unverified.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Test Objectives](#test-objectives)
* [Test Scope](#test-scope)
* [Test Strategy](#test-strategy)
* [Requirements Traceability](#requirements-traceability)
* [Test Environment](#test-environment)
* [Test Data](#test-data)
* [Test Tools and Automation](#test-tools-and-automation)
* [Test Case and Procedure Design](#test-case-and-procedure-design)
* [Pass / Fail Criteria](#pass--fail-criteria)
* [Entry, Suspension, Resumption, and Completion Criteria](#entry-suspension-resumption-and-completion-criteria)
* [Defect and Test-Incident Management](#defect-and-test-incident-management)
* [Regression and Retesting Strategy](#regression-and-retesting-strategy)
* [Specialized Quality Testing](#specialized-quality-testing)
* [Roles and Responsibilities](#roles-and-responsibilities)
* [Test Schedule and Milestones](#test-schedule-and-milestones)
* [Test Risks and Contingencies](#test-risks-and-contingencies)
* [Test Metrics and Reporting](#test-metrics-and-reporting)
* [Test Deliverables](#test-deliverables)
* [Test Evidence and Reproducibility](#test-evidence-and-reproducibility)
* [Approval and Release Recommendation](#approval-and-release-recommendation)
* [Open Issues](#open-issues)
* [References](#references)

## Purpose and Scope

### Purpose

Verify requirements and investigate whether the initial prototype/session increment is usable, bounded, and supported by honest evidence. This plan distinguishes planned procedures from configuration-only execution evidence. It does not claim completed system acceptance.

### System Under Test

The target system includes a local Python coordinator, provider/budget adapters, JavaScript runner, scoring/search, evidence store, guided import and inert replay. Configuration validation and local prompt/sample storage now exist; [61 passing component tests](./42_storage_validation.md) record their evidence. The unused program/test templates have been removed. Other components and full system procedures remain planned.

### Test Basis

[Requirements](./10_requirements.md), [Architecture](./21_architecture.md), [Design](./20_design.md), [Pseudocode](./26_pseudocode.txt), [PDL](./29_pdl.md), pinned original game source, and stated risks/acceptance criteria. Algorithm and profile versions form part of every execution record.

## Test Objectives

Establish correct score denominators and scheduling; bounded spending; reliable interruption/resume; genuine isolation and trusted outcomes; recorded game-profile parity; leakage-free holdout; usable guided/replay fallback; and reproducible portfolio evidence. Experiment improvement is an empirical finding, separate from software correctness.

## Test Scope

### Features to Be Tested

All FR-001–FR-022 and NFR-001–NFR-010, including invalid inputs, bot failures, service/engine faults, source/profile changes, missing records, and inert handling of imported content.

### Features Not to Be Tested

Dashboard/cloud deployment, distributed scheduling, model training, arbitrary third-party services, institutional compliance certification, and proof of an optimal strategy. Those capabilities are outside the initial scope.

### Test Assumptions and Constraints

Use fake adapters and synthetic fixtures before paid tests. Live tests require operator-selected finite bounds and a verified isolated environment. Runtime versions, reference profile and exact workload remain pilot decisions. No sensitive participant data or real keys belong in test fixtures.

## Test Strategy

### Test Levels

| Test Level | Objective | Scope | Responsible Role |
| --- | --- | --- | --- |
| Unit / contract | Correct domain logic and adapter contracts | Config, scoring, search, reservations, schemas | Developer |
| Integration | Correct data flow and recovery | Fake loops, provider/runner boundary, files/reports | Developer / operator |
| System | End-to-end behavior under bounded conditions | Actual isolated game, small live pilot | Operator |
| Acceptance | Usable session/portfolio increment | Guided exercise, replay, real comparison and reviewed evidence | Facilitator / developer |
| Regression | Preserve accepted behavior after change | Affected logic and stable core fixtures | Developer |

### Test Types

Functional, boundary, negative, contract, deterministic trace parity, isolation/misuse, interruption/recovery, cost-bound, portability, usability, and manual accessibility review. Statistical comparison is reported separately from deterministic software checks.

### Test Techniques

Use independently calculated examples, equivalence classes for statuses and limits, adversarial input traces, property checks for fixed population/schedule sizes, fault injection, and realistic end-to-end scenarios. Preserve original-rule quirks in parity tests and identify proposed corrections separately.

### Test Prioritization

First test scoring, budget, failure classification and evidence integrity. Next prove game semantics and isolation. Then verify full fake/live integration and holdout. Guided/replay acceptance runs early and again before the session. No live generated source executes before the security gate.

## Requirements Traceability

| Requirement / Objective | Test ID(s) | Test Level / Type | Expected Evidence |
| --- | --- | --- | --- |
| `FR-001` | `TC-001` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-002` | `TC-002` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-003` | `TC-003` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-004` | `TC-004` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-005` | `TC-005` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-006` | `TC-006` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-007` | `TC-007` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-008` | `TC-008` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-009` | `TC-009` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-010` | `TC-010` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-011` | `TC-011` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-012` | `TC-012` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-013` | `TC-013` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-014` | `TC-014` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-015` | `TC-015` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-016` | `TC-016` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-017` | `TC-017` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-018` | `TC-018` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-019` | `TC-019` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-020` | `TC-020` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-021` | `TC-021` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `FR-022` | `TC-022` | Contract / integration / system as applicable | Procedure record, actual result and artifact IDs |
| `NFR-001` | `TC-023` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-002` | `TC-024` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-003` | `TC-025` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-004` | `TC-026` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-005` | `TC-027` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-006` | `TC-028` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-007` | `TC-029` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-008` | `TC-030` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-009` | `TC-031` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |
| `NFR-010` | `TC-032` | Quality / boundary / fault / manual as applicable | Execution log and declared environment |

## Test Environment

### Hardware and Infrastructure

Operator-controlled computer; proposed Ubuntu reference environment; disposable browser process with enforceable capabilities and resource bounds; loopback-only viewer; local storage. Record CPU, memory, OS and browser at execution. Windows/macOS are tested only when available and reported accurately.

### Software and Versions

Record exact Python, browser, supporting JavaScript tooling, selected packages/locks, original/adapted game profile, system/API instructions, model identifier/settings, provider adapter, and source commit. Python 3.12 is proposed; no complete version matrix has been verified yet.

### Environment Configuration

Use versioned fixture configurations and disjoint optimization/holdout seeds. Clear bot-local state between matches. Isolate game/browser assets from operator credentials and user profile. Paid tests use finite request/cost bounds and distinct request journals. Store synthetic and real-run evidence separately.

### Monitoring and Logging

Capture test ID, timestamp, tester, commit, environment, inputs/procedure, expected/actual results, status, event/trace hashes, cost reservations and usage status. Keep keys and personal data out of logs. Preserve counterexamples for failed rule-parity and deterministic-trace tests.

## Test Data

### Test Data Requirements

Small scored fixtures with independently calculated values; valid and malformed bot outputs; distinct/duplicate prompt fragments; normal/invalid JSON and CSV; synthetic secret markers; injected provider/runner/storage failures; adversarial collision/helper traces; and complete/partial recorded bundles.

### Test Data Preparation

Version fixtures and reset state for each case. Label synthetic data in every example/report. Use original source as a reference and record adaptation differences. Manual data retains unknown seed status. Genuine session records are created during pilot/construction; no example score becomes a claimed result.

### Sensitive or Regulated Test Data

No real participant data. Test secrets are synthetic markers. Operator credentials are transient live-test inputs, never fixtures or exported evidence.

## Test Tools and Automation

Select/pin Python and JavaScript test tools during construction. Automate unit/contract, schema, scoring, schedule, recovery, budget, and runner tests where practical. Manual facilitator review covers understandable reports, keyboard workflow, and screen-reader use. A browser isolation test is necessary even when source screening passes. CI uses fake/offline inputs unless a separately authorized bounded live workflow is explicitly configured.

## Test Case and Procedure Design

Common preconditions: implemented component at a recorded commit; compatible fixture schema; offline mode unless the procedure explicitly requires controlled game/live execution. Runner misuse/parity cases require the isolated environment. TC-001 validation and local manifest assertions have passed. Local storage assertions also provide partial evidence for TC-002, TC-003, TC-021, and TC-024. Their broader coordinator/live-generation/checkpoint procedures remain pending; all other system procedures remain **Not run**. See [the 61-test execution record](./42_storage_validation.md). Detailed automation can later refine these procedures without changing their IDs or expected behavior.

| Test ID | Objective / Requirement | Preconditions | Inputs / Steps | Expected Result | Automation |
| --- | --- | --- | --- | --- | --- |
| `TC-001` | `FR-001` | Implemented component + versioned fixtures | Unknown key, zero sample count, overlapping seed sets, and missing budget in live configuration. | Reject before network or code execution; valid configuration produces a normalized manifest. | Validation and local manifest assertions passed; execution gating pending; see [storage evidence](./42_storage_validation.md) |
| `TC-002` | `FR-002` | Implemented component + versioned fixtures | Invoke help and each planned command with a small fixture bundle. | Each command performs only its declared workflow; offline modes have no provider calls. | validate/init/inspect assertions passed; planned experiment commands Not run |
| `TC-003` | `FR-003` | Implemented component + versioned fixtures | Change a strategy prompt, then attempt to change frozen API/model/system context on resume. | Prompt changes are versioned; incompatible resume is rejected and baseline hash is unchanged. | Baseline/lineage and incompatible store-open assertions passed; scheduler resume Not run |
| `TC-004` | `FR-004` | Implemented component + versioned fixtures | Initialize population twice with identical search seed; generate mutation and crossover children. | Population and lineage match; exact duplicates are rejected after bounded retries. | Planned automated; Not run |
| `TC-005` | `FR-005` | Implemented component + versioned fixtures | Use a fake provider returning K distinct responses and a replacement fake adapter. | Exactly K samples are recorded per prompt; provider replacement preserves contract and metadata. | Planned automated; Not run |
| `TC-006` | `FR-006` | Implemented component + versioned fixtures | Submit valid fenced code, prose-only output, missing playerAI, oversized source, and invalid return. | Only compatible outputs proceed; failures retain reason and raw response without silent repair. | Planned automated; Not run |
| `TC-007` | `FR-007` | Controlled runner environment | Replay a saved valid bot with the same seed/profile and then with a deliberately changed frame policy. | Identical profiles reproduce; profile changes are explicit and incompatible comparisons are rejected. | Planned automated; Not run |
| `TC-008` | `FR-008` | Implemented component + versioned fixtures | Build schedules for baseline and two candidates over two opponents and three seeds. | Each has identical scheduled slots for K samples; no opponent or seed is silently omitted. | Planned automated; Not run |
| `TC-009` | `FR-009` | Implemented component + versioned fixtures | Complete, invalidate, and interrupt separate slots. | One terminal record per completed slot; interruptions remain pending/blocked and are not wins or losses. | Planned automated; Not run |
| `TC-010` | `FR-010` | Implemented component + versioned fixtures | Supply opponent rates 0.92, 0.88, 0.90, 0.20, then all wins, draws, and invalid samples. | Fitness is 0.5675 for the example, 1 for all wins, 0 for all draws; invalid samples contribute zero to their scheduled slots. | Planned automated; Not run |
| `TC-011` | `FR-011` | Implemented component + versioned fixtures | Evolve a ranked fixture population with fixed seed and elite count. | Configured population size is retained; elites preserve prompts; children obey immutable constraints and lineage. | Planned automated; Not run |
| `TC-012` | `FR-012` | Implemented component + versioned fixtures | Reach each configured limit separately and interrupt in-flight work. | No new job starts after the stop condition; completed work is saved and ambiguous requests remain reserved. | Planned automated; Not run |
| `TC-013` | `FR-013` | Implemented component + versioned fixtures | Export a complete run and a partial run using the same report command. | Markdown/JSON/CSV agree; partial results are labeled; complete report includes baseline and uncertainty limitations. | Planned automated; Not run |
| `TC-014` | `FR-014` | Implemented component + versioned fixtures | Kill after saving a slot, resume, then modify a manifest field. | Completed slot is reused once; changed manifest is rejected; an uncertain request is not silently repeated. | Planned automated; Not run |
| `TC-015` | `FR-015` | Implemented component + versioned fixtures | Import a manually observed CSV with valid and duplicate/missing records. | Valid manual provenance is retained; malformed import rejected; no model API used. | Planned automated; Not run |
| `TC-016` | `FR-016` | Implemented component + versioned fixtures | Replay a valid bundle, then a bundle with malicious HTML and stored JavaScript. | Displays inert text and stored events only; no API request or stored-bot execution; markup is escaped. | Planned automated; Not run |
| `TC-017` | `FR-017` | Implemented component + versioned fixtures | Inspect seed split and attempt selection after viewing holdout results. | Optimization and holdout seeds are disjoint; holdout never feeds selection; a new experiment is needed for tuning. | Planned automated; Not run |
| `TC-018` | `FR-018` | Implemented component + versioned fixtures | Run pilot planning with costs known, unknown, just within cap, and one request beyond cap. | Estimates include independent samples and retries; unknown upper bound blocks live work; over-cap request rejected. | Planned automated; Not run |
| `TC-019` | `FR-019` | Implemented component + versioned fixtures | Inject model syntax failure, bot exception, provider timeout, and runner crash. | Bot failures score as defined; infrastructure faults block completion and never become artificial losses. | Planned automated; Not run |
| `TC-020` | `FR-020` | Controlled runner environment | Have a bot send forged victory records, mutate its snapshot, and return an invalid direction. | Trusted game ignores forged outcomes and mutated copies; invalid action is a bot failure; host state remains unchanged. | Planned automated; Not run |
| `TC-021` | `FR-021` | Implemented component + versioned fixtures | Change one artifact byte and remove required model metadata. | Hash mismatch or missing required provenance is reported; the bundle cannot be treated as verified. | Local artifact/catalog/metadata assertions passed; full live-generation provenance Not run |
| `TC-022` | `FR-022` | Implemented component + versioned fixtures | Freeze winning prompt, generate fresh holdout bot samples for it and baseline, export comparison. | Same schedules and sample counts; fresh-sample evidence is separate from optimization evidence; no improvement claim without data. | Planned automated; Not run |
| `TC-023` | `NFR-001` | Implemented component + versioned fixtures | Reserve costs for an in-flight request, uncertain timeout, and retry. | Each request has its own reservation; uncertain cost is not released; total committed bound never exceeds cap. | Planned automated; Not run |
| `TC-024` | `NFR-002` | Implemented component + versioned fixtures | Interrupt writes at manifest, event, and checkpoint boundaries and attempt repeated resume. | Atomic replacement or recovery yields one valid state; no duplicate slots and no automatic reissue of uncertain paid calls. | Injected initialization/flush/record/catalog fault assertions passed; process-kill/event/checkpoint/resume procedures Not run |
| `TC-025` | `NFR-003` | Controlled runner environment | Attempt file, network, credential, dynamic-import, and infinite-loop access in the disposable execution environment. | Forbidden capabilities unavailable; infinite loop terminated; no host secret in environment or exported artifact. | Planned automated; Not run |
| `TC-026` | `NFR-004` | Implemented component + versioned fixtures | Place a synthetic credential marker and a participant email in an export fixture. | Export blocks forbidden fields/markers; safe fixture exports; no real credentials used in tests. | Planned automated; Not run |
| `TC-027` | `NFR-005` | Implemented component + versioned fixtures | Navigate help/reports by keyboard and inspect plain-text reports with a screen reader. | Commands explain recovery; report tables have headings and textual outcomes; visuals are supplementary. | Manual + automated checks; Not run |
| `TC-028` | `NFR-006` | Implemented component + versioned fixtures | Disconnect provider service and run pure-unit plus fake-adapter tests. | Core tests pass without network, credentials, or game execution. | Planned automated; Not run |
| `TC-029` | `NFR-007` | Implemented component + versioned fixtures | Perform documented fixture smoke run on Ubuntu; attempt the same on Windows/macOS if available. | Record exact tested versions and outcome; unsupported/unavailable platforms explicitly remain unverified. | Manual + automated checks; Not run |
| `TC-030` | `NFR-008` | Controlled runner environment | Run original-source reference and adapted runner over adversarial traces and identical random inputs. | Direction/state/outcome traces agree within the declared profile; differences including collision ordering block parity claims. | Planned automated; Not run |
| `TC-031` | `NFR-009` | Controlled runner environment | Exceed every configured resource bound with synthetic code or messages. | Runner rejects or terminates within configured limit; errors identify which bound was hit. | Planned automated; Not run |
| `TC-032` | `NFR-010` | Implemented component + versioned fixtures | Recalculate report from exported slots; alter a denominator, suppress a loss, then truncate evidence. | Valid bundle exactly reproduces fitness; tampered/incomplete evidence fails verification. | Planned automated; Not run |

## Pass / Fail Criteria

### Test Case Pass Criteria

Pass only when actual behavior matches the expected result and evidence is retained. Fail when behavior differs. Block when required environment/service/evidence is unavailable. Not run means no execution attempted. Inconclusive means evidence is insufficient to decide. Skipped cases include a reason and cannot count as passed Must evidence.

### Test Suite Acceptance Criteria

All Must-associated cases pass on the declared reference environment; no unresolved critical isolation, budget, scoring, integrity or recovery defects. Unavailable platform tests remain explicit limitations. A complete real run must produce recalculable evidence and a usable guided/replay bundle. Automated correctness checks do not establish that evolution improved prompts.

## Entry, Suspension, Resumption, and Completion Criteria

### Entry Criteria

Reviewed baseline and implemented slice, recorded commit/versions, valid fixtures/config, and prerequisite construction gates. Live execution additionally requires verified isolation, explicit operator provider/model/caps, and cost reservations.

### Suspension Criteria

Credential exposure, failed isolation, uncontrolled costs, invalid profile/parity, corrupted evidence, unusable environment, or a critical engine fault. Stop scheduling work and preserve safe diagnostic evidence.

### Resumption Criteria

Resolve the trigger, document fixes/profile decisions, re-run affected prerequisite tests, verify manifest compatibility, and reconcile ambiguous request reservations. Change profile/model/context through a new run rather than silently resuming.

### Completion / Exit Criteria

Planned Must cases executed and passed for the declared release, defects triaged, real run and holdout evidence reviewed, guided/replay rehearsal complete, and test completion report signed off by the project owner. A partial prototype may be described honestly but must not be labeled fully accepted.

## Defect and Test-Incident Management

Record issue ID, requirement/test IDs, expected/actual behavior, severity, commit/profile, minimum reproduction, sanitized artifacts, and owner. Distinguish software defects, environment faults, and experiment findings. Fix, retest the case, and run affected regression tests before closure. Security reports use accurate project reporting arrangements rather than automatically treating this independent repo as Microsoft-supported.

## Regression and Retesting Strategy

Run pure/contract regression for every functional change. Re-run isolation and runner parity when browser, helper, engine or worker changes. Re-run budget/recovery cases for provider, ledger or store changes. Re-run report/import/replay checks for schemas/presentation changes. New model/settings require a new experiment comparison, not merely a software regression pass.

## Specialized Quality Testing

### Performance and Scalability Testing

Measure observed pilot request latency, match time, memory, trace size, generation validity and cost. Test each configured resource limit at/below/above its boundary. Extrapolate only from measured workloads and label the projection; no untested throughput target is promised. Sequential bounded execution is the initial design.

### Security Testing

Attempt unauthorized worker network/file/credential access, dynamic imports, malicious action messages, state mutation, infinite loops, oversized output, and executable report content. Trusted controller alone determines winners. Tests operate only on disposable local environments and synthetic data.

### Reliability, Recovery, and Resilience Testing

Interrupt at request reservation, response persistence, slot completion and checkpoint replacement. Confirm exactly-once completed evidence, retained uncertain cost bounds, compatible resume, no duplicate terminal outcomes, and actionable failure messages. Inject engine faults without scoring them as bot losses.

### Usability and Accessibility Testing

Have the facilitator use terminal help and a plain-text report without animation. Verify keyboard navigation, table headings, textual outcomes, escaped content and screen-reader readability. Supply a text description of diagrams and recorded matches. Identify any original canvas limitations and avoid unsupported compliance claims.

## Roles and Responsibilities

Developer writes/executes offline and integration tests and records self-review. Operator controls live pilot credentials/caps and observes actual costs. Facilitator validates the session path and clarity. A second reviewer is desirable for isolation/scoring if available, but is not assumed. One person may fill roles; document that limitation rather than inventing independent review.

## Test Schedule and Milestones

Test design accompanies each construction slice. Core offline and guided tests precede the live pilot. Game/isolation checks precede generated-source evaluation. Holdout/reproducibility checks follow selection freeze. Final rehearsal occurs by one week before the December session if feasible; exact date remains unconfirmed.

## Test Risks and Contingencies

| Risk | Impact on Testing / Product | Mitigation | Contingency |
| --- | --- | --- | --- |
| Provider/model variability | Identical prompt may yield different source | Independent samples; preserve raw outputs | Report validity and variation; do not claim exact regeneration. |
| Shared seeds / dependent games | Apparent precision can be overstated | Separate source-sample and seed evidence | Avoid treating every match as independent statistical evidence. |
| Unknown original-rule quirks | Adapter can unintentionally alter competition | Adversarial source-reference traces | Version differences and repeat baseline. |
| Live API unavailable | System test/session interruption | Offline fake tests and genuine recorded fallback | Guided manual experiment; mark live tests blocked. |
| Small pilot | Cannot establish reliable improvement | Label descriptive results and limits | Collect more preregistered trials in a later run. |

## Test Metrics and Reporting

Report planned/executed/passed/failed/blocked/Not run counts, defect severity, schedule completeness, invalid-generation fraction, bot/infrastructure faults, realized/reserved cost, elapsed time, and parity/isolation gate status. Report prompt fitness with scheduled denominators and played-game counts separately. Record variation across generated samples; do not use naive independent-game confidence claims when samples share source/seeds. Improvement claims require baseline and fresh holdout evidence; small pilot findings may remain descriptive/inconclusive.

## Test Deliverables

This plan, implemented tests/fixtures, environment/version manifest, execution records, defect reports, raw/aggregate result bundle, actual usage/cost records, guided/replay rehearsal evidence, and a test completion report with recommendation and limitations. Passing [configuration](./41_configuration_validation.md) and [local storage](./42_storage_validation.md) execution records exist. No completed system acceptance report is claimed.

## Test Evidence and Reproducibility

Each executed case records ID, expected/actual result, status, commit, profile/API/schema/scoring hashes, environment, config, input artifacts, seeds, timestamp and tester. Preserve source artifacts and traces to replay saved-bot behavior. Provider nondeterminism/version changes can prevent identical source regeneration even when game replay is deterministic; state that distinction explicitly.

## Approval and Release Recommendation

The project owner reviews executed evidence against AC-01–AC-06. Recommend accepted, conditional prototype, or not ready with clear reasons. Verified software and honest negative findings can support a strong portfolio. A planning document, fixture demonstration, or tournament victory alone does not justify full release acceptance.

## Open Issues

Implement tests; select runtime/tool versions and isolation strategy; select pilot settings/caps; confirm session date; obtain real recorded results. Validation, local manifest, frozen-context, integrity, and injected storage-fault assertions have executed. Their partial mapping to TC-001/002/003/021/024 is recorded above; full coordinator and system procedures remain pending/Not run. The requirement/design baseline can be reviewed now without implying later quality gates have passed.

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Test Plan"
description: "Initial project baseline for software test plan."
document_type: "Software Test Plan (STP)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.2"
updated: "2026-10-07T19:39:33-04:00"
toc: true
tags: ["testing", "stp", "portfolio"]
-->
