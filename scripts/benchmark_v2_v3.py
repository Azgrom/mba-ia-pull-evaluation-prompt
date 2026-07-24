"""
Benchmark local (somente leitura) que compara dois prompts locais contra o
dataset, replicando EXATAMENTE a pontuação de src/evaluate.py — mas carregando
os prompts do YAML local, sem push para o Hub público.

Para cada exemplo: gera com o LLM_MODEL (gpt-4o-mini) e pontua com os três
juízes de metrics.py (EVAL_MODEL, gpt-4o). Agrega como evaluate.py:216-221:
    helpfulness = (clarity + precision) / 2
    correctness = (f1 + precision) / 2

Custo por prompt: 15 gerações + 45 chamadas de juiz = 60 chamadas de LLM.
NÃO modifica src/, datasets/ ou prompts/. NÃO faz push. Não é importado pelo pipeline.

Uso (a partir da raiz do repo, com a venv ativa):
    python scripts/benchmark_v2_v3.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from utils import load_yaml, get_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()

DATASET_PATH = "datasets/bug_to_user_story.jsonl"
PROMPTS = {
    "v2": "prompts/bug_to_user_story_v2.yml",
    "v3": "prompts/bug_to_user_story_v3.yml",
}
OUTPUT_PATH = "spdd/analysis/diagnostics/benchmark-v2-vs-v3.md"


def load_examples(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            rows.append({
                "index": i,
                "bug_report": p["inputs"]["bug_report"],
                "reference": p["outputs"]["reference"],
                "tier": (p.get("metadata", {}) or {}).get("complexity", "?"),
            })
    return rows


def build_chain(yaml_path, llm):
    data = load_yaml(yaml_path)
    node = data[next(iter(data))]  # single top-level prompt key
    prompt = ChatPromptTemplate.from_messages([
        ("system", node["system_prompt"]),
        ("user", node["user_prompt"]),
    ])
    return prompt | llm


def score_prompt(label, yaml_path, examples, llm):
    print(f"\n{'=' * 60}\nAvaliando {label}: {yaml_path}\n{'=' * 60}")
    chain = build_chain(yaml_path, llm)
    rows = []
    for ex in examples:
        try:
            answer = chain.invoke({"bug_report": ex["bug_report"]}).content
            f1 = evaluate_f1_score(ex["bug_report"], answer, ex["reference"])
            clarity = evaluate_clarity(ex["bug_report"], answer, ex["reference"])
            precision = evaluate_precision(ex["bug_report"], answer, ex["reference"])
            rows.append({
                "index": ex["index"], "tier": ex["tier"], "answer": answer,
                "f1": f1["score"], "f1_p": f1.get("precision"), "f1_r": f1.get("recall"),
                "clarity": clarity["score"], "precision": precision["score"],
                "reason_precision": precision["reasoning"],
            })
            print(f"  [{ex['index']:>2}/{len(examples)}] {ex['tier']:<7} "
                  f"F1:{f1['score']:.2f} (R:{f1.get('recall')}) "
                  f"Cla:{clarity['score']:.2f} Pre:{precision['score']:.2f}")
        except Exception as e:
            print(f"  [{ex['index']}] FALHA: {e}")
            rows.append({"index": ex["index"], "tier": ex["tier"], "error": str(e)})
    return rows


def aggregate(rows):
    ok = [r for r in rows if "error" not in r]

    def m(k):
        vals = [r[k] for r in ok if r.get(k) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    f1, clarity, precision = m("f1"), m("clarity"), m("precision")
    return {
        "n": len(ok),
        "f1_score": round(f1, 4),
        "clarity": round(clarity, 4),
        "precision": round(precision, 4),
        "helpfulness": round((clarity + precision) / 2, 4),
        "correctness": round((f1 + precision) / 2, 4),
        "f1_recall_half": round(m("f1_r"), 4),
    }


def verdict(agg):
    reported = ["helpfulness", "correctness", "f1_score", "clarity", "precision"]
    fails = [k for k in reported if agg[k] < 0.8]
    return ("APROVADO" if not fails else f"REPROVADO ({', '.join(fails)})")


def main():
    examples = load_examples(DATASET_PATH)
    llm = get_llm(temperature=0)

    results = {}
    for label, path in PROMPTS.items():
        rows = score_prompt(label, path, examples, llm)
        results[label] = {"rows": rows, "agg": aggregate(rows)}

    # ---- report ----
    lines = ["# Benchmark local — v2 (atual) vs v3", "",
             "Pontuação idêntica a `evaluate.py`, prompts carregados do YAML local (sem push).", "",
             "| Métrica | v2 | v3 | Δ | Limite |",
             "|---------|----|----|---|--------|"]
    keys = ["f1_score", "clarity", "precision", "helpfulness", "correctness"]
    a2, a3 = results["v2"]["agg"], results["v3"]["agg"]
    for k in keys:
        d = a3[k] - a2[k]
        flag = "" if a3[k] >= 0.8 else " ✗"
        lines.append(f"| {k} | {a2[k]:.4f} | {a3[k]:.4f}{flag} | {d:+.4f} | 0.80 |")
    lines += ["", f"- v2 F1-recall (juiz): {a2['f1_recall_half']:.4f} | v3: {a3['f1_recall_half']:.4f}",
              f"- **v2**: {verdict(a2)}", f"- **v3**: {verdict(a3)}", "",
              "## Δ por exemplo (F1 / Precision)", "",
              "| # | tier | v2 F1 | v3 F1 | v2 Pre | v3 Pre |",
              "|---|------|-------|-------|--------|--------|"]
    r2 = {r["index"]: r for r in results["v2"]["rows"]}
    r3 = {r["index"]: r for r in results["v3"]["rows"]}
    for i in sorted(r2):
        a, b = r2[i], r3[i]
        def g(r, k):
            return f"{r[k]:.2f}" if "error" not in r and r.get(k) is not None else "—"
        lines.append(f"| {i} | {a.get('tier','?')} | {g(a,'f1')} | {g(b,'f1')} "
                     f"| {g(a,'precision')} | {g(b,'precision')} |")

    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_PATH).write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    for k in keys:
        print(f"  {k:<13} v2 {a2[k]:.3f}  ->  v3 {a3[k]:.3f}  ({a3[k]-a2[k]:+.3f})")
    print(f"\n  v2: {verdict(a2)}")
    print(f"  v3: {verdict(a3)}")
    print(f"\nRelatório: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
