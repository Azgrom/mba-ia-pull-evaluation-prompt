"""
Script de diagnóstico (descartável, somente leitura) do prompt v2 publicado.

Produz uma linha de diagnóstico por exemplo do dataset, combinando duas fontes
de evidência independentes que se validam mutuamente:

1. Diff estrutural determinístico (zero chamadas de LLM): tier emitido vs.
   esperado, cabeçalhos de seção emitidos vs. os da referência, contagem de
   bullets de critérios, tamanho em chars/linhas, vazamento de preâmbulo e
   polaridade de persona.
2. As strings `reasoning` que os juízes retornam e que `evaluate.py:206-214`
   calcula e descarta.

Custo: 60 chamadas de LLM (15 gerações + 45 chamadas de juiz) — idêntico a uma
execução de `evaluate.py`.

NÃO modifica nenhum arquivo em `src/`, `datasets/` ou `prompts/`. Não é
importado por nenhum código do pipeline.

Uso: python scripts/diagnose_v2.py    (a partir da raiz do repositório)
"""

import os
import re
import sys
import json
from pathlib import Path

# Adicionar src ao path (mesmo padrão de tests/test_prompts.py:10)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from langchain import hub

from utils import get_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()

DATASET_PATH = "datasets/bug_to_user_story.jsonl"
OUTPUT_PATH = "spdd/analysis/diagnostics/iteration-3-baseline.md"

# Cabeçalho de seção: banner "=== X ===" ou linha "Header:" iniciada em maiúscula
BANNER_RE = re.compile(r"^===.*===$")
HEADER_RE = re.compile(r"^[A-ZÀ-Ú][^\n]{2,60}:$")
AC_BULLET_RE = re.compile(r"^- (Dado|Quando|Então|E )")


def extract_section_headers(text: str) -> list:
    """Extrai os cabeçalhos de seção de um texto (banners e linhas 'Header:')."""
    headers = []
    for line in text.splitlines():
        stripped = line.strip()
        if BANNER_RE.match(stripped) or HEADER_RE.match(stripped):
            headers.append(stripped)
    return headers


def count_ac_bullets(text: str) -> int:
    """Conta os bullets de critérios de aceitação (Dado/Quando/Então/E)."""
    return sum(1 for line in text.splitlines() if AC_BULLET_RE.match(line.strip()))


def classify_tier(text: str) -> str:
    """
    Classifica o tier de um texto (gerado ou referência) pela sua estrutura.

    - complex: contém qualquer banner '=== ... ==='
    - medium: contém ao menos um 'Header:' além de 'Critérios de Aceitação:'
    - simple: caso contrário
    """
    if any(BANNER_RE.match(line.strip()) for line in text.splitlines()):
        return "complex"

    other_headers = [
        h for h in extract_section_headers(text)
        if h != "Critérios de Aceitação:"
    ]
    return "medium" if other_headers else "simple"


def build_reference_index(jsonl_path: str) -> list:
    """
    Lê o JSONL e computa o perfil estrutural de cada referência.

    Returns:
        Lista de dicts com bug_report, reference, expected_tier e métricas
        estruturais da referência.
    """
    rows = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for index, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            payload = json.loads(line)
            reference = payload["outputs"]["reference"]

            rows.append({
                "index": index,
                "bug_report": payload["inputs"]["bug_report"],
                "reference": reference,
                "expected_tier": payload.get("metadata", {}).get("complexity", "?"),
                "refCharCount": len(reference),
                "refLineCount": len(reference.splitlines()),
                "refSectionHeaders": extract_section_headers(reference),
                "refAcBulletCount": count_ac_bullets(reference),
            })

    return rows


