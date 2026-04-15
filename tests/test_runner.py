from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.metrics import load_jsonl
from sip_bench.runner import (
    build_skillsbench_plan,
    execute_command_plan,
    import_skillsbench_results,
    import_tau_results,
)


class RunnerTests(unittest.TestCase):
    def test_build_skillsbench_plan(self) -> None:
        plan = build_skillsbench_plan(
            registry_path=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
            repo_root="benchmarks/skillsbench",
            replay_count=2,
            adapt_count=1,
            heldout_count=2,
            seed=13,
            agent="oracle",
            categories={"research", "document-processing", "travel-planning", "media-processing", "financial-analysis"},
        )
        self.assertEqual(plan["benchmark_name"], "skillsbench")
        self.assertEqual(plan["manifest"]["counts"]["replay"], 2)
        self.assertEqual(plan["manifest"]["counts"]["adapt"], 1)
        self.assertEqual(plan["manifest"]["counts"]["heldout"], 2)
        self.assertTrue(plan["commands"]["heldout"])

    def test_import_tau_results_writes_runs_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tau_runs.jsonl"
            runs = import_tau_results(
                source=ROOT / "tests" / "fixtures" / "tau_results_sample.json",
                out=output_path,
                env="retail",
                task_split="test",
                benchmark_split="heldout",
                phase="T1",
                path_type="external",
                model_name="gpt-5-mini",
                agent_name="tau-import",
                agent_version="0.1.0",
                seed=9,
            )
            self.assertEqual(len(runs), 2)
            written = load_jsonl(output_path)
            self.assertEqual(len(written), 2)
            self.assertEqual(written[0]["phase"], "T1")
            self.assertEqual(written[0]["path_type"], "external")
            self.assertEqual(written[0]["benchmark_split"], "heldout")

    def test_import_skillsbench_results_writes_runs_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "skillsbench_runs.jsonl"
            runs = import_skillsbench_results(
                source=ROOT / "tests" / "fixtures" / "skillsbench_results_sample.json",
                out=output_path,
                benchmark_split="golden",
                phase="T1",
                seed=3,
                registry_source=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
                agent_version="fixture-import",
                benchmark_version="skillsbench-fixture",
                conditions={"noskills", "withskills"},
            )
            self.assertEqual(len(runs), 3)
            written = load_jsonl(output_path)
            self.assertEqual(len(written), 3)
            self.assertEqual(written[0]["benchmark_name"], "skillsbench")
            self.assertEqual(written[0]["benchmark_split"], "golden")

    def test_execute_command_plan_mock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "mock_report.json"
            report = execute_command_plan(
                plan_source=ROOT / "tests" / "fixtures" / "mock_execute_plan.json",
                out=report_path,
                mode="mock",
            )
            self.assertEqual(report["summary"]["executed"], 2)
            self.assertEqual(report["summary"]["status_counts"]["success"], 2)
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["summary"]["executed"], 2)

    def test_execute_command_plan_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            plan = json.loads(
                (ROOT / "tests" / "fixtures" / "mock_execute_plan.json").read_text(
                    encoding="utf-8"
                )
            )
            replay_command = plan["commands"]["replay"][0]
            heldout_command = plan["commands"]["heldout"][0]
            replay_command[replay_command.index("--out") + 1] = str(tmp_path / "mock_replay.txt")
            heldout_command[heldout_command.index("--out") + 1] = str(tmp_path / "mock_heldout.txt")
            plan_path = tmp_path / "plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            report_path = Path(tmpdir) / "subprocess_report.json"
            report = execute_command_plan(
                plan_source=plan_path,
                out=report_path,
                mode="subprocess",
                cwd=ROOT,
            )
            self.assertEqual(report["summary"]["executed"], 2)
            self.assertEqual(report["summary"]["status_counts"]["success"], 2)
            replay_output = tmp_path / "mock_replay.txt"
            heldout_output = tmp_path / "mock_heldout.txt"
            self.assertTrue(replay_output.exists())
            self.assertTrue(heldout_output.exists())


if __name__ == "__main__":
    unittest.main()
