# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

A Full Cycle AI MBA challenge: pull a deliberately low-quality prompt from the LangSmith Prompt Hub, optimize it with prompt-engineering techniques, push it back, and iterate until 5 LLM-judged metrics all score >= 0.8. Full requirements are in `PROJECT_INSTRUCTIONS.md` (source of truth) and `README.md` (your write-up of the same, plus results). This file only covers what those two don't: how the code is wired and what's non-obvious.

## Commands

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python src/pull_prompts.py     # pull v1 from LangSmith Hub -> prompts/bug_to_user_story_v1.yml
python src/push_prompts.py     # push prompts/bug_to_user_story_v2.yml -> {username}/bug_to_user_story_v2 (public)
python src/evaluate.py         # pull v2 back from the Hub and score it against datasets/bug_to_user_story.jsonl

pytest tests/test_prompts.py -v
```

Docker (alternative to venv): `docker build -t prompt-opt . && docker run --env-file .env prompt-opt` — runs `evaluate.py` by default (`Dockerfile` uses `uv pip install`, no compose file).

## Architecture

- `src/pull_prompts.py`, `src/push_prompts.py` — **skeletons, bodies are `...`**. This is what you implement first. Use `langchain.hub.pull` / `hub.push`, and `utils.save_yaml` / `utils.load_yaml` for the local YAML round-trip.
- `src/evaluate.py`, `src/metrics.py`, `src/utils.py` — **complete, do not modify** (per `PROJECT_INSTRUCTIONS.md`).
- `prompts/bug_to_user_story_v1.yml` — the intentionally-bad prompt (already pulled). Problems are deliberate: `{bug_report}` duplicated in both system and user prompt, no persona, no examples, vague instructions.
- `prompts/bug_to_user_story_v2.yml` — **your deliverable, create from scratch**. Must include a `techniques_applied` list (>= 2 entries, enforced by `utils.validate_prompt_structure` and the `test_minimum_techniques` test) and no leftover `TODO` markers.
- `datasets/bug_to_user_story.jsonl` — 15 fixed examples (5 simple / 7 medium / 3 complex bugs), each `{"inputs": {"bug_report": ...}, "outputs": {"reference": ...}, "metadata": {...}}`. Never edit this file.
- `tests/test_prompts.py` — 6 stub tests (`pass` bodies) to implement against `prompts/bug_to_user_story_v2.yml`, loaded via the module-level `load_prompts()` helper and validated with `utils.validate_prompt_structure`.

## Evaluation pipeline gotchas

- `evaluate.py` only evaluates the **v2 prompt pulled live from the LangSmith Hub** — never the local YAML and never v1. A `push_prompts.py` run must succeed first, or `evaluate.py` fails with a "prompt not found" error and prints the exact remediation steps.
- Of the 7 metric functions in `metrics.py`, only 3 feed the actual eval run: `evaluate_f1_score`, `evaluate_clarity`, `evaluate_precision`. The 5 reported scores are derived from just those three:
  - `helpfulness = (clarity + precision) / 2`
  - `correctness = (f1_score + precision) / 2`
  - `f1_score`, `clarity`, `precision` reported as-is
- The other 4 functions (`evaluate_tone_score`, `evaluate_acceptance_criteria_score`, `evaluate_user_story_format_score`, `evaluate_completeness_score`) exist and are exercised by `metrics.py`'s own `if __name__ == "__main__"` smoke test, but **evaluate.py never calls them** — don't expect them to move your score.
- All 5 reported metrics must individually be >= 0.8 (checked, not just the average) for `evaluate.py` to print APROVADO.
- The eval dataset is auto-created in LangSmith on first run as `{LANGSMITH_PROJECT}-eval`; if a dataset with that name already exists it's reused as-is (no diffing against the current `.jsonl`).

## Environment

Copy `.env.example` to `.env` (gitignored) and fill in real values there — **never put real keys in `.env.example`**, it's tracked in git.

- `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `USERNAME_LANGSMITH_HUB` — required. Username is found by publishing any prompt to the Hub, opening it, and clicking the lock icon.
- `LLM_PROVIDER` — `openai` or `google`, switches which SDK `utils.get_llm` instantiates.
- `LLM_MODEL` — the model under test (drives `push`/pull-and-run). `EVAL_MODEL` — the judge model used by every function in `metrics.py`. Keep these distinct: OpenAI setups typically use `gpt-4o-mini` / `gpt-4o`; Gemini free-tier setups use `gemini-2.5-flash` for both.
- `OPENAI_API_KEY` required only if `LLM_PROVIDER=openai`; `GOOGLE_API_KEY` only if `google`.

## Workflow

1. `python src/pull_prompts.py` (once — v1 is already committed).
2. Hand-edit `prompts/bug_to_user_story_v2.yml`: few-shot examples are mandatory, plus at least one of CoT / Tree-of-Thought / Skeleton-of-Thought / ReAct / Role Prompting.
3. `python src/push_prompts.py`, then `python src/evaluate.py`.
4. Repeat 2-3 until all 5 metrics >= 0.8 (expect 3-5 iterations per `PROJECT_INSTRUCTIONS.md`).
5. Document technique choices and final metrics in `README.md`.
