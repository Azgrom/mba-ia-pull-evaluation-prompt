# SPDD Analysis: v2 Prompt Metric Remediation (Iteration 2)

## Original Business Requirement

> ```
> ==================================================
> Prompt: azgrom/bug_to_user_story_v2
> ==================================================
>
> Métricas Derivadas:
>   - Helpfulness: 0.76 ✗
>   - Correctness: 0.82 ✓
>
> Métricas Base:
>   - F1-Score: 0.90 ✓
>   - Clarity: 0.80 ✗
>   - Precision: 0.73 ✗
>
> --------------------------------------------------
> 📊 MÉDIA GERAL: 0.8022
> --------------------------------------------------
>
> ❌ STATUS: REPROVADO
> ⚠️  Métricas abaixo de 0.8: helpfulness, clarity, precision
> ⚠️  Média atual: 0.8022 | Necessário: 0.8000
>
> ==================================================
> RESUMO FINAL
> ==================================================
>
> Prompts avaliados: 1
> Aprovados: 0
> Reprovados: 1
>
> ⚠️  Alguns prompts não atingiram todas as métricas >= 0.8
> ```
>
> Considering this result for @prompts/bug_to_user_story_v2.yml pass /review-claude-md directives to /spdd-analysis to build an analysis of what needs to be improved.

Secondary requirement carried in from `/review-claude-md`: surface repo context (commands, gotchas, config quirks, evaluation-pipeline behaviours) that was missing and would have made this iteration faster, and propose concrete `CLAUDE.md` additions.

---

## Domain Concept Identification

### Existing Concepts (from codebase)

- **Reported Metric Set** (`evaluate.py:216-229`): five values — `f1_score`, `clarity`, `precision` measured directly by LLM-as-judge, plus `helpfulness = (clarity + precision) / 2` and `correctness = (f1_score + precision) / 2`. Only three judge calls per example produce all five numbers.
- **Judge Rubrics** (`metrics.py`): each of the three active judges is itself a *composite mean of sub-criteria*, and this decomposition is the actual optimisation target:
  - `evaluate_clarity` → mean of **Organização, Linguagem, Ausência de Ambiguidade, Concisão** (4 sub-scores).
  - `evaluate_precision` → mean of **Ausência de Alucinações, Foco na Pergunta, Correção Factual** (3 sub-scores).
  - `evaluate_f1_score` → harmonic mean of judge-estimated precision and recall against the reference.
- **Reference Output Corpus** (`datasets/bug_to_user_story.jsonl`): 15 immutable ground-truth answers. Every judge compares the generated answer against these, so the references — not general prompt-engineering theory — define what "correct" means here. They fall into three distinct formats (see *Reference Format Taxonomy* below).
- **Adaptive Output Contract** (`prompts/bug_to_user_story_v2.yml:23-26`): the v2 prompt's own simple/médio/complexo branching, plus its three few-shot exemplars (lines 35-103). This is the artefact under test and the only file that may change between iterations.
- **Hub Commit** (`{username}/bug_to_user_story_v2`): the only thing `evaluate.py` scores. The local YAML is inert until `push_prompts.py` republishes it.
- **Protected Pipeline**: `evaluate.py`, `metrics.py`, `utils.py`, and the dataset are declared unmodifiable by `PROJECT_INSTRUCTIONS.md`. All remediation must therefore be expressed *inside the v2 prompt text*.

### New Concepts Required

- **Reference Format Taxonomy** — an explicit, evidence-based description of what each complexity tier's reference answer actually looks like. This does not exist as a written artefact anywhere in the repo, yet it is the target the prompt must imitate. Derived by reading all 15 references:

  | Tier | Examples | Structure observed in **every** reference of the tier |
  |------|----------|------------------------------------------------------|
  | Simple | 1-5 (5 ex.) | US paragraph + `Critérios de Aceitação:` + **exactly 5** Dado/Quando/Então/E/E bullets. **No** further sections. |
  | Medium | 6-12 (7 ex.) | US paragraph + `Critérios de Aceitação:` (5-6 bullets) + **plain-text section headers ending in `:`** — never `===` banners. **All 7** carry a context section, whose name varies by bug type: `Contexto Técnico` (4×: ex. 6, 7, 9, 12), `Contexto do Bug` (2×: ex. 10, 11), `Contexto de Segurança` (1×: ex. 8). 5 of 7 (ex. 8-12) *additionally* carry a second criteria group (`Critérios Adicionais para Admins`, `Exemplo de Cálculo`, `Critérios Técnicos`, `Critérios de Prevenção`, `Critérios de Acessibilidade`). |
  | Complex | 13-15 (3 ex.) | US paragraph + `=== USER STORY PRINCIPAL ===` (with `Título:` and `Descrição:`) + `=== CRITÉRIOS DE ACEITAÇÃO ===` with **exactly four** groups `A.`–`D.` + `=== CRITÉRIOS TÉCNICOS ===` + `=== CONTEXTO DO BUG ===` + `=== TASKS TÉCNICAS SUGERIDAS ===` (grouped by Sprint/Fase in 2 of 3). The banner sections are themselves **sub-headed** with plain `Header:` lines (`Impacto Business:`, `Problemas Técnicos:`, `Problemas Identificados:`, `SLA Atual vs Esperado:`). Example 15 additionally ends with `=== MÉTRICAS DE SUCESSO ===`. |

