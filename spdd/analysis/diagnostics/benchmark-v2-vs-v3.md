# Benchmark local — v2 (atual) vs v3

Pontuação idêntica a `evaluate.py`, prompts carregados do YAML local (sem push).

| Métrica | v2 | v3 | Δ | Limite |
|---------|----|----|---|--------|
| f1_score | 0.7539 | 0.7397 ✗ | -0.0142 | 0.80 |
| clarity | 0.8733 | 0.8667 | -0.0066 | 0.80 |
| precision | 0.7880 | 0.8093 | +0.0213 | 0.80 |
| helpfulness | 0.8307 | 0.8380 | +0.0073 | 0.80 |
| correctness | 0.7710 | 0.7745 ✗ | +0.0035 | 0.80 |

- v2 F1-recall (juiz): 0.7167 | v3: 0.6967
- **v2**: REPROVADO (correctness, f1_score, precision)
- **v3**: REPROVADO (correctness, f1_score)

## Δ por exemplo (F1 / Precision)

| # | tier | v2 F1 | v3 F1 | v2 Pre | v3 Pre |
|---|------|-------|-------|--------|--------|
| 1 | simple | 1.00 | 0.90 | 0.67 | 0.67 |
| 2 | simple | 0.80 | 0.80 | 0.90 | 0.90 |
| 3 | simple | 0.80 | 0.85 | 0.90 | 0.93 |
| 4 | simple | 0.60 | 0.60 | 0.67 | 0.67 |
| 5 | simple | 0.80 | 0.80 | 0.90 | 0.83 |
| 6 | medium | 0.69 | 0.69 | 0.67 | 0.67 |
| 7 | medium | 0.65 | 0.65 | 0.67 | 0.67 |
| 8 | medium | 0.75 | 0.69 | 0.67 | 0.80 |
| 9 | medium | 0.75 | 0.75 | 0.83 | 0.83 |
| 10 | medium | 0.85 | 0.75 | 0.90 | 0.90 |
| 11 | medium | 0.58 | 0.58 | 0.67 | 0.67 |
| 12 | medium | 0.69 | 0.69 | 0.67 | 0.90 |
| 13 | complex | 0.87 | 0.87 | 0.90 | 0.90 |
| 14 | complex | 0.75 | 0.75 | 0.90 | 0.90 |
| 15 | complex | 0.75 | 0.75 | 0.90 | 0.90 |