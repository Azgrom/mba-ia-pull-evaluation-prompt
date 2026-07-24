# v2 Prompt — Iteration Benchmark & Retrospective (through Iteration 4)

## CAVEMAN TL;DR

Prompt bad. Fix prompt 3 times. F1 stuck 0.77. Iteration 4 add more criteria — F1 no move, precision drop 0.84 → 0.81, correctness break too. Two metric red now, was one. Ran same prompt 3 times to test noise. Answer: aggregate NOT noisy — F1 = 0.76, 0.76, 0.77, rock steady. Per-example jitter big (±0.10) but wash out over 15. So F1 0.77 is REAL WALL, not noise. Iteration 4 truly no help + truly hurt precision (now touch 0.80 floor). Weak model write (gpt-4o-mini), strong model grade (gpt-4o). Add words no help F1: more recall = more precision tax, cancel. NEXT: revert Iteration 4 (get precision safe back), accept F1 0.77 prompt ceiling. Real unlock = bigger model, not more words.

---

## ZOOM-OUT (the whole arc)

The challenge: pull a deliberately bad prompt, optimize it, clear all 5 LLM-judged metrics ≥ 0.80. Four iterations in — and after a three-run noise-floor test — the shape of the problem is clear:

- **The bottleneck is the prompt+subject, not the measurement.** A hypothesis from earlier drafts — "judge noise ±0.10 swamps every fix" — was **tested and refuted**: three runs of the *identical* Iteration-4 prompt give aggregate F1 = 0.77 / 0.76 / 0.76 (range 0.01). Per-example jitter is ±0.10 but averages out over 15 examples. So the aggregate is trustworthy, and **F1 ≈ 0.77 is a real, reproducible ceiling.**
- **The task is a moving equilibrium, not a hill to climb.** F1 is a harmonic mean of judge-estimated recall and precision. Adding content (to lift recall) raises the surface the precision-half penalizes. The two halves cancel, so F1 sits near 0.77 regardless of direction. Iteration 3 subtracted content (helped precision, hurt simple-tier F1); Iteration 4 added content (helped nothing, hurt precision). Same equilibrium, approached from both sides — and now confirmed stable, not noisy.
- **Subject/judge asymmetry is structural.** `gpt-4o-mini` writes, `gpt-4o` grades. The judge can reliably detect deviations the subject cannot reliably avoid. No prompt edit closes that capability gap.
- **The honest strategic question is answered.** "Can prompt-only optimization clear 0.80 F1 with this subject model?" The reproducible 0.77 ceiling says: **not by continuing in this direction.** The genuine unlock is the subject model, which is out of scope by challenge rules.

---

## BENCHMARK — all iterations

Metrics as reported by `evaluate.py` (the Hub-published commit). All five must individually be ≥ 0.80 **and** the mean ≥ 0.80.

| Iteration | What changed | F1 | Clarity | Precision | Helpfulness | Correctness | Média | Status |
|-----------|--------------|----|---------|-----------|-------------|-------------|-------|--------|
| **v1** (baseline) | deliberately bad prompt | 0.48 | 0.50 | 0.46 | 0.45 | 0.52 | ~0.48 | REPROVADO (all 5) |
| **Iter 2** (first v2) | Role + CoT + Few-shot; reported run | 0.90 | 0.80 | 0.73 | 0.77 | 0.82 | 0.802 | REPROVADO (helpful, clarity, precision) |
| — *Iter 2 diagnostic* | *same prompt, re-measured* | *0.79* | *0.87* | *0.83* | — | — | — | *reveals ±0.10 judge noise* |
| **Iter 3** (metric remediation) | 8-change ledger: subtractive precision fix + complex-tier scale-up | 0.77 | 0.87 | 0.84 | 0.85 | 0.81 | 0.828 | REPROVADO (f1) |
| **Iter 4** (F1 recall remediation) | medium 2nd criteria group + simple-boundary + rule-(a) split + system persona | **0.77** | 0.88 | **0.81** | 0.84 | **0.79** | 0.815 | REPROVADO (**f1, correctness**) |

### Iteration 4 per-example F1 (user's published run)

| Ex | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|----|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|
| F1 | 0.75 | 0.75 | 0.87 | 0.69 | 0.69 | 0.69 | 0.75 | 0.85 | 0.65 | 0.69 | **0.80** | 0.69 | 0.85 | 0.80 | 1.00 |