- **Reference Size Budget** — the measured length profile of the corpus. The rubrics that are failing (clarity's *Concisão*, precision's *Foco na Pergunta*) are volume judgements, and until now this document asserted "over-production" without a number to test it against. Measured across all 15 references:

  | Tier | Examples | Characters | Lines |
  |------|----------|------------|-------|
  | Simple | 1-5 | 389 – 447 | **8 in all five** |
  | Medium | 6-12 | 664 – 963 | 14 – 20 |
  | Complex | 13-15 | 3 605 – 5 756 | 92 – 161 |

  A simple-tier answer is ~400 characters and 8 lines — user story paragraph, blank line, `Critérios de Aceitação:`, five bullets. This is a far tighter budget than the v2 contract implies, and conformance to it is measurable with zero LLM calls.

- **Persona Polarity** — the reference corpus does **not** always use a human persona. Three references open with the system as actor: ex. 6 `Como o sistema de e-commerce…`, ex. 8 `Como o sistema…`, ex. 11 `Como o sistema de e-commerce…` — in every case a backend/system-level bug with no human-facing surface (webhook delivery, endpoint authorisation, stock validation). The remaining 12 use a human role. v2 rule (b) mandates `Como um [persona]` and the vague-report edge case instructs the model to *infer a plausible persona*, both of which push away from system-as-actor on exactly those three examples.

- **Complexity Trigger Fidelity** — a corrected mapping from bug-report surface features to output tier. The current trigger disjunction is demonstrably mis-calibrated (see Risk analysis).
- **Per-Example Diagnostic Table** — a read-only diagnostic pass combining two evidence sources that cross-check each other: (a) *deterministic structural diff* — which tier the model actually emitted, which section headers it emitted vs. the reference's, AC bullet counts, and char/line length against the Reference Size Budget, all computable without an LLM; and (b) the `reasoning` strings the judges already return. `evaluate.py:206-214` computes those and prints only the numeric score, discarding the explanation. Without both, every iteration is a blind guess.
- **Score Margin Budget** — a target above 0.8 rather than at it, to absorb judge nondeterminism (see Technical Risks).

### Key Business Rules

- **Precision carries 40% of the aggregate.** Expanding the five reported values gives `total = 1.5·clarity + 1.5·f1 + 2·precision`. Precision is the only variable appearing in three of the five reported numbers (itself, helpfulness, correctness). It is also the lowest-scoring metric (0.73). It is unambiguously the primary lever.
- **All five metrics must individually clear 0.8 *and* the mean must clear 0.8** (`evaluate.py:262-263`). The current run passes the mean (0.8022) and still fails — mean improvement is not a goal.
- **Every judge scores against the reference, not against abstract quality.** A structurally excellent answer that does not resemble its reference scores badly. Imitation of the corpus dominates.
- **The output contract must be inferable from `{bug_report}` alone.** `evaluate.py:149-160` passes only `example.inputs` into the chain; `metadata.complexity` never reaches the model.
- **Only `prompts/bug_to_user_story_v2.yml` may change.** Dataset, judges, and threshold logic are fixed.

---

## Strategic Approach

### Solution Direction

Treat this as a **calibration problem, not an enrichment problem**. F1 at 0.90 proves content coverage and recall are already strong; the answers contain what the references contain. The deficit is concentrated in the two rubrics that penalise *surplus and unfounded material* — precision's "Foco na Pergunta" / "Ausência de Alucinações", and clarity's "Concisão". The direction is therefore **subtractive and corrective**: tighten what the prompt authorises the model to emit, and align section vocabulary and tier triggers with the reference corpus, rather than adding more instructions or more sections.

