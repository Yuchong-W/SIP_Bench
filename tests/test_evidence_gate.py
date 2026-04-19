from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evidence_gate  # type: ignore


class EvidenceGateTests(unittest.TestCase):
    def test_load_summary_rows_skips_empty_lines(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl") as handle:
            handle.write("\n")
            handle.write(json.dumps({"attempts": 1}) + "\n")
            handle.write("  \n")
            handle.flush()
            rows = evidence_gate._load_summary_rows(Path(handle.name))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {"attempts": 1})

    def test_evaluate_gate_returns_blocked_for_empty_summary(self) -> None:
        gate = evidence_gate._evaluate_gate(
            rows=[],
            attempts=3,
            ceiling_gap=0.02,
            protocol_shift=0.02,
            ie_shift=0.0005,
        )
        self.assertEqual(gate["evidence_status"], "blocked")
        self.assertFalse(gate["non_ceiling"])
        self.assertFalse(gate["required_repeats_ok"])

    def test_evaluate_gate_marks_evidence_when_depth_and_non_ceiling(self) -> None:
        rows = [
            {
                "run_name": "t0_replay",
                "attempts": 3,
                "metrics": {
                    "t0_replay_mean": 1.0,
                    "t1_replay_mean": 1.0,
                    "t0_heldout_mean": 1.0,
                    "t1_heldout_mean": 1.0,
                    "fg_mean": 0.03,
                    "br_mean": 0.0,
                    "ie_mean": 0.001,
                },
            }
        ]
        gate = evidence_gate._evaluate_gate(
            rows=rows,
            attempts=3,
            ceiling_gap=0.02,
            protocol_shift=0.02,
            ie_shift=0.0005,
        )
        self.assertEqual(gate["evidence_status"], "evidence")
        self.assertTrue(gate["non_ceiling"])
        self.assertTrue(gate["required_repeats_ok"])
        self.assertEqual(gate["max_repeats_observed"], 3)

    def test_evaluate_gate_uses_summary_repeats_when_attempts_is_missing(self) -> None:
        rows = [
            {
                "run_name": "t0_replay",
                "repeats": 3,
                "metrics": {
                    "t0_replay_mean": 0.93,
                    "fg_mean": 0.03,
                    "br_mean": 0.0,
                    "ie_mean": 0.001,
                },
            }
        ]
        gate = evidence_gate._evaluate_gate(
            rows=rows,
            attempts=3,
            ceiling_gap=0.02,
            protocol_shift=0.02,
            ie_shift=0.0005,
        )
        self.assertEqual(gate["evidence_status"], "evidence")
        self.assertTrue(gate["required_repeats_ok"])
        self.assertEqual(gate["max_repeats_observed"], 3)

    def test_evaluate_gate_screening_when_repeats_short(self) -> None:
        rows = [
            {
                "run_name": "t0_replay",
                "attempts": 1,
                "metrics": {"t0_replay_mean": 1.0, "t1_replay_mean": 1.0},
            }
        ]
        gate = evidence_gate._evaluate_gate(
            rows=rows,
            attempts=3,
            ceiling_gap=0.02,
            protocol_shift=0.02,
            ie_shift=0.0005,
        )
        self.assertEqual(gate["evidence_status"], "screening")
        self.assertFalse(gate["required_repeats_ok"])


if __name__ == "__main__":
    unittest.main()
