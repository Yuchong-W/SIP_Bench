from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_task_family_ablation as task_family_ablation  # type: ignore


class TaskFamilyAblationTests(unittest.TestCase):
    def test_summarize_family_tracks_families_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            combined = Path(tmpdir) / "combined_runs.jsonl"
            rows = [
                {
                    "run_id": "skillsbench::suite::T0",
                    "phase": "T0",
                    "benchmark_split": "heldout",
                    "task_id": "task-a",
                    "score": 0.6,
                    "success": True,
                    "metadata": {"difficulty": "easy", "category": "game"},
                },
                {
                    "run_id": "skillsbench::suite::T1",
                    "phase": "T1",
                    "benchmark_split": "heldout",
                    "task_id": "task-a",
                    "score": 0.8,
                    "success": True,
                    "metadata": {"difficulty": "easy", "category": "game"},
                },
                {
                    "run_id": "skillsbench::suite::T0",
                    "phase": "T0",
                    "benchmark_split": "replay",
                    "task_id": "task-a",
                    "score": 1.0,
                    "success": False,
                    "metadata": {
                        "difficulty": "easy",
                        "category": "game",
                        "exception_message": "UtilBindVsockAnyPort",
                    },
                },
            ]
            with combined.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")

            loaded = task_family_ablation.load_rows(combined)
            summary = task_family_ablation.summarize_family(loaded)

            self.assertEqual(len(summary), 1)
            item = summary[0]
            self.assertEqual(item["difficulty"], "easy")
            self.assertEqual(item["category"], "game")
            self.assertAlmostEqual(item["heldout_t0_mean"], 0.6)
            self.assertAlmostEqual(item["heldout_t1_mean"], 0.8)
            self.assertEqual(item["fg"], 0.2)
            self.assertEqual(item["failure_count"], 1)
            self.assertIn("docker", item["failure_signature"])