A second constraint points the same way. The pipeline runs a **weak subject against a strong judge**: `.env` sets `LLM_MODEL=gpt-4o-mini` (the model executing the prompt) and `EVAL_MODEL=gpt-4o` (all three judges). The binding limit is therefore not only what the prompt *authorises* the model to emit, but how much conditional logic `gpt-4o-mini` can execute reliably. v2 currently asks it to apply 5 behavioural rules, run a 4-step internal reasoning chain, infer a tier from surface features via a disjunctive trigger, and select one of 3 output contracts — while imitating 3 exemplars. Every additional conditional is a place a small model drifts, and drift shows up as exactly the symptom observed: correct content (f1 0.90) in the wrong shape and volume (precision 0.73). **Subtraction of prompt complexity is therefore a lever in its own right**, not merely a means to subtract output.

Sequenced as: (1) run one diagnostic pass producing the per-example table (structural diff + judge reasoning); (2) fix the tier-trigger mis-calibration and reduce the branching to a single mechanical signal; (3) remove the invention-authorising language and the speculation-teaching exemplar; (4) align persona polarity, section naming and structure per tier; (5) re-push and re-measure against the change ledger's predictions.

### Key Design Decisions

- **Localise the over-production before assuming where it is.**
  The subtractive thesis rests on precision 0.73 against f1 0.90, which is the signature of surplus material. But measuring the v2 exemplars against the Reference Size Budget shows the exemplars are **not** obviously the source, and this materially changes what to edit:

  | Exemplar | `v2.yml` lines | Emitted size | Reference budget for its tier | Verdict |
  |----------|----------------|--------------|-------------------------------|---------|
  | 1 (simple) | 38-45 | 8 lines | 8 lines (all five refs) | conforms exactly |
  | 2 (medium) | 50-62 | 13 lines | 14-20 lines | marginally under |
  | 3 (complex) | 67-103 | ~37 lines | 92-161 lines | **~60% under** |

  So the demonstrated output volume is calibrated for simple and medium and *under*-scaled for complex. If over-production is real, it originates in the contract prose (`v2.yml:23-26`) and in tier drift rather than in imitation of the exemplars — and it may be concentrated in a few examples rather than spread evenly.
  *Trade-off*: acting on this without the diagnostic pass means guessing between two incompatible edits — subtract from the contract, or scale up the complex exemplar. They pull in opposite directions and would cancel.
  → **Recommendation**: treat the diagnostic pass as a genuine prerequisite rather than a formality. It is the only step that distinguishes "every answer is 20% too long" from "three answers are the wrong tier", and those demand opposite fixes. Everything below is conditional on it.

- **Fix the complexity trigger — cheap and certain, but not the headline lever.**
  The current rule reads *"Complexo (múltiplos problemas distintos **ou** impacto/severidade explícitos)"* (`bug_to_user_story_v2.yml:26`). Dataset example 8 is a **single**-problem medium bug that ends with `Severidade: ALTA - vazamento de dados pessoais`. The disjunction fires on it, so the model emits the full `===`-banner complex format — banners, technical criteria, bug context, suggested tasks — against a reference that is a modest medium-format answer.

  **The blast radius is one example, not five.** Scanning all 15 bug reports for explicit severity/impact markers (`Severidade`, `IMPACTO`/`Impacto`, `SLA`, `crítico`), example 8 is the **only** non-complex report that carries one; the three complex reports (13-15) all do, and the other eleven carry none. Examples 7, 10 and 11 contain impact-flavoured prose ("Usuários reclamando de lentidão no horário comercial", "ANR em alguns casos", "Sistema gera pedido mas não tem estoque para enviar") but no labelled severity, so the second disjunct is unlikely to fire on them.

  *Trade-off*: making the trigger stricter risks under-formatting a genuinely complex report; the mechanical test below removes that risk for this corpus. The more consequential implication is for **sequencing**: since exactly one example can be mis-tiered by this rule, the trigger fix cannot by itself account for a 0.07 precision deficit spread over 15 examples. One example moving from ~0.4 to ~0.9 is worth ~+0.03 on the average at best. **The precision deficit must therefore be broad-based over-production across all three tiers, not a tier misfire** — which promotes the Reference Size Budget and the subtractive edits (ledger changes 1-3) above the trigger fix in expected value, and makes the diagnostic pass the only way to confirm it.
  → **Recommendation**: still fix the trigger — it is cheap, certain, and removes a known defect — but stop treating it as the headline lever.

  **The trigger must be phrased as a single mechanical test, and "counts numbered items" is the wrong one.** The obvious simplification — "3+ numbered items ⇒ complex" — misfires on two medium reports: ex. 6 numbers five items under `Steps to reproduce:` and ex. 11 numbers six under `Fluxo do bug:`. Both are *sequences*, not problem sets. The signal that separates the corpus cleanly is that complex reports carry an explicit **problems list whose items are labelled with a domain category**, under a heading of the form `PROBLEMAS…:`:

  | Example | Enumeration heading | Item labels | Tier |
  |---------|--------------------|-------------|------|
  | 6 | `Steps to reproduce:` | none (sequential steps) | medium |
  | 11 | `Fluxo do bug:` | none (sequential steps) | medium |
  | 13 | `PROBLEMAS IDENTIFICADOS:` | SEGURANÇA / INTEGRAÇÃO / LÓGICA DE NEGÓCIO / UX | complex |
  | 14 | `PROBLEMAS:` | PERFORMANCE / … (4) | complex |
  | 15 | `PROBLEMAS REPORTADOS:` | CONFLITO DE DADOS / … (4) | complex |

  A corroborating ordinal signal, useful for validating the diff harness rather than for stating in the prompt: input length separates the three tiers with no overlap and wide gaps — simple 63-85 chars, medium 238-322, complex 977-2 559.

