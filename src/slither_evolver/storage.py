"""Local immutable evidence, without providers or execution of saved code.

FR-003 / FR-021: freeze validated configuration; hash and preserve prompts
and sample artifacts. This is a single-writer store, not a scheduler,
checkpoint/resume engine, secret scanner, or authenticated evidence archive.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from slither_evolver.config import ConfigError, RunConfig, validate_config


SCHEMA_VERSION = 1
RECORD_LIMIT = 64 * 1024
CONFIG_LIMIT = 1024 * 1024


class StorageError(ValueError):
    """Invalid, incompatible, damaged, or inaccessible stored evidence."""


def text_hash(text: str) -> str:
    """SHA-256 of exact UTF-8 text; line endings are significant."""
    return _digest(_encode(text))


def _encode(text):
    if type(text) is not str:
        raise StorageError("artifact: expected text")
    try:
        return text.encode("utf-8")
    except UnicodeError:
        raise StorageError("artifact: text must be valid UTF-8") from None


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                           allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise StorageError("record: expected finite UTF-8 JSON data") from None


def _identifier(value, field):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise StorageError(f"{field}: use 1–64 letters, digits, underscores, or hyphens")
    return value


def _hash(value):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise StorageError("record: expected a lowercase SHA-256 hash")
    return value


def _fields(record, names):
    if type(record) is not dict or set(record) != set(names.split()):
        raise StorageError("record: missing or unknown fields")


def _bounded_text(value, field, maximum):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise StorageError(f"{field}: expected nonempty text of at most {maximum} characters")
    _encode(value)
    return value


def _plain(path, *, directory=False):
    if path.is_symlink() or (not path.is_dir() if directory else not path.is_file()):
        raise StorageError("store: expected an ordinary file/directory; links are not supported")


def _read(path, limit):
    _plain(path)
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise StorageError("store: file exceeds the supported size limit")
    return data


def _parse(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise StorageError("store: duplicate JSON fields")
            result[key] = value
        return result

    def constant(value):
        raise StorageError("store: nonfinite JSON numbers")

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, StorageError):
            raise
        raise StorageError("store: invalid UTF-8 JSON") from None


@contextmanager
def _io_errors():
    try:
        yield
    except OSError:
        raise StorageError("store: filesystem operation failed; check permissions and free space") from None


@contextmanager
def _writer(path):
    """Cooperating readers/writers see a complete record, or refuse access."""
    _plain(path, directory=True)
    lock = path / ".write-lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise StorageError("store: writer lock exists; inspect an active or interrupted writer before retrying") from None
    try:
        yield
    finally:
        lock.rmdir()


def _atomic_file(path, data):
    """Flush a sibling temporary file, then publish by atomic replacement.

    Caller holds the writer lock and checks that the immutable target is new.
    Filesystem rename/fsync support is required; power-loss durability of the
    directory entry is not claimed across all platforms/filesystems.
    """
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _envelope(payload, manifest_hash):
    return {"schema_version": SCHEMA_VERSION, "manifest_hash": manifest_hash,
            "record_hash": _digest(_json_bytes(payload)), "record": payload}


def _catalog_bytes(payload):
    return _json_bytes({**payload, "catalog_hash": _digest(_json_bytes(payload))})


class RunStore:
    """Open via create/open. Returned records are detached JSON dictionaries."""

    def __init__(self, path, config, manifest):
        self.path = path
        self.config = config
        self._manifest = manifest
        self._manifest_hash = manifest["manifest_hash"]

    @classmethod
    def create(cls, root, config: RunConfig, *, provenance: str, description: str):
        if not isinstance(config, RunConfig):
            raise StorageError("config: expected a validated RunConfig")
        # Revalidate even if a caller constructed or replaced a dataclass.
        try:
            config = validate_config(config.to_dict())
        except ConfigError as error:
            raise StorageError(f"config: {error}") from None
        if provenance not in ("synthetic", "manual", "automated"):
            raise StorageError("provenance: choose synthetic, manual, or automated")
        _bounded_text(description, "description", 2048)
        config_data = _json_bytes(config.to_dict())
        if len(config_data) > CONFIG_LIMIT:
            raise StorageError("config: normalized configuration exceeds 1 MiB")
        manifest = {
            "schema_version": SCHEMA_VERSION, "run_id": config.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "configuration_hash": _digest(config_data),
            "fixed_context": config.to_dict()["fixed_context"],
            "provider": config.to_dict()["provider"], "scoring_version": config.scoring.version,
            "provenance": {"kind": provenance, "description": description},
        }
        manifest["manifest_hash"] = _digest(_json_bytes(manifest))
        path = Path(root) / config.run_id
        with _io_errors():
            Path(root).mkdir(parents=True, exist_ok=True)
            try:
                path.mkdir()
            except FileExistsError:
                raise StorageError("run_id: directory already exists; open it or choose a new run ID") from None
            # A missing final manifest identifies incomplete initialization.
            # Preserve interrupted evidence instead of silently replacing it.
            with _writer(path):
                for name in ("artifacts", "prompts", "samples"):
                    (path / name).mkdir()
                _atomic_file(path / "config.json", config_data)
                catalog = {"schema_version": SCHEMA_VERSION, "manifest_hash": manifest["manifest_hash"],
                           "prompts": {}, "samples": {}}
                _atomic_file(path / "catalog.json", _catalog_bytes(catalog))
                _atomic_file(path / "manifest.json", _json_bytes(manifest))
        return cls.open(path, expected_config=config)

    @classmethod
    def open(cls, path, *, expected_config: RunConfig | None = None):
        path = Path(path)
        with _io_errors(), _writer(path):
            manifest = _parse(_read(path / "manifest.json", CONFIG_LIMIT))
            _fields(manifest, "schema_version run_id created_at configuration_hash fixed_context provider scoring_version provenance manifest_hash")
            if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
                raise StorageError("manifest: unsupported schema version")
            payload = {key: value for key, value in manifest.items() if key != "manifest_hash"}
            if _hash(manifest["manifest_hash"]) != _digest(_json_bytes(payload)):
                raise StorageError("manifest: hash mismatch")
            try:
                created = datetime.fromisoformat(manifest["created_at"])
                if created.utcoffset() is None or created.utcoffset().total_seconds() != 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise StorageError("manifest: expected a UTC creation timestamp") from None
            _fields(manifest["provenance"], "kind description")
            if manifest["provenance"]["kind"] not in ("synthetic", "manual", "automated"):
                raise StorageError("manifest: unknown provenance kind")
            _bounded_text(manifest["provenance"]["description"], "description", 2048)
            config_data = _read(path / "config.json", CONFIG_LIMIT)
            if _hash(manifest["configuration_hash"]) != _digest(config_data):
                raise StorageError("config: hash mismatch")
            try:
                config = validate_config(_parse(config_data))
            except ConfigError as error:
                raise StorageError(f"config: {error}") from None
            if (path.name != config.run_id or manifest["run_id"] != config.run_id
                    or manifest["fixed_context"] != config.to_dict()["fixed_context"]
                    or manifest["provider"] != config.to_dict()["provider"]
                    or type(manifest["scoring_version"]) is not int
                    or manifest["scoring_version"] != config.scoring.version):
                raise StorageError("manifest: incompatible configuration or run identity")
            if expected_config is not None:
                if not isinstance(expected_config, RunConfig) or expected_config.to_dict() != config.to_dict():
                    raise StorageError("config: incompatible with the frozen run")
            store = cls(path, config, manifest)
            store._verify_locked()
        return store

    def manifest(self):
        """Return a detached snapshot after rechecking stored integrity."""
        with _io_errors(), _writer(self.path):
            self._verify_locked()
            return _parse(_json_bytes(self._manifest))

    def verify(self):
        """Verify hashes/record relationships; never execute source text."""
        with _io_errors(), _writer(self.path):
            return self._verify_locked()

    def _verify_locked(self):
        current = _parse(_read(self.path / "manifest.json", CONFIG_LIMIT))
        if current != self._manifest:
            raise StorageError("manifest: changed since the store was opened")
        if _digest(_read(self.path / "config.json", CONFIG_LIMIT)) != self._manifest["configuration_hash"]:
            raise StorageError("config: hash mismatch")
        for name in ("artifacts", "prompts", "samples"):
            _plain(self.path / name, directory=True)
        artifact_count = 0
        limit = max(self.config.limits.max_prompt_chars * 4,
                    self.config.limits.max_source_bytes, self.config.limits.max_response_bytes)
        for path in (self.path / "artifacts").iterdir():
            if path.name.startswith(".pending-") and not path.is_symlink() and path.is_file():
                continue  # Unpublished bytes left by a killed writer; not evidence.
            if not path.name.endswith(".txt"):
                raise StorageError("artifact: unexpected file")
            digest = _hash(path.stem)
            if _digest(_read(path, limit)) != digest:
                raise StorageError("artifact: hash mismatch")
            artifact_count += 1
        prompts = self._records("prompts")
        samples = self._records("samples")
        catalog = self._catalog()
        for folder, records in (("prompts", prompts), ("samples", samples)):
            if set(catalog[folder]) != set(records):
                raise StorageError("catalog: missing or unpublished record; inspect an interrupted write or deletion")
            for identity, digest in catalog[folder].items():
                data = _read(self.path / folder / (identity + ".json"), RECORD_LIMIT)
                if _digest(data) != digest:
                    raise StorageError("catalog: record hash mismatch")
        baseline_count = 0
        for prompt in prompts.values():
            self._check_prompt(prompt, prompts)
            baseline_count += prompt["operator"] == "baseline"
        if baseline_count > 1:
            raise StorageError("prompt: only one baseline identity is allowed")
        slots = set()
        request_ids = set()
        for sample in samples.values():
            self._check_sample(sample, prompts)
            slot = (sample["prompt_id"], sample["phase"], sample["sample_index"])
            if slot in slots or sample["request_id"] in request_ids:
                raise StorageError("sample: duplicate sample slot or request ID")
            slots.add(slot)
            request_ids.add(sample["request_id"])
        return {"run_id": self.config.run_id, "provenance": self._manifest["provenance"]["kind"],
                "prompts": len(prompts), "samples": len(samples), "artifacts": artifact_count}

    def _catalog(self):
        catalog = _parse(_read(self.path / "catalog.json", CONFIG_LIMIT))
        _fields(catalog, "schema_version manifest_hash prompts samples catalog_hash")
        if type(catalog["schema_version"]) is not int or catalog["schema_version"] != SCHEMA_VERSION:
            raise StorageError("catalog: unsupported schema version")
        payload = {key: value for key, value in catalog.items() if key != "catalog_hash"}
        if catalog["manifest_hash"] != self._manifest_hash or _hash(catalog["catalog_hash"]) != _digest(_json_bytes(payload)):
            raise StorageError("catalog: manifest/hash mismatch")
        for folder in ("prompts", "samples"):
            if type(catalog[folder]) is not dict:
                raise StorageError("catalog: expected record IDs and hashes")
            for identity, digest in catalog[folder].items():
                _identifier(identity, "record ID")
                _hash(digest)
        return payload

    def _records(self, folder):
        records = {}
        for path in sorted((self.path / folder).iterdir()):
            if path.name.startswith(".pending-") and not path.is_symlink() and path.is_file():
                continue
            if path.suffix != ".json":
                raise StorageError("record: unexpected file")
            _identifier(path.stem, "record ID")
            envelope = _parse(_read(path, RECORD_LIMIT))
            _fields(envelope, "schema_version manifest_hash record_hash record")
            if type(envelope["schema_version"]) is not int or envelope["schema_version"] != SCHEMA_VERSION:
                raise StorageError("record: unsupported schema version")
            if envelope["manifest_hash"] != self._manifest_hash:
                raise StorageError("record: belongs to a different manifest")
            if _hash(envelope["record_hash"]) != _digest(_json_bytes(envelope["record"])):
                raise StorageError("record: hash mismatch")
            records[path.stem] = envelope["record"]
            id_field = "prompt_id" if folder == "prompts" else "sample_id"
            if type(envelope["record"]) is not dict or envelope["record"].get(id_field) != path.stem:
                raise StorageError("record: filename/identity mismatch")
        return records

    def _artifact(self, digest, byte_limit, supplied=None):
        _hash(digest)
        if supplied is None:
            data = _read(self.path / "artifacts" / (digest + ".txt"), byte_limit)
        else:
            data = _encode(supplied[digest])
            if len(data) > byte_limit:
                raise StorageError("artifact: exceeds its configured byte limit")
        if _digest(data) != digest:
            raise StorageError("artifact: hash mismatch")
        try:
            return data.decode("utf-8")
        except UnicodeError:
            raise StorageError("artifact: expected UTF-8 text") from None

    def _check_prompt(self, record, prompts, supplied=None):
        _fields(record, "prompt_id generation text_hash parents operator")
        _identifier(record["prompt_id"], "prompt_id")
        generation = record["generation"]
        if type(generation) is not int or not 0 <= generation < self.config.generation_count:
            raise StorageError("generation: outside the configured range")
        parents = record["parents"]
        if type(parents) is not list or len(parents) > 2:
            raise StorageError("parents: expected at most two parent IDs")
        for parent in parents:
            _identifier(parent, "parent ID")
            if parent not in prompts:
                raise StorageError("parents: must reference existing earlier-generation prompts")
            _fields(prompts[parent], "prompt_id generation text_hash parents operator")
            if type(prompts[parent]["generation"]) is not int or prompts[parent]["generation"] >= generation:
                raise StorageError("parents: must reference existing earlier-generation prompts")
        if len(parents) != len(set(parents)):
            raise StorageError("parents: duplicate IDs")
        operator = record["operator"]
        if operator in ("baseline", "seed"):
            if generation != 0 or parents:
                raise StorageError("prompt: baseline/seed requires generation zero and no parents")
        elif operator == "mutation":
            if len(parents) != 1:
                raise StorageError("prompt: mutation requires one parent")
        elif operator == "crossover":
            if len(parents) != 2:
                raise StorageError("prompt: crossover requires two parents")
        else:
            raise StorageError("operator: expected baseline, seed, mutation, or crossover")
        text = self._artifact(record["text_hash"], self.config.limits.max_prompt_chars * 4, supplied)
        _bounded_text(text, "prompt text", self.config.limits.max_prompt_chars)
        if operator == "baseline" and record["text_hash"] != self.config.fixed_context.baseline_prompt_hash:
            raise StorageError("baseline: text does not match the frozen baseline hash")

    def _check_sample(self, record, prompts, supplied=None):
        _fields(record, "sample_id prompt_id phase sample_index request_id status reason response_hash source_hash")
        for name in ("sample_id", "prompt_id", "request_id"):
            _identifier(record[name], name)
        if record["prompt_id"] not in prompts:
            raise StorageError("sample: unknown prompt")
        if record["phase"] not in ("optimization", "holdout"):
            raise StorageError("phase: expected optimization or holdout")
        if type(record["sample_index"]) is not int or not 0 <= record["sample_index"] < self.config.samples_per_prompt:
            raise StorageError("sample_index: outside the configured range")
        if record["status"] == "unvalidated":
            if record["source_hash"] is None or record["reason"] is not None:
                raise StorageError("sample: unvalidated requires source and no failure reason")
        elif record["status"] == "invalid":
            _bounded_text(record["reason"], "reason", 2048)
        else:
            raise StorageError("status: only unvalidated or invalid is supported; no bot validity is certified")
        self._artifact(record["response_hash"], self.config.limits.max_response_bytes, supplied)
        if record["source_hash"] is not None:
            source = self._artifact(record["source_hash"], self.config.limits.max_source_bytes, supplied)
            _bounded_text(source, "source", self.config.limits.max_source_bytes)

    def _save_artifact(self, text, limit):
        data = _encode(text)
        if len(data) > limit:
            raise StorageError("artifact: exceeds its configured byte limit")
        digest = _digest(data)
        path = self.path / "artifacts" / (digest + ".txt")
        if path.exists() or path.is_symlink():
            if _read(path, limit) != data:
                raise StorageError("artifact: existing content is incompatible")
        else:
            _atomic_file(path, data)
        return digest

    def _save_record(self, folder, record, artifacts):
        identity = record["prompt_id" if folder == "prompts" else "sample_id"]
        _identifier(identity, "record ID")
        data = _json_bytes(_envelope(record, self._manifest_hash))
        if len(data) > RECORD_LIMIT:
            raise StorageError("record: exceeds 64 KiB")
        path = self.path / folder / (identity + ".json")
        if path.exists() or path.is_symlink():
            if _read(path, RECORD_LIMIT) != data:
                raise StorageError("record ID: already exists with different content")
            return  # Exact repetition is idempotent.
        for text, limit in artifacts:
            self._save_artifact(text, limit)
        catalog = self._catalog()
        catalog[folder][identity] = _digest(data)
        catalog_data = _catalog_bytes(catalog)
        if len(catalog_data) > CONFIG_LIMIT:
            raise StorageError("catalog: exceeds 1 MiB; start a new bounded run")
        _atomic_file(path, data)
        # Final catalog replacement commits the record. An interrupted gap
        # blocks verification; it never invents completion or paid-call retries.
        _atomic_file(self.path / "catalog.json", catalog_data)

    def add_prompt(self, prompt_id, text, *, generation=0, parents=(), operator="seed"):
        """Preserve exact text and lineage. Existing IDs never change content."""
        _bounded_text(text, "prompt text", self.config.limits.max_prompt_chars)
        if not isinstance(parents, (list, tuple)):
            raise StorageError("parents: expected a list or tuple")
        record = {"prompt_id": prompt_id, "generation": generation, "text_hash": text_hash(text),
                  "parents": list(parents), "operator": operator}
        with _io_errors(), _writer(self.path):
            self._verify_locked()
            prompts = self._records("prompts")
            # Validate before publishing any bytes, using the prospective text.
            self._validate_new_prompt(record, text, prompts)
            self._save_record("prompts", record, [(text, self.config.limits.max_prompt_chars * 4)])
        return record

    def _validate_new_prompt(self, record, text, prompts):
        self._check_prompt(record, prompts, {record["text_hash"]: text})
        if record["operator"] == "baseline" and any(
                item["operator"] == "baseline" and item["prompt_id"] != record["prompt_id"]
                for item in prompts.values()):
            raise StorageError("baseline: a different identity already exists")

    def get_prompt(self, prompt_id):
        _identifier(prompt_id, "prompt_id")
        with _io_errors(), _writer(self.path):
            self._verify_locked()
            record = self._records("prompts").get(prompt_id)
            if record is None:
                raise StorageError("prompt_id: not found")
            return {**record, "text": self._artifact(record["text_hash"], self.config.limits.max_prompt_chars * 4)}

    def add_sample(self, sample_id, prompt_id, *, phase, sample_index, request_id,
                   response, source, status="unvalidated", reason=None):
        """Record a supplied sample; does not generate, validate, or run it."""
        record = {"sample_id": sample_id, "prompt_id": prompt_id, "phase": phase,
                  "sample_index": sample_index, "request_id": request_id, "status": status,
                  "reason": reason, "response_hash": text_hash(response),
                  "source_hash": None if source is None else text_hash(source)}
        artifacts = [(response, self.config.limits.max_response_bytes)]
        if source is not None:
            artifacts.append((source, self.config.limits.max_source_bytes))
        for text, limit in artifacts:
            if len(_encode(text)) > limit:
                raise StorageError("artifact: exceeds its configured byte limit")
        with _io_errors(), _writer(self.path):
            self._verify_locked()
            prompts = self._records("prompts")
            supplied = {record["response_hash"]: response}
            if source is not None:
                supplied[record["source_hash"]] = source
            self._check_sample(record, prompts, supplied)
            for saved in self._records("samples").values():
                if saved["sample_id"] != sample_id and (
                        (saved["prompt_id"], saved["phase"], saved["sample_index"]) == (prompt_id, phase, sample_index)
                        or saved["request_id"] == request_id):
                    raise StorageError("sample: duplicate sample slot or request ID")
            self._save_record("samples", record, artifacts)
        return record

    def get_sample(self, sample_id):
        _identifier(sample_id, "sample_id")
        with _io_errors(), _writer(self.path):
            self._verify_locked()
            record = self._records("samples").get(sample_id)
            if record is None:
                raise StorageError("sample_id: not found")
            return {**record,
                    "response": self._artifact(record["response_hash"], self.config.limits.max_response_bytes),
                    "source": None if record["source_hash"] is None else self._artifact(
                        record["source_hash"], self.config.limits.max_source_bytes)}
