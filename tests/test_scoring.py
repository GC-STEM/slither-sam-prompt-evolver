"""Independent arithmetic oracles and negative evidence-contract checks."""

from contextlib import redirect_stderr, redirect_stdout
import copy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from slither_evolver.__main__ import main
from slither_evolver.config import validate_config
from slither_evolver.scoring import (
    IncompleteEvidence, ScoringError, configuration_hash, load_results, score_results, slot_id,
)
from slither_evolver.storage import RunStore


EXAMPLE = Path(__file__).resolve().parents[1] / "configs/offline.example.json"


def make_bundle(config, *, phase="optimization"):
    digest = configuration_hash(config)
    bundle = dict(schema_version=1, run_id=config.run_id, configuration_hash=digest,
                  prompt_id="synthetic-prompt", prompt_hash="a" * 64, phase=phase,
                  provenance=dict(kind="synthetic", description="Handwritten outcomes, no games."),
                  samples=[], results=[])
    seeds = config.optimization_seeds if phase == "optimization" else config.holdout_seeds
    for index in range(config.samples_per_prompt):
        sample = dict(sample_id=f"sample-{index}", sample_index=index, source_hash="b" * 64,
                      generation_status="accepted", reason=None)
        bundle["samples"].append(sample)
        for opponent in config.opponents:
            for seed in seeds:
                identity = slot_id(digest, bundle["prompt_id"], bundle["prompt_hash"], phase,
                                   sample["sample_id"], sample["source_hash"], opponent.id, seed)
                bundle["results"].append(dict(
                    slot_id=identity, sample_id=sample["sample_id"], opponent_id=opponent.id,
                    opponent_source_hash=opponent.source_hash, profile_hash=opponent.profile_hash,
                    seed=seed, status="played", outcome="win", cause=None, reason=None,
                ))
    return bundle