- **Delete the speculation taught by few-shot Example 2.**
  Rule (a) says *"Nunca invente informações que não estejam presentes no relato do bug"*, but the prompt's own medium exemplar then demonstrates `Causa provável: recursão ou acúmulo de chamadas sem otimização para volumes grandes de páginas` — a cause the bug report never states. Demonstration reliably overrides stated rule. The reference corpus never speculates about unstated causes: example 7's `Problema identificado: falta de índice na coluna data_venda` restates a fact the bug report explicitly gave.
  *Trade-off*: dropping "causa provável" slightly reduces content volume, which could nick recall. F1 at 0.90 leaves headroom to absorb that.
  → **Recommendation**: rewrite Example 2's technical section to restate only bug-report facts; state the restriction as a demonstrated pattern, not just a rule.

- **Reverse rule (e) — restatement of bug facts is required, not forbidden.**
  Rule (e) currently forbids repeating the bug report. The references do the opposite: example 9 states `Bug atual: desconto sendo aplicado apenas no primeiro produto / Resultado incorreto: R$ 1.400`, example 12 states `z-index modal (1000) < z-index menu (1050)`, example 7 states `Performance atual: >120s`. Suppressing this costs points on precision's "Correção Factual" (which compares against the reference) while gaining nothing, because the anti-redundancy concern is already covered by clarity's Concisão criterion.
  *Trade-off*: over-restating would hurt Concisão. Scope the permission to context sections only.
  → **Recommendation**: replace the blanket prohibition with "restate bug-report facts verbatim inside context sections; never re-narrate the report as prose".

- **Align section vocabulary and reserve `===` banners for the complex tier.**
  12 of 15 references use plain `Header:` lines; only the 3 complex ones use `=== BANNER ===`. The v2 contract names only `Contexto Técnico` for medium, but the corpus uses `Contexto do Bug` and `Contexto de Segurança` too, and 5 of 7 medium references carry a *second* criteria group that the v2 contract does not describe at all. This mismatch reads as a structural error to clarity's Organização sub-score.
  *Trade-off*: enumerating more section names risks the model emitting all of them. Frame them as a menu selected by bug type (security → `Contexto de Segurança`, etc.), not as a checklist.
  → **Recommendation**: teach the medium tier a two-section pattern (one supplementary criteria group + one context section) with type-driven naming.

- **Add `=== USER STORY PRINCIPAL ===` to the complex contract.**
  All three complex references open with the US paragraph and then a `=== USER STORY PRINCIPAL ===` block containing `Título:` and `Descrição:`. The v2 contract and Example 3 both omit it. Cheap structural win on 3 examples across f1, clarity and precision.

- **Use system-as-actor persona for system-level bugs.**
  Rule (b) mandates `Como um [persona]` and the vague-report edge case instructs the model to *infer a plausible persona*. But 3 of the 15 references open with the system as the actor — ex. 6 `Como o sistema de e-commerce…`, ex. 8 `Como o sistema…`, ex. 11 `Como o sistema de e-commerce…` — in each case a bug with no human-facing surface (webhook delivery, endpoint authorisation, stock validation at checkout). The prompt as written pushes the model to invent a human role on exactly those three, which reads to "Correção Factual" as a mismatch against the reference's opening line, the single most heavily-weighted sentence in the answer.
  *Trade-off*: the distinction is a judgement call the subject has to make, and `gpt-4o-mini` may over-apply it to user-facing bugs, which would damage 12 examples to fix 3. Gate it narrowly on the actor being a backend process rather than on the bug being "technical".
  → **Recommendation**: state that when the affected actor is a backend process or the system's own integrity rules, the persona is the system itself (`Como o sistema…`); otherwise a human role. Demonstrate it — the three exemplars are all human-persona today, so the rule has no supporting demonstration.

