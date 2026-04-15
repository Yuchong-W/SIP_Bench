from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.runner import (
    build_skillsbench_plan,
    execute_command_plan,
    import_skillsbench_results,
    import_tau_results,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or import benchmark runs for SIP-Bench."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    skillsbench = subparsers.add_parser(
        "plan-skillsbench",
        help="Build a split manifest and per-task Harbor commands for SkillsBench.",
    )
    skillsbench.add_argument("--registry", required=True, help="Path to SkillsBench task registry JSON.")
    skillsbench.add_argument("--repo-root", required=True, help="Path to local SkillsBench checkout root.")
    skillsbench.add_argument("--replay-count", type=int, required=True)
    skillsbench.add_argument("--adapt-count", type=int, required=True)
    skillsbench.add_argument("--heldout-count", type=int, required=True)
    skillsbench.add_argument("--drift-count", type=int, default=0)
    skillsbench.add_argument("--seed", type=int, default=0)
    skillsbench.add_argument("--agent", default="oracle")
    skillsbench.add_argument("--model")
    skillsbench.add_argument("--harbor-bin", default="harbor")
    skillsbench.add_argument("--category", action="append", default=[], help="Repeatable category filter.")
    skillsbench.add_argument("--difficulty", action="append", default=[], help="Repeatable difficulty filter.")
    skillsbench.add_argument("--extra-arg", action="append", default=[], help="Repeatable extra Harbor argument.")
    skillsbench.add_argument("--out", required=True, help="Path to write plan JSON.")

    execute_plan = subparsers.add_parser(
        "execute-plan",
        help="Execute or mock-execute commands from a plan JSON and write an execution report.",
    )
    execute_plan.add_argument("--plan", required=True, help="Path to plan JSON.")
    execute_plan.add_argument("--out", required=True, help="Path to execution report JSON.")
    execute_plan.add_argument("--split", default="all", choices=["all", "replay", "adapt", "heldout", "drift"])
    execute_plan.add_argument("--mode", default="mock", choices=["mock", "subprocess"])
    execute_plan.add_argument("--artifacts-dir", help="Optional directory for stdout/stderr artifacts.")
    execute_plan.add_argument("--cwd", help="Optional working directory for subprocess execution.")
    execute_plan.add_argument("--max-tasks", type=int)
    execute_plan.add_argument("--fail-fast", action="store_true")

    tau_import = subparsers.add_parser(
        "import-tau-results",
        help="Convert tau-bench result JSON into SIP-Bench runs.jsonl records.",
    )
    tau_import.add_argument("--source", required=True, help="Path to tau-bench result JSON.")
    tau_import.add_argument("--out", required=True, help="Path to output runs.jsonl.")
    tau_import.add_argument("--env", required=True, choices=["retail", "airline"])
    tau_import.add_argument("--task-split", required=True, choices=["train", "dev", "test"])
    tau_import.add_argument(
        "--benchmark-split",
        required=True,
        choices=["replay", "adapt", "heldout", "drift", "smoke", "golden"],
        help="SIP-Bench protocol split label for these imported runs.",
    )
    tau_import.add_argument("--phase", required=True, choices=["T0", "T1", "T2"])
    tau_import.add_argument("--path-type", required=True, choices=["frozen", "external", "parameter", "oracle"])
    tau_import.add_argument("--model-name", required=True)
    tau_import.add_argument("--agent-name", required=True)
    tau_import.add_argument("--agent-version", required=True)
    tau_import.add_argument("--seed", required=True, type=int)

    skillsbench_import = subparsers.add_parser(
        "import-skillsbench-results",
        help="Convert SkillsBench trajectory/result JSON into SIP-Bench runs.jsonl records.",
    )
    skillsbench_import.add_argument("--source", required=True, help="Path to SkillsBench trajectories JSON.")
    skillsbench_import.add_argument("--out", required=True, help="Path to output runs.jsonl.")
    skillsbench_import.add_argument(
        "--benchmark-split",
        required=True,
        choices=["replay", "adapt", "heldout", "drift", "smoke", "golden"],
    )
    skillsbench_import.add_argument("--phase", required=True, choices=["T0", "T1", "T2"])
    skillsbench_import.add_argument("--seed", required=True, type=int)
    skillsbench_import.add_argument("--registry", help="Optional explicit path to tasks-registry.json.")
    skillsbench_import.add_argument("--repo-root", help="Optional SkillsBench checkout root for registry and git revision discovery.")
    skillsbench_import.add_argument("--path-type", choices=["frozen", "external", "parameter", "oracle"])
    skillsbench_import.add_argument("--model-name", help="Optional override for model_name.")
    skillsbench_import.add_argument("--agent-name", help="Optional override for agent_name.")
    skillsbench_import.add_argument("--agent-version", default="upstream-import")
    skillsbench_import.add_argument("--benchmark-version", help="Optional override for benchmark_version.")
    skillsbench_import.add_argument(
        "--condition",
        action="append",
        default=[],
        help="Optional repeatable filter over SkillsBench conditions such as noskills, withskills, gen.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "plan-skillsbench":
        payload = build_skillsbench_plan(
            registry_path=args.registry,
            repo_root=args.repo_root,
            replay_count=args.replay_count,
            adapt_count=args.adapt_count,
            heldout_count=args.heldout_count,
            drift_count=args.drift_count,
            seed=args.seed,
            agent=args.agent,
            model=args.model,
            harbor_bin=args.harbor_bin,
            categories=set(args.category) if args.category else None,
            difficulties=set(args.difficulty) if args.difficulty else None,
            extra_args=args.extra_arg or None,
        )
        write_json(args.out, payload)
        print(
            json.dumps(
                {
                    "command": args.command,
                    "out": args.out,
                    "counts": payload["manifest"]["counts"],
                    "filtered_tasks": payload["selection"]["filtered_tasks"],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "execute-plan":
        report = execute_command_plan(
            plan_source=args.plan,
            out=args.out,
            split=args.split,
            mode=args.mode,
            artifacts_dir=args.artifacts_dir,
            fail_fast=args.fail_fast,
            cwd=args.cwd,
            max_tasks=args.max_tasks,
        )
        print(
            json.dumps(
                {
                    "command": args.command,
                    "out": args.out,
                    "executed": report["summary"]["executed"],
                    "status_counts": report["summary"]["status_counts"],
                    "halted_early": report["summary"]["halted_early"],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "import-tau-results":
        runs = import_tau_results(
            source=args.source,
            out=args.out,
            env=args.env,
            task_split=args.task_split,
            benchmark_split=args.benchmark_split,
            phase=args.phase,
            path_type=args.path_type,
            model_name=args.model_name,
            agent_name=args.agent_name,
            agent_version=args.agent_version,
            seed=args.seed,
        )
        print(
            json.dumps(
                {
                    "command": args.command,
                    "out": args.out,
                    "runs": len(runs),
                    "env": args.env,
                    "task_split": args.task_split,
                    "benchmark_split": args.benchmark_split,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "import-skillsbench-results":
        runs = import_skillsbench_results(
            source=args.source,
            out=args.out,
            benchmark_split=args.benchmark_split,
            phase=args.phase,
            seed=args.seed,
            registry_source=args.registry,
            repo_root=args.repo_root,
            path_type=args.path_type,
            model_name=args.model_name,
            agent_name=args.agent_name,
            agent_version=args.agent_version,
            benchmark_version=args.benchmark_version,
            conditions=set(args.condition) if args.condition else None,
        )
        print(
            json.dumps(
                {
                    "command": args.command,
                    "out": args.out,
                    "runs": len(runs),
                    "benchmark_split": args.benchmark_split,
                    "phase": args.phase,
                    "conditions": args.condition,
                },
                indent=2,
            )
        )
        return 0

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
