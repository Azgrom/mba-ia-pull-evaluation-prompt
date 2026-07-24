# SPDD Analysis: Bug-to-User-Story Prompt Optimization Pipeline

## Original Business Requirement

> Você deve entregar um software capaz de:
>
> 1. Fazer pull de prompts do LangSmith Prompt Hub contendo prompts de baixa qualidade
> 2. Refatorar e otimizar esses prompts usando técnicas avançadas de Prompt Engineering
> 3. Fazer push dos prompts otimizados de volta ao LangSmith
> 4. Avaliar a qualidade através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
> 5. Atingir pontuação mínima de 0.8 (80%) em todas as métricas de avaliação
>
> **Requisitos do prompt otimizado (Seção 2):**
> - Deve conter instruções claras e específicas
> - Deve incluir regras explícitas de comportamento
> - Deve ter exemplos de entrada/saída (Few-shot) — obrigatório
> - Deve incluir tratamento de edge cases
> - Deve usar System vs User Prompt adequadamente
> - Aplicar obrigatoriamente Few-shot Learning e pelo menos uma das seguintes: Chain of Thought (CoT), Tree of Thought, Skeleton of Thought, ReAct, Role Prompting
>
> **Critério de Aprovação (Seção 4):** TODAS as 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision) devem estar >= 0.8, não apenas a média. Espera-se 3-5 iterações.
>
> **Testes de Validação (Seção 5):** implementar 6 testes pytest em `tests/test_prompts.py` — presença de `system_prompt`, definição de persona, menção a formato Markdown/User Story, presença de few-shot examples, ausência de `[TODO]`, mínimo de 2 técnicas nos metadados.
>
> **O que já vem pronto (não alterar):** `src/evaluate.py`, `src/metrics.py`, `src/utils.py`, `datasets/bug_to_user_story.jsonl`.
>
> **O que deve ser implementado:** `prompts/bug_to_user_story_v2.yml` (do zero), `src/pull_prompts.py` (corpo, esqueleto existe), `src/push_prompts.py` (corpo, esqueleto existe), `tests/test_prompts.py` (corpo, esqueleto existe), `README.md`.
>
> Immediate trigger for this analysis: running `docker run --env-file .env prompt-opt` (which executes `src/evaluate.py`) failed with a 404 — `Resource not found for /commits/{username}/bug_to_user_story_v2/latest` — because `prompts/bug_to_user_story_v2.yml` does not exist yet and `push_prompts.py` has never been run. The user asked for a plan to design `prompts/bug_to_user_story_v2.yml` (and the pipeline around it) so that all 5 metrics reach >= 0.8, and requested it be run through `/spdd-analysis`.

## Domain Concept Identification

#### Existing Concepts (from codebase)

- **Prompt (local YAML)**: the versioned local representation of an LLM instruction set — `description`, `system_prompt`, `user_prompt`, `version`, `created_at`, `tags` fields, keyed under a top-level `bug_to_user_story_v{N}` mapping. Currently only `prompts/bug_to_user_story_v1.yml` exists, hand-crafted to be deliberately bad (`{bug_report}` duplicated in system and user prompt, no persona, no examples).
- **LangSmith Hub Prompt**: the remote, versioned counterpart identified by `{username}/{prompt_name}`, accessed via `langchain.hub.pull()` / `langsmith.Client().push_prompt()`. This is the single source of truth `evaluate.py` reads from — it never reads the local YAML.
- **Evaluation Dataset**: `datasets/bug_to_user_story.jsonl`, 15 fixed `{inputs: {bug_report}, outputs: {reference}, metadata: {domain, type, complexity}}` records (5 simple / 7 medium / 3 complex), mirrored into a LangSmith dataset named `{LANGSMITH_PROJECT}-eval` on first run and reused thereafter. Immutable per explicit instruction ("Não altere os datasets de avaliação").
- **Metric (LLM-as-Judge)**: `metrics.py` functions (`evaluate_f1_score`, `evaluate_clarity`, `evaluate_precision`, plus 4 unused-by-evaluate.py specialized functions) that prompt an evaluator LLM (`EVAL_MODEL`) for a JSON `{score, reasoning}` (or `{precision, recall, reasoning}` for F1) comparing generated `answer` against `reference`.
- **Derived Metric**: `evaluate.py` computes `helpfulness = (clarity + precision) / 2` and `correctness = (f1_score + precision) / 2` — only these 5 values (helpfulness, correctness, f1_score, clarity, precision) are checked against the 0.8 threshold.
- **Prompt Structural Validation**: `utils.validate_prompt_structure()` — checks required fields present, `system_prompt` non-empty and free of the literal string `TODO`, and `techniques_applied` has >= 2 entries. Independent of and narrower than the 6 pytest checks required by the challenge.