- **Reduce the branching, not just the output.**
  With `gpt-4o-mini` as the subject (see *Solution Direction*), prompt complexity is itself a failure mode. The current prompt stacks 5 lettered rules, a 4-step internal reasoning chain, a 3-branch output contract, a 3-case edge-case list and 3 exemplars, several of which restate or contradict each other — rule (a) forbids invention while exemplar 2 demonstrates it; rule (e) forbids restatement while the corpus requires it; the reasoning chain's step 3 duplicates the output contract's tier definitions.
  *Trade-off*: removing the explicit CoT scaffold risks the `techniques_applied` claim and the `test_few_shot_examples` / persona assertions in `tests/test_prompts.py`. Chain-of-Thought can be retained as a shorter directive without the numbered four-step block.
  → **Recommendation**: collapse the duplicated tier logic into one place, delete rules that the exemplars contradict, and keep the technique inventory intact. Expected gain is on clarity via Organização, with a secondary effect on tier-trigger reliability.

- **Suppress reasoning leakage — verify before fixing.**
  The prompt says the four reasoning steps are to be followed *"internamente"* but never says the reasoning must not appear in the output, so a leaked preamble ("1. Persona identificada: …") would damage Concisão, Organização and "Foco na Pergunta" simultaneously. This was previously listed here as a likely cause on the assumption that the subject was a thinking model; it is not (`gpt-4o-mini`), so leakage is now only a cheap possibility rather than a hypothesis worth acting on blind.
  → **Recommendation**: let the diagnostic pass answer it — the structural diff detects a leaked preamble deterministically. Add the output-only instruction only if it appears. Near-zero cost either way.

- **Target ≈0.85, not 0.80.**
  Clarity printed as `0.80 ✗` means the true value lies in `[0.7950, 0.7999]` — `display_results` formats with `:.2f` while the threshold check uses the unrounded value. Tuning to exactly 0.80 will not survive judge variance: `gpt-4o` at `temperature=0` is not bit-reproducible, and each judge score is the model's own arithmetic mean over 3-4 sub-criteria it also produces, so per-example jitter compounds before averaging.

### Alternatives Considered

- **Add more content / more sections to raise scores** — rejected *as a general direction*. F1 0.90 vs precision 0.73 is the signature of over-production, not under-production; adding material across the board would push precision further down. The one deliberate exception is the complex tier, where exemplar 3 is measurably ~60% under the reference size budget and two reference sections are absent from the contract entirely (ledger change 7). Adding there is a targeted correction against measured evidence, not enrichment — and it is the first change to revert if precision fails to move.
- **Change `EVAL_MODEL` (currently `gpt-4o`)** — rejected as a remediation. It changes the measuring instrument rather than the artefact under test, and any resulting score movement would be uninterpretable against previous iterations.
- **Upgrade `LLM_MODEL` from `gpt-4o-mini` to `gpt-4o`** — rejected, but honestly the most likely single change to clear all five thresholds, since the *Solution Direction* argues the subject's instruction-following capacity is a binding constraint. It is rejected because the challenge is to optimise the prompt, not the runtime: a pass obtained by upgrading the subject would demonstrate nothing about the prompt, and it would make the subject and judge the same model, introducing self-preference bias that is absent today. Worth stating explicitly in the README as a deliberate constraint rather than leaving it unexamined.
- **Modify the judge rubrics or thresholds in `metrics.py` / `evaluate.py`** — prohibited by `PROJECT_INSTRUCTIONS.md`.
- **Edit the dataset references to match the prompt's output** — prohibited, and inverts the exercise.
- **Chase the four unused specialised metrics** (`evaluate_tone_score`, `evaluate_acceptance_criteria_score`, `evaluate_user_story_format_score`, `evaluate_completeness_score`) — rejected. `evaluate.py:30` imports only three functions; the other four cannot influence the reported score.

### Change Ledger

Each decision above, bound to the lines it touches and to a prediction that the next run can falsify. Predicted deltas are **estimates to be tested, not commitments** — their purpose is that after the next `evaluate.py` run you can tell which change did nothing, instead of attributing a single aggregate movement to eight simultaneous edits. Ordered by expected leverage.

