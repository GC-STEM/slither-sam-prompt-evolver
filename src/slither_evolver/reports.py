"""Recalculable local reports from declared evidence, including partial runs.

FR-013 / FR-022 / NFR-010: one data model drives Markdown, JSON, and CSV.
No source is executed. Provenance is declared, not authenticated. Export
checks cover known secret patterns, not every secret or personal detail.
"""

from dataclasses import asdict
import csv
from fractions import Fraction
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from slither_evolver.config import ConfigError, RunConfig, load_config, validate_config
from slither_evolver.scoring import (
    IncompleteEvidence, ScoringError, MAX_RESULTS_BYTES, configuration_hash, load_results,
    score_results, validate_results,
)


REPORT_SCHEMA_VERSION = 1
MAX_EXPORT_FILE_BYTES = 64 * 1024 * 1024
PHASES = ("optimization", "holdout")
SECRET_PATTERN = re.compile(
    r"SYNTHETIC_SECRET_DO_NOT_EXPORT|"
    r"(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})|"
    r"Bearer\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"(?:api[_ -]?key|access[_ -]?token|api[_ -]?token|password|secret|authorization)"
    r"['\"]?\s*[:=]\s*['\"]?[^\s,'\";]{4,}|"
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)
FORBIDDEN_FIELDS = {
    "api_key", "apikey", "api_token", "access_token", "authorization", "password",
    "secret", "credentials", "email", "student_email", "participant_email",
    "student_name", "participant_name",
}


class ReportError(ValueError):
    """Invalid, unsafe, incompatible, damaged, or inaccessible report evidence."""


