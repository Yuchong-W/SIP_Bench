from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.metrics import load_jsonl
from sip_bench.protocol_runner import (
    _allocate_attempt_job_name,
    _apply_task_patch,
    _normalize_shell_scripts,
    _plan_skillsbench_retry,
    _resolve_command_value,
    _strip_skills_from_dockerfile_text,
    build_skillsbench_explicit_plan,
    build_tau_explicit_plan,
    load_protocol_suite_config,
    run_skillsbench_suite,
    run_tau_bench_suite,
)


class ProtocolRunnerTests(unittest.TestCase):
    def test_allocate_attempt_job_name_avoids_existing_job_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jobs_dir = Path(tmpdir)
            (jobs_dir / "retry-suite-t0_replay-attempt01").mkdir()
            (jobs_dir / "retry-suite-t0_replay-attempt01-rerun02").mkdir()

            allocated = _allocate_attempt_job_name(
                jobs_dir=jobs_dir,
                base_job_name="retry-suite-t0_replay",
                attempt_number=1,
                max_attempts=2,
            )

            self.assertEqual(allocated, "retry-suite-t0_replay-attempt01-rerun03")

    def test_plan_skillsbench_retry_matches_message_substrings(self) -> None:
        decision = _plan_skillsbench_retry(
            attempt_number=1,
            execution_report={
                "summary": {
                    "executed": 1,
                    "status_counts": {"success": 1},
                    "halted_early": False,
                }
            },
            imported_runs=[
                {
                    "run_id": "skillsbench::attempt01",
                    "task_id": "dialogue-parser",
                    "success": False,
                    "metadata": {
                        "exception_type": "RuntimeError",
                        "exception_message": "E: Failed to fetch package because the connection was forcibly closed",
                    },
                }
            ],
            retry_policy={
                "max_attempts": 2,
                "require_all_records_failed": True,
                "retry_on_execution_statuses": [],
                "retry_on_exception_types": [],
                "retry_on_message_substrings": [
                    "e: failed to fetch",
                    "connection was forcibly closed",
                ],
            },
        )
        self.assertTrue(decision["retry"])
        self.assertEqual(decision["reason"], "exception_message:e: failed to fetch")
        self.assertEqual(decision["matched_failures"][0]["task_id"], "dialogue-parser")

    def test_resolve_command_value_prefers_extensionless_wrapper_on_posix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            scripts_dir = tmp_path / "scripts"
            scripts_dir.mkdir()
            wrapper = scripts_dir / "harbor312"
            wrapper.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            cmd_wrapper = scripts_dir / "harbor312.cmd"
            cmd_wrapper.write_text("@echo off\r\n", encoding="utf-8")

            resolved = _resolve_command_value(tmp_path, "scripts/harbor312.cmd")
            self.assertEqual(resolved, str(wrapper))

    def test_resolve_command_value_prefers_cmd_wrapper_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            scripts_dir = tmp_path / "scripts"
            scripts_dir.mkdir()
            wrapper = scripts_dir / "harbor312"
            wrapper.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            cmd_wrapper = scripts_dir / "harbor312.cmd"
            cmd_wrapper.write_text("@echo off\r\n", encoding="utf-8")

            with patch("sip_bench.protocol_runner.os.name", "nt"):
                resolved = _resolve_command_value(tmp_path, "scripts/harbor312")
            self.assertEqual(resolved, str(cmd_wrapper))

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

    def test_run_skillsbench_suite_can_rerun_selected_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            success_job = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "success",
                fixture_relative_path="citation-check__fixture001/result.json",
            )
            failure_job = self._make_single_trial_job_dir(
                tmp_path / "jobs" / "failure",
                fixture_relative_path="court-form-filling__fixture002/result.json",
            )

            config = {
                "schema_version": "0.1.0",
                "suite_name": "resume-suite",
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
                    "agent_version": "resume-suite",
                    "seed": 11,
                    "extra_args": [],
                },
                "runs": [
                    {
                        "run_name": "t0_replay",
                        "phase": "T0",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                        "source_job_dir": str(success_job),
                    },
                    {
                        "run_name": "t0_heldout",
                        "phase": "T0",
                        "benchmark_split": "heldout",
                        "task_ids": ["court-form-filling"],
                        "source_job_dir": str(failure_job),
                    },
                    {
                        "run_name": "t1_replay",
                        "phase": "T1",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                        "source_job_dir": str(success_job),
                    },
                    {
                        "run_name": "t1_heldout",
                        "phase": "T1",
                        "benchmark_split": "heldout",
                        "task_ids": ["court-form-filling"],
                        "source_job_dir": str(failure_job),
                    },
                ],
            }
            config_path = tmp_path / "resume_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            initial_report = run_skillsbench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=True,
            )
            self.assertEqual(initial_report["run_count"], 4)
            initial_combined = load_jsonl(Path(initial_report["combined_runs_path"]))
            self.assertEqual(
                [row["task_id"] for row in initial_combined if row["phase"] == "T0" and row["benchmark_split"] == "replay"],
                ["citation-check"],
            )

            config["runs"][0]["task_ids"] = ["court-form-filling"]
            config["runs"][0]["source_job_dir"] = str(failure_job)
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            resumed_report = run_skillsbench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=True,
                selected_run_names={"t0_replay"},
            )
            self.assertEqual(resumed_report["run_count"], 4)

            combined_runs = load_jsonl(Path(resumed_report["combined_runs_path"]))
            t0_replay_rows = [
                row for row in combined_runs if row["phase"] == "T0" and row["benchmark_split"] == "replay"
            ]
            t1_replay_rows = [
                row for row in combined_runs if row["phase"] == "T1" and row["benchmark_split"] == "replay"
            ]
            self.assertEqual(len(combined_runs), 4)
            self.assertEqual(len(t0_replay_rows), 1)
            self.assertEqual(t0_replay_rows[0]["task_id"], "court-form-filling")
            self.assertFalse(t0_replay_rows[0]["success"])
            self.assertEqual(len(t1_replay_rows), 1)
            self.assertEqual(t1_replay_rows[0]["task_id"], "citation-check")
            self.assertTrue(t1_replay_rows[0]["success"])

    @patch("sip_bench.protocol_runner.validate_data_file")
    @patch("sip_bench.protocol_runner.import_skillsbench_job")
    @patch("sip_bench.protocol_runner.execute_command_plan")
    @patch("sip_bench.protocol_runner.hydrate_skillsbench_checkout")
    def test_run_skillsbench_suite_retries_transient_failures(
        self,
        hydrate_mock,
        execute_mock,
        import_mock,
        validate_mock,
    ) -> None:
        validate_mock.return_value = {"valid": True, "errors": []}
        hydrate_mock.return_value = {
            "schema_version": "0.1.0",
            "action": "skillsbench_hydration",
            "hydrated_paths": ["tasks/citation-check"],
        }
        import_mock.side_effect = [
            [
                {
                    "schema_version": "0.1.0",
                    "run_id": "skillsbench::attempt01",
                    "benchmark_name": "skillsbench",
                    "benchmark_version": "skillsbench-upstream",
                    "benchmark_split": "replay",
                    "phase": "T0",
                    "path_type": "oracle",
                    "model_name": "oracle",
                    "agent_name": "oracle",
                    "agent_version": "retry-suite",
                    "task_id": "citation-check",
                    "attempt_index": 0,
                    "score": 0.0,
                    "success": False,
                    "token_input": 0,
                    "token_output": 0,
                    "token_total": 0,
                    "tool_calls_total": 0,
                    "memory_reads": 0,
                    "memory_writes": 0,
                    "wall_clock_seconds": 1.0,
                    "cost_usd": 0.0,
                    "human_interventions": 0,
                    "seed": 17,
                    "started_at": "2026-04-18T01:00:00Z",
                    "finished_at": "2026-04-18T01:00:01Z",
                    "metadata": {
                        "exception_type": "EnvironmentStartTimeoutError",
                        "exception_message": "environment startup timed out",
                    },
                }
            ],
            [
                {
                    "schema_version": "0.1.0",
                    "run_id": "skillsbench::attempt02",
                    "benchmark_name": "skillsbench",
                    "benchmark_version": "skillsbench-upstream",
                    "benchmark_split": "replay",
                    "phase": "T0",
                    "path_type": "oracle",
                    "model_name": "oracle",
                    "agent_name": "oracle",
                    "agent_version": "retry-suite",
                    "task_id": "citation-check",
                    "attempt_index": 0,
                    "score": 1.0,
                    "success": True,
                    "token_input": 0,
                    "token_output": 0,
                    "token_total": 0,
                    "tool_calls_total": 0,
                    "memory_reads": 0,
                    "memory_writes": 0,
                    "wall_clock_seconds": 1.0,
                    "cost_usd": 0.0,
                    "human_interventions": 0,
                    "seed": 17,
                    "started_at": "2026-04-18T01:05:00Z",
                    "finished_at": "2026-04-18T01:05:01Z",
                    "metadata": {
                        "score_source": "verifier_rewards",
                    },
                }
            ],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_root = tmp_path / "benchmarks" / "skillsbench"
            repo_root.mkdir(parents=True, exist_ok=True)
            jobs_root = tmp_path / "jobs"

            def execute_side_effect(*args, **kwargs):
                plan_source = Path(kwargs["plan_source"])
                payload = json.loads(plan_source.read_text(encoding="utf-8"))
                command = payload["commands"]["replay"][0]
                job_name = command[command.index("--job-name") + 1]
                (jobs_root / job_name).mkdir(parents=True, exist_ok=True)
                return {
                    "schema_version": "0.1.0",
                    "summary": {"executed": 1, "status_counts": {"success": 1}, "halted_early": False},
                    "records": [],
                }

            execute_mock.side_effect = execute_side_effect
            config = {
                "schema_version": "0.1.0",
                "suite_name": "retry-suite",
                "benchmark_name": "skillsbench",
                "repo_root": str(repo_root),
                "registry_path": str(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json"),
                "out_root": str(tmp_path / "suite_out"),
                "execution": {
                    "agent": "oracle",
                    "model": None,
                    "harbor_bin": "harbor",
                    "jobs_dir": str(jobs_root),
                    "path_type": "oracle",
                    "agent_version": "retry-suite",
                    "seed": 17,
                    "extra_args": [],
                    "retry_policy": {
                        "max_attempts": 2,
                        "retry_on_exception_types": ["EnvironmentStartTimeoutError"],
                    },
                },
                "runs": [
                    {
                        "run_name": "t0_replay",
                        "phase": "T0",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                    }
                ],
            }
            config_path = tmp_path / "retry_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            report = run_skillsbench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=False,
            )

            run_report = report["runs"][0]
            self.assertEqual(run_report["attempt_count"], 2)
            self.assertEqual(run_report["selected_attempt"], 2)
            self.assertEqual(run_report["success_count"], 1)
            self.assertEqual(run_report["failure_count"], 0)
            self.assertEqual(run_report["job_name"], "retry-suite-t0_replay-attempt02")
            self.assertTrue(run_report["attempts"][0]["retry_decision"]["retry"])
            self.assertEqual(
                run_report["attempts"][0]["retry_decision"]["reason"],
                "exception_type:EnvironmentStartTimeoutError",
            )
            self.assertFalse(run_report["attempts"][1]["retry_decision"]["retry"])
            self.assertEqual(run_report["attempts"][1]["retry_decision"]["reason"], "non_failed_record_present")
            self.assertIn("attempt01", run_report["attempts"][0]["plan_path"])
            self.assertIn("attempt02", run_report["attempts"][1]["plan_path"])

            combined_runs = load_jsonl(Path(report["combined_runs_path"]))
            self.assertEqual(len(combined_runs), 1)
            self.assertTrue(combined_runs[0]["success"])
            self.assertEqual(combined_runs[0]["run_id"], "skillsbench::attempt02")
            self.assertEqual(import_mock.call_count, 2)
            self.assertEqual(execute_mock.call_count, 2)

    @patch("sip_bench.protocol_runner.validate_data_file")
    @patch("sip_bench.protocol_runner.import_skillsbench_job")
    @patch("sip_bench.protocol_runner.execute_command_plan")
    @patch("sip_bench.protocol_runner.hydrate_skillsbench_checkout")
    def test_run_skillsbench_suite_autodiscovers_local_env_file_for_execution(
        self,
        hydrate_mock,
        execute_mock,
        import_mock,
        validate_mock,
    ) -> None:
        validate_mock.return_value = {"valid": True, "errors": []}
        hydrate_mock.return_value = {
            "schema_version": "0.1.0",
            "action": "skillsbench_hydration",
            "hydrated_paths": ["tasks/citation-check"],
        }
        import_mock.return_value = [
            {
                "schema_version": "0.1.0",
                "run_id": "skillsbench::env-file",
                "benchmark_name": "skillsbench",
                "benchmark_version": "skillsbench-upstream",
                "benchmark_split": "replay",
                "phase": "T0",
                "path_type": "external",
                "model_name": "gpt-5.4",
                "agent_name": "codex",
                "agent_version": "env-suite",
                "task_id": "citation-check",
                "attempt_index": 0,
                "score": 0.0,
                "success": False,
                "token_input": 0,
                "token_output": 0,
                "token_total": 0,
                "tool_calls_total": 0,
                "memory_reads": 0,
                "memory_writes": 0,
                "wall_clock_seconds": 1.0,
                "cost_usd": 0.0,
                "human_interventions": 0,
                "seed": 19,
                "started_at": "2026-04-18T02:00:00Z",
                "finished_at": "2026-04-18T02:00:01Z",
                "metadata": {
                    "score_source": "exception_fallback",
                    "exception_type": "ValueError",
                    "exception_message": "Model name is required",
                },
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_path = tmp_path / ".env.local"
            env_path.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
            repo_root = tmp_path / "benchmarks" / "skillsbench"
            repo_root.mkdir(parents=True, exist_ok=True)
            jobs_root = tmp_path / "jobs"

            def execute_side_effect(*args, **kwargs):
                plan_source = Path(kwargs["plan_source"])
                payload = json.loads(plan_source.read_text(encoding="utf-8"))
                command = payload["commands"]["replay"][0]
                job_name = command[command.index("--job-name") + 1]
                (jobs_root / job_name).mkdir(parents=True, exist_ok=True)
                return {
                    "schema_version": "0.1.0",
                    "summary": {"executed": 1, "status_counts": {"success": 1}, "halted_early": False},
                    "records": [],
                }

            execute_mock.side_effect = execute_side_effect
            config = {
                "schema_version": "0.1.0",
                "suite_name": "skillsbench-env-suite",
                "benchmark_name": "skillsbench",
                "repo_root": str(repo_root),
                "registry_path": str(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json"),
                "out_root": str(tmp_path / "suite_out"),
                "execution": {
                    "agent": "codex",
                    "model": "gpt-5.4",
                    "harbor_bin": "harbor",
                    "jobs_dir": str(jobs_root),
                    "path_type": "external",
                    "agent_version": "env-suite",
                    "seed": 19,
                    "extra_args": [],
                },
                "runs": [
                    {
                        "run_name": "t0_replay",
                        "phase": "T0",
                        "benchmark_split": "replay",
                        "task_ids": ["citation-check"],
                    }
                ],
            }
            config_path = tmp_path / "skillsbench_env_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            report = run_skillsbench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=False,
            )

            self.assertTrue(report["runs_validation"]["valid"])
            execute_call = execute_mock.call_args
            self.assertEqual(execute_call.kwargs["env_overrides"]["OPENAI_API_KEY"], "test-key")
            self.assertEqual(report["runs"][0]["env_override_keys"], ["OPENAI_API_KEY"])
            self.assertEqual(report["runs"][0]["attempts"][0]["env_override_keys"], ["OPENAI_API_KEY"])

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

    @patch("sip_bench.protocol_runner.tau_bench_preflight")
    def test_run_tau_suite_autodiscovers_local_env_file_for_preflight(self, preflight_mock) -> None:
        preflight_mock.return_value = {
            "schema_version": "0.1.0",
            "action": "tau_bench_preflight",
            "ready": True,
            "required_env_vars": ["OPENAI_API_KEY"],
            "env_status": {"OPENAI_API_KEY": True},
            "env_override_keys": ["OPENAI_API_KEY"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_path = tmp_path / ".env.local"
            env_path.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
            config = {
                "schema_version": "0.1.0",
                "suite_name": "tau-env-suite",
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
                    "agent_version": "tau-env-suite",
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
                    }
                ],
            }
            config_path = tmp_path / "tau_env_suite.json"
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            report = run_tau_bench_suite(
                config_path=config_path,
                execute_mode="subprocess",
                aggregate=True,
            )
            self.assertTrue(report["runs_validation"]["valid"])
            first_call = preflight_mock.call_args_list[0]
            self.assertEqual(first_call.kwargs["env_overrides"]["OPENAI_API_KEY"], "test-key")
            self.assertEqual(report["runs"][0]["env_override_keys"], ["OPENAI_API_KEY"])

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

    def test_normalize_shell_scripts_rewrites_crlf_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_root = Path(tmpdir) / "tasks" / "dialogue-parser"
            tests_dir = task_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            script_path = tests_dir / "test.sh"
            script_path.write_bytes(b"#!/bin/bash\r\necho ok\r\n")

            patched_files = _normalize_shell_scripts(task_root)
            self.assertEqual(patched_files, [str(script_path)])
            self.assertEqual(script_path.read_bytes(), b"#!/bin/bash\necho ok\n")

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

    def test_apply_dialogue_parser_patch_adds_apt_retry_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_root = Path(tmpdir) / "tasks" / "dialogue-parser"
            dockerfile_path = task_root / "environment" / "Dockerfile"
            dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
            dockerfile_path.write_text(
                "FROM python:3.12.8-slim\n\n"
                "RUN pip install --no-cache-dir graphviz==0.20.3\n\n"
                "RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*\n",
                encoding="utf-8",
            )

            patched_files = _apply_task_patch(
                task_id="dialogue-parser",
                patch_name="dialogue_parser_apt_retry",
                task_root=task_root,
            )
            updated = dockerfile_path.read_text(encoding="utf-8")
            self.assertIn("Acquire::Retries=5", updated)
            self.assertIn("Acquire::http::Timeout=30", updated)
            self.assertIn("Acquire::https::Timeout=30", updated)
            self.assertIn("--fix-missing", updated)
            self.assertIn("graphviz", updated)
            self.assertEqual(patched_files, [str(dockerfile_path)])

    def test_apply_citation_check_patch_adds_apt_retry_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_root = Path(tmpdir) / "tasks" / "citation-check"
            dockerfile_path = task_root / "environment" / "Dockerfile"
            dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
            dockerfile_path.write_text(
                "FROM ubuntu:24.04\n\n"
                "RUN apt-get update && apt-get install -y \\\n"
                "    python3 \\\n"
                "    python3-pip \\\n"
                "    python3-venv \\\n"
                "    wget \\\n"
                "    curl \\\n"
                "    ca-certificates \\\n"
                "    && rm -rf /var/lib/apt/lists/*\n",
                encoding="utf-8",
            )

            patched_files = _apply_task_patch(
                task_id="citation-check",
                patch_name="citation_check_apt_retry",
                task_root=task_root,
            )
            updated = dockerfile_path.read_text(encoding="utf-8")
            self.assertIn("Acquire::Retries=5", updated)
            self.assertIn("Acquire::http::Timeout=30", updated)
            self.assertIn("Acquire::https::Timeout=30", updated)
            self.assertIn("--fix-missing", updated)
            self.assertIn("python3-venv", updated)
            self.assertEqual(patched_files, [str(dockerfile_path)])

    def test_apply_citation_check_python_runtime_patch_rewrites_dockerfile_and_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_root = Path(tmpdir) / "tasks" / "citation-check"
            dockerfile_path = task_root / "environment" / "Dockerfile"
            test_script_path = task_root / "tests" / "test.sh"
            test_script_path.parent.mkdir(parents=True, exist_ok=True)
            dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
            dockerfile_path.write_text("FROM ubuntu:24.04\n", encoding="utf-8")
            test_script_path.write_text("#!/bin/bash\napt-get update\n", encoding="utf-8")

            patched_files = _apply_task_patch(
                task_id="citation-check",
                patch_name="citation_check_python_runtime",
                task_root=task_root,
            )
            dockerfile_text = dockerfile_path.read_text(encoding="utf-8")
            test_script_text = test_script_path.read_text(encoding="utf-8")
            self.assertIn("FROM python:3.12.8-slim", dockerfile_text)
            self.assertIn("requests==2.32.3", dockerfile_text)
            self.assertIn("bibtexparser==1.4.2", dockerfile_text)
            self.assertNotIn("apt-get", dockerfile_text)
            self.assertIn("python3 -m pip install --no-cache-dir", test_script_text)
            self.assertIn("/logs/verifier/reward.txt", test_script_text)
            self.assertIn("pytest_output.txt", test_script_text)
            self.assertNotIn("apt-get", test_script_text)
            self.assertNotIn("uv", test_script_text)
            self.assertEqual(patched_files, [str(dockerfile_path), str(test_script_path)])

    def _make_single_trial_job_dir(self, job_dir: Path, *, fixture_relative_path: str) -> Path:
        source = ROOT / "tests" / "fixtures" / "skillsbench_harbor_job_sample" / fixture_relative_path
        trial_name = Path(fixture_relative_path).parts[0]
        target = job_dir / trial_name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target / "result.json")
        return job_dir


if __name__ == "__main__":
    unittest.main()
