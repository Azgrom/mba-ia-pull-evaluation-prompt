# Method — Breaking (or proving) an LLM-judge metric ceiling

A reusable playbook for the situation this project kept hitting: you're optimizing
a prompt whose quality is scored by one or more LLM-as-judge metrics with a numeric
pass bar, you've made a couple of edits, and a metric won't move — or moved down, or
fixing one metric broke another. This doc distills the discipline that the four
iterations here earned (see the worked example at the end and the retrospective
`GGQPA-XXX-202607240930-[Analysis]-v2-iteration-benchmark-retrospective.md`).

It is a *method*, not a skill: the goal is to know **which** ceilings are breakable
(omission, format mismatch, mis-targeted metrics) versus which are real capability
bounds where the honest move is to document and stop.

---

## The mental model

An LLM-judge suite is **not a hill you climb**. It's three things at once, and each
defeats a different naive tactic:

1. **A noisy measurement.** Judges at `temperature=0` are still not bit-reproducible;
   per-example scores jitter. If you don't know the size of that jitter you can't tell
   a real gain from a lucky roll.
2. **A coupled system.** Reported metrics are usually *derived* from a few base judge
   scores by fixed formulas. Change one base score and several reported numbers move
   together — sometimes against you.
3. **An equilibrium, not a monotone lever — especially F1.** F1 is the harmonic mean
   of judge-estimated *precision* and *recall*. Adding content raises recall **and** the
   surface the precision half penalizes; the halves cancel, so F1 sits near the same
   value whether you add or cut. "More detail" and "less detail" fail for the same reason.

The steps below are countermeasures to these three, ordered so the cheap, decisive
checks come first.

## Step 1 — Reconstruct the scoring function before touching the prompt

Read the evaluation code, not the docs or the dashboard. Produce a one-page **score map**:

- **Which numbers are reported, and which are actually independent?** Write the formulas
  out. Here: `helpfulness = (clarity + precision)/2`, `correctness = (f1 + precision)/2` —
  five reported metrics driven by three judges, and **precision feeds three of the five**.
- **What are the sub-criteria inside each judge, and how are they combined?** Judges
  average sub-scores; the sub-criterion is the real target, and one weak sub-score drags
  the metric by ~1/N. Here: precision = mean(no-hallucination, **focus-on-the-question**,
  factual-correctness); clarity = mean(organization, language, non-ambiguity, **concision**).
- **How does the threshold read the number?** Displayed scores round; the check usually
  doesn't. `0.80 ✗` means raw < 0.80 — aim for ~0.85. Confirm per-metric vs mean.
- **Which examples count?** Averages are often over *successful* examples only, so a silent
  per-example failure shifts the mean for reasons unrelated to your edit.

*Why first:* you can't optimize a number you can't decompose. The most common wasted
iteration edits a reported metric ("improve correctness") when correctness is just
`(f1 + precision)/2` and the real lever is one judge sub-criterion.

## Step 2 — Measure the noise floor before believing any ceiling

Run the **identical** configuration N≥3 times. Record each metric's range.

- **If the aggregate range is comparable to your distance-to-threshold**, you're chasing
  noise. No prompt edit is verifiable at that resolution; get more signal (more examples /
  more runs), not more words.
- **If the aggregate is stable but per-example scores jitter**, averaging over the dataset
  is itself your variance-reducer: the aggregate is trustworthy, a single run is adequate
  aggregate evidence, and **a stuck aggregate is a real ceiling, not a low roll.**

*This project's pivotal moment:* an earlier draft *assumed* ±0.10 aggregate noise and
concluded "the judge is too noisy to optimize against." Three identical runs showed
aggregate F1 stable at 0.76–0.77 (range 0.01) — refuting the assumption and flipping the
strategy from "keep editing" to "this is a genuine wall." (Later same-run v2/v3 benchmarks
put the aggregate jitter closer to ±0.02 on precision — still far below the assumed ±0.10,
and enough to leave a metric sitting on 0.80 dependent on run luck.) **Measure it; don't
assume its size.**

## Step 3 — Localize: per-example diagnostics with the judge's discarded reasoning