| # | Change | `v2.yml` lines | Examples affected | Metric targeted | Predicted | Falsified if |
|---|--------|----------------|-------------------|-----------------|-----------|--------------|
| 1 | Rewrite exemplar 2's technical section to restate only bug-report facts (drop `Causa provável`) | 62 | all medium (6-12) | precision | +0.02 – 0.04 | no invented causes appear in the generated answers |
| 2 | Reverse rule (e): restate bug facts verbatim **inside context sections**, never re-narrate as prose | 15 | 6-12 | precision, f1 | +0.02 | clarity/Concisão falls by more than precision rises |
| 3 | Reduce branching; delete rules the exemplars contradict; collapse duplicated tier logic | 11-31 | all 15 | clarity | +0.02 | clarity is unchanged and f1 drops |
| 4 | Medium contract → always a context section (type-named), plus a second criteria group when a distinct actor/concern exists | 25 | 6-12 | clarity, f1 | +0.03 | medium answers already emit both sections |
| 5 | Tier trigger → labelled-problems-list test only; severity/impact demoted to a context-section cue | 26 | **8 only** (sole non-complex report with a severity label) | precision | +0.02 – 0.03 | the diff shows ex. 8 already tiering as medium |
| 6 | System-as-actor persona for backend/system-integrity bugs | 12, 31 | 6, 8, 11 | precision, f1 | +0.02 | those three already open with `Como o sistema` |
| 7 | Add `=== USER STORY PRINCIPAL ===` (Título/Descrição) and `=== MÉTRICAS DE SUCESSO ===` to the complex contract; scale exemplar 3 toward the 92-161-line budget | 26, 64-103 | 13-15 | f1 (protect) | 0 – +0.02 | precision falls on 13-15 (over-production) |
| 8 | Output-only instruction suppressing the reasoning scaffold | 17-21 | all 15 | clarity, precision | 0, unless leakage is observed | no leaked preamble in the diff — then skip the change |

Three ledger-level cautions. **The ordering is conditional on the diagnostic pass**, not established by it — the sequence above reflects expected leverage given that only one example (8) can be mis-tiered, so broad subtractive edits outrank the trigger fix; if the diagnostic instead shows a handful of examples badly mis-shaped, changes 5 and 7 move to the top. **Changes 2, 4 and 7 push toward more content while 1, 3 and 5 push away**; if the aggregate barely moves, the likely explanation is that they cancelled, and the per-example table is what separates them. And **change 7 is the only purely additive one**: it spends precision headroom to protect f1 on the three complex examples. If the next run shows f1 holding but precision still short, change 7 is the first to revert.

Summing the optimistic column gives roughly +0.13 on precision and +0.07 on clarity. Precision needs +0.07 to clear the threshold and +0.12 to reach the 0.85 margin target; clarity needs +0.005 to clear and +0.055 to reach 0.85. The budget is therefore adequate only if most predictions land near the top of their range — which is the argument for making all eight changes in one iteration rather than testing them singly at 60 calls each, and for treating a result that merely clears 0.80 as not yet done.

---

## Risk & Gap Analysis

### Requirement Ambiguities

- **Which of the 15 examples actually failed is unknown.** `evaluate.py:214` prints a per-example `[i/15] F1/Clarity/Precision` line, but only the aggregate summary was captured. A 0.73 mean could be twelve answers at 0.78 or three answers at 0.35 — these demand opposite fixes. This must be resolved before editing the prompt.
- **The judges' `reasoning` strings are computed and discarded.** Every hypothesis in this document is inferred from rubric text and reference structure rather than from the judges' stated objections.
- **"Persona inferida"** — the prompt authorises inferring a plausible persona for vague reports. The references do infer personas for user-facing bugs ("Como um cliente navegando na loja"), so this is legitimate; but the permission is stated adjacent to technical-cause inference, blurring where invention stops, and it is silent on the system-as-actor case that 3 of 15 references use (see *Persona Polarity*).

**Resolving these — the diagnostic pass.** One throwaway script, run once, outside `src/`, importing `metrics.py` without modifying it (permitted: `PROJECT_INSTRUCTIONS.md` forbids changing the pipeline files, not reading them). It pulls the same Hub prompt `evaluate.py` does, generates the 15 answers, and emits one row per example combining two independent evidence sources:

| Column group | Source | Cost |
|---|---|---|
| tier emitted, section headers emitted vs. reference's, AC bullet counts, char/line length vs. the Reference Size Budget, leaked-preamble flag, persona polarity of the opening line | deterministic string analysis of the generated answer | zero LLM calls |
| f1 / clarity / precision per example **plus the `reasoning` string each judge returns** | `metrics.py` | 45 `gpt-4o` calls |

Total 60 calls — the same as one `evaluate.py` run. The deterministic half is what makes ledger changes 4, 5, 6 and 8 checkable before spending anything; the judge reasoning explains only what the structural diff cannot. Persist the raw output to a file: at 15 examples × 3 reasonings it will not fit comfortably in a terminal scrollback, and it is the baseline the next iteration is diffed against.

### Edge Cases

