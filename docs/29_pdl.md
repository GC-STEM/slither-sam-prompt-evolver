# Slither Sam Prompt Evolver | Program Design Language

**Document status:** Baseline revision 0.1.3. Configuration validation, local run storage, and offline scoring have implementation/test evidence; other capabilities and full system acceptance remain unverified.

<!-- omit from toc -->
## Table of Contents

* [Purpose and Scope](#purpose-and-scope)
* [Entry Points and Dispatch](#entry-points-and-dispatch)
* [Module Contracts and Refinement](#module-contracts-and-refinement)
* [Generation and Cost Gate](#generation-and-cost-gate)
* [Trusted Game and Worker Boundary](#trusted-game-and-worker-boundary)
* [Scoring and Evidence Invariants](#scoring-and-evidence-invariants)
* [Search Refinement](#search-refinement)
* [States, Stops and Recovery](#states-stops-and-recovery)
* [Implementation and Test Traceability](#implementation-and-test-traceability)
* [Open Implementation Decisions](#open-implementation-decisions)
* [References](#references)

## Purpose and Scope

The source `29_pdl.md` was empty. This project-specific PDL refines the language-independent pseudocode into implementation-oriented responsibilities without supplying executable source. The proposed construction organization uses Python for control and JavaScript for game decisions; functions below are planned interfaces except the configuration, local storage, and offline scoring operations identified here.

PDL uses indentation, named records, IF/ELSE, FOR/WHILE, REQUIRE, RETURN and LET. It describes intent and invariants rather than a specific language's syntax. The high-level algorithm remains in [26_pseudocode.txt](./26_pseudocode.txt).

## Entry Points and Dispatch

Implemented dispatch handles `validate`, `init`, `inspect`, and `score`. Initialization revalidates configuration, requires a provenance label, and publishes a local manifest. Inspection verifies existing evidence without loading a provider or executing source. Scoring validates declared JSON samples/results and requires complete scoreable schedules; it emits no final fitness for missing/blocked evidence. The following dispatcher describes the future experiment coordinator.

```text
PROCEDURE main(arguments)
    LET intent = cli.parse(arguments)
    LET config = config_module.validate(intent)
    IF intent.mode == guided
        RETURN guided.import_and_report(config)
    ELSE IF intent.mode == replay
        RETURN replay.display_recorded_data(config)
    ELSE IF intent.mode == report
        RETURN reports.verify_and_export(config)
    ELSE IF intent.mode == pilot AND intent.live != true
        RETURN budget.show_plan(config)
    ELSE
        REQUIRE live settings, finite caps and verified isolated environment
        RETURN orchestrator.execute_or_resume(config)
    END IF
END PROCEDURE
```

Offline modes must not construct a live provider or execute stored bot source. Exit statuses and proposed command spelling are specified in [Design](./20_design.md#user-interface-design).

## Module Contracts and Refinement

| Unit | Input → Output | Preconditions / Postconditions | Failure Contract |
| --- | --- | --- | --- |
| config.validate | Input JSON → immutable RunConfig | Known schema and valid finite bounds; disjoint seeds | InvalidInput; no external work |
| prompts.initialize | Baseline + variants → Population | Baseline preserved; distinct text hashes; valid P | PopulationError after bounded attempts |
| providers.generate | GenerationRequest → GenerationResult | Reservation persisted; fixed context; bounded output | Typed provider failure/uncertain charge |
| validation.extract | Raw response → Sample | Original retained; frozen API and source limits | invalid_bot; no silent repair |
| evaluation.schedule | Samples + profiles + seeds → Slots | Same K and profile/seed sets for comparisons | InvalidSchedule |
| runner.evaluate | MatchRequest → MatchResult | Verified isolation/profile; action-only worker messages | bot_fault versus engine/isolation_fault |
| score_results | Validated config + versioned declared results → immutable FitnessResult | Every scheduled denominator represented; exact configured weights; played/synthetic counts separate | ScoringError or IncompleteEvidence; no final score on incomplete/blocked evidence |
| evolution.next | Ranked prompts + RNG/config → Population | Strategy-only changes; bounded search; E < P | PopulationError with operation evidence |
| RunStore.create/open/add/get/verify | Valid config or supplied text → frozen local evidence | Existing IDs immutable; content/metadata hashes checked; incomplete catalog blocked | StorageError; no external execution |
| storage.checkpoint | Valid state → durable snapshot | Single writer; atomic replacement | StorageFault; scheduling suspends |
| reports.export | Verified records → Markdown/JSON/CSV | Recalculate; safe content; full provenance | InvalidBundle or UnsafeExport |
| guided.import | CSV + manual manifest → ManualBundle | Unique records; unknown seed explicit | InvalidImport; no provider call |
| replay.display | Verified stored events → inert view | Escaped data; no source loading | InvalidBundle; no model/bot execution |

## Generation and Cost Gate

```text
PROCEDURE request_sample(prompt, sample_index, phase)
    LET key = hash(prompt, sample_index, phase, complete_fixed_context)
    IF compatible_artifact_exists(key)
        RETURN saved_artifact(key)
    END IF
    LET request = construct_generation_request(key)
    LET cost_bound = adapter.conservative_bound(request)
    REQUIRE cost_bound is known and finite
    REQUIRE request_capacity >= 1 AND cost_bound <= remaining_cost_capacity
    persist_reserved_request_before_send(request, cost_bound)
    LET response = adapter.send(request)
    IF response.charge_state == uncertain
        retain_reservation_and_pause(request)
    END IF
    persist_raw_response_and_available_metadata(response)
    reconcile_only_confirmed_usage_or_retain_bound(response)
    RETURN validation.extract(response)
END PROCEDURE
```

Every retry is a new request, reservation and sample-attempt record. Bot-invalid output is an experimental failure, not a reason for a free replacement request. A saved elite artifact can be reused within optimization, but holdout's phase key forces fresh generations.

## Trusted Game and Worker Boundary

```text
PROCEDURE run_match(request)
    initialize_trusted_game_from_versioned_profile(request)
    start_disposable_worker_without_host_capabilities_or_secrets()
    WHILE game_has_no_terminal_result AND frames < request.max_frames
        LET snapshot = copy_supported_game_state()
        LET action = worker.request_direction(snapshot, deadline)
        IF action is timeout OR exception OR invalid_direction
            RETURN trusted_bot_loss(action.reason)
        END IF
        apply_valid_direction_in_trusted_game(action)
        advance_one_recorded_clock_frame_in_original_update_order()
        record_bounded_trusted_state_and_decision_event()
    END WHILE
    IF game_has_terminal_result
        RETURN trusted_game_outcome()
    END IF
    RETURN draw_due_to_profile_frame_cap()
FINALLY
    terminate_worker_and_release_match_resources()
END PROCEDURE
```

This conceptual refinement must be adapted to the original source's per-frame AI calls and movement timing, not interpreted as permission to change them. The worker helper facade and persistent bot-local state need parity tests. Trusted original opponents keep their own supported state. Clock/RNG adaptations are declared in the profile. The current source's Direction enum is strings; helper return types follow actual code.

Workers cannot write real game state or assert a winner. A forged worker message is rejected or interpreted only as a validated direction. Engine/browser failures are infrastructure faults and do not become bot losses.

## Scoring and Evidence Invariants

```text
PROCEDURE calculate_fitness(slots)
    REQUIRE no missing or infrastructure-blocked scheduled slots
    FOR EACH opponent_profile
        LET wins = number_of_win_records(opponent_profile)
        LET denominator = scheduled_slot_count(opponent_profile)
        REQUIRE denominator > 0
        LET rate[opponent_profile] = wins / denominator
    END FOR
    LET overall = sum(wins) / sum(denominator)
    LET worst = minimum(rate)
    RETURN overall_weight * overall + worst_weight * worst
END PROCEDURE
```

Implemented result validation binds slot IDs to configuration/prompt/sample/opponent/seed coordinates, rejects duplicates and contradictory statuses, and checks the exact Cartesian schedule count. Exact rational calculation follows this refinement; generation acceptance and actual match outcomes remain caller declarations pending trusted pipeline integration.

Synthetic invalid-generation exposures preserve K × seed-count denominators but are reported separately from played games. Draws score zero under version 1. Holdout is a reporting phase only. A report includes sample count, validity, played outcomes, scheduled outcomes, costs, limitations, and whether the comparison completed.

## Search Refinement

Selection reads optimization scores only. Stable ranking uses fitness, validity, text length, and hash. Seeded tournament selection chooses parents; strategy-fragment mutation/crossover create candidates. Elites keep text and saved optimization samples. Duplicate/unchanged/invalid candidates consume a bounded proposal attempt, not a paid generation request. Persist lineage, operator version and RNG state before advancing generation.

Instruction-fragment operations are an initial project design choice, not a mandated course technique. LLM-generated mutations and alternative selection methods can be separate, versioned future experiments.

## States, Stops and Recovery

State transitions match [Design](./20_design.md#state-and-mode-behavior). Request/spending limits prohibit new paid requests; generation limits prohibit another optimization population; elapsed-time/operator stop suspends all new work. Completed evidence can still be saved and reported. An unfinished generation or holdout is explicitly partial.

Local `open(expected_config=...)` now verifies frozen configuration equality, catalog membership, artifact hashes, baseline identity, and lineage. This opens evidence; it does not resume work. Write locks and incomplete commits block access for review; injected fault tests are partial evidence, not process-kill recovery.

Planned scheduler resume validates manifest/profile/schema hashes, rebuilds completed slot IDs from durable records, retains uncertain request reservations, restores search state, and schedules only compatible unfinished work. Unknown paid-request status requires reconciliation or a retained worst-case reservation before a separately bounded retry.

## Implementation and Test Traceability

| PDL Area | Planned Files | Requirements | Planned Verification |
| --- | --- | --- | --- |
| Dispatch/configuration | cli.py, config.py | FR-001–FR-002 | TC-001–TC-002 |
| Generation/cost gate | providers/, budget.py | FR-005, FR-018, NFR-001 | TC-005, TC-018, TC-023 |
| Schedule/worker/game | evaluation.py, validation.py, runner/ | FR-006–FR-009, FR-019–FR-020 | TC-006–TC-009, TC-019–TC-020, TC-025, TC-030–TC-031 |
| Score/search | scoring.py, evolution.py, prompts.py | FR-003–FR-004, FR-010–FR-011 | TC-003–TC-004, TC-010–TC-011, TC-028, TC-032 |
| Durability/report/holdout | storage.py, reports.py, orchestrator.py | FR-012–FR-014, FR-017, FR-021–FR-022 | TC-012–TC-014, TC-017, TC-021–TC-024, TC-026 |
| Guided/replay | guided.py, replay.py | FR-015–FR-016, NFR-005 | TC-015–TC-016, TC-027 |

## Open Implementation Decisions

Select and verify provider SDK/client, exact runtime/tool versions, isolation arrangement, resource limits, and pilot scale. Record any original-game behavior changes before implementation. No PDL function is claimed implemented, and no planned test is claimed passed.

## References

* [Project repository](https://github.com/GC-STEM/slither-sam-prompt-evolver), inspected at commit `59536cf1030fd9ba04e893d046e317d8531b6529` on October 7, 2026.
* [Repository SDLC templates](https://github.com/GC-STEM/slither-sam-prompt-evolver/tree/59536cf1030fd9ba04e893d046e317d8531b6529/docs), adapted for this independent portfolio project.
* [Slither Slam activity](https://aka.ms/slither-slam) and [educator resources](https://aka.ms/slither-slam-educator), original learning resources.
* [Bundled course and game source](https://github.com/GC-STEM/slither-sam-prompt-evolver/blob/59536cf1030fd9ba04e893d046e317d8531b6529/index.yml), including the model's system instructions, Snake helpers, game rules, opponents, and browser dependencies.

<!--
title: "Slither Sam Prompt Evolver | Program Design Language"
description: "Initial project baseline for program design language."
document_type: "Program Design Language (PDL)"
owner: "GC-STEM, Computer Science"
scope: "slither-sam-prompt-evolver"
version: "0.1.3"
updated: "2026-10-07T21:07:12-04:00"
toc: true
tags: ["pdl", "algorithms", "portfolio"]
-->