def analyse_structure(answer: str, ref: dict) -> dict:
    """
    Diff estrutural determinístico entre a resposta gerada e sua referência.

    Zero chamadas de LLM. É esta metade do diagnóstico que torna as mudanças
    4, 5, 6 e 8 do change ledger verificáveis antes de qualquer gasto.
    """
    answer_headers = extract_section_headers(answer)
    ref_headers = ref["refSectionHeaders"]

    answer_lines = [line for line in answer.splitlines() if line.strip()]
    opening_line = answer_lines[0].strip() if answer_lines else ""
    ref_opening = ref["reference"].splitlines()[0].strip()

    tier_emitted = classify_tier(answer)

    return {
        "tierEmitted": tier_emitted,
        "tierExpected": ref["expected_tier"],
        "headersMissing": [h for h in ref_headers if h not in answer_headers],
        "headersSurplus": [h for h in answer_headers if h not in ref_headers],
        "charCount": len(answer),
        "lineCount": len(answer.splitlines()),
        "charDelta": len(answer) - ref["refCharCount"],
        "acBulletCount": count_ac_bullets(answer),
        "refAcBulletCount": ref["refAcBulletCount"],
        "openingLine": opening_line,
        "bannerMisuse": "===" in answer and ref["expected_tier"] != "complex",
        "preambleLeak": not opening_line.startswith("Como "),
        "personaPolarityMismatch": (
            opening_line.startswith("Como o sistema")
            != ref_opening.startswith("Como o sistema")
        ),
    }


def run_diagnostic(prompt_id: str) -> list:
    """
    Gera as 15 respostas com o prompt publicado e as pontua com os três juízes.

    Falha rápido se o `hub.pull` quebrar (toda linha depende dele). Falhas por
    exemplo são capturadas e registradas — o loop nunca aborta, pois uma passada
    parcial ainda vale o que foi gasto.
    """
    print(f"📥 Puxando prompt do Hub: {prompt_id}")
    prompt_template = hub.pull(prompt_id)
    print("   ✓ Prompt obtido")

    references = build_reference_index(DATASET_PATH)
    print(f"   Dataset: {len(references)} exemplos")

    llm = get_llm(temperature=0)
    chain = prompt_template | llm

    rows = []

    for ref in references:
        index = ref["index"]

        try:
            answer = chain.invoke({"bug_report": ref["bug_report"]}).content

            delta = analyse_structure(answer, ref)

            f1 = evaluate_f1_score(ref["bug_report"], answer, ref["reference"])
            clarity = evaluate_clarity(ref["bug_report"], answer, ref["reference"])
            precision = evaluate_precision(ref["bug_report"], answer, ref["reference"])

            rows.append({
                "index": index,
                "expected_tier": ref["expected_tier"],
                "delta": delta,
                "answer": answer,
                "f1": f1["score"],
                "f1_precision": f1.get("precision"),
                "f1_recall": f1.get("recall"),
                "clarity": clarity["score"],
                "precision": precision["score"],
                "reasonings": {
                    "f1": f1["reasoning"],
                    "clarity": clarity["reasoning"],
                    "precision": precision["reasoning"],
                },
                "error": None,
            })

            print(
                f"      [{index}/{len(references)}] "
                f"F1:{f1['score']:.2f} Clarity:{clarity['score']:.2f} "
                f"Precision:{precision['score']:.2f} "
                f"| {delta['tierExpected']}→{delta['tierEmitted']} "
                f"| Δchars:{delta['charDelta']:+d}"
            )

        except Exception as e:
            print(f"      ⚠️  [{index}] Falha: {e}")
            rows.append({
                "index": index,
                "expected_tier": ref["expected_tier"],
                "delta": None,
                "answer": "",
                "f1": None,
                "f1_precision": None,
                "f1_recall": None,
                "clarity": None,
                "precision": None,
                "reasonings": {},
                "error": str(e),
            })

    return rows