#### New Concepts Required

- **v2 Prompt Content**: the optimized `system_prompt` / `user_prompt` pair — does not exist yet. Must fix the v1 duplication defect, add persona, add explicit rules, add few-shot examples, add `techniques_applied` metadata (>= 2 entries, no leftover `TODO`).
- **Complexity-Adaptive Output Contract**: not an existing code concept, but a pattern *discovered by reading the dataset*: reference outputs for simple bugs are a short user story + ~5 acceptance-criteria bullets; medium bugs sometimes add a "Contexto Técnico" section; complex bugs (examples 13-15) use a much richer structure (Título, Descrição, lettered criteria groups A/B/C/D, Critérios Técnicos, Contexto do Bug, Tasks Técnicas Sugeridas organized by sprint/fase). The v2 prompt must teach the model to infer this depth from the bug report itself, since `evaluate.py` never passes the `metadata.complexity` field into the chain — only `{bug_report}` is passed as input.
- **`pull_prompts.py` implementation**: concrete logic to turn a pulled `ChatPromptTemplate` object into the existing local YAML schema (message template extraction, `save_yaml`).
- **`push_prompts.py` implementation**: concrete logic to build a `ChatPromptTemplate` from the local v2 YAML and publish it via `langsmith.Client().push_prompt(...)` with `is_public=True`, `description`, and `tags` (including `techniques_applied`).
- **Prompt Test Suite (`tests/test_prompts.py`)**: 6 concrete pytest assertions binding v2 YAML content to the challenge's explicit checklist, layered on top of (but not identical to) `utils.validate_prompt_structure`.

#### Key Business Rules

- All 5 reported metrics (Helpfulness, Correctness, F1-Score, Clarity, Precision) must **individually** be >= 0.8 — governs v2 Prompt Content quality bar and the iteration loop; average alone is insufficient (`display_results` in `evaluate.py` already enforces this).
- `techniques_applied` must list >= 2 techniques and `system_prompt` must contain zero `TODO` markers — governs v2 Prompt Content, double-enforced by `utils.validate_prompt_structure` and the pytest suite (AC6/`test_minimum_techniques`, `test_prompt_no_todos`).
- Few-shot examples are mandatory; at least one of CoT / ToT / SoT / ReAct / Role Prompting is mandatory — governs v2 Prompt Content technique selection.
- `evaluate.py` only ever scores the Hub-hosted `{username}/bug_to_user_story_v2` commit — governs sequencing: `push_prompts.py` must succeed before *every* `evaluate.py` run, not just the first.
- The dataset must never be edited — governs all iteration; only `prompts/bug_to_user_story_v2.yml` may change between rounds.
- `{bug_report}` must not be duplicated across system and user messages — this is the deliberate v1 flaw and the first thing v2 must fix.

## Strategic Approach

#### Solution Direction

Three-stage pipeline, following the repo's existing skeleton/complete-module split (`evaluate.py`/`metrics.py`/`utils.py` are finished; `pull_prompts.py`/`push_prompts.py` are the stated first implementation task):

1. **`pull_prompts.py`** hydrates the local YAML from the Hub (`leonanluppi/bug_to_user_story_v1` → `prompts/bug_to_user_story_v1.yml`); largely a verification step since `v1.yml` is already committed and matches the expected content.
2. **Hand-authored `prompts/bug_to_user_story_v2.yml`** encodes the optimized instructions — the actual quality-bearing artifact.
3. **`push_prompts.py` + `evaluate.py`** form the publish/score loop the user reruns every iteration (3-5 expected per the challenge instructions).

