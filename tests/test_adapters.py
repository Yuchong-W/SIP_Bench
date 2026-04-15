from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.adapters import SkillsBenchAdapter, TauBenchAdapter


class SkillsBenchAdapterTests(unittest.TestCase):
    def test_discover_and_split_registry_sample(self) -> None:
        adapter = SkillsBenchAdapter()
        tasks = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json")
        self.assertEqual(len(tasks), 6)

        manifest = adapter.build_manifest(
            tasks,
            replay_count=2,
            adapt_count=2,
            heldout_count=2,
            seed=3,
        )
        adapter.validate_manifest(manifest)
        self.assertEqual(manifest.counts()["heldout"], 2)
        self.assertEqual(len(manifest.all_task_ids()), 6)

    def test_build_harbor_command(self) -> None:
        adapter = SkillsBenchAdapter()
        task = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json")[0]
        command = adapter.build_harbor_command(
            repo_root="benchmarks/skillsbench",
            task=task,
            agent="oracle",
            harbor_bin="harbor",
        )
        self.assertEqual(command[:3], ["harbor", "run", "-p"])
        self.assertIn("tasks/citation-check", command[3].replace("\\", "/"))


class TauBenchAdapterTests(unittest.TestCase):
    def test_build_manifest_from_ids(self) -> None:
        adapter = TauBenchAdapter()
        manifest = adapter.build_manifest_from_ids(
            env="retail",
            task_split="test",
            replay_ids=[1, 2],
            adapt_ids=[3],
            heldout_ids=[4, 5],
            drift_ids=[6],
        )
        adapter.validate_manifest(manifest)
        self.assertEqual(manifest.counts(), {"replay": 2, "adapt": 1, "heldout": 2, "drift": 1})

    def test_build_run_command(self) -> None:
        adapter = TauBenchAdapter()
        command = adapter.build_run_command(
            repo_root="benchmarks/tau-bench",
            env="retail",
            task_split="test",
            task_ids=[4, 5],
            model="gpt-4o",
            model_provider="openai",
            user_model="gpt-4o",
            user_model_provider="openai",
        )
        self.assertEqual(command[:2], ["python", str(Path("benchmarks/tau-bench") / "run.py")])
        self.assertIn("--task-ids", command)
        self.assertEqual(command[-2:], ["4", "5"])

    def test_parse_result_file(self) -> None:
        adapter = TauBenchAdapter()
        runs = adapter.parse_result_file(
            ROOT / "tests" / "fixtures" / "tau_results_sample.json",
            env="retail",
            task_split="test",
            phase="T0",
            path_type="frozen",
            model_name="gpt-5-mini",
            agent_name="tau-smoke",
            agent_version="0.1.0",
            seed=11,
        )
        self.assertEqual(len(runs), 2)
        self.assertTrue(runs[0]["success"])
        self.assertEqual(runs[0]["benchmark_split"], "heldout")
        self.assertEqual(runs[1]["metadata"]["traj_length"], 1)


if __name__ == "__main__":
    unittest.main()
