# SIP-Bench Positioning Note After v0.1.0

## Purpose

This note clarifies what `SIP-Bench` is trying to be after `v0.1.0`.
It is especially important now that public benchmark-first self-evolution suites such as `EvoAgentBench` are appearing.

The goal is not to argue that benchmark-first evaluation is unimportant.
The goal is to make clear that `SIP-Bench` is solving a different layer of the problem.

## Public Comparison Point

As of `2026-04-18`, the publicly visible `EvoAgentBench` materials describe:

1. a benchmark for AI agent self-evolution
2. standardized `train` and `test` splits across five task domains
3. a `Train -> Extract -> Evaluate` protocol
4. evaluation centered on whether reusable knowledge improves test-time performance on unseen tasks

Public sources at the time of writing:

1. <https://huggingface.co/datasets/EverMind-AI/EvoAgentBench>
2. <https://evermind.ai/>

The `EvoAgentBench` dataset card also states that the paper is "coming soon" at the time of this note.

## The Short Version

`EvoAgentBench` is benchmark-first.
`SIP-Bench` is protocol-first.

That is the key distinction.

One asks:

1. does experience reuse improve performance on held-out test tasks?

The other asks:

1. what changed across checkpoints?
2. what improved?
3. what regressed?
4. what did the improvement cost?
5. how stable was it over time?
6. what operational failures happened along the way?

## Comparison Table

| Dimension | Benchmark-first self-evolution suites | `SIP-Bench` |
| --- | --- | --- |
| Primary object of evaluation | whether a self-evolution method improves downstream task success on unseen test tasks | how an agent's capability profile changes across protocol checkpoints |
| Default protocol shape | `Train -> Extract -> Evaluate` | `T0 / T1 / T2` with `replay / adapt / heldout / drift` |
| Main claim type | generalization after experience reuse | gain, retention, stability, efficiency, and failure-aware provenance |
| Main output style | benchmark scores on test tasks | `runs.jsonl`, `summary.jsonl`, `FG`, `BR`, `IE`, `PDS`, `NIS`, attempt artifacts |
| Failure treatment | often compressed into final benchmark outcome | failures, retries, reruns, and recovered runs are first-class artifacts |
| Best use today | comparing self-evolution methods on shared task splits | diagnosing whether "improvement" came with forgetting, instability, or excess cost |

## Why SIP-Bench Should Not Imitate EvoAgentBench

If `SIP-Bench` tries to win on breadth alone, it will likely lose its sharpest idea.

The strongest current reason for `SIP-Bench` to exist is not:

1. more tasks
2. more domains
3. another train/test split

The strongest reason is:

1. a reusable longitudinal contract
2. protocol metrics that separate held-out gain from replay retention
3. explicit cost accounting
4. explicit operational provenance for failure and recovery

That is why the current post-`v0.1.0` plan prioritizes repo-hosted tables and figures that show:

1. held-out gain versus replay loss
2. cost versus gain
3. stability from `T1` to `T2`
4. attempt-level recovery evidence

## Why The Two Approaches Are Complementary

The two approaches can strengthen each other.

A benchmark-first suite can tell us whether an experience-reuse method improves test performance on unseen tasks.
`SIP-Bench` can then tell us whether that same improvement:

1. damaged replay retention
2. softened by `T2`
3. required disproportionate cost
4. depended on fragile operational recovery

In other words:

1. benchmark-first evaluation is good at asking whether improvement generalized
2. protocol-first evaluation is good at asking what kind of improvement actually happened

## Design Implications For The Next Phase

The next phase should keep these design consequences explicit:

1. do not add a third benchmark before the current two-environment evidence story is stronger
2. prefer stronger interpretation assets over benchmark-count inflation
3. prefer repeatable result bundles over one-off headline numbers
4. only expand into prepared-suite or provider-backed paths when the resulting evidence can still be interpreted through protocol metrics

## Practical Reading Rule

If a future result can be summarized only as "the score went up," then it is not yet strong `SIP-Bench` evidence.

Strong `SIP-Bench` evidence should answer at least four questions at once:

1. did held-out performance improve?
2. did replay retention hold?
3. what did the gain cost?
4. was the gain operationally and temporally stable?

## What We Mean by Non-Ceiling Evidence

SIP-Bench uses explicit non-ceiling criteria to avoid calling saturated tasks protocol-value.

1. A suite is non-ceiling if at least one replay/heldout mean is below `1 - 0.02`.
2. A suite is non-ceiling if `|FG| >= 0.02`, `|BR| >= 0.02`, or `|IE| >= 0.0005`.
3. Protocol status is `Evidence` only when criteria 1/2/3 are met with at least 3 attempts across the family (repeat/recover path visibility).
4. If only attempt depth is missing, status remains `Screening`, even when some families are clear.