Data flow: `LangSmith Hub ⇄ local YAML (langchain.hub + save_yaml/load_yaml) ⇄ hand-editing ⇄ client.push_prompt() ⇄ evaluate.py scoring loop ⇄ LangSmith dashboard`.

v2 prompt content strategy (user-approved technique choice): a persona-driven system prompt (**Role Prompting** — senior Product Owner / Business Analyst) sets tone and empathy for Clarity; an explicit step-by-step analysis phase (**Chain-of-Thought** — identify actors, extract technical facts, classify complexity tier, *then* draft) drives Precision/F1 by making the model extract facts systematically rather than guessing; reinforced by 3 embedded **few-shot** examples, one per complexity tier, that concretely demonstrate the complexity-adaptive depth observed in the reference dataset.

#### Key Design Decisions

1. **Where does `{bug_report}` live?** → Only in the user/human message, never repeated in the system message. Trade-off: none — this strictly fixes the deliberate v1 defect. → System prompt carries role/rules/format/examples only; user message is just `"{bug_report}"`.

2. **How many few-shot examples, and how selected?** → Trade-off between prompt length/token cost and coverage of the reference's complexity-adaptive structure. → Exactly 3 hand-written examples (not verbatim dataset rows, since the dataset must stay a held-out eval set), one per complexity tier, each demonstrating the differing depth: plain 5-bullet criteria (simple) vs. + Contexto Técnico (medium) vs. full lettered A/B/C/D breakdown + tasks técnicas (complex).

3. **Reasoning mechanism: CoT vs. rigid Skeleton-of-Thought** → The reference structure *varies* by complexity rather than following one fixed skeleton; a rigid skeleton would force complex-style sections onto simple bugs and hurt Precision/Clarity there. → CoT: instruct the model to internally reason (actors → technical facts → complexity classification → draft) before producing the final structured output.

4. **`push_prompts.py` API choice: `langchain.hub.push` vs. `langsmith.Client().push_prompt`** → Confirmed via LangChain reference docs during this analysis that `Client().push_prompt(prompt_identifier, *, object, is_public, description, tags, commit_description, ...)` is the documented surface exposing exactly the `is_public`/`description`/`tags` parameters the requirement needs ("Adiciona metadados (tags, descrição, técnicas utilizadas)", "Deixá-lo público"). → Use `langsmith.Client().push_prompt()` directly rather than the thinner `hub.push` wrapper.

5. **`pull_prompts.py` extraction approach** → Iterate `prompt.messages`, read each message's `.prompt.template` to recover raw text, map `system`→`system_prompt` and `human`/`user`→`user_prompt`, then `save_yaml(...)` under the same `bug_to_user_story_v1:` top-level key structure already present in the committed `v1.yml` — so a re-run stays consistent with the currently committed file.

#### Alternatives Considered

- **ReAct**: rejected — no external tool/action loop exists in this single-shot generation task; ReAct's reason-then-act framing doesn't map onto "read bug report → write user story."
- **Tree-of-Thought**: rejected — adds output verbosity/latency without a clear metric payoff; the task is convergent (one correct-ish target per bug) rather than requiring exploration of divergent solution paths.
- **Rigid Skeleton-of-Thought for all complexity tiers**: rejected in favor of adaptive CoT (see Decision 3) — a single fixed skeleton can't represent both a 5-bullet simple answer and a 5-section complex answer without either bloating simple cases or truncating complex ones.

## Risk & Gap Analysis

#### Requirement Ambiguities

- `PROJECT_INSTRUCTIONS.md`'s example pull target is `leonanluppi/bug_to_user_story_v1` (a fixed, shared username) while the push target is `{seu_username}/bug_to_user_story_v2` (the developer's own `USERNAME_LANGSMITH_HUB`). `pull_prompts.py` must hardcode the fixed source; `push_prompts.py` must use the user's own env var — mixing these up would silently push to (or attempt to pull from) the wrong namespace.
- "Deixá-lo público" (Section 3, item 3) is a stated manual/process requirement, but `push_prompt`'s `is_public` defaults to `None` (private-for-new-prompts). This must be set to `True` explicitly on every push, not assumed to persist from a dashboard toggle done once.
- Whether `v1.yml`'s intentionally-bad content should be "fixed" during `pull_prompts.py` implementation — no: `CLAUDE.md` and `PROJECT_INSTRUCTIONS.md` are explicit that `v1.yml` is deliberately bad and untouched; only `v2` changes.

