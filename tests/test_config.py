"""FR-001 / TC-001 validation assertions using synthetic data only."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from slither_evolver.__main__ import main
from slither_evolver.config import ConfigError, load_config, validate_config


EXAMPLE = Path(__file__).resolve().parents[1] / "configs" / "offline.example.json"


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def live_example():
    document = example()
    document["provider"] = {
        "adapter": "synthetic-provider", "model": "synthetic-model",
        "credential_env": "SYNTHETIC_KEY", "max_output_tokens": 1000,
        "settings": {"temperature": 0.2, "stop": ["synthetic-stop"]},
    }
    document["budget"] = {
        "max_requests": 3, "max_cost": "0.30", "currency": "USD",
        "max_request_cost": "0.10", "pricing_version": "synthetic-price-v1",
    }
    return document


class ConfigTests(unittest.TestCase):
    def reject(self, document, message):
        with self.assertRaisesRegex(ConfigError, message):
            validate_config(document)

    def test_offline_example_and_roundtrip(self):
        config = load_config(EXAMPLE)
        self.assertEqual(config.run_id, "synthetic-config-check")
        self.assertEqual(config.optimization_seeds, (0, 1, 2))
        self.assertEqual(config.scoring.overall_weight, 0.7)
        self.assertEqual(config.to_dict(), example())
        self.assertEqual(validate_config(config.to_dict()), config)

    def test_input_is_unchanged(self):
        document = live_example()
        original = deepcopy(document)
        validate_config(document, live=True)
        self.assertEqual(document, original)

    def test_deep_immutability_and_detached_snapshot(self):
        config = validate_config(live_example(), live=True)
        with self.assertRaises(FrozenInstanceError):
            config.population_size = 20
        with self.assertRaises(FrozenInstanceError):
            config.search.seed = 4
        with self.assertRaises(TypeError):
            config.provider.settings["temperature"] = 0.5
        with self.assertRaises(TypeError):
            config.provider.settings["stop"][0] = "changed"
        snapshot = config.to_dict()
        snapshot["provider"]["settings"]["stop"].append("changed")
        self.assertEqual(config.provider.settings["stop"], ("synthetic-stop",))

    def test_closed_nested_records(self):
        paths = [(), ("search",), ("scoring",), ("limits",),
                 ("fixed_context",), ("budget",), ("provider",), ("opponents", 0)]
        for path in paths:
            for change in ["unknown", "missing"]:
                with self.subTest(path=path, change=change):
                    document = live_example()
                    target = document
                    for key in path:
                        target = target[key]
                    if change == "unknown":
                        target["typo"] = 1
                    else:
                        del target[next(iter(target))]
                    self.reject(document, change + " field")

    def test_top_level_requires_json_object(self):
        for value in [None, [], 1, "text", {1: "bad-key"}]:
            with self.subTest(value=value):
                self.reject(value, "JSON object")

    def test_counts_reject_bad_types_and_bounds(self):
        for field in ["population_size", "generation_count", "samples_per_prompt"]:
            for value in [True, False, 0, -1, 1.5, "2", None, 2**53]:
                with self.subTest(field=field, value=value):
                    document = example()
                    document[field] = value
                    self.reject(document, field)
        document = example()
        document.update(population_size=2, generation_count=1, samples_per_prompt=1)
        self.assertEqual(validate_config(document).samples_per_prompt, 1)

    def test_versions_and_modes(self):
        for field, value in [("schema_version", 2), ("schema_version", True),
                             ("mode", "replay"), ("mode", " live ")]:
            document = example()
            document[field] = value
            self.reject(document, field)
        document = example()
        document["scoring"]["version"] = 2
        self.reject(document, "scoring.version")
        document = example()
        document["mode"] = "evolve"
        self.assertEqual(validate_config(document).mode, "evolve")

    def test_run_id_cannot_be_a_path(self):
        for value in ["../run", "run/name", "", "a" * 65, "name with spaces"]:
            document = example()
            document["run_id"] = value
            self.reject(document, "run_id")

    def test_search_integer_bounds(self):
        for field, value in [("elite_count", 0), ("elite_count", 4),
                             ("tournament_size", 0), ("tournament_size", 5),
                             ("max_population_attempts", 0), ("seed", -1),
                             ("seed", True), ("seed", 2**32)]:
            document = example()
            document["search"][field] = value
            self.reject(document, field)

    def test_probabilities_and_weights(self):
        for section, field in [("search", "mutation_probability"),
                               ("scoring", "overall_weight")]:
            for value in [True, -0.1, 1.1, float("nan"), float("inf"), "0.7", 0.6]:
                with self.subTest(section=section, value=value):
                    document = example()
                    document[section][field] = value
                    self.reject(document, section)
        document = example()
        document["search"].update(mutation_probability=0, crossover_probability=1)
        validate_config(document)

    def test_seeds_unique_nonempty_bounded_and_disjoint(self):
        for field in ["optimization_seeds", "holdout_seeds"]:
            for value in [[], [1, 1], [-1], [True], [2**32], [1.5], "1"]:
                with self.subTest(field=field, value=value):
                    document = example()
                    document[field] = value
                    self.reject(document, field)
        document = example()
        document["holdout_seeds"] = [2, 100]
        self.reject(document, "must not overlap")
        document = example()
        document["holdout_seeds"] = [2**32 - 1]
        validate_config(document)

    def test_opponent_records_and_hashes(self):
        document = example()
        document["opponents"] = []
        self.reject(document, "opponents")
        document = example()
        document["opponents"] *= 2
        self.reject(document, "unique")
        document = example()
        document["opponents"][0]["source_hash"] = "not-a-hash"
        self.reject(document, "source_hash")
        for field in example()["fixed_context"]:
            document = example()
            document["fixed_context"][field] = "missing"
            self.reject(document, field)

    def test_resource_bounds_and_coherent_deadlines(self):
        for field in example()["limits"]:
            for value in [0, -1, True, float("inf"), 10**400]:
                with self.subTest(field=field, kind=type(value).__name__):
                    document = example()
                    document["limits"][field] = value
                    self.reject(document, "limits")
        document = example()
        document["limits"]["decision_timeout_ms"] = 10001
        self.reject(document, "fit within")

    def test_live_requires_provider(self):
        with self.assertRaisesRegex(ConfigError, "provider: required"):
            validate_config(example(), live=True)

    def test_live_requires_each_budget_field(self):
        for field in live_example()["budget"]:
            document = live_example()
            document["budget"][field] = None
            with self.assertRaisesRegex(ConfigError, "live readiness requires"):
                validate_config(document, live=True)

    def test_budget_amounts_counts_currency_and_per_request_cap(self):
        for field in ["max_cost", "max_request_cost"]:
            for value in [0, -1, True, "NaN", "Infinity", "bad", " 1 ", "1_0"]:
                document = live_example()
                document["budget"][field] = value
                self.reject(document, field)
        for value in [0, True, 1.5, float("inf")]:
            document = live_example()
            document["budget"]["max_requests"] = value
            self.reject(document, "max_requests")
        document = live_example()
        document["budget"]["max_request_cost"] = "0.31"
        self.reject(document, "must not exceed")
        document = live_example()
        document["budget"]["currency"] = "usd"
        self.reject(document, "currency")

    def test_decimal_precision_and_json_roundtrip(self):
        document = live_example()
        document["budget"]["max_request_cost"] = "0.1000000000000000001"
        config = validate_config(document, live=True)
        self.assertEqual(config.budget.max_request_cost, Decimal("0.1000000000000000001"))
        encoded = json.dumps(config.to_dict(), allow_nan=False)
        self.assertEqual(validate_config(json.loads(encoded), live=True), config)

    def test_provider_fields_and_json_setting_types(self):
        for field, value in [("max_output_tokens", 0), ("model", ""),
                             ("credential_env", "not-a-variable"),
                             ("settings", []), ("adapter", "../adapter")]:
            document = live_example()
            document["provider"][field] = value
            self.reject(document, "provider")
        for value in [float("nan"), {1, 2}, object()]:
            document = live_example()
            document["provider"]["settings"]["bad"] = value
            self.reject(document, "finite JSON")

    def test_nested_credential_fields_rejected_without_echoing_value(self):
        document = live_example()
        document["provider"]["settings"]["nested"] = {"api-key": "synthetic-sensitive-marker"}
        with self.assertRaises(ConfigError) as result:
            validate_config(document)
        self.assertNotIn("synthetic-sensitive-marker", str(result.exception))

    def test_no_environment_or_network_access_even_in_live_check(self):
        with patch("os.getenv", side_effect=AssertionError("secret lookup")), \
             patch("socket.socket", side_effect=AssertionError("network access")):
            validate_config(live_example(), live=True)

    def test_live_flag_must_be_boolean(self):
        with self.assertRaisesRegex(ConfigError, "Boolean"):
            validate_config(example(), live="true")

    def test_json_syntax_duplicate_fields_and_nonfinite_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for text in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{broken']:
                path.write_text(text)
                with self.assertRaises(ConfigError):
                    load_config(path)
            path.write_bytes(b'\xff')
            with self.assertRaisesRegex(ConfigError, "UTF-8"):
                load_config(path)
            path.unlink()
            with self.assertRaisesRegex(ConfigError, "path and permissions"):
                load_config(path)

    def test_deep_json_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            document = live_example()
            nested = "synthetic"
            for _ in range(70):
                nested = [nested]
            document["provider"]["settings"]["deep"] = nested
            path.write_text(json.dumps(document))
            with self.assertRaisesRegex(ConfigError, "nesting is too deep"):
                load_config(path)

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_bytes(b" " * (1024 * 1024 + 1))
            with self.assertRaisesRegex(ConfigError, "1 MiB"):
                load_config(path)

    def test_huge_json_integer_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"samples_per_prompt":' + '9' * 10000 + '}')
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_cli_success_and_failure_exit_statuses(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main(["validate", "--config", str(EXAMPLE)]), 0)
            self.assertEqual(main(["validate", "--config", str(EXAMPLE), "--live"]), 2)
        self.assertIn("No requests made", stdout.getvalue())
        self.assertIn("provider: required", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