Aggregates tell you *that* you're stuck, never *where*. Most eval scripts compute a rich
`reasoning` string per judgment and throw it away. Recover it with a throwaway, read-only
diagnostic that imports the judges (importing to read is not modifying the eval). Per example, record:

- generated output and reference;
- each base score **and its reasoning string**;
- for F1, the judge's **precision half and recall half separately** — the single most
  informative number (Step 4);
- a **deterministic structural diff** (no LLM calls): expected vs emitted format, headers
  present/missing/surplus, length delta, item counts. This half is free and makes format
  bugs obvious before you spend anything.

Concrete implementations in this repo: `scripts/diagnose_v2.py` (per-example diff + judge
reasoning + F1 precision/recall split) and `scripts/benchmark_v2_v3.py` (two prompts scored
side by side with `evaluate.py`'s exact math, from local YAML, no Hub push).

## Step 4 — Classify the gap: omission vs over-production vs equilibrium

Using the per-example F1 precision/recall split:

| What you see | Diagnosis | The only fix that works |
|---|---|---|
| Recall low, precision fine | **Omission** — reference content uncovered | **Additive**, *reference-specific*: add the missing content, not filler |
| Precision low, recall fine | **Over-production** — emitting content the reference lacks | **Subtractive**: cut the surplus; don't add |
| Both move together under length changes; F1 flat either way | **Harmonic-mean equilibrium** | Neither adding nor cutting helps; only rewriting the *same-length* answer toward the reference's *specific* wording moves it, and only a little |

*The trap to name aloud:* at the equilibrium, adding content to lift recall raises recall
*and* the precision penalty equally — F1 stays flat while standalone precision drops. Because
precision is coupled, that dip then knocks out a *second* metric. That is exactly how a loop
goes from one failing metric to two while the target never budges.

## Step 5 — Spend precision (or whatever is coupled) like it's expensive

Identify the base metric feeding the most reported metrics — your highest-leverage **and**
most dangerous lever. **Never trade a coupled metric for recall without checking the math.**
Before an additive edit, estimate: does the recall gain lift F1 by more than the precision
drop costs across *all* the metrics precision feeds? If you can't show it does, the edit is a
net regression even when the watched number rises. Quantify with the Step 3 data.

## Step 6 — Match the reference's shape, per stratum

If the dataset is stratified (difficulty tiers, categories), reverse-engineer the reference
**format taxonomy per stratum** and emit that exact shape — a missing section, a wrong banner
style, an off bullet count is cheap recall/clarity fixable without guessing content. But match
*structure*, not example-specific *facts*: teaching the prompt particular reference wording is
overfitting the (supposedly held-out) eval set. Structural matching generalizes; memorizing does not.

## Step 7 — Recognize the capability bound, and stop honestly

When a **weak generator is graded by a strong judge**, the judge reliably detects deviations the
generator cannot reliably avoid; no prompt closes that gap. You're at this bound when *all* hold:

- the aggregate is stable across runs (Step 2), so it's not noise;
- remaining per-example losses need reference-*specific* facts the generator can't reliably produce
  (Step 4), and coaxing them edges into overfitting (Step 6);
- every additive fix trades against a coupled metric (Step 5).

Then **document the ceiling as a finding, not another regression**: state it with the noise-floor
numbers that prove it's real, the coupling that makes it a trade-off, and the named out-of-scope
change most likely to break it (usually: upgrade the generator model). Knowing when to stop is part
of the method, not a failure of it.

## Red flags — thoughts that mean you've skipped a step

| Thought | What it means | Go to |
|---|---|---|
| "Let me just add more detail / examples." | Haven't classified omission vs equilibrium. | 3–4 |
| "Failed by 0.01, re-run and hope." | Don't know the noise floor. | 2 |
| "Correctness is low, tell it to be more correct." | Editing a derived metric, not its base sub-criterion. | 1 |
| "F1 didn't move but I *know* it got better." | Probably the harmonic-mean equilibrium. | 4 |
| "Precision dipped a little but recall's up, net win." | Precision is coupled — a small dip fails two metrics. | 5 |
| "One more tweak to nail these specific examples." | Overfitting the held-out set. | 6–7 |
| "The judge is just noisy / wrong." | Prove it with the noise-floor test first. | 2 |

---

## Worked example — the bug-to-user-story F1 wall

Task: take a deliberately bad prompt, optimize it, clear five LLM-judged metrics (F1, clarity,
precision, helpfulness, correctness) each ≥ 0.80. Generator `gpt-4o-mini`; judge `gpt-4o`.

**Score map (Step 1):** three judges (`f1`, `clarity`, `precision`) drive five metrics via
`helpfulness=(clarity+precision)/2`, `correctness=(f1+precision)/2`. Precision feeds three of five.
Dataset stratifies into simple / medium / complex, each with a distinct reference format.

**The arc:**

| Iteration | Change | F1 | Clarity | Precision | Helpful | Correct | Status |
|---|---|---|---|---|---|---|---|
| v1 baseline | deliberately bad | 0.48 | 0.50 | 0.46 | 0.45 | 0.52 | fail (all 5) |
| Iter 2 | Role + CoT + Few-shot | 0.90→0.79* | 0.80 | 0.73 | 0.77 | 0.82 | fail (3) |
| Iter 3 | subtractive precision fix + complex scale-up | 0.77 | 0.87 | **0.84** | 0.85 | 0.81 | fail (f1 only) |
| Iter 4 | medium 2nd criteria group "quase sempre" | 0.77 | 0.88 | **0.81** | 0.84 | **0.79** | fail (f1 **and** correctness) |
| v3 | Iter-4 minus the 2nd-group rule (isolated revert) | 0.74 | 0.87 | **0.81** | 0.84 | 0.77 | fail (f1, correctness) |

\*Iter 2 read 0.90 on the reported run but 0.79 re-measured — an outlier run, the first hint at jitter.

**Noise floor (Step 2):** three identical Iter-4 runs gave aggregate F1 0.77/0.76/0.76 (range 0.01),
refuting the assumed ±0.10 — F1 ≈ 0.77 is a real, reproducible wall. Per-example scores swing ±0.10
but ~8/15 are bit-stable and the jitter averages out.

**Localize + classify (Steps 3–4):** F1 = 0.777 with **precision-half 0.827, recall-half 0.737** —
low recall ⇒ **omission** in the medium tier (dropped second criteria group). Iter 4 targeted that
omission and lifted it *locally* (ex.11 recall 0.50→0.80) but the aggregate stayed flat: the added
bullets raised recall *and* the precision penalty in equal measure — the **equilibrium**.

**Coupling regression (Step 5):** the added content also cost the standalone precision "focus" sub-score
(0.84→0.81); since `correctness=(f1+precision)/2` and F1 was flat, correctness fell 0.81→0.79. One
failing metric became two while the target never moved.

**Isolated revert (v3):** reverting *only* the 2nd-group rule recovered precision (+0.021, back to passing)
and left F1 unmoved — confirming the lever was precision, not F1. But **correctness is welded to F1**:
with F1 ~0.74–0.77, correctness needs precision ≥ 0.85 to reach 0.80, and precision saturates ~0.81–0.84.

**Capability bound + honest stop (Step 7):** the "focus-on-the-question" precision penalty stayed pinned at
0.5 on the stuck examples regardless of prompt wording — fixed judge behavior a weak generator can't reach.
Best prompt-only state: **3/5 passing (4/5 on a lucky precision run); F1 and the correctness chained to it
are the wall.** The named out-of-scope unlock is promoting the subject model to `gpt-4o`.

## Transferable takeaways

1. Read the eval code and write the score map — derived metrics hide the real levers.
2. Measure the noise floor before believing a ceiling; don't assume its size.
3. Split F1 into precision/recall halves to tell omission from over-production.
4. Watch for the harmonic-mean equilibrium: local F1 wins that vanish in aggregate.
5. Coupled metrics turn a small precision dip into a second failure — do the math first.
6. Match reference *structure* per stratum; refuse to memorize reference *facts*.
7. A weak generator under a strong judge has a ceiling prompts can't break — stop and document.