#### Edge Cases

- The dataset's `metadata.complexity` field is **not** passed into the chain at inference time — `evaluate_prompt_on_example` in `evaluate.py` only forwards `inputs = {"bug_report": ...}`. The v2 prompt cannot rely on an explicit complexity signal and must infer it from the bug_report text itself via the CoT reasoning step.
- Dataset example #4 has an unescaped/malformed quote in its reference JSON (`"status \"ativo` missing a closing quote) — not ours to edit, but worth knowing in case F1/Precision scoring on that specific example behaves oddly and needs to be discounted when diagnosing low scores.
- Complex bug reports (examples 13-15) are very long and multi-section; the model must stay within a reasonable output length while still covering all required sections — risk of truncating or under-covering one of the lettered criteria groups (A/B/C/D) on the longest inputs.
- LLM-as-judge scoring has known run-to-run variance even at `temperature=0`, depending on provider — score fluctuation between identical evaluation runs is a risk the prompt design can reduce (via unambiguous, deterministic-feeling instructions) but not eliminate.

#### Technical Risks

- `client.push_prompt` defaults `parent_commit_hash='latest'`; since `bug_to_user_story_v2` doesn't exist yet, the first push is effectively a create. `Client()` should pick up `LANGSMITH_API_KEY`/`LANGSMITH_ENDPOINT` from env the same way the already-working `evaluate.py`'s `Client()` call does — low risk, but worth a smoke check on first run.
- Gemini free-tier limits (15 req/min, 1500/day per `PROJECT_INSTRUCTIONS.md`) mean one `evaluate.py` run costs up to 15 examples × (1 generation + 3 metric calls) = ~60 LLM calls, i.e. a minimum ~4 minutes per run at the rate cap. 3-5 iteration cycles could approach the daily cap — a pacing risk to flag to the user, not something the code can route around.
- `save_yaml`'s `yaml.dump(..., sort_keys=False)` doesn't guarantee literal block (`|`) style survives every re-save of multi-line strings — a pull→push→pull round-trip could subtly reformat `system_prompt` whitespace. Worth a sanity diff after implementing `pull_prompts.py`, not a design blocker.

#### Acceptance Criteria Coverage

| AC# | Description | Addressable? | Gaps/Notes |
|-----|-------------|--------------|------------|
| 1 | `pull_prompts.py` implemented, pulls `leonanluppi/bug_to_user_story_v1`, saves to `prompts/bug_to_user_story_v1.yml` | Yes | Straightforward; v1.yml already committed gives a reference to validate against. |
| 2 | `prompts/bug_to_user_story_v2.yml` created with Few-shot + >= 1 of CoT/ToT/SoT/ReAct/Role | Yes | Role Prompting + CoT + Few-shot selected (user-approved). |
| 3 | v2 prompt has clear instructions, explicit behavior rules, few-shot examples, edge-case handling, appropriate system/user split | Yes | Directly covered by Key Design Decision 1 and the technique choice. |
| 4 | `push_prompts.py` implemented, pushes to `{username}/bug_to_user_story_v2` with metadata (tags, description, techniques), public | Yes | Covered by Key Design Decision 4 (`Client().push_prompt`). |
| 5 | All 5 metrics >= 0.8 | Partial | Design targets this via adaptive CoT + tiered few-shot, but actual attainment can only be confirmed empirically through iteration (3-5 rounds expected per the instructions) — this is a validation gap, not a design gap. |
| 6 | 6 pytest tests in `tests/test_prompts.py` implemented | Yes | Skeleton with correct test names already exists; bodies need implementing against the v2 YAML. |
| 7 | `README.md` documents techniques + results + comparison table + LangSmith dashboard evidence | Yes | Documentation task, sequenced after AC5 is empirically met — out of scope for this design's code-level decisions. |
