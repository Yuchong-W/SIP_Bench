from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import sip_bench.adapters as adapters
from sip_bench.adapters import BenchmarkAdapter, MockBenchAdapter, SkillsBenchAdapter, TauBenchAdapter


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

    def test_filter_tasks_by_task_ids(self) -> None:
        adapter = SkillsBenchAdapter()
        tasks = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json")
        filtered = adapter.filter_tasks(tasks, task_ids={"citation-check", "court-form-filling"})
        self.assertEqual({task.task_id for task in filtered}, {"citation-check", "court-form-filling"})
        with self.assertRaises(ValueError):
            adapter.filter_tasks(tasks, task_ids={"missing-task"})

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

    def test_build_harbor_command_supports_agent_import_path(self) -> None:
        adapter = SkillsBenchAdapter()
        task = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json")[0]
        command = adapter.build_harbor_command(
            repo_root="benchmarks/skillsbench",
            task=task,
            agent="codex",
            model="gpt-5.4",
            agent_import_path="sip_bench.harbor_codex_host_agent:CodexLocalAuthAgent",
            harbor_bin="harbor",
        )
        self.assertIn("--agent-import-path", command)
        self.assertIn("sip_bench.harbor_codex_host_agent:CodexLocalAuthAgent", command)

    def test_parse_result_file_infers_path_types_and_registry_metadata(self) -> None:
        adapter = SkillsBenchAdapter()
        runs = adapter.parse_result_file(
            ROOT / "tests" / "fixtures" / "skillsbench_results_sample.json",
            benchmark_split="golden",
            phase="T1",
            seed=5,
            registry_source=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
            agent_version="fixture-import",
            benchmark_version="skillsbench-fixture",
        )
        self.assertEqual(len(runs), 4)
        self.assertEqual(runs[0]["path_type"], "frozen")
        self.assertEqual(runs[1]["path_type"], "external")
        self.assertEqual(runs[3]["path_type"], "external")
        self.assertEqual(runs[1]["score"], 0.7)
        self.assertEqual(runs[1]["tool_calls_total"], 2)
        self.assertEqual(runs[0]["task_template_id"], "1.0")
        self.assertEqual(runs[0]["metadata"]["category"], "research")
        self.assertEqual(runs[0]["metadata"]["task_source_path"], "tasks/citation-check")

    def test_parse_result_file_condition_filter_and_attempt_index(self) -> None:
        adapter = SkillsBenchAdapter()
        runs = adapter.parse_result_file(
            ROOT / "tests" / "fixtures" / "skillsbench_results_sample.json",
            benchmark_split="heldout",
            phase="T1",
            seed=7,
            registry_source=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
            conditions={"withskills"},
        )
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]["attempt_index"], 0)
        self.assertEqual(runs[1]["attempt_index"], 1)
        self.assertTrue(all(run["path_type"] == "external" for run in runs))
        self.assertEqual(runs[0]["started_at"], "2026-01-29T08:00:00Z")
        self.assertEqual(runs[0]["finished_at"], "2026-01-29T08:00:30Z")

    def test_parse_harbor_job_dir_maps_success_and_failure(self) -> None:
        adapter = SkillsBenchAdapter()
        runs = adapter.parse_harbor_job_dir(
            ROOT / "tests" / "fixtures" / "skillsbench_harbor_job_sample",
            benchmark_split="smoke",
            phase="T0",
            path_type="oracle",
            seed=19,
            registry_source=ROOT / "tests" / "fixtures" / "skillsbench_registry_sample.json",
            benchmark_version="skillsbench-harbor-fixture",
        )
        self.assertEqual(len(runs), 2)
        by_task = {run["task_id"]: run for run in runs}
        self.assertTrue(by_task["citation-check"]["success"])
        self.assertEqual(by_task["citation-check"]["score"], 1.0)
        self.assertEqual(by_task["citation-check"]["token_total"], 42)
        self.assertEqual(by_task["citation-check"]["tool_calls_total"], 3)
        self.assertFalse(by_task["court-form-filling"]["success"])
        self.assertEqual(by_task["court-form-filling"]["score"], 0.0)
        self.assertEqual(by_task["court-form-filling"]["metadata"]["exception_type"], "RuntimeError")


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
            benchmark_split="heldout",
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


