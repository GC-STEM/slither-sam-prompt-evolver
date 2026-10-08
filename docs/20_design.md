# Slither Sam Prompt Evolver | Software Design Description

**Document status:** Baseline revision 0.1.4. Configuration validation, local run storage, offline scoring, and declared-evidence report exports have implementation/test evidence; other capabilities and full system acceptance remain unverified.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Design Overview](#design-overview)
* [Component and Module Design](#component-and-module-design)
* [Data Design](#data-design)
* [Interface Design](#interface-design)
* [Control and Behavioral Design](#control-and-behavioral-design)
* [Error Handling, Fault Tolerance, and Recovery](#error-handling-fault-tolerance-and-recovery)
* [Security and Privacy Design](#security-and-privacy-design)
* [Logging, Monitoring, and Diagnostics](#logging-monitoring-and-diagnostics)
* [Configuration and Environment Design](#configuration-and-environment-design)
* [Performance and Resource Design](#performance-and-resource-design)
* [Design Patterns and Reuse](#design-patterns-and-reuse)
* [Design Decisions and Rationale](#design-decisions-and-rationale)
* [Design Verification and Traceability](#design-verification-and-traceability)
* [Open Issues and Deferred Design Work](#open-issues-and-deferred-design-work)
* [References](#references)

## Purpose and Scope

### Purpose

Translate requirements and architecture into implementable contracts, data structures, algorithms, and failure behavior. The design remains a planned baseline; provider and game feasibility findings may require a versioned revision.

### Design Scope

Initial local prototype plus guided/replay workflows. No browser dashboard, hosted multi-user system, or model training.

### Design Inputs

[Requirements](./10_requirements.md), [Architecture](./21_architecture.md), the pinned source bundle and README, and the confirmed user decisions. [Pseudocode](./26_pseudocode.txt) expresses language-independent control flow; [PDL](./29_pdl.md) refines module responsibilities and invariants.

### Definitions, Acronyms, and Abbreviations

**K** is generated samples per prompt. **S** is seeds per opponent/profile. **P** is population size. **G** is generation count. A slot is one planned trial. A game profile fixes all engine/API/timing/limit semantics. Synthetic zero-credit slots represent generated-code failure, not played matches.

## Design Overview

### Design Approach

Use small procedural modules and immutable domain records. Keep scoring and search logic pure. Isolate provider and game dependencies behind contracts. Configuration names proposed below are design contracts and do not imply runnable commands or schemas already exist.

### Design Diagram

[23_diagram.drawio](./23_diagram.drawio) contains experiment flow and system boundaries. Its flow decisions correspond to the run state machine below. Generated bots can propose actions; trusted code alone advances real game state and calculates outcomes.

### Design Responsibilities

Coordinator owns transitions; budget adapter owns reservations; runner owns outcomes; scorer owns fitness; evolution owns prompt changes; store owns durable evidence; reports own presentation. No component silently repairs bot code or modifies the frozen comparison context.

## Component and Module Design

### Command Line and Configuration

#### Purpose and Responsibilities

Parse mode and validate a normalized experiment configuration. Traces: FR-001–FR-002, NFR-005.

#### Public Interface

dispatch(command, arguments) → exit status; validate_config(document) → immutable RunConfig.

#### Internal Structure

Small argument parser, schema validator, normalized configuration record.

#### Dependencies

Coordinator and schema definitions; no provider SDK dependency.

#### Algorithms and Logic

Validate modes and ranges before creating any request; offline modes reject live-generation flags.

#### Data Used or Produced

RunConfig, command intent, validation diagnostics.

#### Error and Exception Behavior

Invalid configuration exits with a specific message and no paid request or code execution.

### Provider and Budget Adapter

#### Purpose and Responsibilities

Obtain independent bot samples through a provider-neutral, bounded request interface. Traces: FR-005, FR-018, NFR-001.

#### Public Interface

generate(request) → GenerationResult; reserve(request_bound) → Reservation; reconcile(reservation, usage) → LedgerEntry.

#### Internal Structure

Provider protocol, adapter implementation, ledger and request journal.

#### Dependencies

Operator credentials, configured provider API, conservative price/usage bounds, store.

#### Algorithms and Logic

Persist reservation before sending; retain uncertain charges; every retry is a new bounded request.

#### Data Used or Produced

Raw response, provider/model/settings metadata, request ID, usage, reservation, charge state.

#### Error and Exception Behavior

Bot-output failures are distinct from provider faults; authentication/unknown cost blocks live work; uncertain requests pause for reconciliation.

### Experiment Coordinator and Scheduler

#### Purpose and Responsibilities

Own run state, identical comparison schedules, stop checks, and phase boundaries. Traces: FR-007–FR-009, FR-012, FR-014, FR-017, FR-019.

#### Public Interface

run(config) → RunSummary; schedule(prompts, samples, opponents, seeds) → SlotList; resume(run_id) → RunSummary.

#### Internal Structure

Sequential job loop, run state machine, optimization and holdout phases.

#### Dependencies

All domain services through contracts, including fake adapters for tests.

#### Algorithms and Logic

Evaluate fixed slots, save results before ranking; freeze selection before holdout; check applicable limits before each job.

#### Data Used or Produced

Run/slot IDs, job statuses, manifest, checkpoint and phase records.

#### Error and Exception Behavior

Infrastructure faults pause incomplete scoring; user stop saves completed work; incompatible resume rejected.

### Validation and JavaScript Match Runner

#### Purpose and Responsibilities

Validate bot source and run decisions with trusted outcomes and bounded resources. Traces: FR-006–FR-007, FR-020, NFR-003, NFR-008–NFR-009.

#### Public Interface

validate(source, api_profile) → ValidationResult; evaluate(MatchRequest) → MatchResult.

#### Internal Structure

Source extractor, interface checks, trusted game controller, isolated decision worker, helper facade.

#### Dependencies

Frozen game source/profile, seeded random inputs, controlled clock, verified disposable browser environment.

#### Algorithms and Logic

Preserve original update/collision order; read copied state; validate returned Direction; use explicit bot and engine timeouts.

#### Data Used or Produced

Source/hash, state/decision traces, outcome, termination reason and diagnostics.

#### Error and Exception Behavior

Bot syntax/contract errors receive zero evaluation credit; bot decision exception/deadline gives a loss; engine/isolation fault blocks scoring.

### Scoring and Evolution

#### Purpose and Responsibilities

Calculate prompt fitness and create strategy-only descendants. Traces: FR-003–FR-004, FR-010–FR-011, NFR-006, NFR-010.

#### Public Interface

Implemented `score_results(config, bundle) → FitnessResult`: the versioned bundle declares samples and slot results, and a complete compatible scoreable schedule is required. See [the scoring contract](./13_offline_scoring.md). Planned `evolve(ranked_prompts, search_state, config) → Population`.

#### Internal Structure

Implemented pure scorer with frozen result dataclasses, exact rational calculation, closed result schema, and separate played/synthetic counts. Seeded parent selection and fragment operations remain planned.

#### Dependencies

Validated slot records, configuration, prompt store; no direct provider/network use.

#### Algorithms and Logic

Versioned 70/30 scoring; rank with stable tie-break; retain elites; bounded mutation/crossover and duplicate rejection.

#### Data Used or Produced

Fitness with denominators, selected IDs, child text/hashes, parent IDs and operation logs.

#### Error and Exception Behavior

Incomplete infrastructure-blocked schedules have no final score; malformed children are rejected with bounded attempts.

### Evidence Store and Reporting

#### Purpose and Responsibilities

Persist provenance and produce recalculable reports. Traces: FR-013–FR-014, FR-021–FR-022, NFR-002, NFR-004, NFR-010.

#### Public Interface

Implemented: RunStore.create/open, add_prompt/get_prompt, add_sample/get_sample, manifest, and verify; see [the storage contract](./12_local_storage.md). Implemented separately: `build_report`, `export_report`, and `verify_report` consume a frozen configuration and declared result bundles; see [the report contract](./14_reports.md). Planned: append_event(record), checkpoint(state), and integrated full verify_bundle.

#### Internal Structure

Implemented: exclusive per-run writer lock, frozen configuration/manifest, immutable hashed text/record files, and an atomic catalog of prompt/sample IDs and hashes. The catalog detects deleted records. The report builder and versioned archive exporter are implemented separately. Append-only events and checkpoints remain planned.

#### Dependencies

Local filesystem, schema definitions, scorer; no live provider during report.

#### Algorithms and Logic

Implemented storage rejects conflicting IDs and duplicate sample slots/request IDs, verifies local hashes and lineage, and requires declared synthetic/manual/automated provenance. Interrupted publication blocks inspection when completion cannot be established. Declared slot IDs, escaped report markup, synthetic labels, and recalculation are implemented for result snapshots. Trusted match production and coordinator integration remain pending.

#### Data Used or Produced

Manifests, prompts, source/responses, ledgers, slots, traces, Markdown/JSON/CSV.

#### Error and Exception Behavior

Storage failures suspend work; unknown schemas/tampering block verified reports; export secrets block publication.

### Guided Import and Replay

#### Purpose and Responsibilities

Support participant observations and presentation of genuine stored results. Traces: FR-015–FR-016, NFR-005.

#### Public Interface

import_manual(csv, manifest) → ManualBundle; replay(bundle) → InertPresentation.

#### Internal Structure

CSV validator, provenance labeling, text/state-event viewer.

#### Dependencies

Evidence schemas and reporting; no provider or generated-code loader.

#### Algorithms and Logic

Keep unknown seeds unknown; reject duplicates; replay stored trusted state events only.

#### Data Used or Produced

Manual observation records, guided comparison sheet and recorded outcome/state tables.

#### Error and Exception Behavior

Missing recordings are reported; unsafe markup is escaped; incomparable manual/automated results remain separate.

## Data Design

### Domain Model

A Run owns a frozen configuration and profile. A Prompt owns strategy text and lineage. Each Prompt has K generation Samples. Each Sample has the same set of Slots. Optimization slots feed Fitness and Selection; holdout slots belong to a frozen comparison only. Requests and reservations are independent records because a timed-out paid request may still be charged.

### Data Structures

| Record | Required Fields | Invariants |
| --- | --- | --- |
| RunConfig | schema_version, run_id, mode, P/G/K, opponents, optimization_seeds, holdout_seeds, fixed_context_hashes, limits | Known schema; finite positive bounds; disjoint seeds; live settings explicit. |
| Prompt | prompt_id, generation, text, text_hash, parents, operator, fragment_changes | Baseline immutable; parent IDs exist; context excluded from evolved text. |
| GenerationRequest | request_id, prompt_id, sample_index, context_hash, model/settings, output_limit, reservation_id | A unique request per independent sample; retries get new IDs. |
| GenerationResult | request_id, raw_text, source_hash, provider/model, usage, charge_state, status, reason | Raw response preserved; metadata available or explicitly unavailable; uncertain costs retained. |
| Slot | slot_id, phase, sample_id, opponent_id/hash, seed, profile_hash, limits | Schedule fixed before execution; one terminal record per slot. |
| MatchResult | slot_id, outcome, status, cause, decision_count, lengths, elapsed, trace_hash | outcome: win/loss/draw only for played trials; distinct bot/engine failures. |
| FitnessResult | prompt_id, scoring_version, per_opponent_counts, scheduled_slots, wins, synthetic_failures, fitness | Final score only after complete scoreable schedule; denominators preserved. |
| Checkpoint | manifest_hash, completed_IDs, phase, search_rng_state, reservations, pending_jobs | Compatible resume; no ambiguous request silently repeated. |

### Persistent Storage

Implemented `runs/<run_id>/` contains manifest/configuration JSON, an atomic `catalog.json`, immutable `prompts/` and `samples/` JSON records, and exact text in content-addressed `artifacts/`. Each record is bound to the frozen manifest. Provenance labels are required; SHA-256 is integrity checking, not authentication. Initialization publishes the manifest last; record publication commits through the catalog. Uncommitted records and stale locks block verification without automatic repair. Planned additions are append-only `requests.jsonl`, `events.jsonl`, `slots.jsonl`, atomic `checkpoint.json`, and trusted replay traces. Declared-evidence reports currently use separate versioned directories containing configuration, result snapshots, derived formats, and hashes. Files are UTF-8. Artifact hashes identify exact content; new scoring versions create new reports rather than rewriting raw records.

### Data Flow and Transformation

Operator inputs become normalized configuration and a manifest. Provider responses become preserved raw artifacts plus extracted source. Valid samples receive scheduled matches; invalid generation fills its planned slots with explicit synthetic zero-credit records. Trusted results become fitness and lineage. Reports re-read evidence and display provenance separately for automated, manual, and replay use.

## Interface Design

### User Interface Design

Proposed command family: `python -m slither_evolver pilot --config PATH`, `evolve --config PATH`, `guided --input PATH --manifest PATH`, `replay --run PATH`, `report --run PATH`, and `resume --run PATH`. Each supports help. `pilot` plans work offline by default; explicit `--live` permits bounded generation when required settings exist. These experiment commands are targets for implementation. The first implemented command is `python -m slither_evolver validate --config PATH [--live]`; see [the configuration contract](./11_configuration.md). Implemented `init --config PATH --provenance KIND --description TEXT [--runs-dir PATH]` creates local evidence and `inspect --run PATH` verifies it. Neither command starts live work. Implemented `score --config PATH --results PATH` emits JSON for complete scoreable evidence and exit 5 without final fitness for valid incomplete/blocked evidence; malformed scoring input returns 2. Implemented `report --config PATH --results PATH [--results PATH ...] --baseline ID --selected ID --output NEW_DIR` exports complete or explicitly partial declared evidence. `verify-report --report DIR` checks hashes and rebuilds every format. Successful partial export/verification returns 0 with partial status; report integrity/export errors return 4. All six offline commands are covered by tests; storage faults return exit 4.

Exit statuses: 0 completed requested workflow; 2 invalid input; 3 missing dependency/isolation prerequisite; 4 external service/infrastructure failure; 5 bounded or operator stop. Messages identify what was saved and a recovery action. Report replay uses inert content only. Visual match watching is a separate trusted viewer workflow and may run only after execution isolation is verified.

### API and Service Interface Design

Provider request includes fixed system/API context, evolved strategy text, exact configured model, generation settings, output bound, and request ID. Adapter normalizes service-specific response and usage fields. Service credentials remain in the trusted process. Runner request/response schema uses IDs and profile hashes. Worker decision messages contain a sequence ID and one direction; unknown/extra fields never determine game outcomes.

The inspected source defines Direction.UP/DOWN/LEFT/RIGHT as strings. `player.currentDirection()` returns coordinates in the Snake source. Helper and opponent behavior must follow the actual pinned implementation, including stateful opponent fields. Preserve a worker's bot-local state within a match, reset it between matches, and never reuse it to leak real host state.

### File and Data Exchange Interfaces

Schema-versioned JSON and JSONL; CSV columns are explicit, header-based, and stable. Missing fields fail validation. Numbers serialize as unrounded values; reports may display six decimals but retain full exported score precision. Manual observation CSV records outcome, opponent/profile, source/prompt reference, observer label without personal data, and seed only if known. Unknown manual seeds do not satisfy deterministic-run evidence.

### Hardware / Device Interface Design

No device-specific interfaces are required.

## Control and Behavioral Design

### Main Processing Flow

Validate → manifest → baseline/population → generation samples → interface validation → fixed match schedule → complete fitness → selection/evolution → stop/freeze → fresh holdout samples for baseline and selection → report. Inspect [26_pseudocode.txt](./26_pseudocode.txt) for branches and bounded loops.

**Implemented offline scoring version 1:** For each opponent/configuration profile o, let N_o = K × S scheduled slots and W_o be wins. Invalid generated samples contribute synthetic zero-credit slots. Played draws and bot-caused losses contribute zero wins. Define R_o = W_o / N_o; overall R = sum(W_o) / sum(N_o); worst R_min = min(R_o). Fitness F = 0.70R + 0.30R_min. An infrastructure-blocked or missing slot prevents final scoring. Reports call these **effective scheduled-trial win rates** and separately report ordinary played-match wins/losses/draws and generation validity, so synthetic failures are never described as played matches.

With equal opponent schedules, rates 0.92, 0.88, 0.90, and 0.20 yield R = 0.725 and F = 0.5675. All valid wins score 1; all draws or invalid samples score 0. Weights are configurable but frozen in the scoring-version manifest before comparison. The implemented scorer retains supplied weights without renormalization, calculates with exact rational values, and exports both float values and reduced fractions. Its sample acceptance/provenance labels are declarations; it does not certify provider/runner output. Slot persistence and trusted outcome production remain future integrations.

**Search version 1:** Rank by fitness descending, then valid-generation fraction descending, strategy character count ascending, and prompt hash ascending. Retain a configured elite count E where 1 <= E < P. Choose parents using seeded tournament selection (configured tournament size). For remaining slots choose mutation or crossover with configured probabilities summing to 1. Represent strategy text as ordered instruction fragments; mutation adds/removes/rewrites/reorders one allowed fragment using a versioned proposal bank, and crossover combines parent fragments then resolves exact duplicates. Do not mutate fixed API/system instructions. Reject empty, oversized, unchanged, or duplicate candidates. After bounded attempts, use distinct configured seed variants; if still insufficient, stop with a clear population-construction error. This first search design uses no extra LLM calls for mutations.

**Sampling:** Generate K independent source outputs for each unique new prompt. Retained elites keep their saved samples and optimization evidence within the unchanged schedule; this reduces cost and is reported as a selection-bias limitation. Fresh samples of both baseline and frozen selection are generated for holdout. Seeds are reused equally across candidates; they need not conceal stochastic model generation. Do not present saved-source replay as identical model regeneration.

### State and Mode Behavior

Run states: planned → generating → evaluating → scored → evolving; repeat until a stop guard; then frozen → holdout → completed. Any active phase can enter paused or failed. Resume returns to the recorded phase after manifest validation. A budget/time stop may preserve a partial report without declaring holdout complete. Guided and replay are separate modes and never enter generation.

### Event Handling

User interrupt saves completed work, terminates workers, and preserves in-flight request reservations. Provider error, worker bot error, engine crash, and storage failure produce typed events. A game frame advances according to recorded virtual time, not browser rendering or worker response speed.

### Concurrency and Synchronization

Sequential coordinator; one writer; one isolated decision job at a time. Game state advances only after a validated decision or recorded bot fault. Deadlines terminate a worker without leaving it connected to later matches. Independent seeded streams for game, opponent, and bot helpers are a proposed profile choice to verify and declare, because changing RNG ownership changes original behavior.

## Error Handling, Fault Tolerance, and Recovery

Generation syntax/contract failure receives zero scheduled-trial credit without source repair or free re-generation. Bot exception, illegal direction, or decision deadline gives a bot-caused loss. Reaching the configured game-frame cap with no winner is a draw in this adapted profile; it is not an original-game claim. Provider/rate-limit/engine/storage faults block affected work and do not penalize prompts. Automated retries, if configured, are bounded, separately reserved, and recorded; uncertain paid requests pause. Restore only exact compatible manifests. Checkpoint and output hash mismatches require investigation rather than silent replacement.

## Security and Privacy Design

Generated source executes only after isolation tests pass. Browser controller and workers inherit no provider secrets or operator browser session. Workers get copies and a supported helper facade, no host capability bindings; prohibit network and dynamic resource loading with verified browser/process policies. Trusted code validates action messages and calculates collision/outcome records. Source screening is defense in depth, not a security boundary. Reports escape markup; replay cannot execute stored source. All exports are reviewed for secrets and personal data.

## Logging, Monitoring, and Diagnostics

Record timestamp, run/job ID, phase, event type, provider request/usage status, reserved/confirmed cost, slot outcome, bot-vs-infrastructure cause, elapsed time, profile/hash, and checkpoint version. Use operator pseudonymous labels only where useful. Never log keys or authorization headers. Capture bounded decision/state traces for selected real matches and derive all plots/tables from records.

## Configuration and Environment Design

Required live fields: provider adapter name, model identifier, credential environment-variable name, max output tokens, conservative cost bound/pricing version, max_requests and max_cost. Core fields include P/G/K, elite/tournament settings, mutation/crossover probabilities, prompt/source/message limits, opponents/profiles, disjoint seed lists, and time/frame/memory limits. Default mode is offline planning. No numerical pilot workload or price is silently chosen. Experiment-profile settings become immutable after manifest creation.

## Performance and Resource Design

Planned optimization match count is U × K × O × S for U unique evaluated prompts and O opponent/profile combinations. Worst-case U <= P × G under the definition that G includes generation zero. Holdout adds 2 × K × O × H slots and 2K requests for a distinct selection/baseline pair; if selection equals baseline, report that fact and use one fresh shared comparison set. Generation retries add explicit bounded requests. Match/frame traces are bounded; report projection shows scale before live work. Timeouts and source/message limits are selected by the pilot, then tested at boundary values.

## Design Patterns and Reuse

Ports/adapters for provider and runner; immutable value records for manifests; strategy functions for scoring/search; append-only journal with atomic snapshots for recovery. Reuse original game/helper source and applicable notices. Keep adapted engine changes small, versioned, and independently tested against a reference implementation.

## Design Decisions and Rationale

| ID | Decision | Alternatives Considered | Rationale / Trade-offs | Related Requirements |
| --- | --- | --- | --- | --- |
| DD-001 | Multiple independent bots per prompt | One bot per prompt | Measures generation variation; costs more | FR-005, FR-022 |
| DD-002 | Invalid generation gets synthetic zero-credit slots | Drop failed outputs or repair code | Fixed denominator; exposes reliability; report must separate played games | FR-006, FR-009–FR-010, FR-019 |
| DD-003 | Deterministic fragment search, saved elite evidence | LLM mutation and repeated elite generation | Bounded initial scope/cost; final fresh samples address some selection bias | FR-004, FR-011, FR-018 |
| DD-004 | Holdout after freeze with fresh bot samples | Reuse optimization bots alone | Tests prompt generation as well as game conditions | FR-017, FR-022 |
| DD-005 | Draws score zero; frame cap is a draw | Half-credit draws or length-based winner | Matches initial win-rate objective; conservative and explicit | FR-007, FR-010 |
| DD-006 | No silent engine corrections | Fix source while building runner | Preserve comparison meaning; known quirks stay visible | FR-007, FR-021, NFR-008 |

## Design Verification and Traceability

The requirement-to-module/test mapping in [Requirements](./10_requirements.md#requirements-traceability) is authoritative. Component sections above identify requirement groups. Scorer component tests now cover independent arithmetic, normal/boundary outcomes, malformed evidence, and incomplete/infrastructure-blocked schedules. Search tests remain planned; runner tests cover helper/rule parity and isolation; local storage tests cover injected publication/flush failures and incompatible context; paid-request ambiguity and full interruption/recovery tests remain planned. All planned tests are specified in [Testing](./40_testing.md).

## Open Issues and Deferred Design Work

Pilot chooses exact resource limits, provider/model, budgets, and sample counts. Verify worker facade compatibility and seeded-clock profile before live execution. Resolve any desired engine correction as a separately versioned decision and re-run baseline. Future extensions include dashboard, parallel scheduling, additional mutation methods, richer statistical inference, and unseen-opponent generalization. None is needed to complete the initial document baseline.

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Software Design Description"
description: "Initial project baseline for software design description."
document_type: "Software Design Description (SDD)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.4"
updated: "2026-10-08T07:10:16-04:00"
toc: true
tags: ["design", "sdd", "portfolio"]
-->
