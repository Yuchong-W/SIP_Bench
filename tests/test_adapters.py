from __future__ import annotations

import inspect
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

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


@unittest.skipUnless(adapters.EVOAGENTBENCH_AVAILABLE, "optional EvoAgentBench adapter is not installed")
class EvoAgentBenchAdapterTests(unittest.TestCase):
    def test_build_run_command_and_parse_result_filter(self) -> None:
        adapter = adapters.require_evoagentbench_adapter()()
        command = adapter.build_run_command(
            repo_root="benchmarks/EvoAgentBench",
            domain="omni_math",
            split="test",
            task_ids=["omni_demo_01"],
            agent="nanobot",
            model="gpt-5.4-mini",
            python_bin="python3.12",
            config_path="config.yaml",
            job_name="omni-demo",
        )
        self.assertEqual(command[:2], ["python3.12", str(Path("benchmarks/EvoAgentBench") / "src" / "run.py")])
        self.assertIn("--job", command)
        self.assertIn("omni-demo", command)
        self.assertIn("--task", command)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first_dir = root / "omni_demo_01"
            second_dir = root / "omni_demo_02"
            first_dir.mkdir()
            second_dir.mkdir()
            (first_dir / "result.json").write_text(
                '{"task_name":"omni_demo_01","trial":1,"attempt":1,"started_at":"2026-04-20T00:00:00Z","ended_at":"2026-04-20T00:00:10Z","agent_result":{"elapsed_sec":10.0,"completion_status":"completed","token_usage":{"turns":2,"input":10,"output":20,"total":30}},"verifier_result":{"reward":1.0,"method":"exact"}}\n',
                encoding="utf-8",
            )
            (second_dir / "result.json").write_text(
                '{"task_name":"omni_demo_02","trial":1,"attempt":1,"started_at":"2026-04-20T00:01:00Z","ended_at":"2026-04-20T00:01:10Z","agent_result":{"elapsed_sec":10.0,"completion_status":"completed","token_usage":{"turns":1,"input":5,"output":10,"total":15}},"verifier_result":{"reward":0.0,"method":"exact"}}\n',
                encoding="utf-8",
            )

            runs = adapter.parse_result_file(
                root,
                domain="omni_math",
                benchmark_split="heldout",
                phase="T1",
                path_type="external",
                model_name="gpt-5.4-mini",
                agent_name="nanobot",
                agent_version="fixture-strategy",
                seed=3,
                task_ids={"omni_demo_01"},
            )

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["task_id"], "omni_demo_01")
        self.assertTrue(runs[0]["success"])
        self.assertEqual(runs[0]["token_total"], 30)

    def test_parse_result_file_prefers_completed_attempt_and_falls_back_to_top_level_usage(self) -> None:
        adapter = adapters.require_evoagentbench_adapter()()
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "omni_demo_03"
            task_dir.mkdir()
            (task_dir / "result.json").write_text(
                (
                    '{"task_name":"omni_demo_03","trial":1,"attempt":2,'
                    '"started_at":"2026-04-20T00:02:00Z","ended_at":"2026-04-20T00:02:10Z",'
                    '"agent_result":{"elapsed_sec":10.0,"completion_status":"completed"},'
                    '"token_usage":{"turns":3,"input":7,"output":11,"total":18},'
                    '"verifier_result":{"reward":1.0,"method":"exact"}}\n'
                ),
                encoding="utf-8",
            )
            stale_dir = task_dir / "retry_attempt_0"
            stale_dir.mkdir()
            (stale_dir / "result.json").write_text(
                (
                    '{"task_name":"omni_demo_03","trial":1,"attempt":1,'
                    '"started_at":"2026-04-20T00:01:00Z","ended_at":"2026-04-20T00:01:10Z",'
                    '"agent_result":{"elapsed_sec":0.0,"completion_status":"unknown"},'
                    '"verifier_result":{"reward":0.0,"method":"exact"}}\n'
                ),
                encoding="utf-8",
            )

            runs = adapter.parse_result_file(
                Path(tmpdir),
                domain="omni_math",
                benchmark_split="heldout",
                phase="T1",
                path_type="external",
                model_name="gpt-5.2",
                agent_name="codex",
                agent_version="baseline",
                seed=0,
            )

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["task_id"], "omni_demo_03")
        self.assertEqual(runs[0]["attempt_index"], 1)
        self.assertEqual(runs[0]["token_input"], 7)
        self.assertEqual(runs[0]["token_output"], 11)
        self.assertEqual(runs[0]["token_total"], 18)

    def test_parse_result_file_falls_back_to_session_usage_when_result_omits_tokens(self) -> None:
        adapter = adapters.require_evoagentbench_adapter()()
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "omni_demo_04"
            task_dir.mkdir()
            (task_dir / "result.json").write_text(
                (
                    '{"task_name":"omni_demo_04","trial":1,"attempt":1,'
                    '"started_at":"2026-04-20T00:03:00Z","ended_at":"2026-04-20T00:03:10Z",'
                    '"agent_result":{"elapsed_sec":10.0,"completion_status":"completed"},'
                    '"verifier_result":{"reward":0.0,"method":"exact"}}\n'
                ),
                encoding="utf-8",
            )
            (task_dir / "session.jsonl").write_text(
                (
                    '{"type":"thread.started"}\n'
                    '{"type":"turn.completed","usage":{"input_tokens":13,"output_tokens":21}}\n'
                ),
                encoding="utf-8",
            )

            runs = adapter.parse_result_file(
                task_dir / "result.json",
                domain="omni_math",
                benchmark_split="drift",
                phase="T2",
                path_type="external",
                model_name="gpt-5.2",
                agent_name="codex",
                agent_version="baseline",
                seed=0,
            )

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["token_input"], 13)
        self.assertEqual(runs[0]["token_output"], 21)
        self.assertEqual(runs[0]["token_total"], 34)


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
            has_local_evaluator = hasattr(adapter, "trajectory") and callable(getattr(adapter, "trajectory"))
            self.assertTrue(
                has_build_plan or has_build_run or has_local_evaluator,
                f"{name} must expose a command builder or local trajectory evaluator",
            )

            has_importer = (
                hasattr(adapter, "parse_result_file") and callable(getattr(adapter, "parse_result_file"))
                or hasattr(adapter, "parse_harbor_job_dir")
                and callable(getattr(adapter, "parse_harbor_job_dir"))
                or has_local_evaluator
            )
            self.assertTrue(
                has_importer,
                f"{name} must expose an importer or local trajectory evaluator",
            )

    def test_missing_optional_adapter_has_actionable_error(self) -> None:
        if adapters.EVOAGENTBENCH_AVAILABLE:
            self.skipTest("optional adapter is installed")
        with self.assertRaisesRegex(RuntimeError, "optional adapter package"):
            adapters.require_evoagentbench_adapter()

    def test_optional_adapter_loader_distinguishes_absence_from_internal_failure(self) -> None:
        module_name = "sip_bench.adapters.evoagentbench"
        absent = ModuleNotFoundError("module absent")
        absent.name = module_name
        with patch.object(adapters, "import_module", side_effect=absent):
            self.assertIsNone(adapters._load_evoagentbench_adapter())

        installed = types.SimpleNamespace(EvoAgentBenchAdapter=MockBenchAdapter)
        with patch.object(adapters, "import_module", return_value=installed):
            self.assertIs(adapters._load_evoagentbench_adapter(), MockBenchAdapter)

        internal = ModuleNotFoundError("jsonschema missing")
        internal.name = "jsonschema"
        with patch.object(adapters, "import_module", side_effect=internal):
            with self.assertRaisesRegex(ModuleNotFoundError, "jsonschema missing"):
                adapters._load_evoagentbench_adapter()

    def test_optional_adapter_is_exported_when_available(self) -> None:
        self.assertIn("EvoAgentBenchAdapter", adapters._public_adapter_exports(True))
        self.assertNotIn("EvoAgentBenchAdapter", adapters._public_adapter_exports(False))