def _json_bytes(value):
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                           allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ReportError("report: expected finite UTF-8 JSON data") from None


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _identifier(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ReportError("report: expected a 1–64-character ASCII prompt identifier")
    return value


def _safe_export(value, depth=0):
    if depth > 128:
        raise ReportError("report: input nesting is too deep")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ReportError("report: expected string JSON keys")
            if key.lower().replace("-", "_") in FORBIDDEN_FIELDS:
                raise ReportError("report: known credential/personal-data field; sanitize inputs before export")
            _safe_export(key, depth + 1)
            _safe_export(item, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _safe_export(item, depth + 1)
    elif isinstance(value, str) and SECRET_PATTERN.search(value):
        raise ReportError("report: known secret marker or email address; sanitize inputs before export")


def _counts(records, scheduled):
    played = [r for r in records if r.status in ("played", "bot_fault")]
    return {
        "scheduled_slots": scheduled, "recorded_slots": len(records),
        "missing_slots": scheduled - len(records), "played_matches": len(played),
        "wins": sum(r.outcome == "win" for r in played),
        "losses": sum(r.outcome == "loss" for r in played),
        "draws": sum(r.outcome == "draw" for r in played),
        "bot_faults": sum(r.status == "bot_fault" for r in records),
        "synthetic_failures": sum(r.status == "invalid_generation" for r in records),
        "infrastructure_faults": sum(r.status == "infrastructure_fault" for r in records),
        "interrupted_slots": sum(r.status == "interrupted" for r in records),
    }


def _entry(config, document, evidence, role):
    seeds = config.optimization_seeds if evidence.phase == "optimization" else config.holdout_seeds
    per_opponent = config.samples_per_prompt * len(seeds)
    counts = _counts(evidence.results, per_opponent * len(config.opponents))
    blockers = dict(missing_samples=config.samples_per_prompt - len(evidence.samples),
                    missing_slots=counts["missing_slots"],
                    blocked_samples=sum(s.generation_status == "blocked" for s in evidence.samples),
                    infrastructure_faults=counts["infrastructure_faults"],
                    interrupted_slots=counts["interrupted_slots"])
    try:
        fitness = score_results(config, document).to_dict()
        status = "complete"
    except IncompleteEvidence:
        fitness = None
        status = "partial"
    entry = {
        "role": role, "prompt_id": evidence.prompt_id, "prompt_hash": evidence.prompt_hash,
        "phase": evidence.phase, "status": status, "provenance": asdict(evidence.provenance),
        "counts": counts, "blockers": blockers, "score": fitness,
        "declared_samples": len(evidence.samples),
        "accepted_samples": sum(s.generation_status == "accepted" for s in evidence.samples),
        "invalid_samples": sum(s.generation_status == "invalid" for s in evidence.samples),
        "opponents": [], "samples": [],
    }
    for opponent in config.opponents:
        records = [r for r in evidence.results if r.opponent_id == opponent.id]
        entry["opponents"].append({
            "opponent_id": opponent.id, "source_hash": opponent.source_hash,
            "profile_hash": opponent.profile_hash, "counts": _counts(records, per_opponent),
        })
    per_sample = len(config.opponents) * len(seeds)
    for sample in sorted(evidence.samples, key=lambda s: s.sample_index):
        records = [r for r in evidence.results if r.sample_id == sample.sample_id]
        entry["samples"].append({**asdict(sample), "counts": _counts(records, per_sample)})
    return entry


def build_report(config: RunConfig, bundles, *, baseline_id, selected_id):
    """Return a detached report model; partial evidence has null final scores.

    Inputs are one or more baseline/selected optimization/holdout snapshots.
    All share a frozen configuration and provenance kind. Missing roles or
    phases are retained as explicit missing evidence, not fabricated records.
    """
    if not isinstance(config, RunConfig):
        raise ReportError("config: expected a validated RunConfig")
    try:
        config = validate_config(config.to_dict())
    except ConfigError:
        raise ReportError("config: invalid experiment configuration") from None
    baseline_id, selected_id = _identifier(baseline_id), _identifier(selected_id)
    if not isinstance(bundles, (list, tuple)) or not 1 <= len(bundles) <= 4:
        raise ReportError("report: supply one through four baseline/selected phase bundles")
    snapshot = config.to_dict()
    _safe_export([snapshot, bundles, baseline_id, selected_id])
    identities = {}
    entries = {}
    inputs = []
    kinds = set()
    for document in bundles:
        try:
            evidence = validate_results(config, document)
        except ScoringError as error:
            raise ReportError(f"results: {error}") from None
        if evidence.prompt_id not in (baseline_id, selected_id):
            raise ReportError("report: bundle is not a requested baseline/selected prompt")
        key = (evidence.phase, evidence.prompt_id)
        if key in entries:
            raise ReportError("report: duplicate prompt/phase bundle")
        if evidence.prompt_id in identities and identities[evidence.prompt_id] != evidence.prompt_hash:
            raise ReportError("report: prompt hash changes between phases")
        identities[evidence.prompt_id] = evidence.prompt_hash
        if evidence.prompt_id == baseline_id and evidence.prompt_hash != config.fixed_context.baseline_prompt_hash:
            raise ReportError("baseline: does not match the configured frozen baseline hash")
        kinds.add(evidence.provenance.kind)
        role = "baseline_and_selected" if baseline_id == selected_id else (
            "baseline" if evidence.prompt_id == baseline_id else "selected")
        entries[key] = _entry(config, document, evidence, role)
        name = f"evidence/{evidence.phase}-{evidence.prompt_id}.results.json"
        inputs.append({"file": name, "sha256": _hash(_json_bytes(document)),
                       "prompt_id": evidence.prompt_id, "phase": evidence.phase})
    if len(kinds) != 1:
        raise ReportError("report: do not compare synthetic, manual, and automated provenance together")
    missing = []
    comparisons = []
    order = []
    roles = (baseline_id,) if baseline_id == selected_id else (baseline_id, selected_id)
    for phase in PHASES:
        for identity in roles:
            if (phase, identity) not in entries:
                missing.append({"phase": phase, "prompt_id": identity})
            else:
                order.append(entries[(phase, identity)])
        baseline, selected = entries.get((phase, baseline_id)), entries.get((phase, selected_id))
        delta = None
        if baseline and selected and baseline["score"] is not None and selected["score"] is not None:
            delta = Fraction(selected["score"]["fitness_fraction"]) - Fraction(baseline["score"]["fitness_fraction"])
        comparisons.append({
            "phase": phase, "status": "complete" if delta is not None else "unavailable",
            "fitness_delta": None if delta is None else float(delta),
            "fitness_delta_fraction": None if delta is None else f"{delta.numerator}/{delta.denominator}",
            "shared_prompt_identity": baseline_id == selected_id,
        })
    kind = next(iter(kinds))
    complete = not missing and all(e["status"] == "complete" for e in order)
    limitations = [
        "Completion means the declared coordinate schedules are complete; it is not system acceptance.",
        "Provenance, accepted generation, and outcomes are declarations; no source or game is executed by this exporter.",
        "Independent model sampling, selection freeze, fresh holdout generation, and trusted runner outcomes are not established here.",
        "Shared source samples/seeds and small workloads limit statistical interpretation; no confidence intervals or significance claims are made.",
        "Provider usage/cost, elapsed time, lineage search, and parity/isolation evidence are unavailable in this result schema.",
        "Raw text still needs human review; automated export checks cover known patterns only.",
    ]
    if kind == "synthetic":
        limitations.insert(0, "SYNTHETIC: these are arithmetic fixtures, not actual played games or experiment findings.")
    same_strategy = identities.get(baseline_id) == identities.get(selected_id) if (
        baseline_id in identities and selected_id in identities) else None
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION, "run_id": config.run_id,
        "configuration_hash": configuration_hash(config), "scoring_version": config.scoring.version,
        "provenance_kind": kind, "status": "complete" if complete else "partial",
        "baseline_id": baseline_id, "selected_id": selected_id, "same_strategy_hash": same_strategy,
        "inputs": sorted(inputs, key=lambda item: item["file"]), "missing_evidence": missing,
        "entries": order, "comparisons": comparisons, "limitations": limitations,
    }


def _md(value):
    text = html.escape(str(value), quote=False).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return re.sub(r"([\\`*_\[\]()!#|>~])", r"\\\1", text)


def _number(value):
    return "Not available" if value is None else str(value)


def _markdown(report):
    lines = ["# Slither Sam Experiment Report", "", f"**Provenance:** {_md(report['provenance_kind']).upper()}",
             f"**Status:** {_md(report['status'])} declared evidence", "",
             f"Run: {_md(report['run_id'])}", f"Configuration SHA-256: {report['configuration_hash']}",
             f"Baseline: {_md(report['baseline_id'])}; selected: {_md(report['selected_id'])}", ""]
    if report["provenance_kind"] == "synthetic":
        lines += ["**SYNTHETIC FIXTURE — no actual games or experiment findings.**", ""]
    lines += ["## Baseline Comparison", "", "Deltas are selected minus baseline within each declared phase.", "",
              "| Phase | Comparison | Fitness delta | Exact delta |", "| --- | --- | --- | --- |"]
    for row in report["comparisons"]:
        lines.append(f"| {row['phase']} | {row['status']} | {_number(row['fitness_delta'])} | {_number(row['fitness_delta_fraction'])} |")
    if report["same_strategy_hash"]:
        lines += ["", "Baseline and selected declarations identify the same strategy text hash."]
    if report["baseline_id"] == report["selected_id"]:
        lines += ["", "The shared prompt is counted once per phase; the comparison does not imply independent groups."]
    lines += ["", "## Prompt and Phase Results", "",
              "Counts are outcome categories in the supplied evidence. Synthetic failures are never played matches.", "",
              "| Phase | Role | Prompt | Status | Scheduled | Recorded | Played category | Wins | Losses | Draws | Synthetic failures | Fitness |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for entry in report["entries"]:
        c, score = entry["counts"], entry["score"]
        values = [entry["phase"], entry["role"], entry["prompt_id"], entry["status"], c["scheduled_slots"],
                  c["recorded_slots"], c["played_matches"], c["wins"], c["losses"], c["draws"],
                  c["synthetic_failures"], "Not available" if score is None else score["fitness_fraction"]]
        lines.append("| " + " | ".join(_md(value) for value in values) + " |")
    for entry in report["entries"]:
        lines += ["", f"### {_md(entry['phase'])}: {_md(entry['prompt_id'])}", "",
                  f"Provenance note: {_md(entry['provenance']['description'])}",
                  f"Declared samples: {entry['declared_samples']}; accepted: {entry['accepted_samples']}; invalid: {entry['invalid_samples']}.",
                  "Blockers: " + "; ".join(f"{key.replace('_', ' ')} = {value}" for key, value in entry["blockers"].items()) + ".", "",
                  "| Opponent | Scheduled | Recorded | Wins | Played category | Synthetic failures | Effective rate |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        scores = {} if entry["score"] is None else {o["opponent_id"]: o for o in entry["score"]["opponents"]}
        for opponent in entry["opponents"]:
            c = opponent["counts"]
            rate = scores.get(opponent["opponent_id"], {}).get("effective_win_rate_fraction")
            values = [opponent["opponent_id"], c["scheduled_slots"], c["recorded_slots"], c["wins"],
                      c["played_matches"], c["synthetic_failures"], _number(rate)]
            lines.append("| " + " | ".join(_md(value) for value in values) + " |")
        lines += ["", "| Sample | Index | Generation declaration | Scheduled | Recorded | Wins | Missing slots |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for sample in entry["samples"]:
            c = sample["counts"]
            values = [sample["sample_id"], sample["sample_index"], sample["generation_status"],
                      c["scheduled_slots"], c["recorded_slots"], c["wins"], c["missing_slots"]]
            lines.append("| " + " | ".join(_md(value) for value in values) + " |")
    lines += ["", "## Missing Evidence", ""]
    if report["missing_evidence"]:
        lines += [f"* {_md(item['phase'])}: {_md(item['prompt_id'])}" for item in report["missing_evidence"]]
    else:
        lines.append("No requested prompt/phase bundle is missing. See blockers above for incomplete slots.")
    lines += ["", "## Limits and Interpretation", ""]
    lines += ["* " + _md(value) for value in report["limitations"]]
    lines += ["", "## Recalculation", "",
              "The export includes normalized config.json, canonical evidence snapshots, exact score ratios, and file hashes.",
              "Use the verify-report command to check files and rebuild every derived format. Hashes are integrity checks, not signatures."]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _csv(fields, rows, *, untrusted=()):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        row = dict(row)
        for field in untrusted:
            value = row.get(field)
            if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@"))
                                           or value.startswith(("\t", "\r", "\n"))):
                row[field] = "'" + value
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _files(config, bundles, report):
    files = {"config.json": _json_bytes(config.to_dict()), "report.json": _json_bytes(report),
             "report.md": _markdown(report)}
    summary, opponents, slots = [], [], []
    for entry in report["entries"]:
        common = {"run_id": report["run_id"], "provenance": report["provenance_kind"],
                  "phase": entry["phase"], "role": entry["role"], "prompt_id": entry["prompt_id"],
                  "prompt_hash": entry["prompt_hash"], "status": entry["status"]}
        score = entry["score"]
        summary.append({**common, **entry["counts"], "accepted_samples": entry["accepted_samples"],
                        "invalid_samples": entry["invalid_samples"],
                        "fitness": None if score is None else score["fitness"],
                        "fitness_fraction": None if score is None else score["fitness_fraction"]})
        scores = {} if score is None else {o["opponent_id"]: o for o in score["opponents"]}
        for opponent in entry["opponents"]:
            values = scores.get(opponent["opponent_id"], {})
            opponents.append({**common, "opponent_id": opponent["opponent_id"],
                              "source_hash": opponent["source_hash"], "profile_hash": opponent["profile_hash"],
                              **opponent["counts"], "effective_win_rate": values.get("effective_win_rate"),
                              "effective_win_rate_fraction": values.get("effective_win_rate_fraction")})
    for document in bundles:
        evidence = validate_results(config, document)
        name = f"evidence/{evidence.phase}-{evidence.prompt_id}.results.json"
        files[name] = _json_bytes(document)
        samples = {sample.sample_id: sample for sample in evidence.samples}
        for record in evidence.results:
            sample = samples[record.sample_id]
            slots.append({"run_id": report["run_id"], "provenance": report["provenance_kind"],
                          "configuration_hash": report["configuration_hash"], "phase": evidence.phase,
                          "prompt_id": evidence.prompt_id, "prompt_hash": evidence.prompt_hash,
                          "sample_index": sample.sample_index, "sample_source_hash": sample.source_hash,
                          **asdict(record)})
    count_fields = list(report["entries"][0]["counts"])
    common_fields = ["run_id", "provenance", "phase", "role", "prompt_id", "prompt_hash", "status"]
    files["summary.csv"] = _csv(common_fields + count_fields + ["accepted_samples", "invalid_samples", "fitness", "fitness_fraction"], summary)
    files["opponents.csv"] = _csv(common_fields + ["opponent_id", "source_hash", "profile_hash"] + count_fields +
                                  ["effective_win_rate", "effective_win_rate_fraction"], opponents)
    slot_fields = ["run_id", "provenance", "configuration_hash", "phase", "prompt_id", "prompt_hash",
                   "sample_index", "sample_source_hash", "slot_id", "sample_id", "opponent_id",
                   "opponent_source_hash", "profile_hash", "seed", "status", "outcome", "cause", "reason"]
    slots.sort(key=lambda row: (row["phase"], row["prompt_id"], row["sample_index"], row["opponent_id"], row["seed"]))
    files["slots.csv"] = _csv(slot_fields, slots, untrusted=("reason",))
    files["comparisons.csv"] = _csv(
        ["run_id", "provenance", "baseline_id", "selected_id", "phase", "status",
         "fitness_delta", "fitness_delta_fraction", "shared_prompt_identity"],
        [{"run_id": report["run_id"], "provenance": report["provenance_kind"],
          "baseline_id": report["baseline_id"], "selected_id": report["selected_id"], **row}
         for row in report["comparisons"]])
    if any(name.endswith(".json") and len(data) > MAX_RESULTS_BYTES for name, data in files.items()):
        raise ReportError("report: JSON output exceeds the 16 MiB reload limit")
    if any(len(data) > MAX_EXPORT_FILE_BYTES for data in files.values()):
        raise ReportError("report: output file exceeds the 64 MiB supported limit")
    manifest = "".join(_hash(data) + "  " + name + "\n" for name, data in sorted(files.items()))
    files["files.sha256"] = manifest.encode("utf-8")
    return files


def export_report(output, config, bundles, *, baseline_id, selected_id):
    """Publish a new directory containing consistent formats and evidence."""
    report = build_report(config, bundles, baseline_id=baseline_id, selected_id=selected_id)
    # Normalize again so programmatically constructed numeric fields use the
    # same representation as the report's validated configuration hash.
    config = validate_config(config.to_dict())
    files = _files(config, bundles, report)
    output = Path(output)
    stage = None
    locked = False
    lock = output.parent / ("." + output.name + ".report-lock")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() or output.is_symlink():
            raise ReportError("output: already exists; choose a new report version directory")
        try:
            lock.mkdir()
        except FileExistsError:
            raise ReportError("output: report lock exists; inspect active/interrupted export before retrying") from None
        locked = True
        if output.exists() or output.is_symlink():
            raise ReportError("output: already exists; choose a new report version directory")
        stage = Path(tempfile.mkdtemp(dir=output.parent, prefix=".report-pending-"))
        for name, data in files.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        os.rename(stage, output)
        stage = None
    except OSError:
        raise ReportError("report: filesystem operation failed; check permissions and free space") from None
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        if locked:
            lock.rmdir()
    return {"path": str(output), "status": report["status"], "provenance": report["provenance_kind"]}


def _read_file(root, name):
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise ReportError("report: expected an ordinary export file; links are not supported")
    if name.startswith("evidence/") and ((root / "evidence").is_symlink() or not (root / "evidence").is_dir()):
        raise ReportError("report: evidence directory must be an ordinary directory")
    with path.open("rb") as stream:
        data = stream.read(MAX_EXPORT_FILE_BYTES + 1)
    if len(data) > MAX_EXPORT_FILE_BYTES:
        raise ReportError("report: file exceeds supported size")
    return data


def verify_report(output):
    """Check file hashes and rebuild all formats from archived evidence.

    Hashes detect damage, not a malicious replacement of the whole archive.
    A consistently recomputed partial archive remains a partial report.
    """
    root = Path(output)
    try:
        if root.is_symlink() or not root.is_dir():
            raise ReportError("report: expected an ordinary export directory")
        receipt = _read_file(root, "files.sha256").decode("utf-8")
        if len(receipt) > 8192:
            raise ReportError("report: oversized file manifest")
        expected = {}
        allowed = {"config.json", "report.json", "report.md", "summary.csv", "opponents.csv", "slots.csv", "comparisons.csv"}
        for line in receipt.splitlines():
            if not re.fullmatch(r"[0-9a-f]{64}  [^\s]+", line):
                raise ReportError("report: malformed file manifest")
            digest, name = line.split("  ", 1)
            if name not in allowed and not re.fullmatch(r"evidence/(optimization|holdout)-[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.results\.json", name):
                raise ReportError("report: unsupported file manifest path")
            if name in expected:
                raise ReportError("report: duplicate file manifest path")
            expected[name] = digest
            if _hash(_read_file(root, name)) != digest:
                raise ReportError("report: file hash mismatch")
        actual_paths = set()
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ReportError("report: links are not supported")
            if path.is_file():
                actual_paths.add(path.relative_to(root).as_posix())
            elif path.relative_to(root).as_posix() != "evidence":
                raise ReportError("report: unexpected export directory")
        if actual_paths != set(expected) | {"files.sha256"} or not allowed <= set(expected):
            raise ReportError("report: missing or unexpected export files")
        config = load_config(root / "config.json")
        saved = load_results(root / "report.json")
        inputs = saved.get("inputs")
        if type(inputs) is not list or not 1 <= len(inputs) <= 4:
            raise ReportError("report: missing or invalid input inventory")
        bundles = []
        for item in inputs:
            if type(item) is not dict or type(item.get("file")) is not str or item["file"] not in expected or not item["file"].startswith("evidence/"):
                raise ReportError("report: invalid evidence reference")
            bundles.append(load_results(root / item["file"]))
        rebuilt = build_report(config, bundles, baseline_id=saved.get("baseline_id"), selected_id=saved.get("selected_id"))
        if saved != rebuilt:
            raise ReportError("report: derived values disagree with archived evidence")
        files = _files(config, bundles, rebuilt)
        if set(files) != actual_paths or any(_read_file(root, name) != data for name, data in files.items()):
            raise ReportError("report: formats disagree with recalculated evidence")
        return {"run_id": rebuilt["run_id"], "status": rebuilt["status"], "provenance": rebuilt["provenance_kind"]}
    except (OSError, UnicodeError):
        raise ReportError("report: cannot read valid UTF-8 export files") from None
    except (ConfigError, ScoringError) as error:
        raise ReportError(f"report: invalid archived evidence: {error}") from None
