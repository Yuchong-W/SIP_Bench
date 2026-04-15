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

from sip_bench.validation import validate_data_file


class ValidationTests(unittest.TestCase):
    def test_validate_runs_sample(self) -> None:
        report = validate_data_file(
            data_path=ROOT / "results" / "dryrun" / "sample_runs.jsonl",
            schema_path=ROOT / "schemas" / "runs.schema.json",
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["records_checked"], 12)

    def test_validate_summary_sample(self) -> None:
        report = validate_data_file(
            data_path=ROOT / "results" / "dryrun" / "summary.jsonl",
            schema_path=ROOT / "schemas" / "summary.schema.json",
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["records_checked"], 1)

    def test_invalid_run_is_caught(self) -> None:
        bad_record = {
            "schema_version": "0.1.0",
            "run_id": "bad-run",
            "benchmark_name": "skillsbench"
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_runs.jsonl"
            path.write_text(json.dumps(bad_record) + "\n", encoding="utf-8")
            report = validate_data_file(
                data_path=path,
                schema_path=ROOT / "schemas" / "runs.schema.json",
            )
            self.assertFalse(report["valid"])
            self.assertGreater(report["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
