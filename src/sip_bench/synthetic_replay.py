"""Versioned, offline synthetic diagnosis artifacts with patient-isolated replay.

This exercises ingestion and replay contracts; fixture label matches are not
evidence of clinical quality. The source declaration is an operator attestation,
not an automated PHI detector.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
from typing import Any, Mapping

from sip_bench.adapters import medical
from sip_bench.adapters.medical import MedicalAdapter
from sip_bench.adapters.base import TaskDescriptor
from sip_bench import medical_runtime
from sip_bench.medical_runtime import RuleMemory, observations


SCHEMA_VERSION = 1
BRIDGE_VERSION = "synthetic-replay-v1"
SPLITS = ("adapt", "replay", "heldout", "drift")
ARTIFACTS = ("manifest.json", "memoryeval.json", "replay.jsonl")
FORMATS = ("compact-json", "compact-jsonl", "fhir-r4")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       indent=2) + "\n").encode("utf-8")


def _query(features: Any) -> str:
    return json.dumps(features, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))


def _implementation() -> dict[str, Any]:
    return {
        "bridge_version": BRIDGE_VERSION,
        "benchmark_version": MedicalAdapter.benchmark_version,
        "python_version": platform.python_version(),
        "code_sha256": {
            "synthetic_replay.py": _sha256(Path(__file__).read_bytes()),
            "medical.py": _sha256(Path(medical.__file__).read_bytes()),
            "medical_runtime.py": _sha256(Path(medical_runtime.__file__).read_bytes()),
        },
    }


def _source_snapshot(source: Path, attestation: Path) -> tuple[bytes, dict[str, Any]]:
    raw = source.read_bytes()
    declaration = json.loads(attestation.read_text(encoding="utf-8"))
    if (
        not isinstance(declaration, dict)
        or type(declaration.get("schema_version")) is not int
        or declaration["schema_version"] != SCHEMA_VERSION
    ):
        raise ValueError("Source declaration requires schema_version=1")
    if declaration.get("synthetic") is not True:
        raise ValueError("Source declaration must explicitly attest synthetic=true")
    metadata = declaration.get("source")
    if not isinstance(metadata, dict):
        raise ValueError("Source declaration requires a source object")
    for key in ("generator", "version", "sha256"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"Source declaration requires a nonempty {key}")
    if metadata.get("format") not in FORMATS:
        raise ValueError(f"Source format must be one of {FORMATS}")
    if type(metadata.get("seed")) is not int:
        raise ValueError("Source declaration seed must be an integer")
    if _sha256(raw) != metadata["sha256"]:
        raise ValueError("Source SHA-256 does not match the attested bytes")
    return raw, {key: metadata[key] for key in ("sha256", "format", "generator", "version", "seed")}


def _tasks(raw: bytes, source_format: str) -> list[TaskDescriptor]:
    text = raw.decode("utf-8")
    if source_format == "compact-jsonl":
        payload = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
    is_bundle = isinstance(payload, dict) and payload.get("resourceType") == "Bundle"
    if (source_format == "fhir-r4") != is_bundle:
        raise ValueError("Attested source format differs from its task payload")
    if is_bundle:
        # Relative references and Bundle fullUrl aliases identify the same patient.
        # Require Patient entries so grouping cannot silently treat aliases as new patients.
        aliases: dict[str, str] = {}
        patients: set[str] = set()
        for entry in payload.get("entry", []):
            if not isinstance(entry, dict) or not isinstance(entry.get("resource"), dict):
                raise ValueError("FHIR Bundle entries require resource objects")
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Patient" or not resource.get("id"):
                continue
            patient = f"Patient/{resource['id']}"
            if patient in patients:
                # Different fullUrls can have the same server-local id. This
                # compact contract cannot safely resolve their relative aliases.
                raise ValueError(f"Duplicate FHIR Patient id: {resource['id']}")
            patients.add(patient)
            for alias in (patient, entry.get("fullUrl")):
                if alias:
                    if alias in aliases and aliases[alias] != patient:
                        raise ValueError("FHIR Patient alias identifies multiple patients")
                    aliases[alias] = patient
        for entry in payload["entry"]:
            resource = entry["resource"]
            if resource.get("resourceType") in {"Encounter", "Condition"}:
                subject = resource.get("subject") or {}
                reference = subject.get("reference")
                if reference is not None:
                    patient = aliases.get(reference)
                    if patient is None:
                        raise ValueError("FHIR patient_id must resolve to a Bundle Patient entry")
                    subject["reference"] = patient
                elif resource.get("resourceType") == "Encounter":
                    raise ValueError("FHIR Encounter requires patient_id")
        text = _query(payload)
    tasks = MedicalAdapter().discover_tasks_from_text(text)
    seen = set()
    for task in tasks:
        if task.task_id in seen:
            raise ValueError(f"Duplicate task_id: {task.task_id}")
        seen.add(task.task_id)
        patient = task.metadata.get("patient_id")
        if not isinstance(patient, str) or not patient.strip() or patient != patient.strip():
            raise ValueError(f"Task {task.task_id} requires a nonempty, whitespace-trimmed patient_id")
    return tasks


def _partition(tasks: list[TaskDescriptor], patient_counts: Mapping[str, int], seed: int) -> dict[str, list[TaskDescriptor]]:
    if type(seed) is not int:
        raise ValueError("Partition seed must be an integer")
    if (
        set(patient_counts) != set(SPLITS)
        or any(type(count) is not int or count < 0 for count in patient_counts.values())
    ):
        raise ValueError("Patient counts require all four splits with nonnegative integers")
    if patient_counts["adapt"] < 1 or sum(patient_counts[split] for split in SPLITS[1:]) < 1:
        raise ValueError("Request at least one training and one evaluation patient")
    patients = {task.metadata["patient_id"] for task in tasks}
    if sum(patient_counts.values()) != len(patients):
        raise ValueError(f"Patient counts must cover all {len(patients)} source patients exactly")
    ranked = sorted(patients, key=lambda patient: (_sha256(_query([seed, patient]).encode("utf-8")), patient))
    result = {}
    start = 0
    for split in SPLITS:
        end = start + patient_counts[split]
        assigned = set(ranked[start:end])
        result[split] = sorted((task for task in tasks if task.metadata["patient_id"] in assigned), key=lambda task: task.task_id)
        start = end
    return result


def build_artifacts(
    source_path: str | Path,
    source_manifest_path: str | Path,
    *,
    patient_counts: Mapping[str, int],
    seed: int = 7,
) -> dict[str, bytes]:
    """Validate frozen source bytes and build deterministic, path-free artifacts."""
    raw, source = _source_snapshot(Path(source_path), Path(source_manifest_path))
    splits = _partition(_tasks(raw, source["format"]), patient_counts, seed)
    patient_splits = {split: sorted({task.metadata["patient_id"] for task in tasks}) for split, tasks in splits.items()}
    execution = {"kind": "offline-rule-replay", "model_calls": 0, "provider_calls": 0,
                 "token_usage": None, "cost_usd": None, "measurement": "not_applicable_offline"}
    common = {"schema_version": SCHEMA_VERSION, "synthetic": True, "source": source,
              "implementation": _implementation()}
    envelope = {**common,
                "partitions": {"train": patient_splits["adapt"],
                               "evaluation": sorted(patient for split in SPLITS[1:] for patient in patient_splits[split])},
                "tasks": []}
    for split, tasks in splits.items():
        for task in tasks:
            clinical = task.metadata["clinical"]
            envelope["tasks"].append({
                "task_id": task.task_id, "source_task_id": task.task_id,
                "patient_id": task.metadata["patient_id"], "split": split,
                "query": _query(observations(clinical)),
                "trajectory": clinical["diagnosis"], "reward": 1.0,
                "metadata": {"expected_answer": clinical["diagnosis"], "reward_origin": "fixture_target",
                             "case_sha256": MedicalAdapter.provenance({"task_id": task.task_id,
                                                                       "patient_id": task.metadata["patient_id"],
                                                                       **clinical})["case_sha256"]},
            })
    records = []
    training_ids = [task.task_id for task in splits["adapt"]]
    for phase in ("T0", "T1", "T2"):
        memory = RuleMemory()
        if phase != "T0":
            for task in splits["adapt"]:
                clinical = task.metadata["clinical"]
                memory.adapt(observations(clinical), clinical["diagnosis"])
        for split, tasks in splits.items():
            for task in tasks:
                clinical = task.metadata["clinical"]
                prediction = memory.predict(observations(clinical))
                safe, reason = MedicalAdapter.safety_gate(clinical, prediction)
                records.append({
                    "task_id": task.task_id, "source_task_id": task.task_id,
                    "patient_id": task.metadata["patient_id"], "phase": phase, "split": split,
                    "prediction": prediction, "fixture_label_match": prediction == clinical["diagnosis"],
                    "safety_gate_passed": safe, "safety_failure": reason,
                    "training_task_ids": [] if phase == "T0" else training_ids,
                })
    replay = b"".join((_query(record) + "\n").encode("utf-8") for record in records)
    outputs = {"memoryeval.json": _json_bytes(envelope), "replay.jsonl": replay}
    manifest = {**common, "partition_algorithm": "sha256-seed-patient-v1", "partition_seed": seed,
                "patient_counts": dict(patient_counts), "patient_splits": patient_splits,
                "splits": {split: [task.task_id for task in tasks] for split, tasks in splits.items()},
                "execution": execution, "replay_records": len(records),
                "artifact_sha256": {name: _sha256(data) for name, data in outputs.items()}}
    return {"manifest.json": _json_bytes(manifest), **outputs}


def write_replay(artifacts: Mapping[str, bytes], out_root: str | Path) -> None:
    """Write only the fixed bridge inventory after all source validation succeeds."""
    if set(artifacts) != set(ARTIFACTS):
        raise ValueError("Replay requires the fixed artifact inventory")
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACTS:
        (root / name).write_bytes(artifacts[name])


def verify_replay(out_root: str | Path, source_path: str | Path, source_manifest_path: str | Path) -> dict[str, Any]:
    """Regenerate from the attested source and compare every persisted artifact byte."""
    root = Path(out_root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    expected = build_artifacts(source_path, source_manifest_path,
                               patient_counts=manifest["patient_counts"], seed=manifest["partition_seed"])
    for name in ARTIFACTS:
        if (root / name).read_bytes() != expected[name]:
            raise ValueError(f"Replay differs from current source/implementation: {name}")
    return {"verified": True, "source_sha256": manifest["source"]["sha256"],
            "artifact_sha256": {name: _sha256(data) for name, data in expected.items()},
            "replay_records": manifest["replay_records"], "model_calls": 0}
