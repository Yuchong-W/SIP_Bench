# Medical continuous-learning adapter

This adapter adds a small, deterministic medical task family to SIP-Bench. The
fixture follows the Synthea-shaped contract: `patient_id`, `encounter_id`,
`symptoms[]`, `vitals{}`, and `diagnosis`. Replace `cases.json` with a de-identified
Synthea export (or a file containing `{ "cases": [...] }`) without changing the
runner.

Run an end-to-end protocol experiment:

```bash
PYTHONPATH=src python3 scripts/run_medical_demo.py
python3 scripts/aggregate_metrics.py --runs results/medical_demo/runs.jsonl \
  --out results/medical_demo/summary.jsonl
```

The experiment emits all T0/T1/T2 × replay/adapt/heldout/drift records, a
manifest, costs, and per-run failure/safety metadata. T0 is frozen; T1 writes
diagnoses from adapt cases to an external memory; T2 evaluates drift. The safety
gate blocks under-triage of chest pain, stroke signs, and severe bleeding.

**CaseCapture / CaseGraph integration.** A CaseCapture export can be mapped by
writing `encounter_id` from its case ID, `patient_id` from its subject ID,
`symptoms` from normalized observations, `vitals` from measurements, and the
reference label to `diagnosis`. CaseGraph edges (prior encounters, medications,
or contraindications) can be carried in an optional `graph` object; adapters
should expose it through `TaskDescriptor.metadata` and never include direct
identifiers. Keep `adapt` and `heldout` disjoint by encounter ID and version the
mapping alongside the fixture.

Retrieval probes use `normalize_query` and `utility_aware_retrieve` from
`sip_bench.adapters.medical`. NFKC normalization preserves Japanese text and
removes optional whitespace, so `胸 痛` and `胸痛` match the same case. An
optional utility map prioritizes labels with deterministic encounter-id ties.
The adapter also accepts a minimal FHIR `Bundle` with Encounter and Condition
resources, as well as the compact cases and JSONL forms.

This is a research fixture, not clinical decision support. Do not use it with
identifiable or live patient data.