Tier means: Simple (1–5) **0.75**, Medium (6–12) **0.73**, Complex (13–15) **0.88**.

---

## NOISE-FLOOR MEASUREMENT — three runs of the identical Iteration-4 prompt

Run #1 = user's published run; Runs #2–#3 = Docker (`langchain-prompt-optimization:latest`, `-v ./:/app`, same Hub commit, `temperature=0`). No prompt change between runs — this isolates run-to-run judge variance.

| Metric | Run #1 | Run #2 | Run #3 | Range | Mean | Threshold verdict |
|--------|--------|--------|--------|-------|------|-------------------|
| **F1-Score** | 0.77 | 0.76 | 0.76 | **0.01** | 0.766 | **fails all 3** |
| Clarity | 0.88 | 0.86 | 0.86 | 0.02 | 0.867 | passes all 3 |
| Precision | 0.81 | 0.82 | 0.80 | 0.02 | 0.810 | **flips: fails run #3** |
| Helpfulness | 0.84 | 0.84 | 0.83 | 0.01 | 0.837 | passes all 3 |
| Correctness | 0.79 | 0.79 | 0.78 | 0.01 | 0.787 | **fails all 3** |
| Média Geral | 0.815 | 0.814 | 0.806 | 0.009 | 0.812 | — |

**Result: the aggregate is stable to ±0.01; the earlier ±0.10 "noise floor" claim is refuted.** Per-example F1 does jitter (ex.7: 0.75/0.75/0.85; ex.8: 0.85/0.85/0.75; ex.12: 0.69/0.60/0.69 — up to ±0.10), but ~8 of 15 examples are bit-stable and the jitter averages out. Averaging over 15 examples is itself the variance-reduction mechanism.

**Consequences:**
- **F1 ≈ 0.766 is a genuine ceiling.** Not a run that happened to land low — three did.
- **Precision sits exactly on the knife-edge** (0.80–0.82). Iteration 4's added medium content pushed it from Iteration 3's safe 0.84 down to where it fails 1 run in 3. This is a real regression, not variance.
- **Correctness cannot pass** while F1 is stuck: `(0.766 + 0.81)/2 = 0.788 < 0.80`.

---

## DIAGNOSIS — why Iteration 4 failed (reproduce → hypothesise → verify)

**Symptom.** Predicted F1 +0.09–0.14 (dominant lever: emit the medium second criteria group). Observed F1 Δ ≈ 0.00; standalone precision −0.03; correctness crossed from pass (0.81) to fail (0.79).

**Hypothesis 1 — the second-group lever is self-cancelling on F1.** F1 = 2·(P·R)/(P+R) over judge-estimated precision and recall. Adding the second criteria group raises recall (more reference content covered) *and* raises the count of bullets the precision-half can tag "desnecessário". On a harmonic mean the two moves offset. **Consistent with observed flat F1.**

**Hypothesis 2 — added content costs standalone precision.** The standalone `precision` judge weights "Foco na Pergunta". Longer, two-group medium answers drift from the single reported symptom, so "Foco" drops. Precision fell 0.84 → 0.81, and since `correctness = (f1 + precision)/2`, a precision dip with flat f1 mechanically pushed correctness under 0.80. **Consistent, and it is why a second metric now fails.**

**Hypothesis 3 — the moves are inside the noise band. TESTED AND REFUTED.** The earlier draft asserted ±0.10 aggregate noise (from an Iter-2 cross-harness comparison). The three-run measurement above shows aggregate F1 is stable to ±0.01, so this hypothesis is false: F1 0.77 is a *reproducible* value, and Iteration 4's failure to move it is real, not masked by noise. The corrected load-bearing finding is the opposite of the original: **the ceiling is genuine, so same-direction prompt edits cannot clear it.**

**Cross-check (structural, from `iteration-3-baseline.md`).** The diagnostic correctly identified that medium references carry a dropped second group (recall gap). The fix *did* address that gap — ex.11 moved 0.55 → 0.80. But the aggregate did not follow, because the gains are local and the losses (precision, simple tier) are spread. The per-example evidence was right; the aggregate lever was not.

**Verdict.** Iteration 4 is a **regression** (one failing metric → two), and its central hypothesis is **falsified**: matching the reference's medium volume does not lift F1, because F1's own precision-half taxes the added recall, and standalone precision pays for the extra length.

