"""Offline persistence, integrity, compatibility, and interrupted-write tests."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from slither_evolver.__main__ import main
from slither_evolver.config import validate_config
from slither_evolver.storage import RunStore, StorageError, text_hash


EXAMPLE = Path(__file__).resolve().parents[1] / "configs" / "offline.example.json"
BASELINE = "Avoid walls.\nPrefer open space.\n"


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "runs"
        self.document = json.loads(EXAMPLE.read_text())
        self.document["run_id"] = "storage-fixture"
        self.document["fixed_context"]["baseline_prompt_hash"] = text_hash(BASELINE)
        self.config = validate_config(self.document)
        self.store = RunStore.create(self.root, self.config, provenance="synthetic",
                                     description="Synthetic unit-test fixture; no model or games.")

    def seed(self):
        return self.store.add_prompt("baseline", BASELINE, operator="baseline")

    def sample(self, **changes):
        values = dict(sample_id="s0", prompt_id="baseline", phase="optimization",
                      sample_index=0, request_id="request0", response="synthetic raw response\r\n",
                      source="function playerAI() { return 'UP'; }\n")
        values.update(changes)
        return self.store.add_sample(**values)

    def test_initialize_reopen_and_manifest_is_detached(self):
        first = self.store.manifest()
        self.assertEqual(first["provenance"]["kind"], "synthetic")
        self.assertEqual(first["fixed_context"], self.document["fixed_context"])
        self.assertIsNone(first["provider"])
        first["provenance"]["kind"] = "automated"
        reopened = RunStore.open(self.store.path, expected_config=self.config)
        self.assertEqual(reopened.manifest()["provenance"]["kind"], "synthetic")
        self.assertEqual(reopened.config.to_dict(), self.config.to_dict())
        self.assertEqual(reopened.verify()["prompts"], 0)

    def test_small_numeric_money_survives_persistence_without_exponent_notation(self):
        document = copy.deepcopy(self.document)
        document["run_id"] = "small-money"
        document["budget"].update(max_cost=1e-7, max_request_cost=1e-8)
        config = validate_config(document)
        store = RunStore.create(self.root, config, provenance="synthetic", description="Decimal fixture")
        reopened = RunStore.open(store.path, expected_config=config)
        self.assertEqual(reopened.config.to_dict()["budget"]["max_cost"], "0.0000001")
        self.assertEqual(reopened.config.to_dict()["budget"]["max_request_cost"], "0.00000001")

    def test_existing_run_is_never_reinitialized(self):
        before = (self.store.path / "manifest.json").read_bytes()
        with self.assertRaisesRegex(StorageError, "already exists"):
            RunStore.create(self.root, self.config, provenance="manual", description="different")
        self.assertEqual((self.store.path / "manifest.json").read_bytes(), before)

    def test_create_revalidates_dataclass_and_requires_provenance(self):
        from dataclasses import replace
        for bad in (None, replace(self.config, run_id="../escape"),
                    replace(self.config, samples_per_prompt=0)):
            with self.subTest(config=bad), self.assertRaises(StorageError):
                RunStore.create(self.root, bad, provenance="synthetic", description="test")
        for kind, note in (("unknown", "test"), ("synthetic", ""), ("manual", "x" * 2049)):
            with self.subTest(kind=kind), self.assertRaises(StorageError):
                RunStore.create(self.root, self.config, provenance=kind, description=note)

    def test_prompt_text_lineage_and_unicode_roundtrip(self):
        self.seed()
        text = "Turn toward open space. 🐍\r\n"
        self.store.add_prompt("child", text, generation=1, parents=["baseline"], operator="mutation")
        reopened = RunStore.open(self.store.path)
        record = reopened.get_prompt("child")
        self.assertEqual(record["text"], text)
        self.assertEqual(record["parents"], ["baseline"])
        record["parents"].clear()
        self.assertEqual(reopened.get_prompt("child")["parents"], ["baseline"])
        self.assertEqual(reopened.get_prompt("baseline")["text"], BASELINE)

    def test_prompt_idempotence_and_conflicting_write(self):
        self.seed()
        self.seed()
        self.assertEqual(self.store.verify()["prompts"], 1)
        with self.assertRaisesRegex(StorageError, "different content"):
            self.store.add_prompt("baseline", "different text", operator="seed")
        self.assertEqual(self.store.get_prompt("baseline")["text"], BASELINE)

    def test_baseline_requires_frozen_hash_and_single_identity(self):
        with self.assertRaisesRegex(StorageError, "baseline hash"):
            self.store.add_prompt("wrong", "wrong text", operator="baseline")
        self.seed()
        with self.assertRaisesRegex(StorageError, "different identity"):
            self.store.add_prompt("other", BASELINE, operator="baseline")
        self.assertEqual(self.store.verify()["prompts"], 1)

    def test_invalid_prompt_ids_bounds_and_lineage_do_not_publish_records(self):
        self.seed()
        cases = [dict(prompt_id="../escape"), dict(prompt_id="x", generation=True),
                 dict(prompt_id="x", generation=2), dict(prompt_id="x", operator="repair"),
                 dict(prompt_id="x", parents="baseline"),
                 dict(prompt_id="x", generation=1, parents=["missing"], operator="mutation"),
                 dict(prompt_id="x", generation=0, parents=["baseline"], operator="mutation"),
                 dict(prompt_id="x", generation=1, parents=[], operator="mutation"),
                 dict(prompt_id="x", generation=1, parents=["baseline", "baseline"], operator="crossover")]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(StorageError):
                self.store.add_prompt(text="new prompt", **values)
        self.assertEqual(self.store.verify()["prompts"], 1)
        self.assertEqual(self.store.verify()["artifacts"], 1)

    def test_crossover_requires_distinct_earlier_parents(self):
        self.seed()
        self.store.add_prompt("seed2", "Second strategy")
        self.store.add_prompt("cross", "Combined strategy", generation=1,
                              parents=["baseline", "seed2"], operator="crossover")
        self.assertEqual(self.store.get_prompt("cross")["parents"], ["baseline", "seed2"])

    def test_prompt_character_limit_and_invalid_utf8(self):
        for text in ("", " ", "x" * (self.config.limits.max_prompt_chars + 1), "\ud800"):
            with self.subTest(length=len(text)), self.assertRaises(StorageError):
                self.store.add_prompt("p", text)
        self.assertEqual(self.store.verify()["artifacts"], 0)

    def test_sample_response_and_source_roundtrip_without_execution(self):
        self.seed()
        source = "throw new Error('NEVER EXECUTE');\r\n"
        self.sample(source=source)
        restored = RunStore.open(self.store.path).get_sample("s0")
        self.assertEqual(restored["source"], source)
        self.assertEqual(restored["response"], "synthetic raw response\r\n")
        self.assertEqual(restored["status"], "unvalidated")
        self.assertEqual(restored["source_hash"], text_hash(source))

    def test_invalid_sample_preserves_empty_response_and_failure(self):
        self.seed()
        self.sample(response="", source=None, status="invalid", reason="No bot source returned")
        restored = self.store.get_sample("s0")
        self.assertEqual(restored["response"], "")
        self.assertIsNone(restored["source"])
        self.assertEqual(restored["reason"], "No bot source returned")

    def test_sample_idempotence_conflicts_and_duplicate_slot_request(self):
        self.seed()
        self.sample()
        self.sample()
        for change in (dict(response="changed"), dict(sample_id="s1", request_id="request1"),
                       dict(sample_id="s1", sample_index=1)):
            with self.subTest(change=change), self.assertRaises(StorageError):
                self.sample(**change)
        self.assertEqual(self.store.verify()["samples"], 1)

    def test_phases_and_sample_indices_have_distinct_identities(self):
        self.seed()
        self.sample()
        self.sample(sample_id="s1", sample_index=1, request_id="request1")
        self.sample(sample_id="h0", phase="holdout", request_id="holdout0")
        self.assertEqual(self.store.verify()["samples"], 3)

    def test_sample_types_status_and_reference_validation(self):
        self.seed()
        cases = [dict(sample_id="../escape"), dict(prompt_id="missing"), dict(phase="unknown"),
                 dict(sample_index=True), dict(sample_index=-1), dict(sample_index=2),
                 dict(request_id="bad/request"), dict(status="valid"), dict(source=None),
                 dict(source=""), dict(reason="unexpected"), dict(status="invalid", reason=None)]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(StorageError):
                self.sample(**values)
        self.assertEqual(self.store.verify()["samples"], 0)
        self.assertEqual(self.store.verify()["artifacts"], 1)

    def test_sample_limits_use_utf8_bytes(self):
        self.seed()
        for field, limit in (("source", self.config.limits.max_source_bytes),
                             ("response", self.config.limits.max_response_bytes)):
            with self.subTest(field=field), self.assertRaises(StorageError):
                self.sample(**{field: "🐍" * (limit // 4 + 1)})
        self.assertEqual(self.store.verify()["samples"], 0)

    def test_artifact_deduplication_preserves_separate_records(self):
        self.store.add_prompt("a", "same text")
        self.store.add_prompt("b", "same text")
        self.assertEqual(self.store.verify()["prompts"], 2)
        self.assertEqual(self.store.verify()["artifacts"], 1)

    def test_different_config_context_and_model_are_incompatible(self):
        modifications = [("fixed_context", "game_hash", "f" * 64),
                         ("fixed_context", "source_commit", "f" * 40),
                         ("scoring", "overall_weight", 0.6)]
        for section, key, value in modifications:
            document = copy.deepcopy(self.document)
            document[section][key] = value
            if section == "scoring":
                document[section]["worst_weight"] = 0.4
            with self.subTest(key=key), self.assertRaisesRegex(StorageError, "incompatible"):
                RunStore.open(self.store.path, expected_config=validate_config(document))
        changed = copy.deepcopy(self.document)
        changed["provider"] = dict(adapter="fake", model="fake-model", credential_env="FAKE_KEY",
                                    max_output_tokens=100, settings={"temperature": 0.5})
        with self.assertRaisesRegex(StorageError, "incompatible"):
            RunStore.open(self.store.path, expected_config=validate_config(changed))

    def test_configuration_bytes_tampering_blocks_open_and_existing_handle(self):
        with (self.store.path / "config.json").open("ab") as stream:
            stream.write(b" ")
        for action in (lambda: RunStore.open(self.store.path), self.store.verify):
            with self.assertRaisesRegex(StorageError, "hash mismatch"):
                action()

    def test_deleted_sample_is_detected_by_committed_catalog(self):
        self.seed()
        self.sample()
        (self.store.path / "samples" / "s0.json").unlink()
        with self.assertRaisesRegex(StorageError, "missing or unpublished record"):
            RunStore.open(self.store.path)

    def test_deleted_prompt_and_catalog_tampering_are_detected(self):
        self.seed()
        (self.store.path / "prompts" / "baseline.json").unlink()
        with self.assertRaisesRegex(StorageError, "missing or unpublished record"):
            self.store.verify()
        path = self.store.path / "catalog.json"
        document = json.loads(path.read_bytes())
        document["prompts"] = {}
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(StorageError, "hash mismatch"):
            self.store.verify()

    def test_failure_before_catalog_commit_blocks_incomplete_record(self):
        original_catalog = (self.store.path / "catalog.json").read_bytes()
        real_replace = __import__("os").replace
        def fail_catalog(source, destination):
            if Path(destination).name == "catalog.json":
                raise OSError("injected interruption before commit")
            real_replace(source, destination)
        with patch("slither_evolver.storage.os.replace", side_effect=fail_catalog):
            with self.assertRaises(StorageError):
                self.seed()
        self.assertEqual((self.store.path / "catalog.json").read_bytes(), original_catalog)
        self.assertTrue((self.store.path / "prompts" / "baseline.json").exists())
        with self.assertRaisesRegex(StorageError, "missing or unpublished record"):
            RunStore.open(self.store.path)

    def test_manifest_schema_missing_fields_and_hash_tampering(self):
        path = self.store.path / "manifest.json"
        original = path.read_bytes()
        for modification in (lambda d: d.update(schema_version=2),
                             lambda d: d.pop("provider"), lambda d: d.update(run_id="changed")):
            document = json.loads(original)
            modification(document)
            path.write_text(json.dumps(document))
            with self.assertRaises(StorageError):
                RunStore.open(self.store.path)
        path.write_bytes(original)
        self.assertEqual(self.store.verify()["prompts"], 0)

    def test_changed_artifact_and_missing_artifact_block_verification(self):
        record = self.seed()
        path = self.store.path / "artifacts" / (record["text_hash"] + ".txt")
        original = path.read_bytes()
        path.write_bytes(original + b"x")
        with self.assertRaisesRegex(StorageError, "hash mismatch"):
            RunStore.open(self.store.path)
        path.unlink()
        with self.assertRaises(StorageError):
            self.store.verify()

    def test_record_metadata_tampering_and_cross_run_record_rejected(self):
        self.seed()
        path = self.store.path / "prompts" / "baseline.json"
        original = path.read_bytes()
        document = json.loads(original)
        document["record"]["operator"] = "seed"
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(StorageError, "hash mismatch"):
            self.store.verify()
        document = json.loads(original)
        document["manifest_hash"] = "f" * 64
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(StorageError, "different manifest"):
            self.store.verify()

    def test_strict_json_duplicate_fields_and_nonfinite_values(self):
        path = self.store.path / "manifest.json"
        for data in (b'{"run_id":"a","run_id":"b"}', b'{"number":NaN}', b'\xff', b'{'):
            with self.subTest(data=data):
                path.write_bytes(data)
                with self.assertRaises(StorageError):
                    RunStore.open(self.store.path)

    def test_oversized_and_unexpected_record_files_rejected(self):
        path = self.store.path / "prompts" / "huge.json"
        path.write_bytes(b"x" * (64 * 1024 + 1))
        with self.assertRaisesRegex(StorageError, "size limit"):
            self.store.verify()
        path.unlink()
        (self.store.path / "samples" / "unexpected.txt").write_text("not a record")
        with self.assertRaisesRegex(StorageError, "unexpected file"):
            self.store.verify()

    def test_paths_and_links_do_not_redirect_artifact_access(self):
        self.seed()
        external = Path(self.temporary.name) / "external.txt"
        external.write_text(BASELINE)
        path = self.store.path / "artifacts" / (text_hash(BASELINE) + ".txt")
        path.unlink()
        try:
            path.symlink_to(external)
        except OSError:
            self.skipTest("Symlink creation unavailable on this platform")
        with self.assertRaisesRegex(StorageError, "links"):
            self.store.verify()
        self.assertEqual(external.read_text(), BASELINE)

    def test_active_or_stale_lock_refuses_access(self):
        lock = self.store.path / ".write-lock"
        lock.mkdir()
        for action in (self.store.verify, lambda: RunStore.open(self.store.path), self.seed):
            with self.assertRaisesRegex(StorageError, "writer lock"):
                action()
        self.assertTrue(lock.exists())
        lock.rmdir()
        self.assertEqual(self.store.verify()["prompts"], 0)

    def test_failed_record_publication_leaves_no_partial_record_and_allows_retry(self):
        real_replace = __import__("os").replace
        def fail_record(source, destination):
            if Path(destination).parent.name == "prompts":
                raise OSError("injected disk error")
            real_replace(source, destination)
        with patch("slither_evolver.storage.os.replace", side_effect=fail_record):
            with self.assertRaises(StorageError):
                self.seed()
        self.assertFalse((self.store.path / "prompts" / "baseline.json").exists())
        self.assertEqual(self.store.verify()["prompts"], 0)
        self.seed()
        self.assertEqual(RunStore.open(self.store.path).verify()["prompts"], 1)

    def test_failed_flush_never_publishes_prompt_or_partial_bytes(self):
        with patch("slither_evolver.storage.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(StorageError):
                self.seed()
        self.assertEqual(self.store.verify()["prompts"], 0)
        self.assertEqual(self.store.verify()["artifacts"], 0)
        self.assertFalse(list(self.store.path.rglob(".pending-*")))

    def test_interrupted_initialization_is_preserved_and_rejected(self):
        document = copy.deepcopy(self.document)
        document["run_id"] = "incomplete"
        config = validate_config(document)
        real_replace = __import__("os").replace
        def fail_manifest(source, destination):
            if Path(destination).name == "manifest.json":
                raise OSError("injected interruption")
            real_replace(source, destination)
        with patch("slither_evolver.storage.os.replace", side_effect=fail_manifest):
            with self.assertRaises(StorageError):
                RunStore.create(self.root, config, provenance="synthetic", description="interruption fixture")
        path = self.root / "incomplete"
        self.assertTrue((path / "config.json").is_file())
        with self.assertRaises(StorageError):
            RunStore.open(path)
        with self.assertRaisesRegex(StorageError, "already exists"):
            RunStore.create(self.root, config, provenance="synthetic", description="retry")

    def test_abandoned_temporary_bytes_are_not_completed_evidence(self):
        (self.store.path / "prompts" / ".pending-killed-writer").write_bytes(b"partial")
        self.assertEqual(self.store.verify()["prompts"], 0)
        self.seed()
        self.assertEqual(self.store.verify()["prompts"], 1)

    def test_no_credentials_network_subprocess_or_bot_execution(self):
        self.seed()
        with patch("os.getenv", side_effect=AssertionError("credential lookup")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("subprocess.Popen", side_effect=AssertionError("process execution")):
            self.sample()
            RunStore.open(self.store.path).get_sample("s0")
            self.store.verify()

    def test_cli_initialization_inspection_duplicate_and_invalid_config(self):
        root = Path(self.temporary.name) / "cli-runs"
        config = Path(self.temporary.name) / "cli.json"
        config.write_text(json.dumps(self.document))
        args = ["init", "--config", str(config), "--runs-dir", str(root),
                "--provenance", "synthetic", "--description", "CLI fixture"]
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            self.assertEqual(main(args), 0)
            self.assertEqual(main(["inspect", "--run", str(root / self.config.run_id)]), 0)
            self.assertEqual(main(args), 4)
            config.write_text("{}")
            self.assertEqual(main(args), 2)
        self.assertIn("Created local run", output.getvalue())
        self.assertIn("Integrity checks passed", output.getvalue())
        self.assertIn("Storage error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
