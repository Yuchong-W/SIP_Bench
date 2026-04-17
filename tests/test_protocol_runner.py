from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.metrics import load_jsonl
from sip_bench.protocol_runner import (
    _apply_task_patch,
    _strip_skills_from_dockerfile_text,
    build_skillsbench_explicit_plan,
    build_tau_explicit_plan,
    load_protocol_suite_config,
    run_skillsbench_suite,
    run_tau_bench_suite,
)


class ProtocolRunnerTests(unittest.TestCase):
    def test_build_skillsbench_explicit_plan_preserves_split_assignment(self) -> None:
        plan = build_skillsbench_explicit_plan(
            registry_path=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
            repo_root="benchmarks/skillsbench",
            split_task_ids={
                "replay": ["citation-check"],
                "adapt": [],
                "heldout": ["court-form-filling"],
                "drift": [],
            },
            agent="oracle",
            harbor_bin="harbor",
            extra_args=["--artifact", "/logs/verifier"],
        )
        self.assertEqual(plan["manifest"]["counts"]["replay"], 1)
        self.assertEqual(plan["manifest"]["counts"]["heldout"], 1)
        self.assertEqual(plan["manifest"]["replay"][0]["task_id"], "citation-check")
        self.assertEqual(plan["manifest"]["heldout"][0]["task_id"], "court-form-filling")
        self.assertIn("--artifact", plan["commands"]["replay"][0])

    def test_run_skillsbench_suite_import_only_aggregates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            replay_job_t0 = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "t0_replay",
                fixture_relative_path="citation-check__fixture001/result.json",
            )
            heldout_job_t0 = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "t0_heldout",
                fixture_relative_path="court-form-filling__fixture002/result.json",
            )
            replay_job_t1 = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "t1_replay",
                fixture_relative_path="citation-check__fixture001/result.json",
            )
            heldout_job_t1 = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "t1_heldout",
                fixture_relative_path="court-form-filling__fixture002/result.json",
            )

            config = {
                "schema_version": "0.1.0",
                "suite_name": "fixture-suite",
                "benchmark_name": "skillsbench",
                "repo_root": "benchmarks/skillsbench",
                "registry_path": str(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json"),
                "out_root": str(tmp_path / "suite_out"),
                "execution": {
                    "agent": "oracle",
                    "model": None,
                    "harbor_bin": "harbor",
                    "jobs_dir": str(tmp_path / "jobs_unused"),
                    "path_type": "oracle",
                    "agent_version": "fixture-suite",
                    "seed": 11,
                    "extra_args": [],
                },
                "runs": [
                    {
                        "run_name": "t0_replay",
                        "phase": "T0",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                        "source_job_dir": str(replay_job_t0),
                    },
                    {
                        "run_name": "t0_heldout",
                        "phase": "T0",
                        "benchmark_split": "heldout",
                        "task_ids": ["court-form-filling"],
                        "source_job_dir": str(heldout_job_t0),
                    },
                    {
                        "run_name": "t1_replay",
                        "phase": "T1",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                        "source_job_dir": str(replay_job_t1),
                    },
                    {
                        "run_name": "t1_heldout",
                        "phase": "T1",
                        "benchmark_split": "heldout",
                        "task_ids": ["court-form-filling"],
                        "source_job_dir": str(heldout_job_t1),
                    },
                ],
            }
            config_path = tmp_path / "fixture_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            report = run_skillsbench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=True,
            )
            self.assertTrue(report["runs_validation"]["valid"])
            self.assertTrue(report["summary"]["generated"])

            combined_runs = load_jsonl(Path(report["combined_runs_path"]))
            self.assertEqual(len(combined_runs), 4)
            summary_rows = load_jsonl(Path(report["summary"]["summary_path"]))
            self.assertEqual(len(summary_rows), 1)
            self.assertEqual(summary_rows[0]["metrics"]["fg_mean"], 0.0)
            self.assertEqual(summary_rows[0]["metrics"]["br_mean"], 0.0)

    def test_build_tau_explicit_plan_preserves_split_assignment(self) -> None:
        plan = build_tau_explicit_plan(
            repo_root="benchmarks/tau-bench",
            env="retail",
            task_split="test",
            split_task_ids={
                "replay": [0],
                "adapt": [1],
                "heldout": [2],
                "drift": [],
            },
            model="gpt-4o-mini",
            model_provider="openai",
            user_model="gpt-4o-mini",
            user_model_provider="openai",
        )
        self.assertEqual(plan["manifest"]["counts"]["replay"], 1)
        self.assertEqual(plan["manifest"]["counts"]["heldout"], 1)
        self.assertEqual(plan["manifest"]["replay"][0]["task_id"], "retail:test:0")
        self.assertIn("--task-ids", plan["commands"]["replay"][0])

    def test_run_tau_suite_import_only_aggregates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config = {
                "schema_version": "0.1.0",
                "suite_name": "tau-fixture-suite",
                "benchmark_name": "tau-bench",
                "repo_root": str(ROOT / "benchmarks" / "tau-bench"),
                "out_root": str(tmp_path / "suite_out"),
                "execution": {
                    "python_bin": "python",
                    "env": "retail",
                    "task_split": "test",
                    "model": "gpt-4o-mini",
                    "model_provider": "openai",
                    "user_model": "gpt-4o-mini",
                    "user_model_provider": "openai",
                    "agent_strategy": "tool-calling",
                    "user_strategy": "llm",
                    "num_trials": 1,
                    "max_concurrency": 1,
                    "log_dir": str(tmp_path / "tau_logs"),
                    "path_type": "external",
                    "agent_version": "tau-fixture-suite",
                    "seed": 13,
                    "extra_args": [],
                },
                "runs": [
                    {
                        "run_name": "t0_replay",
                        "phase": "T0",
                        "benchmark_split": "replay",
                        "task_ids": [4],
                        "source_result_file": str(ROOT / "tests" / "fixtures" / "tau_results_sample.json"),
                    },
                    {
                        "run_name": "t0_heldout",
                        "phase": "T0",
                        "benchmark_split": "heldout",
                        "task_ids": [5],
                        "source_result_file": str(ROOT / "tests" / "fixtures" / "tau_results_sample.json"),
                    },
                    {
                        "run_name": "t1_adapt",
                        "phase": "T1",
                        "benchmark_split": "adapt",
                        "task_ids": [4],
                        "source_result_file": str(ROOT / "tests" / "fixtures" / "tau_results_sample.json"),
                    },
                    {
                        "run_name": "t1_replay",
                        "phase": "T1",
                        "benchmark_split": "replay",
                        "task_ids": [4],
                        "source_result_file": str(ROOT / "tests" / "fixtures" / "tau_results_sample.json"),
                    },
                    {
                        "run_name": "t1_heldout",
                        "phase": "T1",
                        "benchmark_split": "heldout",
                        "task_ids": [5],
                        "source_result_file": str(ROOT / "tests" / "fixtures" / "tau_results_sample.json"),
                    },
                ],
            }
            config_path = tmp_path / "tau_fixture_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            report = run_tau_bench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=True,
            )
            self.assertTrue(report["runs_validation"]["valid"])
            self.assertTrue(report["summary"]["generated"])
            combined_runs = load_jsonl(Path(report["combined_runs_path"]))
            self.assertEqual(len(combined_runs), 5)
            self.assertTrue(all(run["benchmark_name"] == "tau-bench" for run in combined_runs))
            summary_rows = load_jsonl(Path(report["summary"]["summary_path"]))
            self.assertEqual(len(summary_rows), 1)
            self.assertEqual(summary_rows[0]["metrics"]["fg_mean"], 0.0)
            self.assertEqual(summary_rows[0]["metrics"]["br_mean"], 0.0)

    def test_load_protocol_suite_config_rejects_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "bad_suite.json"
            config_path.write_text(
                json.dumps({"schema_version": "0.1.0", "suite_name": "bad"}, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_protocol_suite_config(config_path)

    def test_load_protocol_suite_config_rejects_invalid_tau_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "bad_tau_suite.json"
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "suite_name": "bad-tau",
                        "benchmark_name": "tau-bench",
                        "repo_root": "benchmarks/tau-bench",
                        "out_root": "results/bad",
                        "execution": {
                            "env": "retail",
                            "task_split": "test",
                            "path_type": "external",
                            "agent_version": "bad",
                        },
                        "runs": [
                            {
                                "run_name": "t0_replay",
                                "phase": "T0",
                                "benchmark_split": "replay",
                                "task_ids": [0],
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_protocol_suite_config(config_path)

    def test_strip_skills_from_dockerfile_text_removes_skill_copy_and_pythonpath(self) -> None:
        original = (
            "FROM python:3.12-slim\n"
            "COPY skills /root/.codex/skills\n"
            "COPY file.txt /app/file.txt\n"
            'ENV PYTHONPATH="/root/.codex/skills/example/scripts"\n'
        )
        updated = _strip_skills_from_dockerfile_text(original)
        self.assertNotIn("COPY skills", updated)
        self.assertNotIn("ENV PYTHONPATH", updated)
        self.assertIn("COPY file.txt /app/file.txt", updated)

    def test_apply_offer_letter_patch_rewrites_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_root = Path(tmpdir) / "tasks" / "offer-letter-generator"
            dockerfile_path = task_root / "environment" / "Dockerfile"
            dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
            dockerfile_path.write_text(
                "FROM ubuntu:24.04\n\n"
                "RUN apt-get update && apt-get install -y \\\n"
                "    python3 \\\n"
                "    python3-pip \\\n"
                "    curl \\\n"
                "    && rm -rf /var/lib/apt/lists/*\n\n"
                "# Install Python packages\n"
                "RUN pip3 install --break-system-packages \\\n"
                "    python-docx==1.1.2\n",
                encoding="utf-8",
            )

            patched_files = _apply_task_patch(
                task_id="offer-letter-generator",
                patch_name="offer_letter_generator_system_docx",
                task_root=task_root,
            )
            updated = dockerfile_path.read_text(encoding="utf-8")
            self.assertIn("python3-docx", updated)
            self.assertNotIn("python-docx==1.1.2", updated)
            self.assertEqual(patched_files, [str(dockerfile_path)])

    def _make_single_trial_job_dir(self, job_dir: Path, *, fixture_relative_path: str) -> Path:
        source = ROOT / "tests" / "fixtures" / "skillsbench_harbor_job_sample" / fixture_relative_path
        trial_name = Path(fixture_relative_path).parts[0]
        target = job_dir / trial_name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target / "result.json")
        return job_dir


if __name__ == "__main__":
    unittest.main()
