import json
import tempfile
import unittest
from pathlib import Path

from sip_bench.adapters.medical import MedicalAdapter
from scripts.run_medical_demo import run_demo


class MedicalAdapterTests(unittest.TestCase):
    def test_demo_does_not_use_labels_to_predict_heldout(self):
        manifest, runs = run_demo(Path("benchmarks/medical/cases.json"))
        heldout_t0 = [r for r in runs if r["phase"] == "T0" and r["benchmark_split"] == "heldout"]
        self.assertTrue(heldout_t0)
        self.assertTrue(all(r["metadata"]["adaptation_examples"] == 0 for r in heldout_t0))
        self.assertTrue(all("diagnosis" not in r["metadata"] for r in heldout_t0))

    def test_feedback_disagreement_is_error(self):
        result = MedicalAdapter.attribute_feedback(
            prediction="uti", diagnosis="viral_uri", feedback="I disagree with this answer"
        )
        self.assertEqual(result["category"], "diagnosis_error")

    def test_fhir_mismatched_subject_is_rejected(self):
        bundle = {"resourceType": "Bundle", "entry": [
            {"resource": {"resourceType": "Encounter", "id": "e1", "subject": {"reference": "Patient/p1"}}},
            {"resource": {"resourceType": "Condition", "id": "c1", "subject": {"reference": "Patient/p2"}, "encounter": {"reference": "Encounter/e1"}, "code": {"coding": [{"code": "x"}]}}},
        ]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(bundle, handle); handle.flush()
            with self.assertRaises(ValueError):
                MedicalAdapter().discover_tasks(handle.name)

    def test_fhir_bundle_without_encounter_condition_pair_is_rejected(self):
        bundle = {"resourceType": "Bundle", "entry": [
            {"resource": {"resourceType": "Observation", "id": "o1"}},
            {"resource": {"resourceType": "Condition", "id": "c1", "code": {"coding": [{"code": "x"}]}}},
        ]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(bundle, handle); handle.flush()
            with self.assertRaisesRegex(ValueError, "different task contract"):
                MedicalAdapter().discover_tasks(handle.name)

    def test_fhir_pair_preserves_condition_label(self):
        bundle = {"resourceType": "Bundle", "entry": [
            {"resource": {"resourceType": "Encounter", "id": "e1", "subject": {"reference": "Patient/p1"}}},
            {"resource": {"resourceType": "Condition", "id": "c1", "subject": {"reference": "Patient/p1"}, "encounter": {"reference": "Encounter/e1"}, "code": {"coding": [{"code": "diagnosis-x"}]}}},
        ]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(bundle, handle); handle.flush()
            task = MedicalAdapter().discover_tasks(handle.name)[0]
        self.assertEqual(task.task_id, "e1")
        self.assertEqual(task.metadata["clinical"]["diagnosis"], "diagnosis-x")

    def test_navilia_timeline_prediction_json_is_rejected(self):
        task = {
            "schema": "navilia.v1", "benchmark": "SIP-Bench", "task_id": "case_t1",
            "answer": "Condition", "input_event_ids": ["event-1"], "evidence": ["event-2"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(task, handle); handle.flush()
            with self.assertRaisesRegex(ValueError, "different task contract"):
                MedicalAdapter().discover_tasks(handle.name)

    def test_navilia_timeline_prediction_jsonl_is_rejected(self):
        task = {
            "schema": "navilia.v1", "benchmark": "SIP-Bench", "task_id": "case_t1",
            "answer": "Condition", "input_event_ids": ["event-1"], "evidence": ["event-2"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl") as handle:
            handle.write(json.dumps(task) + "\n"); handle.flush()
            with self.assertRaisesRegex(ValueError, "different task contract"):
                MedicalAdapter().discover_tasks(handle.name)


if __name__ == "__main__":
    unittest.main()