class MockBenchAdapterTests(unittest.TestCase):
    def test_discover_tasks_supports_dict_and_list_inputs(self) -> None:
        adapter = MockBenchAdapter()
        tasks = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "mock_tasks_sample.json")
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].task_id, "mock-qa")

    def test_build_run_command_includes_import_path(self) -> None:
        adapter = MockBenchAdapter()
        task = adapter.discover_tasks(ROOT / "tests" / "fixtures" / "mock_tasks_sample.json")[0]
        command = adapter.build_run_command(
            repo_root=".",
            task=task,
            model="gpt-5.4",
            python_bin="python3",
            agent_import_path="mock.module:Agent",
            extra_args=["--max-steps", "4"],
        )
        self.assertEqual(command[:2], ["python3", "-c"])
        self.assertIn("mock-bench task=mock-qa model=gpt-5.4", command[2])
        self.assertIn("--agent-import-path", command)
        self.assertIn("mock.module:Agent", command)

    def test_parse_result_file_filters_and_assigns_attempt_indices(self) -> None:
        adapter = MockBenchAdapter()
        runs = adapter.parse_result_file(
            ROOT / "tests" / "fixtures" / "mock_results_sample.json",
            benchmark_split="replay",
            phase="T0",
            seed=17,
            path_type="oracle",
            task_ids={"mock-qa"},
            model_name="fixture-model",
            agent_name="fixture-agent",
        )
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]["task_id"], "mock-qa")
        self.assertEqual(runs[0]["attempt_index"], 0)
        self.assertEqual(runs[1]["attempt_index"], 1)
        self.assertEqual(runs[0]["model_name"], "fixture-model")
        self.assertEqual(runs[1]["path_type"], "external")
        self.assertFalse(runs[1]["success"])


if __name__ == "__main__":
    unittest.main()


class AdapterAgnosticContractTests(unittest.TestCase):
    def test_adapters_expose_protocol_contract_methods(self) -> None:
        adapter_names = [
            name
            for name in adapters.__all__
            if name.endswith("Adapter") and name != "BenchmarkAdapter"
        ]

        for name in adapter_names:
            adapter_cls = getattr(adapters, name)
            self.assertTrue(inspect.isclass(adapter_cls), f"{name} should be a class")
            self.assertTrue(
                issubclass(adapter_cls, BenchmarkAdapter),
                f"{name} should inherit BenchmarkAdapter",
            )

            adapter = adapter_cls()
            self.assertTrue(hasattr(adapter, "discover_tasks"))
            self.assertTrue(callable(getattr(adapter, "discover_tasks")))
            self.assertTrue(hasattr(adapter, "build_manifest"))
            self.assertTrue(callable(getattr(adapter, "build_manifest")))
            self.assertTrue(hasattr(adapter, "validate_manifest"))

            has_build_plan = hasattr(adapter, "build_harbor_command") and callable(getattr(adapter, "build_harbor_command"))
            has_build_run = hasattr(adapter, "build_run_command") and callable(getattr(adapter, "build_run_command"))
            self.assertTrue(
                has_build_plan or has_build_run,
                f"{name} must expose build_harbor_command or build_run_command",
            )

            has_importer = (
                hasattr(adapter, "parse_result_file") and callable(getattr(adapter, "parse_result_file"))
                or hasattr(adapter, "parse_harbor_job_dir")
                and callable(getattr(adapter, "parse_harbor_job_dir"))
            )
            self.assertTrue(
                has_importer,
                f"{name} must expose parse_result_file or parse_harbor_job_dir",
            )
