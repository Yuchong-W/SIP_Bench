"""Synthetic Synthea-compatible medical continual-learning adapter."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping
from .base import BenchmarkAdapter, TaskDescriptor


class MedicalAdapter(BenchmarkAdapter):
    benchmark_name = "medical-synthea"
    benchmark_version = "synthetic-v1"
    red_flags = frozenset({"chest_pain", "stroke_signs", "severe_bleeding"})

    def discover_tasks(self, source: str | Path) -> list[TaskDescriptor]:
        source_path = Path(source)
        text = source_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = [json.loads(line) for line in text.splitlines() if line.strip()]
        if isinstance(payload, dict) and payload.get("resourceType") == "Bundle":
            rows = _bundle_to_cases(payload)
            if not rows:
                raise ValueError(
                    "FHIR Bundle has no labeled Encounter/Condition pairs; "
                    "timeline event prediction is a different task contract"
                )
        else:
            rows = payload.get("cases", payload) if isinstance(payload, dict) else payload
            if isinstance(rows, dict) and ("diagnosis" in rows or "answer" in rows or "task_id" in rows):
                rows = [rows]
        if not isinstance(rows, list):
            raise ValueError("Medical fixture must be a list or {cases: [...]}")
        out: list[TaskDescriptor] = []
        for row in rows:
            case = self.normalize_case(row)
            tid = case["encounter_id"]
            clinical = {"symptoms": case["symptoms"], "vitals": case["vitals"], "diagnosis": case["diagnosis"]}
            out.append(TaskDescriptor(self.benchmark_name, tid, str(source),
                str(case.get("title", "Clinical case")), case.get("category", "triage"),
                case.get("difficulty", "synthetic"), {"patient_id": case.get("patient_id"), "case_id": case.get("case_id"), "clinical": clinical}))
        return out

    @classmethod
    def normalize_case(cls, case: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(case, Mapping):
            raise ValueError("Each medical case must be an object")
        if (
            case.get("schema") == "navilia.v1"
            and case.get("benchmark") == "SIP-Bench"
            and ("input_event_ids" in case or "evidence" in case)
        ):
            raise ValueError(
                "Navilia SIP timeline event prediction is a different task contract; "
                "do not map its answer to a diagnosis"
            )
        encounter = str(case.get("task_id") or case.get("encounter_id") or case.get("case_id") or case.get("id") or "")
        diagnosis = str(case.get("diagnosis") or case.get("answer") or "")
        if not encounter or not diagnosis:
            raise ValueError("Medical case requires encounter_id/task_id and diagnosis")
        symptoms = case.get("symptoms", [])
        if not symptoms and isinstance(case.get("timeline"), list):
            symptoms = [str(e.get("type")) for e in case["timeline"] if e.get("type")]
        if not isinstance(symptoms, list):
            raise ValueError("Medical case symptoms must be a list")
        return {**dict(case), "encounter_id": encounter, "diagnosis": diagnosis,
                "symptoms": [str(s) for s in symptoms], "vitals": dict(case.get("vitals") or {})}

    @classmethod
    def safety_gate(cls, case: Mapping[str, Any], prediction: str) -> tuple[bool, str | None]:
        symptoms = set(case.get("symptoms", []))
        if symptoms & cls.red_flags and prediction not in {"emergency", "urgent"}:
            return False, "red_flag_under-triage"
        return True, None

    @classmethod
    def evidence_coverage(cls, case: Mapping[str, Any], evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Return auditable coverage of symptoms/vitals used by a reasoning trace."""
        case = cls.normalize_case(case); evidence = evidence or {}
        text = " ".join(str(evidence.get(k, "")) for k in ("reasoning", "evidence", "rationale")).lower()
        symptoms = case["symptoms"]
        covered = [s for s in symptoms if s.lower().replace("_", " ") in text or s.lower() in text]
        vitals = case["vitals"]
        vital_keys = [k for k in vitals if str(k).lower().replace("_", " ") in text]
        total = len(symptoms) + len(vitals)
        return {"covered": len(covered) + len(vital_keys), "available": total,
                "coverage_rate": (len(covered) + len(vital_keys)) / total if total else 1.0,
                "symptoms_covered": covered, "vitals_covered": vital_keys}

    @classmethod
    def attribute_feedback(cls, *, prediction: str, diagnosis: str, feedback: str | Mapping[str, Any], safety_gate_passed: bool = True) -> dict[str, Any]:
        text = feedback if isinstance(feedback, str) else json.dumps(feedback, sort_keys=True)
        low = text.lower(); correct = prediction == diagnosis
        if not safety_gate_passed or any(x in low for x in ("unsafe", "under-triage", "red flag")):
            category = "safety"
        elif not correct or any(x in low for x in ("wrong", "incorrect", "missed", "disagree", "not correct")):
            category = "diagnosis_error"
        elif correct and any(x in low for x in ("good", "correct", "agree")):
            category = "affirmation"
        else:
            category = "clinical_reasoning"
        return {"category": category, "prediction": prediction, "diagnosis": diagnosis, "correct": correct, "feedback": text}

    @classmethod
    def trajectory(cls, case: Mapping[str, Any], *, prediction: str, phase: str, split: str,
                   evidence: Mapping[str, Any] | None = None, feedback: str | Mapping[str, Any] | None = None,
                   provenance: Mapping[str, Any] | None = None) -> dict[str, Any]:
        case = cls.normalize_case(case); safe, reason = cls.safety_gate(case, prediction)
        success = prediction == case["diagnosis"] and safe
        row = {"phase": phase, "benchmark_split": split, "task_id": case["encounter_id"],
               "patient_id": case.get("patient_id"), "prediction": prediction, "diagnosis": case["diagnosis"],
               "success": success, "safety_gate_passed": safe, "failure_reason": reason or (None if success else "wrong_or_unknown"),
               "evidence_coverage": cls.evidence_coverage(case, evidence)}
        if feedback is not None: row["feedback_attribution"] = cls.attribute_feedback(prediction=prediction, diagnosis=case["diagnosis"], feedback=feedback, safety_gate_passed=safe)
        row["provenance"] = cls.provenance(case, provenance)
        return row

    @classmethod
    def provenance(cls, case: Mapping[str, Any], extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        case = cls.normalize_case(case); raw = json.dumps(case, sort_keys=True, separators=(",", ":"))
        result = {"adapter": cls.__name__, "benchmark_name": cls.benchmark_name, "benchmark_version": cls.benchmark_version,
                  "patient_id": case.get("patient_id"), "encounter_id": case["encounter_id"],
                  "case_sha256": hashlib.sha256(raw.encode()).hexdigest()}
        if extra: result["source"] = dict(extra)
        return result


def normalize_query(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE)


def utility_aware_retrieve(cases: list[Mapping[str, Any]], query: str, *, k: int = 5,
                           utility: Mapping[str, float] | None = None) -> list[Mapping[str, Any]]:
    q = normalize_query(query)
    if not q:
        return []
    utility = utility or {}; ranked = []
    for case in cases:
        text = normalize_query(" ".join([str(case.get("diagnosis", "")), *map(str, case.get("symptoms", [])), str(case.get("category", ""))]))
        overlap = sum(c in text for c in set(q)) / max(1, len(set(q)))
        score = overlap * (1 + float(utility.get(str(case.get("diagnosis", "")), 0)))
        if score: ranked.append((score, case))
    ranked.sort(key=lambda x: (-x[0], str(x[1].get("encounter_id", ""))))
    return [c for _, c in ranked[:max(0, k)]]


search_cases = utility_aware_retrieve


def _bundle_to_cases(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries = [e for e in bundle.get("entry", []) if isinstance(e, Mapping) and isinstance(e.get("resource"), Mapping)]
    resources = [e["resource"] for e in entries]
    encounters = [r for r in resources if r.get("resourceType") == "Encounter"]
    conditions = [r for r in resources if r.get("resourceType") == "Condition"]
    out = []
    for enc in encounters:
        eid = str(enc.get("id") or "")
        if not eid:
            raise ValueError("FHIR Encounter requires an id")
        refs = {f"Encounter/{eid}"}
        refs.update(e["fullUrl"] for e in entries if e["resource"] is enc and e.get("fullUrl"))
        patient_ref = (enc.get("subject") or {}).get("reference")
        labels = set()
        for cond in conditions:
            if (cond.get("encounter") or {}).get("reference") not in refs:
                continue
            subject = (cond.get("subject") or {}).get("reference")
            if subject and patient_ref and subject != patient_ref:
                raise ValueError(f"Condition subject differs from Encounter/{eid}")
            coding = ((cond.get("code") or {}).get("coding") or [{}])[0]
            label = coding.get("code") or coding.get("display")
            if label:
                labels.add(str(label))
        if len(labels) > 1:
            raise ValueError(f"Encounter/{eid} has multiple labels; provide an explicit task label")
        if not labels:
            continue
        out.append({"encounter_id": eid, "patient_id": str(patient_ref or ""), "symptoms": [], "vitals": {}, "diagnosis": labels.pop()})
    return out