---

## STRUCTURED FINDINGS (architecture lens — properties of the system, not one edit)

1. **The aggregate target is stable; the ceiling is real.** Three identical runs give F1 within ±0.01. Per-example jitter (±0.10) averages out over 15 examples. *Implication:* aggregate scores are trustworthy to two decimals, single runs are adequate evidence at the aggregate level, and F1 0.77 is a wall — not a low roll of the dice. (This corrects the earlier "noise swamps the signal" reading.)
2. **F1 has an internal equilibrium that resists content edits.** Recall and precision-of-F1 move together under length changes. *Implication:* F1 cannot be won by "add more" or "cut more" — only by making the *same-length* answer resemble the reference's *specific* wording, which the subject model cannot reliably do.
3. **The metrics are coupled through precision.** `total = 1.5·clarity + 1.5·f1 + 2·precision`; precision feeds itself, helpfulness, and correctness. A precision dip cascades. *Implication:* precision is both the highest-leverage lever and the most dangerous to spend — Iteration 4 spent it and lost correctness.
4. **Subject ≠ judge capability.** The gap is fixed by model choice, not prompt text. *Implication:* the remaining prompt headroom is small and mostly consumed.
5. **The complex tier is solved and stable (~0.88).** *Implication:* do not touch it; all remaining risk/reward is in simple + medium.

---

## OPTIONS (honest, ranked — post noise-floor)

The noise-floor measurement (done) removes the "just re-run for a lucky pass" option: the aggregate is stable, so luck is not available. What remains:

1. **Revert Iteration 4 → Iteration 3. Recommended.** Iteration 4 is a measured regression: it left F1 unchanged (0.77) and pushed precision from a safe 0.84 to a knife-edge 0.80–0.82 that fails 1 run in 3. Reverting restores the best-known prompt-only state — precision safely passing, only F1 below the line — which is a strictly better position to iterate from or to submit with a documented ceiling.
2. **Accept F1 ≈ 0.77 as the prompt-only ceiling and document it.** Three runs make this defensible as a *finding*, not a failure: with `gpt-4o-mini` as subject and `gpt-4o` as judge over these references, F1 tops out at ~0.77 because F1's precision-half taxes every unit of added recall. The README should state this and the deliberate `LLM_MODEL` constraint that causes it.
3. **Targeted per-example recall on the stable losers** (ex.4 "apenas status ativo", ex.5 "qualidade + tempo", ex.9 calc breakdown, ex.10 pagination/RecyclerView, ex.12 acessibilidade). Now attributable, since the aggregate is stable and these examples are consistently low. *Caveat:* these need reference-*specific* content the subject can't reliably guess, and teaching it edges toward overfitting the (supposedly held-out) eval set — expect small, capped gains and watch precision.
4. **Out-of-scope but named honestly:** upgrading `LLM_MODEL` from `gpt-4o-mini` to `gpt-4o` is the single change most likely to clear all five, per the Iteration-2 analysis. *Rejected as a remediation* — it optimizes the runtime, not the prompt — but it is the true bound on what prompt-only work can achieve here, and belongs in the README as the deliberate constraint.

---

## PROVENANCE (iteration → design docs)

- Iter 1–2 pipeline + first v2: `spdd/analysis/GGQPA-XXX-202607232100-[Analysis]-*` → `spdd/prompt/GGQPA-XXX-202607232106-[Feat]-*`
- Iter 3 metric remediation: `spdd/analysis/GGQPA-XXX-202607232223-[Analysis]-*` → `spdd/analysis/diagnostics/iteration-2-baseline.md` → `spdd/prompt/GGQPA-XXX-202607232256-[Fix]-*`
- Iter 4 F1/recall remediation: `spdd/prompt/GGQPA-XXX-202607240900-[Fix]-prompts-v2-f1-recall-remediation.md` → `spdd/analysis/diagnostics/iteration-3-baseline.md` → **this retrospective**

*Noise-floor: three independent measurements of the Iteration-4 commit (1 user run + 2 Docker runs via `langchain-prompt-optimization:latest`) quantify run-to-run variance — see the NOISE-FLOOR MEASUREMENT section. Aggregate F1 range 0.01, refuting the earlier ±0.10 assumption.*