- **Example 8 (medium, single problem, explicit `Severidade: ALTA`)** — the clearest tier-misclassification candidate; worth checking first in the per-example output.
- **Examples 10 and 11** — medium references that use `Critérios Técnicos` and `Contexto do Bug`, section names the v2 contract assigns exclusively to the complex tier. Even correctly classified as medium, the prompt gives the model no licence to emit them.
- **Examples 6 and 11 — the numbered-list trap.** Both are medium reports containing top-level numbered lists (5 and 6 items) under `Steps to reproduce:` and `Fluxo do bug:`. Any tier trigger that keys on enumeration *count* rather than on the items being labelled distinct problems will promote both to the complex tier — a fix that would cost more precision than the mis-calibration it replaces. Noted because it is the obvious simplification and it is wrong.
- **The medium context-section gate is wrong in all 7 cases, not one.** `bug_to_user_story_v2.yml:25` gates the context section on the report mentioning "logs, endpoints ou causas técnicas", but **every** medium reference (6-12) carries a context section, including ex. 11, a pure business-logic flow with no logs, endpoints or stack traces. The gate should be removed, not widened.
- **Example 15** — the only reference ending in `=== MÉTRICAS DE SUCESSO ===`. One of three complex examples; a missing section here costs ~1/3 of the complex-tier f1 and clarity contribution.
- **Simple tier "3-5 bullets"** — all five simple references have exactly 5. An answer at the low end of the authorised range loses recall for no benefit.

### Technical Risks

- **The actual runtime configuration.** `.env` sets `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini` (the subject executing the prompt) and `EVAL_MODEL=gpt-4o` (all three judges). An earlier revision of this document recorded these as `google` / `gemini-2.5-flash` for both roles, which is the commented-out block in `.env` — retained there with a note that `gemini-2.5-flash` now returns 404 for new accounts. The correction removes one risk entirely and reframes two others; the three bullets below supersede it.
- **Subject and judge are asymmetric, and the subject is the weaker model.** `gpt-4o-mini` is being graded by `gpt-4o`. There is no self-preference bias — the two are different models — but the asymmetry is itself the more consequential fact: the judge can reliably detect structural and volume deviations that the subject cannot reliably avoid. This is the basis for treating prompt complexity as a lever (see *Solution Direction* and ledger change 3). Worth stating explicitly in the README write-up.
- **Judge nondeterminism at the 0.8 boundary.** Both models run at `temperature=0`, which is not a determinism guarantee for `gpt-4o`; and each of the three judge scores is a mean the *model itself* computes over 3-4 sub-criteria it also generates, so per-example jitter compounds before the 15-example average is taken. Clarity sitting at ~0.795 could cross 0.8 on a re-run with no prompt change — or fall back below it after a genuine improvement. Mitigation: build margin to ~0.85 and do not treat a single borderline run as signal.
- **Cost per iteration.** One `evaluate.py` run = 15 `gpt-4o-mini` generations + 45 `gpt-4o` judge calls = **60 LLM calls**, and the judge calls carry nearly all the cost — each embeds the bug report, the full generated answer and the full reference, which for the complex examples is 3.6-5.8 kB of reference alone. This is a spend constraint rather than a quota constraint. A run that fails mid-way yields partial averages over fewer examples (`evaluate.py:205` skips examples with empty answers, and the mean is taken over successful ones only — a silent sample-size change).
- **`LANGSMITH_PROJECT` is set but empty.** `evaluate.py:298` reads `os.getenv("LANGSMITH_PROJECT", "prompt-optimization-challenge-resolved")`, but `.env` contains `LANGSMITH_PROJECT=`, so the variable exists as `""` and the default never applies. The eval dataset is consequently created and reused under the literal name `-eval`, and the "confira os resultados" URL printed on success points at an empty project path. Harmless to the scores — the dataset is reused as-is either way — but it makes the LangSmith dashboard evidence for the README write-up hard to locate, and it should be set before the run that is meant to produce screenshots.
- **Push/evaluate desynchronisation.** `evaluate.py` scores the Hub commit exclusively. Editing the YAML and re-running `evaluate.py` without `push_prompts.py` silently re-measures the *previous* prompt — indistinguishable from "my fix did nothing".
- **Prompt-template brace collisions.** The system prompt uses `[persona]`-style square brackets throughout; introducing literal `{` or `}` while editing would be interpreted as a template variable by `ChatPromptTemplate` and fail at `chain.invoke`, surfacing as a per-example exception rather than a clear error.
- **`tests/test_prompts.py` must still pass** after edits — persona presence, few-shot presence, Markdown/User-Story mention, no `TODO`, ≥2 `techniques_applied`. Subtractive edits could plausibly break the persona or few-shot assertions.

### Acceptance Criteria Coverage

The ACs here are the five metric thresholds from `PROJECT_INSTRUCTIONS.md` §4.

