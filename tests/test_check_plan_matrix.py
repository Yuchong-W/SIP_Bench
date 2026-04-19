from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import check_plan_matrix


class CheckPlanMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "skillsbench_suite.json"
        self.out_root = self.root / "results" / "protocol_runs" / "skillsbench_suite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _build_config(self) -> None:
        self.config_path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1.0",
                    "suite_name": "unit-suite",
                    "benchmark_name": "skillsbench",
                    "repo_root": "benchmarks/skillsbench",
                    "registry_path": "benchmarks/skillsbench/website/src/data/tasks-registry.json",
                    "out_root": str(self.out_root.relative_to(self.root)),
                    "execution": {
                        "agent": "codex",
                        "harbor_bin": "scripts/harbor312",
                        "jobs_dir": "results/real_jobs",
                        "path_type": "oracle",
                        "agent_version": "test",
                    },
                    "runs": [
                        {
                            "run_name": "t0_replay",
                            "phase": "T0",
                            "benchmark_split": "replay",
                            "task_ids": ["dialogue-parser"],
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_non_strict_mode_marks_missing_artifacts_as_warning(self) -> None:
        self._build_config()
        (self.out_root / "plans").mkdir(parents=True, exist_ok=True)
        (self.out_root / "plans" / "t0_replay.json").write_text("{}", encoding="utf-8")
        (self.out_root / "hydration").mkdir(parents=True, exist_ok=True)
        (self.out_root / "hydration" / "t0_replay.json").write_text("{}", encoding="utf-8")
        (self.out_root / "execution").mkdir(parents=True, exist_ok=True)
        (self.out_root / "execution" / "t0_replay.json").write_text("{}", encoding="utf-8")
        (self.out_root / "runs").mkdir(parents=True, exist_ok=True)
        (self.out_root / "runs" / "t0_replay.jsonl").write_text("{}\n", encoding="utf-8")

        checks: list[dict] = []
        suite_checks = [check_plan_matrix._run_suite_check(self.config_path, strict=False, checks=checks)]

        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        suite_status = suite_checks[0]["status"]
        run_row = suite_checks[0]["run_rows"][0]
        status_map = {row["label"]: row["status"] for row in run_row["artifacts"]}
        check_labels = {entry["label"]: entry["status"] for entry in checks}

        self.assertEqual(failed, [])
        self.assertEqual(len(warnings), 4)
        self.assertEqual(suite_status, "pass")
        self.assertEqual(status_map["plan"], "pass")
        self.assertEqual(status_map["runs"], "pass")
        self.assertEqual(check_labels["run:t0_replay:source_plan"], "warn")
        self.assertEqual(check_labels["suite:summary"], "warn")

    def test_strict_mode_fails_missing_artifacts(self) -> None:
        self._build_config()
        (self.out_root / "plans").mkdir(parents=True, exist_ok=True)
        (self.out_root / "plans" / "t0_replay.source.json").write_text("{}", encoding="utf-8")
        checks: list[dict] = []
        suite_checks = [check_plan_matrix._run_suite_check(self.config_path, strict=True, checks=checks)]

        failed = [check for check in checks if check["status"] == "fail"]
        suite_status = suite_checks[0]["status"]

        self.assertTrue(failed)
        self.assertEqual(suite_status, "fail")

    def test_source_result_file_path_skips_execution_only_artifacts_in_strict_mode(self) -> None:
        self.config_path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1.0",
                    "suite_name": "tau-suite",
                    "benchmark_name": "tau-bench",
                    "repo_root": "benchmarks/tau-bench",
                    "out_root": str(self.out_root.relative_to(self.root)),
                    "execution": {
                        "python_bin": "scripts/tau311.cmd",
                        "env": "retail",
                        "task_split": "test",
                        "model": "gpt-4o-mini",
                        "model_provider": "openai",
                        "user_model": "gpt-4o-mini",
                        "user_model_provider": "openai",
                        "path_type": "external",
                        "agent_version": "tau-historical",
                    },
                    "runs": [
                        {
                            "run_name": "t0_replay",
                            "phase": "T0",
                            "benchmark_split": "replay",
                            "task_ids": [0],
                            "source_result_file": "history.json",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        (self.out_root / "plans").mkdir(parents=True, exist_ok=True)
        (self.out_root / "plans" / "t0_replay.json").write_text("{}", encoding="utf-8")
        (self.out_root / "runs").mkdir(parents=True, exist_ok=True)
        (self.out_root / "runs" / "t0_replay.jsonl").write_text("{}\n", encoding="utf-8")
        (self.root / "history.json").write_text("{}", encoding="utf-8")
        (self.out_root / "combined_runs.jsonl").write_text("{}\n", encoding="utf-8")
        (self.out_root / "summary.jsonl").write_text("{}\n", encoding="utf-8")
        (self.out_root / "suite_report.json").write_text("{}", encoding="utf-8")

        checks: list[dict] = []
        suite_checks = [check_plan_matrix._run_suite_check(self.config_path, strict=True, checks=checks)]

        failed = [check for check in checks if check["status"] == "fail"]
        status_map = {entry["label"]: entry["status"] for entry in checks}

        self.assertEqual(failed, [])
        self.assertEqual(suite_checks[0]["status"], "pass")
        self.assertEqual(status_map["run:t0_replay:plan"], "pass")
        self.assertEqual(status_map["run:t0_replay:runs"], "pass")
        self.assertEqual(status_map["run:t0_replay:source_result_file"], "pass")
        self.assertNotIn("run:t0_replay:hydration", status_map)
        self.assertNotIn("run:t0_replay:execution", status_map)
        self.assertNotIn("run:t0_replay:source_plan", status_map)


if __name__ == "__main__":
    unittest.main()
