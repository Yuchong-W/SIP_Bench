"""Offline protocol smoke demo; predictions never receive evaluation labels."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from sip_bench.adapters.medical import MedicalAdapter
from sip_bench.medical_runtime import RuleMemory, observations


def run_demo(source: str | Path):
    adapter = MedicalAdapter()
    tasks = adapter.discover_tasks(source)
    manifest = adapter.build_manifest(tasks, replay_count=2, adapt_count=2,
                                      heldout_count=2, drift_count=2, seed=7)
    adapter.validate_manifest(manifest)
    model = RuleMemory()
    runs = []
    for phase in ("T0", "T1", "T2"):
        if phase == "T1":
            for task in manifest.adapt:
                clinical = task.metadata["clinical"]
                model.adapt(observations(clinical), clinical["diagnosis"])
        for split in ("replay", "adapt", "heldout", "drift"):
            for task in getattr(manifest, split):
                clinical = task.metadata["clinical"]
                started = datetime.now(timezone.utc).isoformat()
                clock = perf_counter()
                prediction = model.predict(observations(clinical))
                elapsed = perf_counter() - clock
                safe, reason = adapter.safety_gate(clinical, prediction)
                success = prediction == clinical["diagnosis"] and safe
                runs.append({
                    "schema_version": "0.1.0", "run_id": f"medical::{phase}::{split}::{task.task_id}",
                    "benchmark_name": adapter.benchmark_name, "benchmark_version": "synthetic-v1",
                    "benchmark_split": split, "phase": phase, "path_type": "external",
                    "model_name": "deterministic-baseline", "agent_name": "medical-rule-agent",
                    "agent_version": "0.2", "task_id": task.task_id, "attempt_index": 0,
                    "score": float(success), "success": success, "token_input": 0,
                    "token_output": 0, "token_total": 0, "tool_calls_total": 0,
                    "memory_reads": 1, "memory_writes": 0, "wall_clock_seconds": elapsed,
                    "human_interventions": 0, "seed": 7, "started_at": started,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"prediction": prediction, "safety_gate_passed": safe,
                                 "failure_reason": reason or (None if success else "wrong_or_unknown"),
                                 "execution": "offline_rule_smoke", "training_split": "adapt",
                                 "adaptation_examples": len(manifest.adapt) if phase != "T0" else 0},
                })
    return manifest, runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="benchmarks/medical/cases.json")
    parser.add_argument("--out", default="results/medical_demo")
    args = parser.parse_args()
    manifest, runs = run_demo(args.cases)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in runs) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2))
    print(f"wrote {len(runs)} runs to {out}")


if __name__ == "__main__":
    main()