def write_report(rows: list, out_path: str) -> None:
    """
    Escreve o relatório Markdown: tabela por exemplo, reasonings completos e
    rodapé com as médias calculadas como em `evaluate.py:216-218`.
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Diagnóstico v2 — baseline da iteração 3",
        "",
        "Gerado por `scripts/diagnose_v2.py` contra o commit publicado no Hub.",
        "As colunas F1-P (precision) e F1-R (recall) são as estimativas que o juiz",
        "de F1 calcula antes de tirar a média harmônica — é o recall que revela se a",
        "perda de F1 vem de omissão (recall baixo) ou de excesso (precision baixa).",
        "",
        "## Tabela por exemplo",
        "",
        "| # | Tier esp. | Tier emit. | Δchars | AC (ger/ref) | Banner indev. | Preâmbulo | Persona | Headers faltando | Headers sobrando | F1 | F1-P | F1-R | Clarity | Precision |",
        "|---|-----------|------------|--------|--------------|---------------|-----------|---------|------------------|------------------|----|------|------|---------|-----------|",
    ]

    def fmt(score):
        return f"{score:.2f}" if score is not None else "—"

    for row in rows:
        if row["error"]:
            lines.append(
                f"| {row['index']} | {row['expected_tier']} | ERRO | — | — | — | — | — | — | — | — | — | — | — | — |"
            )
            continue

        d = row["delta"]
        lines.append(
            f"| {row['index']} | {d['tierExpected']} | {d['tierEmitted']} "
            f"| {d['charDelta']:+d} | {d['acBulletCount']}/{d['refAcBulletCount']} "
            f"| {'SIM' if d['bannerMisuse'] else '-'} "
            f"| {'VAZOU' if d['preambleLeak'] else '-'} "
            f"| {'DIVERGE' if d['personaPolarityMismatch'] else '-'} "
            f"| {'; '.join(d['headersMissing']) or '-'} "
            f"| {'; '.join(d['headersSurplus']) or '-'} "
            f"| {fmt(row['f1'])} | {fmt(row['f1_precision'])} | {fmt(row['f1_recall'])} "
            f"| {fmt(row['clarity'])} | {fmt(row['precision'])} |"
        )

    lines += ["", "## Reasoning dos juízes", ""]

    for row in rows:
        lines.append(f"### Exemplo {row['index']} ({row['expected_tier']})")
        lines.append("")

        if row["error"]:
            lines += [f"**ERRO**: {row['error']}", ""]
            continue

        lines.append(f"**Linha de abertura**: `{row['delta']['openingLine']}`")
        lines.append("")

        for metric in ("f1", "clarity", "precision"):
            lines.append(f"- **{metric}** ({fmt(row[metric])}): {row['reasonings'][metric]}")

        lines.append("")

    # Rodapé: médias sobre exemplos bem-sucedidos apenas (como evaluate.py:205-218)
    ok = [r for r in rows if r["error"] is None]

    def mean(key):
        return sum(r[key] for r in ok) / len(ok) if ok else 0.0

    avg_f1, avg_clarity, avg_precision = mean("f1"), mean("clarity"), mean("precision")
    avg_f1_p, avg_f1_r = mean("f1_precision"), mean("f1_recall")

    lines += [
        "## Médias",
        "",
        f"- Exemplos bem-sucedidos: {len(ok)}/{len(rows)}",
        f"- F1-Score: {avg_f1:.4f}",
        f"  - F1 Precision (juiz): {avg_f1_p:.4f}",
        f"  - F1 Recall (juiz): {avg_f1_r:.4f}  ← se baixo, a perda de F1 é omissão, não excesso",
        f"- Clarity: {avg_clarity:.4f}",
        f"- Precision: {avg_precision:.4f}",
        f"- Helpfulness: {(avg_clarity + avg_precision) / 2:.4f}",
        f"- Correctness: {(avg_f1 + avg_precision) / 2:.4f}",
        "",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✓ Relatório escrito em: {out_path}")


def main():
    """Função principal"""
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurada no .env")
        return 1

    if not Path(DATASET_PATH).exists():
        print(f"❌ Dataset não encontrado: {DATASET_PATH}")
        print("   Execute este script a partir da raiz do repositório.")
        return 1

    rows = run_diagnostic(f"{username}/bug_to_user_story_v2")
    write_report(rows, OUTPUT_PATH)

    return 0


if __name__ == "__main__":
    sys.exit(main())