| AC# | Description | Current | Addressable? | Gaps/Notes |
|-----|-------------|---------|--------------|------------|
| 1 | Precision ≥ 0.8 | 0.73 | Yes | Primary target. Driven mainly by broad-based over-production — speculation taught by Example 2, the anti-restatement rule, and prompt-branching drift — with tier over-firing (ex. 8) contributing at most one example. Needs +0.07 to clear, +0.12 for margin; carries 40% of aggregate weight. |
| 2 | Clarity ≥ 0.8 | ~0.795 | Yes | Marginal — true value is in `[0.795, 0.7999]`. Concisão and Organização sub-scores; same root causes plus `===` banners on non-complex tiers. Must reach ~0.85 to be stable. |
| 3 | Helpfulness ≥ 0.8 | 0.765 | Yes | Purely derived: `(clarity + precision)/2`. No independent action; clears automatically once AC1 and AC2 clear. |
| 4 | Correctness ≥ 0.8 | 0.82 | Already passing | `(f1 + precision)/2`. Rises with precision. Only at risk if a subtractive fix damages f1. |
| 5 | F1-Score ≥ 0.8 | 0.90 | Already passing | **Must be protected, not improved.** The 0.10 headroom is the budget for subtractive edits. Adding the missing `=== USER STORY PRINCIPAL ===` and `=== MÉTRICAS DE SUCESSO ===` sections should offset any recall lost elsewhere. |

**Coverage gap**: no AC is unaddressable, but ACs 1 and 2 cannot be *targeted* accurately until the per-example scores, structural diff and judge reasoning are captured. The diagnostic pass is a prerequisite, not an optional step — and the evidence that only one example can be mis-tiered (see *Fix the complexity trigger*) means the deficit's location is currently unknown rather than merely unconfirmed.

---

## Missing Repo Context (from `/review-claude-md`)

Context that was absent and would have shortened this iteration. Each is proposed as a `CLAUDE.md` addition.

- **Score display rounds to 2 decimals while the threshold check does not.** `0.80 ✗` is not a contradiction — the true value is in `[0.795, 0.7999]` (`evaluate.py:253` vs `:262`).
- **Judge rubrics are composite means, and the sub-criteria are the real target.** Clarity = mean(Organização, Linguagem, Ambiguidade, **Concisão**); Precision = mean(Alucinações, **Foco na Pergunta**, Correção Factual). One weak sub-score drags a metric ~0.1.
- **Precision carries 40% of the aggregate** (`total = 1.5·clarity + 1.5·f1 + 2·precision`) — it is always the highest-leverage metric to fix.
- **The reference format taxonomy** (simple = 5 bullets only; medium = plain `Header:` sections, *all seven* with a type-named context section; complex = `===` banners with A-D groups) — the actual optimisation target, previously undocumented.
- **The reference size budget**: simple ≈ 400 chars / 8 lines, medium 664-963 chars / 14-20 lines, complex 3 605-5 756 chars / 92-161 lines. Gives the Concisão and "Foco na Pergunta" sub-criteria a testable target measurable without LLM calls.
- **Personas are not always human**: 3 of 15 references open `Como o sistema…` for backend/system-integrity bugs (ex. 6, 8, 11).
- **Bug-report input length separates the tiers cleanly** — simple 63-85 chars, medium 238-322, complex 977-2 559 — but *enumeration count does not*: two medium reports carry 5- and 6-item numbered lists that are reproduction sequences, not problem sets.
- **The judges return `reasoning` and `evaluate.py` throws it away.** Diagnosis requires a separate read-only script importing `metrics.py` — which does not violate the do-not-modify rule.
- **`evaluate.py` prints per-example scores**; capture that output rather than only the summary.
- **60 LLM calls per run** (15 × 4), and the averages are taken over *successful* examples only, so a partial failure silently changes the sample size.
- **`.env` runs an asymmetric pair**: `LLM_PROVIDER=openai` with `LLM_MODEL=gpt-4o-mini` as the subject and `EVAL_MODEL=gpt-4o` as the judge — a weaker model graded by a stronger one, with no self-preference bias but a real gap in instruction-following capacity. The commented-out `gemini-2.5-flash` block above it is dead config (404 for new accounts); read the active lines.
- **`LANGSMITH_PROJECT=` is set but empty**, so `evaluate.py`'s `getenv` default never fires and the LangSmith eval dataset is named `-eval`. Set it before any run intended to produce dashboard screenshots.
- **`{` and `}` in the system prompt are template variables** to `ChatPromptTemplate`; the prompt deliberately uses `[brackets]` instead.
- **`spdd/analysis/` and `spdd/prompt/` exist** in this repo and carry prior design context for the pipeline.
