import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from sip_bench.synthetic_replay import build_artifacts, verify_replay, write_replay


FIXTURES = Path(__file__).parent / "fixtures" / "synthetic_replay"
COUNTS = {"adapt": 1, "replay": 1, "heldout": 1, "drift": 1}


class SyntheticReplayTests(unittest.TestCase):
    def build(self, source=None, attestation=None, counts=None):
        return build_artifacts(
            source or FIXTURES / "cases.json",
            attestation or FIXTURES / "cases.source.json",
            patient_counts=counts or COUNTS,
            seed=7,
        )

    def write_fixture(self, root, payload, manifest=None):
        source = root / "cases.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        attestation = json.loads((FIXTURES / "cases.source.json").read_text())
        attestation["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        if manifest:
            attestation.update(manifest)
        path = root / "source.json"
        path.write_text(json.dumps(attestation), encoding="utf-8")
        return source, path

    def test_artifact_bytes_and_replay_are_independent_of_output_directory(self):
        expected = self.build()
        with tempfile.TemporaryDirectory() as temp:
            for name in ("first", "second"):
                root = Path(temp) / name
                write_replay(expected, root)
                report = verify_replay(root, FIXTURES / "cases.json", FIXTURES / "cases.source.json")
                self.assertTrue(report["verified"])
                for filename, data in expected.items():
                    self.assertEqual((root / filename).read_bytes(), data)

    def test_whole_patient_groups_and_train_evaluation_ids_are_disjoint(self):
        artifacts = self.build()
        envelope = json.loads(artifacts["memoryeval.json"])
        train = set(envelope["partitions"]["train"])
        evaluation = set(envelope["partitions"]["evaluation"])
        self.assertFalse(train & evaluation)
        self.assertEqual(len(train | evaluation), 4)
        splits = {}
        for task in envelope["tasks"]:
            self.assertEqual(task["source_task_id"], task["task_id"])
            splits.setdefault(task["patient_id"], set()).add(task["split"])
            self.assertNotIn("diagnosis", json.loads(task["query"]))
        self.assertTrue(all(len(value) == 1 for value in splits.values()))
        self.assertEqual(len(envelope["tasks"]), 8)

    def test_heldout_labels_do_not_change_any_prediction(self):
        original = self.build()
        heldout_ids = set(json.loads(original["manifest.json"])["splits"]["heldout"])
        payload = json.loads((FIXTURES / "cases.json").read_text())
        for case in payload["cases"]:
            if case["encounter_id"] in heldout_ids:
                case["diagnosis"] = "changed_fixture_target"
        with tempfile.TemporaryDirectory() as temp:
            source, attestation = self.write_fixture(Path(temp), payload)
            changed = self.build(source, attestation)
        before = [json.loads(line)["prediction"] for line in original["replay.jsonl"].splitlines()]
        after = [json.loads(line)["prediction"] for line in changed["replay.jsonl"].splitlines()]
        self.assertEqual(before, after)

    def test_t0_has_no_training_and_t1_t2_use_only_adapt(self):
        artifacts = self.build()
        manifest = json.loads(artifacts["manifest.json"])
        records = [json.loads(line) for line in artifacts["replay.jsonl"].splitlines()]
        self.assertEqual(len(records), 24)
        for record in records:
            self.assertEqual(record["training_task_ids"], [] if record["phase"] == "T0" else manifest["splits"]["adapt"])
            # The fictional cues repeat across disjoint patients; adaptation must
            # actually affect predictions, not only report training metadata.
            self.assertEqual(record["prediction"] == "unknown", record["phase"] == "T0")
            self.assertEqual(record["fixture_label_match"], record["phase"] != "T0")
        self.assertEqual(manifest["execution"]["model_calls"], 0)
        self.assertIsNone(manifest["execution"]["cost_usd"])

    def test_source_tampering_and_artifact_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, attestation = self.write_fixture(root, json.loads((FIXTURES / "cases.json").read_text()))
            artifacts = self.build(source, attestation)
            out = root / "out"
            write_replay(artifacts, out)
            (out / "replay.jsonl").write_bytes(artifacts["replay.jsonl"] + b"\n")
            with self.assertRaisesRegex(ValueError, "replay.jsonl"):
                verify_replay(out, source, attestation)
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                self.build(source, attestation)

    def test_missing_synthetic_attestation_patient_id_duplicate_task_fail(self):
        original = json.loads((FIXTURES / "cases.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, attestation = self.write_fixture(root, original, {"synthetic": False})
            with self.assertRaisesRegex(ValueError, "synthetic"):
                self.build(source, attestation)
            for kind in ("patient", "task"):
                payload = copy.deepcopy(original)
                if kind == "patient":
                    payload["cases"][0].pop("patient_id")
                else:
                    payload["cases"][1]["encounter_id"] = payload["cases"][0]["encounter_id"]
                source, attestation = self.write_fixture(root, payload)
                with self.assertRaisesRegex(ValueError, "patient_id" if kind == "patient" else "Duplicate"):
                    self.build(source, attestation)

    def test_counts_must_cover_all_patients_and_be_nonnegative_integers(self):
        for counts in (
            {**COUNTS, "drift": 0},
            {**COUNTS, "adapt": -1},
            {**COUNTS, "adapt": True},
            {**COUNTS, "adapt": 1.0},
        ):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                self.build(counts=counts)

    def test_fhir_fixture_resolves_patient_aliases_without_training_observations(self):
        artifacts = self.build(FIXTURES / "bundle.json", FIXTURES / "bundle.source.json")
        envelope = json.loads(artifacts["memoryeval.json"])
        p1 = [task for task in envelope["tasks"] if task["patient_id"] == "Patient/p1"]
        self.assertEqual(len(p1), 2)
        self.assertEqual(len({task["split"] for task in p1}), 1)
        self.assertEqual(envelope["source"]["format"], "fhir-r4")
        for line in artifacts["replay.jsonl"].splitlines():
            self.assertEqual(json.loads(line)["prediction"], "unknown")

    def test_fhir_mixed_subject_aliases_resolve_to_same_patient(self):
        payload = json.loads((FIXTURES / "bundle.json").read_text())
        condition = next(entry["resource"] for entry in payload["entry"] if entry["resource"]["resourceType"] == "Condition")
        condition["subject"]["reference"] = "urn:uuid:patient-1"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, declaration = self.write_fixture(root, payload)
            manifest = json.loads(declaration.read_text())
            manifest["source"]["format"] = "fhir-r4"
            declaration.write_text(json.dumps(manifest))
            self.build(source, declaration)
            condition["subject"]["reference"] = "urn:uuid:patient-2"
            source, declaration = self.write_fixture(root, payload)
            manifest["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            declaration.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "subject differs"):
                self.build(source, declaration)

    def test_fhir_duplicate_local_patient_ids_do_not_merge_distinct_identities(self):
        payload = json.loads((FIXTURES / "bundle.json").read_text())
        second = next(entry["resource"] for entry in payload["entry"]
                      if entry["resource"].get("resourceType") == "Patient" and entry["resource"]["id"] == "p2")
        second["id"] = "p1"
        for entry in payload["entry"]:
            resource = entry["resource"]
            if (resource.get("subject") or {}).get("reference") == "Patient/p2":
                resource["subject"]["reference"] = "urn:uuid:patient-2"
        with tempfile.TemporaryDirectory() as temp:
            source, declaration = self.write_fixture(Path(temp), payload)
            manifest = json.loads(declaration.read_text())
            manifest["source"]["format"] = "fhir-r4"
            declaration.write_text(json.dumps(manifest))
            # A buggy resolver collapses these four source patients into three.
            with self.assertRaisesRegex(ValueError, "Duplicate FHIR Patient"):
                self.build(source, declaration, {**COUNTS, "drift": 0})

    def test_jsonl_and_reordered_case_sources_preserve_splits_and_predictions(self):
        original = self.build()
        payload = json.loads((FIXTURES / "cases.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, declaration = self.write_fixture(root, payload)
            source.write_text("".join(json.dumps(case) + "\n" for case in reversed(payload["cases"])))
            manifest = json.loads(declaration.read_text())
            manifest["source"]["format"] = "compact-jsonl"
            manifest["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            declaration.write_text(json.dumps(manifest))
            reordered = self.build(source, declaration)
        self.assertEqual(json.loads(original["manifest.json"])["splits"], json.loads(reordered["manifest.json"])["splits"])
        self.assertEqual(original["replay.jsonl"], reordered["replay.jsonl"])

    def test_verifier_rejects_wrong_implementation_and_cli_replays_without_writes(self):
        import subprocess
        import sys
        artifacts = self.build()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_replay(artifacts, root)
            command = [sys.executable, "scripts/run_synthetic_replay.py", "--verify",
                       "--source", str(FIXTURES / "cases.json"),
                       "--source-manifest", str(FIXTURES / "cases.source.json"), "--out", str(root)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertTrue(all((root / name).read_bytes() == data for name, data in artifacts.items()))
            manifest = json.loads(artifacts["manifest.json"])
            manifest["implementation"]["bridge_version"] = "changed-version"
            (root / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "manifest.json"):
                verify_replay(root, FIXTURES / "cases.json", FIXTURES / "cases.source.json")


if __name__ == "__main__":
    unittest.main()
