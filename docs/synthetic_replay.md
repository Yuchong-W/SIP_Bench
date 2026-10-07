# Synthetic diagnosis replay bridge

This experimental bridge checks source ingestion, patient isolation and offline
artifact replay. It does not measure clinical quality. The checked-in fixtures
are authored examples with fictional cues and labels, not Synthea simulator
output. No provider, external model or credentials are used.

```bash
python3 scripts/run_synthetic_replay.py \
  --source tests/fixtures/synthetic_replay/cases.json \
  --source-manifest tests/fixtures/synthetic_replay/cases.source.json \
  --out /tmp/sip-synthetic-replay
python3 scripts/run_synthetic_replay.py \
  --source tests/fixtures/synthetic_replay/cases.json \
  --source-manifest tests/fixtures/synthetic_replay/cases.source.json \
  --out /tmp/sip-synthetic-replay --verify
```

The default split requests one **patient** per split. Set `--adapt-patients`,
`--replay-patients`, `--heldout-patients` and `--drift-patients` for a larger source;
their sum must cover every source patient exactly. Every encounter for a patient
stays in the same split. Patient groups are ordered by SHA-256 of the canonical
JSON `[partition_seed, patient_id]`; input case order does not affect assignment.
At least one adaptation patient and one evaluation patient are required.

## Frozen source declaration

The sidecar declares the source generator, version, integer generator seed and
SHA-256 of the exact source bytes:

```json
{
  "schema_version": 1,
  "synthetic": true,
  "source": {
    "sha256": "<64 lowercase hex digits matching the file>",
    "format": "compact-json",
    "generator": "sip-bench-authored-fixture",
    "version": "1",
    "seed": 0
  }
}
```

`synthetic: true` is an explicit operator attestation, not a PHI detector. Only
synthetic data may enter this research path. Declaring a source synthetic does
not establish its origin, license or privacy status; use known synthetic exports
and preserve their generating configuration.

Supported formats are `compact-json`, `compact-jsonl` and `fhir-r4`. Compact cases
use the existing MedicalAdapter diagnosis contract and require canonical,
nonempty patient IDs. FHIR Bundles require Patient entries and an unambiguous
Encounter/Condition diagnosis pair. Patient subject references resolve through
`Patient/id` and Bundle `fullUrl` aliases. Unlabeled or ambiguous bundles and
timeline event prediction are rejected. Duplicate local Patient IDs are rejected
even with distinct fullUrls; this compact contract cannot resolve their relative
aliases safely. It validates the task contract, not full FHIR conformance.
This path does not extract symptoms or
vitals from FHIR Observations; those tasks have empty observations and the rule
baseline predicts `unknown`.

For Synthea exports, record the simulator version, generator seed and exported
file hash in the sidecar. Preserve exporter configuration/metadata separately.
Exporter flags describe configuration, not a guaranteed file inventory; metadata
can contain run IDs and wall time. Replay verifies a frozen source, not identical
bytes across newly generated simulator runs. The generator seed and partition
seed have separate roles.

## Artifacts and consumers

The bridge writes three files without timestamps or absolute paths:

1. `manifest.json`: source identity, Python/bridge/benchmark versions, SHA-256 of
   bridge/adapter/runtime code, partition seed and algorithm, patient and task
   splits, output hashes, and explicit offline execution accounting.
2. `memoryeval.json`: an experimental version 1 interchange envelope with
   `synthetic`, `source`, `implementation`, `partitions` and `tasks`. Each task has
   string `task_id`, `source_task_id`, `patient_id`, `split`, a canonical JSON
   `query` containing only symptoms/vitals, `trajectory` (the fixture target),
   `reward: 1.0`, and metadata including `expected_answer`, `case_sha256` and
   `reward_origin: fixture_target`.
3. `replay.jsonl`: ordered T0/T1/T2 rule predictions with fixture label matches,
   safety-gate results and explicit training task IDs. These are replay records,
   not SIP `runs` schema records or publishable benchmark scores.

`partitions.train` contains only adaptation patients. `partitions.evaluation`
contains replay, held-out and drift patients. All four splits are mutually
patient-disjoint. Memory consumers must populate memory **only from `adapt`**,
use only `query` as evaluation input, retain `trajectory`/`expected_answer` only
for scoring evaluation tasks, and exclude the current `source_task_id` before
retrieval. Fixture rewards express target examples; they are not observed model
rewards. This envelope is a proposed interchange contract for offline MemRL
experiments, not an asserted upstream memoryeval standard or live integration.

T0 uses empty memory. T1 and T2 independently reconstruct RuleMemory from the
adaptation split only. The adaptation split's own predictions are training
diagnostics; evaluation claims must use the other three splits. T2 currently
repeats T1 as a deterministic retention check, without simulating learning drift.
The rule baseline receives only observations; changing held-out labels cannot
change any prediction. `model_calls` and `provider_calls` are zero. Token usage
and dollar cost are `null` with `measurement: not_applicable_offline`; runtime
performance and model spending are not measured by this artifact.

`--verify` reads the recorded partition configuration, regenerates from the
attested source with the current implementation, and compares all three files
byte for byte. It rejects source tampering, changed implementation/runtime and
mutated persisted artifacts. Keep the original source and sidecar beside your
evidence; they are required to replay. SHA-256 establishes consistency, not
authenticity. Artifacts are reproducible for the same source, configuration,
implementation and Python version, regardless of output directory.

```bash
python3 -m unittest discover -s tests -p 'test_synthetic_replay.py'
python3 scripts/run_release_checks.py --plan-matrix
```