def change_sample(config, bundle, index, status, source_hash, reason):
    sample = bundle["samples"][index]
    sample.update(generation_status=status, source_hash=source_hash, reason=reason)
    for record in bundle["results"]:
        if record["sample_id"] == sample["sample_id"]:
            record["slot_id"] = slot_id(configuration_hash(config), bundle["prompt_id"],
                                        bundle["prompt_hash"], bundle["phase"], sample["sample_id"],
                                        source_hash, record["opponent_id"], record["seed"])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(EXAMPLE.read_text())
        self.config = validate_config(self.document)
        self.bundle = make_bundle(self.config)

    def score(self, bundle=None, config=None):
        return score_results(config or self.config, self.bundle if bundle is None else bundle)

    def invalidate(self, index):
        change_sample(self.config, self.bundle, index, "invalid", None, "synthetic invalid source")
        sample_id = self.bundle["samples"][index]["sample_id"]
        for record in self.bundle["results"]:
            if record["sample_id"] == sample_id:
                record.update(status="invalid_generation", outcome=None,
                              cause="generation_contract", reason="synthetic invalid source")

    def test_design_example_uses_independently_calculated_counts(self):
        document = copy.deepcopy(self.document)
        document["optimization_seeds"] = list(range(25))
        document["opponents"] = [dict(id=f"opponent-{i}", source_hash=str(i + 1) * 64,
                                      profile_hash=str(i + 5) * 64) for i in range(4)]
        config = validate_config(document)
        bundle = make_bundle(config)
        win_counts = [46, 44, 45, 10]
        for opponent, wins in zip(config.opponents, win_counts):
            records = [r for r in bundle["results"] if r["opponent_id"] == opponent.id]
            for index, record in enumerate(records):
                record["outcome"] = "win" if index < wins else "loss"
        result = self.score(bundle, config)
        self.assertEqual(result.counts.wins, 145)
        self.assertEqual(result.counts.scheduled_slots, 200)
        self.assertEqual(result.overall_effective_win_rate_fraction, "29/40")
        self.assertEqual(result.worst_opponent_effective_win_rate_fraction, "1/5")
        self.assertEqual(result.fitness_fraction, "227/400")
        self.assertEqual(result.fitness, 0.5675)
        self.assertEqual([r.effective_win_rate for r in result.opponents], [0.92, 0.88, 0.9, 0.2])

    def test_all_wins_losses_and_draws(self):
        for outcome, expected in (("win", 1), ("loss", 0), ("draw", 0)):
            bundle = copy.deepcopy(self.bundle)
            for record in bundle["results"]:
                record["outcome"] = outcome
            result = self.score(bundle)
            with self.subTest(outcome=outcome):
                self.assertEqual(result.fitness, expected)
                self.assertEqual(result.counts.played_matches, 12)
                self.assertEqual(getattr(result.counts, outcome + ("s" if outcome != "loss" else "es")), 12)

    def test_invalid_generation_retains_denominator_and_is_not_played(self):
        self.invalidate(1)
        accepted = [r for r in self.bundle["results"] if r["sample_id"] == "sample-0"]
        losses = [r for r in accepted if r["opponent_id"] == self.config.opponents[1].id][1:]
        for record in losses:
            record["outcome"] = "loss"
        result = self.score()
        self.assertEqual(result.counts.scheduled_slots, 12)
        self.assertEqual(result.counts.played_matches, 6)
        self.assertEqual((result.counts.wins, result.counts.losses, result.counts.synthetic_failures), (4, 2, 6))
        self.assertEqual((result.accepted_samples, result.invalid_samples), (1, 1))
        self.assertEqual(result.accepted_sample_fraction, 0.5)
        self.assertEqual(Fraction(result.fitness_fraction), Fraction(17, 60))

    def test_all_invalid_generation_scores_zero_with_no_played_matches(self):
        self.invalidate(0)
        self.invalidate(1)
        result = self.score()
        self.assertEqual(result.fitness, 0)
        self.assertEqual(result.counts.played_matches, 0)
        self.assertEqual(result.counts.synthetic_failures, 12)
        self.assertEqual(result.accepted_sample_fraction, 0)

    def test_bot_fault_is_a_played_loss_with_separate_count(self):
        record = self.bundle["results"][0]
        record.update(status="bot_fault", outcome="loss", cause="decision_timeout", reason="fixture deadline")
        result = self.score()
        self.assertEqual(result.counts.played_matches, 12)
        self.assertEqual((result.counts.wins, result.counts.losses, result.counts.bot_faults), (11, 1, 1))
        self.assertEqual(Fraction(result.fitness_fraction), Fraction(107, 120))

    def test_one_missing_slot_blocks_fitness(self):
        self.bundle["results"].pop()
        with self.assertRaises(IncompleteEvidence) as caught:
            self.score()
        self.assertEqual(caught.exception.missing_slots, 1)
        self.assertFalse(hasattr(caught.exception, "fitness"))

    def test_missing_sample_declaration_and_results_blocks_fitness(self):
        self.bundle["samples"].pop()
        self.bundle["results"] = [r for r in self.bundle["results"] if r["sample_id"] == "sample-0"]
        with self.assertRaises(IncompleteEvidence) as caught:
            self.score()
        self.assertEqual((caught.exception.missing_samples, caught.exception.missing_slots), (1, 6))

    def test_infrastructure_and_interruption_never_become_losses(self):
        for status, cause, attribute in (("infrastructure_fault", "runner", "infrastructure_faults"),
                                         ("interrupted", "operator_interrupt", "interrupted_slots")):
            bundle = copy.deepcopy(self.bundle)
            bundle["results"][0].update(status=status, outcome=None, cause=cause, reason="fixture stop")
            with self.subTest(status=status), self.assertRaises(IncompleteEvidence) as caught:
                self.score(bundle)
            self.assertEqual(getattr(caught.exception, attribute), 1)
            self.assertFalse(hasattr(caught.exception, "fitness"))

    def test_blocked_generation_stays_infrastructure_evidence(self):
        change_sample(self.config, self.bundle, 1, "blocked", None, "provider unavailable")
        for record in self.bundle["results"]:
            if record["sample_id"] == "sample-1":
                record.update(status="infrastructure_fault", outcome=None, cause="provider", reason="provider unavailable")
        with self.assertRaises(IncompleteEvidence) as caught:
            self.score()
        self.assertEqual(caught.exception.blocked_samples, 1)
        self.assertEqual(caught.exception.infrastructure_faults, 6)

    def test_weights_are_configured_and_not_silently_normalized(self):
        for overall, worst, expected in ((1, 0, Fraction(11, 12)), (0, 1, Fraction(5, 6)),
                                          (0.2, 0.8, Fraction(17, 20))):
            document = copy.deepcopy(self.document)
            document["scoring"].update(overall_weight=overall, worst_weight=worst)
            config = validate_config(document)
            bundle = make_bundle(config)
            bundle["results"][0]["outcome"] = "loss"
            with self.subTest(weights=(overall, worst)):
                self.assertEqual(Fraction(self.score(bundle, config).fitness_fraction), expected)
        document = copy.deepcopy(self.document)
        document["scoring"].update(overall_weight=0.7000000005, worst_weight=0.3)
        config = validate_config(document)
        result = self.score(make_bundle(config), config)
        self.assertEqual(Fraction(result.fitness_fraction), Fraction(2000000001, 2000000000))

    def test_holdout_uses_only_holdout_seeds(self):
        bundle = make_bundle(self.config, phase="holdout")
        result = self.score(bundle)
        self.assertEqual(result.phase, "holdout")
        self.assertEqual(result.counts.scheduled_slots, 8)
        self.assertEqual(result.fitness, 1)
        bundle["results"][0]["seed"] = self.config.optimization_seeds[0]
        with self.assertRaisesRegex(ScoringError, "phase schedule"):
            self.score(bundle)

    def test_equal_opponent_schedule_is_required_even_if_aggregate_count_matches(self):
        self.bundle["results"][-1] = copy.deepcopy(self.bundle["results"][0])
        with self.assertRaisesRegex(ScoringError, "duplicate scheduled slot"):
            self.score()

    def test_duplicate_sample_id_index_and_result_are_rejected(self):
        for modification in (
                lambda b: b["samples"][1].update(sample_id=b["samples"][0]["sample_id"]),
                lambda b: b["samples"][1].update(sample_index=0),
                lambda b: b["results"].append(copy.deepcopy(b["results"][0]))):
            bundle = copy.deepcopy(self.bundle)
            modification(bundle)
            with self.assertRaisesRegex(ScoringError, "duplicate"):
                self.score(bundle)

    def test_sample_types_sources_status_and_reasons_are_checked(self):
        for change in (dict(sample_index=True), dict(sample_index=2), dict(sample_id="../escape"),
                       dict(source_hash=None), dict(source_hash="BAD"), dict(generation_status="unknown"),
                       dict(reason="unexpected"), dict(generation_status="invalid", reason=None),
                       dict(generation_status="blocked", reason="fault")):
            bundle = copy.deepcopy(self.bundle)
            bundle["samples"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ScoringError):
                self.score(bundle)

    def test_sample_status_cannot_contradict_slot_category(self):
        self.invalidate(1)
        for record in self.bundle["results"]:
            if record["sample_id"] == "sample-1":
                record.update(status="played", outcome="loss", cause=None, reason=None)
                break
        with self.assertRaisesRegex(ScoringError, "invalid generation"):
            self.score()
        bundle = make_bundle(self.config)
        bundle["results"][0].update(status="invalid_generation", outcome=None,
                                     cause="generation_contract", reason="contradiction")
        with self.assertRaisesRegex(ScoringError, "accepted source"):
            self.score(bundle)

    def test_results_types_outcomes_causes_and_references_are_checked(self):
        changes = [dict(seed=True), dict(seed=-1), dict(seed=99), dict(sample_id="unknown"),
                   dict(opponent_id="unknown"), dict(opponent_source_hash="f" * 64),
                   dict(profile_hash="f" * 64), dict(slot_id="f" * 64), dict(status="unknown"),
                   dict(outcome="winner"), dict(cause="unexpected"), dict(reason="unexpected"),
                   dict(status="bot_fault", outcome="win", cause="exception", reason="fixture"),
                   dict(status="infrastructure_fault", outcome="loss", cause="runner", reason="fixture"),
                   dict(status="interrupted", outcome=None, cause="operator_interrupt", reason=None)]
        for change in changes:
            bundle = copy.deepcopy(self.bundle)
            bundle["results"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ScoringError):
                self.score(bundle)

    def test_closed_schema_and_provenance(self):
        changes = [lambda b: b.update(schema_version=True), lambda b: b.update(schema_version=2),
                   lambda b: b.update(extra=1), lambda b: b.pop("provenance"),
                   lambda b: b["provenance"].update(kind="unknown"),
                   lambda b: b["provenance"].update(description=""),
                   lambda b: b["samples"][0].update(extra=1),
                   lambda b: b["results"][0].pop("cause"),
                   lambda b: b.update(samples="bad"), lambda b: b.update(results=None),
                   lambda b: b.update(phase="unknown"), lambda b: b.update(prompt_id="../escape"),
                   lambda b: b.update(prompt_hash="bad")]
        for change in changes:
            bundle = copy.deepcopy(self.bundle)
            change(bundle)
            with self.assertRaises(ScoringError):
                self.score(bundle)

    def test_frozen_configuration_hash_and_run_identity(self):
        for change in (dict(run_id="other"), dict(configuration_hash="f" * 64)):
            bundle = copy.deepcopy(self.bundle)
            bundle.update(change)
            with self.assertRaisesRegex(ScoringError, "incompatible"):
                self.score(bundle)
        document = copy.deepcopy(self.document)
        document["scoring"].update(overall_weight=0.5, worst_weight=0.5)
        with self.assertRaisesRegex(ScoringError, "configuration_hash"):
            self.score(self.bundle, validate_config(document))

    def test_slot_identity_protocol_and_store_config_hash_match(self):
        record = self.bundle["results"][0]
        key = [1, self.bundle["configuration_hash"], "synthetic-prompt", "a" * 64,
               "optimization", "sample-0", "b" * 64, record["opponent_id"], record["seed"]]
        encoded = (json.dumps(key, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        self.assertEqual(record["slot_id"], hashlib.sha256(encoded).hexdigest())
        with tempfile.TemporaryDirectory() as root:
            store = RunStore.create(root, self.config, provenance="synthetic", description="hash convention fixture")
            self.assertEqual(configuration_hash(self.config), store.manifest()["configuration_hash"])

    def test_input_order_does_not_change_score_and_inputs_are_unchanged(self):
        before = copy.deepcopy(self.bundle)
        expected = self.score().to_dict()
        self.assertEqual(self.bundle, before)
        random.Random(7).shuffle(self.bundle["results"])
        self.bundle["samples"].reverse()
        self.assertEqual(self.score().to_dict(), expected)

    def test_immutable_result_and_detached_json(self):
        result = self.score()
        with self.assertRaises(FrozenInstanceError):
            result.fitness = 999
        snapshot = result.to_dict()
        snapshot["opponents"][0]["counts"]["wins"] = 999
        snapshot["provenance"]["kind"] = "automated"
        self.assertEqual(result.opponents[0].counts.wins, 6)
        self.assertEqual(result.provenance.kind, "synthetic")
        self.assertEqual(json.loads(json.dumps(result.to_dict()))["fitness"], 1)

    def test_config_dataclass_is_revalidated(self):
        with self.assertRaises(ScoringError):
            score_results(replace(self.config, samples_per_prompt=0), self.bundle)
        with self.assertRaises(ScoringError):
            score_results({}, self.bundle)

    def test_large_expected_schedule_blocks_without_expanding_cartesian_product(self):
        document = copy.deepcopy(self.document)
        document["samples_per_prompt"] = 2**53 - 1
        config = validate_config(document)
        bundle = copy.deepcopy(self.bundle)
        bundle["configuration_hash"] = configuration_hash(config)
        bundle["samples"] = []
        bundle["results"] = []
        with self.assertRaises(IncompleteEvidence) as caught:
            self.score(bundle, config)
        self.assertEqual(caught.exception.missing_slots, (2**53 - 1) * 6)

    def test_loader_strict_json_encoding_size_and_io(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "results.json"
            for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'{', b'[]', b'[' * 2000):
                path.write_bytes(data)
                with self.subTest(data=data[:30]), self.assertRaises(ScoringError):
                    load_results(path)
            path.write_bytes(b"x" * (16 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ScoringError, "16 MiB"):
                load_results(path)
            path.unlink()
            with self.assertRaisesRegex(ScoringError, "cannot read"):
                load_results(path)

    def test_no_environment_network_subprocess_or_bot_execution(self):
        with patch("os.getenv", side_effect=AssertionError("credential lookup")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("subprocess.Popen", side_effect=AssertionError("execution")):
            self.assertEqual(self.score().fitness, 1)

    def test_cli_json_success_invalid_and_blocked_exit_statuses(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "results.json"
            args = ["score", "--config", str(EXAMPLE), "--results", str(path)]
            path.write_text(json.dumps(self.bundle))
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(stdout.getvalue())["fitness"], 1)
            self.assertEqual(stderr.getvalue(), "")
            self.bundle["results"].pop()
            path.write_text(json.dumps(self.bundle))
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main(args), 5)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("no final fitness", stderr.getvalue())
            path.write_text("{}")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 2)


if __name__ == "__main__":
    unittest.main()
