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

from sip_bench.metrics import aggregate_runs, compute_protocol_metrics, load_jsonl


class MetricsCaseTests(unittest.TestCase):
    def test_metric_cases_match_expected_values(self) -> None:
        cases_path = ROOT / "tests" / "metric_cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))

        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                inputs = case["inputs"]
                outputs = compute_protocol_metrics(
                    t0_replay=inputs["t0_replay"],
                    t1_replay=inputs["t1_replay"],
                    t0_heldout=inputs["t0_heldout"],
                    t1_heldout=inputs["t1_heldout"],
                    t2_target=inputs["t2_target"],
                    cost=inputs["cost"],
                    lambda_penalty=inputs.get("lambda", 1.0),
                    eps=inputs.get("eps", 1e-6),
                )
                for metric_name, expected in case["expected"].items():
                    actual = outputs[metric_name]
                    if expected is None:
                        self.assertIsNone(actual)
                    else:
                        self.assertIsNotNone(actual)
                        self.assertAlmostEqual(float(actual), expected, places=8)


class AggregateRunsTests(unittest.TestCase):
    def test_aggregate_runs_returns_expected_summary(self) -> None:
        records = []
        records.extend(
            self._seed_records(
                seed=0,
                replay_t0=0.40,
                replay_t1=0.55,
                heldout_t0=0.30,
                heldout_t1=0.50,
                t2_target=0.48,
                adapt_cost=100,
            )
        )
        records.extend(
            self._seed_records(
                seed=1,
                replay_t0=0.80,
                replay_t1=0.50,
                heldout_t0=0.20,
                heldout_t1=0.35,
                t2_target=0.33,
                adapt_cost=50,
            )
        )

        summaries = aggregate_runs(records, cost_field="token_total")
        self.assertEqual(len(summaries), 1)

        summary = summaries[0]
        self.assertEqual(summary["benchmark_name"], "skillsbench")
        self.assertEqual(summary["path_type"], "external")
        self.assertEqual(summary["repeats"], 2)
        self.assertEqual(summary["sample_sizes"]["adapt"], 2)
        self.assertAlmostEqual(summary["metrics"]["fg_mean"], 0.175, places=8)
        self.assertAlmostEqual(summary["metrics"]["br_mean"], -0.075, places=8)
        self.assertAlmostEqual(summary["metrics"]["br_ratio_mean"], 1.0, places=8)
        self.assertAlmostEqual(summary["metrics"]["ie_mean"], 0.0025, places=8)
        self.assertAlmostEqual(summary["metrics"]["pds_mean"], -0.02, places=8)
        self.assertAlmostEqual(summary["metrics"]["nis_mean"], 0.025, places=8)
        self.assertAlmostEqual(summary["costs"]["token_total_mean"], 75.0, places=8)

    def test_missing_t2_emits_null_pds_fields(self) -> None:
        records = self._seed_records(
            seed=0,
            replay_t0=0.50,
            replay_t1=0.55,
            heldout_t0=0.20,
            heldout_t1=0.30,
            t2_target=None,
            adapt_cost=40,
        )

        summary = aggregate_runs(records, cost_field="token_total")[0]
        self.assertIsNone(summary["metrics"]["t2_heldout_mean"])
        self.assertIsNone(summary["metrics"]["t2_replay_mean"])
        self.assertIsNone(summary["metrics"]["pds_mean"])
        self.assertIsNone(summary["metrics"]["pds_std"])

    def test_zero_cost_emits_null_ie_fields(self) -> None:
        records = self._seed_records(
            seed=0,
            replay_t0=0.30,
            replay_t1=0.35,
            heldout_t0=0.30,
            heldout_t1=0.40,
            t2_target=0.39,
            adapt_cost=0,
        )

        summary = aggregate_runs(records, cost_field="token_total")[0]
        self.assertIsNone(summary["metrics"]["ie_mean"])
        self.assertIsNone(summary["metrics"]["ie_std"])

    def test_load_jsonl_round_trip_on_sample_file(self) -> None:
        sample_path = ROOT / "results" / "dryrun" / "sample_runs.jsonl"
        records = load_jsonl(sample_path)
        self.assertGreater(len(records), 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "summary.jsonl"
            summaries = aggregate_runs(records)
            tmp_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=True) for item in summaries) + "\n",
                encoding="utf-8",
            )
            written_records = load_jsonl(tmp_path)
            self.assertEqual(len(written_records), 1)
            self.assertEqual(written_records[0]["benchmark_name"], "skillsbench")

    def _seed_records(
        self,
        *,
        seed: int,
        replay_t0: float,
        replay_t1: float,
        heldout_t0: float,
        heldout_t1: float,
        t2_target: float | None,
        adapt_cost: int,
    ) -> list[dict[str, object]]:
        base = {
            "schema_version": "0.1.0",
            "benchmark_name": "skillsbench",
            "benchmark_version": "demo-v0",
            "path_type": "external",
            "model_name": "gpt-5-mini",
            "agent_name": "sip-bench-demo",
            "agent_version": "0.1.0",
            "attempt_index": 0,
            "success": True,
            "token_input": 10,
            "token_output": 5,
            "tool_calls_total": 1,
            "memory_reads": 0,
            "memory_writes": 0,
            "wall_clock_seconds": 1.0,
            "cost_usd": 0.0,
            "human_interventions": 0,
            "seed": seed,
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "metadata": {},
        }
        records = [
            self._record(base, run_id=f"{seed}-t0-replay", phase="T0", benchmark_split="replay", task_id=f"replay-{seed}", score=replay_t0, token_total=15),
            self._record(base, run_id=f"{seed}-t1-replay", phase="T1", benchmark_split="replay", task_id=f"replay-{seed}", score=replay_t1, token_total=15),
            self._record(base, run_id=f"{seed}-t0-heldout", phase="T0", benchmark_split="heldout", task_id=f"heldout-{seed}", score=heldout_t0, token_total=15),
            self._record(base, run_id=f"{seed}-t1-heldout", phase="T1", benchmark_split="heldout", task_id=f"heldout-{seed}", score=heldout_t1, token_total=15),
            self._record(base, run_id=f"{seed}-t1-adapt", phase="T1", benchmark_split="adapt", task_id=f"adapt-{seed}", score=1.0, token_total=adapt_cost),
        ]
        if t2_target is not None:
            records.append(
                self._record(
                    base,
                    run_id=f"{seed}-t2-heldout",
                    phase="T2",
                    benchmark_split="heldout",
                    task_id=f"heldout-{seed}",
                    score=t2_target,
                    token_total=15,
                )
            )
        return records

    def _record(self, base: dict[str, object], **updates: object) -> dict[str, object]:
        record = dict(base)
        record.update(updates)
        record["token_total"] = updates.get(
            "token_total",
            int(record["token_input"]) + int(record["token_output"]),
        )
        return record


if __name__ == "__main__":
    unittest.main()
