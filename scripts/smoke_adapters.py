from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.adapters import SkillsBenchAdapter, TauBenchAdapter


def main() -> int:
    fixtures = ROOT / "tests" / "fixtures"

    skills_adapter = SkillsBenchAdapter()
    skills_tasks = skills_adapter.discover_tasks(fixtures / "skillsbench_registry_sample.json")
    skills_manifest = skills_adapter.build_manifest(
        skills_tasks,
        replay_count=2,
        adapt_count=2,
        heldout_count=2,
        seed=7,
    )
    skills_adapter.validate_manifest(skills_manifest)
    example_task = skills_manifest.heldout[0]

    tau_adapter = TauBenchAdapter()
    tau_manifest = tau_adapter.build_manifest_from_ids(
        env="retail",
        task_split="test",
        replay_ids=[1, 2],
        adapt_ids=[3],
        heldout_ids=[4, 5],
    )
    tau_adapter.validate_manifest(tau_manifest)
    tau_runs = tau_adapter.parse_result_file(
        fixtures / "tau_results_sample.json",
        env="retail",
        task_split="test",
        phase="T0",
        path_type="frozen",
        model_name="gpt-5-mini",
        agent_name="tau-smoke",
        agent_version="0.1.0",
        seed=10,
    )

    print(
        json.dumps(
            {
                "skillsbench_manifest_counts": skills_manifest.counts(),
                "skillsbench_example_command": skills_adapter.build_harbor_command(
                    repo_root="benchmarks/skillsbench",
                    task=example_task,
                    agent="oracle",
                    harbor_bin="harbor",
                ),
                "tau_manifest_counts": tau_manifest.counts(),
                "tau_example_command": tau_adapter.build_run_command(
                    repo_root="benchmarks/tau-bench",
                    env="retail",
                    task_split="test",
                    task_ids=[4, 5],
                    model="gpt-4o",
                    model_provider="openai",
                    user_model="gpt-4o",
                    user_model_provider="openai",
                ),
                "tau_parsed_runs": len(tau_runs),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
