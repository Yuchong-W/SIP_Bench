from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

from scripts.run_release_checks import (
    OPTIONAL_HISTORICAL_ARTIFACTS,
    REQUIRED_RELEASE_SCHEMA_ASSETS,
    _run_result_only_suite_check,
    release_artifact_gate,
)

ROOT = Path(__file__).resolve().parents[1]


class ReleaseArtifactGateTests(unittest.TestCase):
    def test_result_only_suite_report_has_schema_counts_hashes_cost_and_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = _run_result_only_suite_check(
                config_path=ROOT / "protocol" / "medical_synthetic_suite.json",
                output_root=Path(tmpdir),
                python_bin=sys.executable,
            )

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["run_count"], 12)
        self.assertEqual(report["record_count"], 24)
        self.assertEqual(len(report["artifact_hashes"]), 3)
        self.assertIn("wall_clock_seconds", report["costs"])
        self.assertTrue(report["failure_families"])

    def _write(self, root: Path, path: Path) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n", encoding="utf-8")

    def test_missing_required_asset_fails_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for path in REQUIRED_RELEASE_SCHEMA_ASSETS[1:]:
                self._write(root, path)
            gate = release_artifact_gate(root)
        self.assertFalse(gate["required_schema_assets_present"])
        self.assertEqual(gate["missing_required"], [str(REQUIRED_RELEASE_SCHEMA_ASSETS[0])])

    def test_missing_optional_history_is_reported_without_failing_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for path in REQUIRED_RELEASE_SCHEMA_ASSETS:
                self._write(root, path)
            gate = release_artifact_gate(root)
        self.assertTrue(gate["required_schema_assets_present"])
        self.assertEqual(gate["missing_optional_historical"], [str(path) for path in OPTIONAL_HISTORICAL_ARTIFACTS])
