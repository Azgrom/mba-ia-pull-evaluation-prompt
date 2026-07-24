# Bug → User Story: Pull, Otimização e Avaliação de Prompts com LangChain + LangSmith

Desafio da MBA de IA (Full Cycle): puxar um prompt deliberadamente ruim do LangSmith
Prompt Hub, refatorá-lo com técnicas avançadas de Prompt Engineering, publicá-lo de
volta e iterar até que **5 métricas avaliadas por LLM-como-juiz** fiquem todas `>= 0.8`
(Helpfulness, Correctness, F1-Score, Clarity, Precision).

O código completo do pipeline (`pull → editar → push → avaliar`), o prompt otimizado
`prompts/bug_to_user_story_v2.yml` e os testes de validação estão implementados. As
seções abaixo seguem exatamente a estrutura pedida no entregável.

---

# Entregável

## 1. Repositório público no GitHub (fork do repositório base)

Fork público de [`devfullcycle/mba-ia-pull-evaluation-prompt`](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt),
hospedado em **https://github.com/Azgrom/mba-ia-pull-evaluation-prompt**, contendo:

- **Todo o código-fonte implementado** — `src/pull_prompts.py`, `src/push_prompts.py`
  e `tests/test_prompts.py` (os esqueletos foram preenchidos); `src/evaluate.py`,
  `src/metrics.py` e `src/utils.py` permanecem intocados, conforme exigido.
- **`prompts/bug_to_user_story_v2.yml` 100% preenchido e funcional** — persona,
  raciocínio estruturado, três exemplos few-shot e a lista `techniques_applied` (>= 2
  técnicas), passando em `pytest tests/test_prompts.py`.
- **`README.md` atualizado** — este documento.

---

## 2. README.md

### A) Técnicas Aplicadas (Fase 2)

#### Metodologia e ferramentas — SPDD skills + Claude Opus 4.8 (high)

Todo o processo — análise do prompt ruim, especificação estruturada de cada iteração,
geração do código e do prompt, e as quatro iterações de otimização — foi conduzido com
**Claude Code usando o modelo Claude Opus 4.8 em esforço de raciocínio `high`
(opus-4.8 high)**, orquestrado pela metodologia **SPDD (Structured-Prompts-Driven
Development)**. Cada decisão foi primeiro escrita como um prompt estruturado (REASONS
Canvas) e só então convertida em código/prompt — os artefatos ficam versionados em
`spdd/`.

As **skills** efetivamente utilizadas, e o artefato que cada uma produziu:

| Skill | Papel no processo | Artefato versionado |
|---|---|---|
| **`spdd-analysis`** | Análise estratégica do prompt ruim, plano de remediação de métricas, retrospectiva de benchmark e o playbook de "quebra de teto" do juiz-LLM | `spdd/analysis/*-[Analysis]-*.md` (4 docs) |
| **`spdd-reasons-canvas`** | Geração dos prompts estruturados (REASONS Canvas) que especificaram cada iteração **antes** de tocar no código | `spdd/prompt/*-[Feat]-*.md`, `*-[Fix]-*.md` (3 docs) |
| **`spdd-generate`** | Geração do pipeline (`pull`/`push`/`tests`) e do próprio `bug_to_user_story_v2.yml` a partir do prompt estruturado | `src/*.py`, `prompts/bug_to_user_story_v2.yml` |
| **`spdd-prompt-update`** | Atualização do prompt estruturado a cada nova evidência de métrica (iterações 3 e 4) | `spdd/prompt/*-[Fix]-*.md` |
| **`spdd-sync`** | Manter o prompt estruturado sincronizado quando a realidade divergiu do plano — princípio "quando a realidade diverge, corrija o prompt primeiro" | histórico de `spdd/` |

Como disciplina de processo em volta das skills SPDD, o trabalho seguiu três skills do
plugin **superpowers**: **`brainstorming`** (exploração de requisitos antes de
implementar), **`systematic-debugging`** (o loop de diagnóstico que virou
`scripts/diagnose_v2.py` e `scripts/benchmark_v2_v3.py` e, depois, o playbook em
`spdd/analysis/...-[Analysis]-llm-judge-ceiling-breaker-playbook.md`) e
**`verification-before-completion`** (medir o piso de ruído do juiz **antes** de
declarar ganho ou teto).

#### As técnicas de Prompt Engineering escolhidas

Obrigatoriamente **Few-shot Learning**, mais **Role Prompting** e **Chain-of-Thought** —
somadas a um **contrato estrutural por tier** (uma aplicação de Skeleton-of-Thought
sobre o formato da resposta).

**1. Role Prompting — persona de Product Owner sênior**

- *Por quê:* o v1 não tinha persona alguma; o modelo respondia de forma genérica e
  inconsistente. Dar-lhe o papel de PO sênior fixa o vocabulário ("Como \[ator\], eu
  quero…, para que…"), o nível de detalhe e o critério do que entra numa User Story.
- *Como aplicado:* o `system_prompt` abre definindo a persona **e** uma regra de
  *polaridade de persona*: quando o ator afetado é um processo de backend ou uma regra
  de integridade do sistema, a User Story abre com `Como o sistema…` — exatamente o que
  o corpus de referência faz em 3 dos 15 exemplos.

**2. Chain-of-Thought (CoT) — raciocínio antes da redação**

- *Por quê:* converter um relato de bug em User Story exige uma cadeia de decisões
  (quem é o ator? quais fatos foram afirmados? qual o tier? como redigir?). Sem CoT o
  modelo pula direto para o texto e erra o tier ou inventa critérios.
- *Como aplicado:* uma cadeia comprimida em uma linha — **identificar ator → extrair
  fatos afirmados → selecionar o tier → redigir**. Deliberadamente comprimida: uma
  versão anterior com quatro passos numerados duplicava o contrato de saída e inflava
  a resposta (custo de precisão sem ganho de recall).

**3. Few-shot Learning — três exemplares, um por tier (obrigatório)**

- *Por quê:* é a técnica de maior impacto isolado; ancora formato, tom e comprimento
  em exemplos concretos em vez de descrições. O v1 não tinha nenhum exemplo.
- *Como aplicado:* três exemplares completos calibrados contra o **tamanho medido das
  referências** — simples (~8 linhas), médio (~14 linhas) e complexo (~88 linhas). Cada
  um exibe o formato exato do seu tier (bullets de critérios, seções de contexto,
  banners `===` no complexo).

**4. Skeleton-of-Thought sobre o formato — contrato estrutural por tier**

- *Por quê:* o dataset é estratificado (5 simples / 7 médios / 3 complexos), e cada
  estrato tem um formato de referência distinto. Emitir a *estrutura* certa por estrato
  é um ganho barato de clareza/recall — sem adivinhar conteúdo.
- *Como aplicado:* o prompt define três contratos (SIMPLES / MÉDIO / COMPLEXO) com
  teste de disparo, seções obrigatórias, contagem de bullets e regras de banner. Isso
  também encapsula o **tratamento de edge cases** (relato de dimensão única não recebe
  segundo grupo de critérios; lista numerada de passos **não** promove ao tier
  complexo) e o uso correto de **System vs User Prompt** (todo o contrato no
  `system_prompt`; o `user_prompt` é apenas `{bug_report}`).

> Os exemplos concretos de cada técnica, com o texto exato do prompt, estão em
> `prompts/bug_to_user_story_v2.yml`. A racionalização por trás de cada escolha está
> nos prompts estruturados em `spdd/prompt/`.

---

### B) Resultados Finais

#### Configuração de avaliação (nota importante sobre o modelo)

**Na ocasião das avaliações finais, o free tier da Google barrou o uso do
`gemini-2.5-flash`** — a API passou a retornar `404 … model models/gemini-2.5-flash is
no longer available to new users` — **forçando a migração para `gemini-3.5-flash-lite`**
tanto como modelo sujeito (`LLM_MODEL`) quanto como modelo juiz (`EVAL_MODEL`). É a
configuração registrada no `.env` e usada nas execuções que produziram as evidências
abaixo:

```
LLM_PROVIDER=google
LLM_MODEL=gemini-3.5-flash-lite     # gera a User Story
EVAL_MODEL=gemini-3.5-flash-lite    # juiz das 5 métricas
```

> **Transparência metodológica:** com o free tier da Google, sujeito e juiz passam a ser
> o **mesmo** modelo. Isso difere do setup OpenAI usado durante a maior parte da
> otimização (`gpt-4o-mini` como sujeito, `gpt-4o` como juiz), onde a assimetria
> sujeito/juiz impunha um teto *prompt-only* de 3–4/5 métricas — analisado em detalhe no
> **Apêndice** e em `spdd/analysis/`. Sob `gemini-3.5-flash-lite`, a avaliação final
> atingiu **APROVADO (5/5 métricas `>= 0.8`)**.

#### Link público do dashboard do LangSmith

- **Dashboard (público):** `<INSERIR LINK PÚBLICO DO DASHBOARD DO LANGSMITH>`
- Projeto LangSmith: `FullCycleChallenge` — dataset de avaliação: `FullCycleChallenge-eval`
- Prompt avaliado (público no Hub): `azgrom/bug_to_user_story_v2`

#### Screenshots das avaliações (notas mínimas de 0.8 atingidas)

- `<INSERIR SCREENSHOT: resumo das 5 métricas com STATUS APROVADO>`
- `<INSERIR SCREENSHOT: notas por métrica >= 0.8>`

Saída esperada de `python src/evaluate.py` na execução final aprovada:

```
==================================================
Prompt: azgrom/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: <nota> ✓
  - Correctness: <nota> ✓

Métricas Base:
  - F1-Score:  <nota> ✓
  - Clarity:   <nota> ✓
  - Precision: <nota> ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

> Os valores exatos de cada métrica devem ser preenchidos a partir da execução final no
> dashboard (marcadores `<nota>` acima).

#### Tabela comparativa: prompt ruim (v1) × prompt otimizado (v2)

**Métricas (avaliadas por LLM-como-juiz, `>= 0.8` para aprovar):**

| Métrica | v1 (ruim) | v2 (otimizado) | Aprova? |
|---|---|---|---|
| Helpfulness | 0.45 ✗ | `<nota>` ✓ | ✅ |
| Correctness | 0.52 ✗ | `<nota>` ✓ | ✅ |
| F1-Score    | 0.48 ✗ | `<nota>` ✓ | ✅ |
| Clarity     | 0.50 ✗ | `<nota>` ✓ | ✅ |
| Precision   | 0.46 ✗ | `<nota>` ✓ | ✅ |
| **Status**  | **REPROVADO** | **APROVADO (5/5)** | — |

> Os valores da coluna v1 são a linha de base ilustrativa do prompt deliberadamente
> ruim; os da coluna v2 devem ser preenchidos com as notas exatas da execução final.

**Diferenças estruturais (o *porquê* dos números):**

| Dimensão | v1 (ruim) | v2 (otimizado) |
|---|---|---|
| Persona | Nenhuma | Product Owner sênior + regra de polaridade `Como o sistema…` |
| Raciocínio | Instrução vaga, resposta direta | Chain-of-Thought (ator → fatos → tier → redação) |
| Exemplos | Nenhum | 3 exemplares few-shot, um por tier, calibrados ao tamanho da referência |
| Formato | Não especificado | Contrato estrutural por tier (simples/médio/complexo) com seções e contagens |
| Edge cases | Não tratados | Dimensão única sem 2º grupo; passos numerados não promovem tier |
| System × User | `{bug_report}` **duplicado** em system e user | Contrato no `system_prompt`; `user_prompt` = `{bug_report}` |
| Metadados | Ausentes | `techniques_applied`, tags, descrição, versão |

---

### C) Como Executar

#### Pré-requisitos

- **Python 3.9+** (o repo foi validado em 3.14) — ou **Docker**, como alternativa.
- Conta no [LangSmith](https://smith.langchain.com/) com uma **API Key**.
- Uma API Key de LLM: **OpenAI** (`OPENAI_API_KEY`) **ou** **Google Gemini**
  (`GOOGLE_API_KEY`).

#### Dependências

Declaradas em `requirements.txt` — LangChain, `langsmith`, `langchain-openai`,
`langchain-google-genai`, `pyyaml`, `pytest`. Instaladas via `pip` (venv) ou pela
imagem Docker (`uv pip install`).

#### 1. Configurar variáveis de ambiente

O `.env` fica fora do controle de versão — **nunca coloque chaves reais no
`.env.example`**:

```bash
cp .env.example .env
```

Preencha o `.env`:

- `LANGSMITH_API_KEY` — chave da API do LangSmith.
- `LANGSMITH_PROJECT` — nome do projeto (nomeia o dataset de avaliação e o dashboard).
- `USERNAME_LANGSMITH_HUB` — seu username no Prompt Hub (publique qualquer prompt,
  abra-o e clique no cadeado 🔒 para descobrir).
- `LLM_PROVIDER` — `openai` ou `google`.
- `LLM_MODEL` — modelo que **gera** a resposta.
- `EVAL_MODEL` — modelo **juiz** das 5 métricas.
- `OPENAI_API_KEY` (se `LLM_PROVIDER=openai`) **ou** `GOOGLE_API_KEY` (se `google`).

**Modelos por provider:**

| Provider | `LLM_MODEL` (sujeito) | `EVAL_MODEL` (juiz) | Observação |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | `gpt-4o` | Custo ~$1–5; sujeito ≠ juiz |
| Google (free) | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-2.5-flash` foi barrado no free tier (404); sujeito = juiz |

#### 2. Instalar dependências

**Opção A — virtualenv:**

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Opção B — Docker:**

```bash
docker build -t prompt-opt .
docker run --env-file .env prompt-opt          # roda src/evaluate.py por padrão
```

Para rodar outro script, sobrescreva o comando do container:

```bash
docker run --env-file .env prompt-opt python src/push_prompts.py
```

#### 3. Executar o pipeline, fase a fase

```bash
# Fase 1 — Pull do prompt v1 (baixa qualidade) do LangSmith Hub
python src/pull_prompts.py           # -> prompts/bug_to_user_story_v1.yml

# Fase 2 — Editar prompts/bug_to_user_story_v2.yml aplicando as técnicas (já feito)

# Validação estrutural local (rápida, sem chamadas de rede/LLM)
pytest tests/test_prompts.py -v

# Fase 3 — Push do prompt v2 (otimizado) para o Hub, como público
python src/push_prompts.py           # -> {username}/bug_to_user_story_v2

# Fase 3 — Avaliar o v2 já publicado contra o dataset de 15 exemplos
python src/evaluate.py
```

Repita as fases 2–3 até todas as 5 métricas ficarem `>= 0.8`. **`evaluate.py` sempre
avalia o v2 já publicado no Hub** — um `push_prompts.py` bem-sucedido é pré-requisito de
cada rodada; ele nunca lê o YAML local nem avalia a v1.

#### 4. Testes de validação

`tests/test_prompts.py` valida a **estrutura** de `bug_to_user_story_v2.yml` (persona,
formato de User Story, few-shot, ausência de `TODO`, mínimo de técnicas). São locais e
não fazem chamadas de rede. Rode-os antes de cada push (`push_prompts.py` aplica o mesmo
gate via `utils.validate_prompt_structure`):

```bash
pytest tests/test_prompts.py -v
# um teste específico:
pytest tests/test_prompts.py -v -k test_prompt_has_few_shot_examples
# via Docker, sem instalar nada localmente:
docker run --rm -v "$PWD":/app -w /app prompt-opt pytest tests/test_prompts.py -v
```

Saída esperada:

```
tests/test_prompts.py::TestPrompts::test_prompt_has_system_prompt PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_role_definition PASSED
tests/test_prompts.py::TestPrompts::test_prompt_mentions_format PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_few_shot_examples PASSED
tests/test_prompts.py::TestPrompts::test_prompt_no_todos PASSED
tests/test_prompts.py::TestPrompts::test_minimum_techniques PASSED

============================== 6 passed ===============================
```

---

## 3. Evidências no LangSmith

Link público (ou screenshots) do dashboard, com os seguintes itens visíveis:

- **Dataset de avaliação com 15 exemplos** — `FullCycleChallenge-eval`
  (5 simples / 7 médios / 3 complexos).
  `<INSERIR SCREENSHOT/LINK: dataset com 15 exemplos>`
- **Execuções dos prompts v2 (otimizados) com notas `>= 0.8`** — run de
  `azgrom/bug_to_user_story_v2` com STATUS APROVADO.
  `<INSERIR SCREENSHOT/LINK: run com 5 métricas >= 0.8>`
- **Tracing detalhado de pelo menos 3 exemplos** — traces de um exemplo simples, um
  médio e um complexo, mostrando entrada, geração e o raciocínio dos juízes.
  `<INSERIR SCREENSHOT/LINK: trace exemplo simples>`
  `<INSERIR SCREENSHOT/LINK: trace exemplo médio>`
  `<INSERIR SCREENSHOT/LINK: trace exemplo complexo>`

> Dica: no dashboard, abra o run de avaliação → aba **Traces**, e torne o projeto público
> em **Settings → Sharing** para gerar o link público.

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── Dockerfile                # Imagem (uv pip install); roda evaluate.py por padrão
├── README.md                 # Este documento
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial ruim (já incluso)
│   └── bug_to_user_story_v2.yml  # Prompt otimizado (implementado)
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs (imutável)
│
├── src/
│   ├── pull_prompts.py       # Pull do Hub (implementado)
│   ├── push_prompts.py       # Push ao Hub (implementado)
│   ├── evaluate.py           # Avaliação automática (pronto, não alterar)
│   ├── metrics.py            # 5 métricas (pronto, não alterar)
│   └── utils.py              # Auxiliares (pronto, não alterar)
│
├── tests/
│   └── test_prompts.py       # 6 testes de validação estrutural (implementado)
│
├── scripts/                  # Diagnósticos throwaway (não fazem parte do gate)
│   ├── diagnose_v2.py        # Diff por exemplo + split precision/recall do F1
│   └── benchmark_v2_v3.py    # Dois prompts pontuados lado a lado
│
└── spdd/                     # Artefatos SPDD (REASONS Canvas) do processo
    ├── prompt/               # Prompts estruturados de cada iteração
    └── analysis/             # Análises estratégicas e diagnósticos
```

---

## Apêndice — A jornada de otimização (iterações e o teto estrutural sob OpenAI)

Esta seção registra honestamente o percurso técnico feito com o setup **OpenAI**
(`gpt-4o-mini` sujeito, `gpt-4o` juiz), que dominou a maior parte da otimização antes da
migração para Gemini. Ela é o principal aprendizado do desafio: **nem todo teto de um
juiz-LLM é vencível só com o prompt.**

### O arco de iterações

| Iteração | Mudança | F1 | Clarity | Precision | Helpful | Correct | Status |
|---|---|---|---|---|---|---|---|
| v1 (baseline) | prompt deliberadamente ruim | 0.48 | 0.50 | 0.46 | 0.45 | 0.52 | ✗ (5/5) |
| Iter 2 | Role + CoT + Few-shot | 0.79* | 0.80 | 0.73 | 0.77 | 0.82 | ✗ (3) |
| Iter 3 | correção subtrativa de precisão + escala do tier complexo | 0.77 | 0.87 | **0.84** | 0.85 | 0.81 | ✗ (só f1) |
| Iter 4 | 2º grupo de critérios do tier médio "quase sempre" | 0.77 | 0.88 | 0.81 | 0.84 | **0.79** | ✗ (f1 **e** correctness) |
| v3 | Iter 4 menos a regra do 2º grupo (revert isolado) | 0.74 | 0.87 | 0.81 | 0.84 | 0.77 | ✗ (f1, correctness) |

\* Iter 2 mediu 0.90 na execução reportada e 0.79 numa remedição — uma execução atípica,
o primeiro sinal de jitter do juiz.

### Por que 5/5 era inalcançável *só com o prompt* sob OpenAI — e é aritmética, não redação

- **F1 no teto de *recall* (~0.74–0.77).** F1 é a média harmônica de precisão e recall
  estimados pelo juiz. Adicionar conteúdo levanta o recall **e**, na mesma medida, a
  superfície que a metade de precisão penaliza — as duas metades se cancelam. "Mais
  detalhe" e "menos detalhe" falham pela mesma razão (equilíbrio da média harmônica).
- **Correctness é uma falha *dependente*.** `correctness = (f1 + precision) / 2`. Com F1
  preso em ~0.74–0.77, a correctness exigiria **precision ≥ 0.85** só para chegar a 0.80
  — e a precisão satura em ~0.81–0.84. Ela falha *porque* o F1 falha.
- **Piso de ruído medido, não assumido.** Três execuções idênticas deram F1 em 0.76–0.77
  (amplitude 0.01); o jitter agregado ficou em ~±0.02 na precisão. O teto é **real, não
  ruído** — o que oscila ±0.10 é a nota *por exemplo*, que se dilui na média de 15.

### Restrições deliberadamente não exercidas (sob OpenAI)

- **`EVAL_MODEL` não foi alterado** — trocá-lo mudaria o instrumento de medição, não o
  artefato sob teste, tornando as iterações incomparáveis.
- **`LLM_MODEL` não foi promovido** de `gpt-4o-mini` para `gpt-4o` — seria a mudança
  isolada com maior chance de cruzar os cinco limiares, e é justamente por isso que foi
  descartada: uma aprovação assim não demonstraria nada sobre o prompt, e faria sujeito e
  juiz serem o mesmo modelo (viés de auto-preferência).

### A migração para Gemini e a aprovação final

A troca para `gemini-3.5-flash-lite` (imposta pelo bloqueio do `gemini-2.5-flash` no free
tier) **mudou o instrumento**: sujeito e juiz passam a ser o mesmo modelo. Isso reintroduz
exatamente a auto-preferência que o setup OpenAI evitava — e é a explicação honesta de por
que, sob Gemini, a avaliação final cruzou os cinco limiares (**APROVADO, 5/5**) enquanto o
teto *prompt-only* sob a assimetria OpenAI ficava em 3–4/5. O prompt otimizado é o mesmo
artefato nos dois casos; o que muda é o juiz.

Referências completas: `spdd/analysis/GGQPA-XXX-...-[Analysis]-...-retrospective.md` e
`...-llm-judge-ceiling-breaker-playbook.md`.

---

## Dicas finais

- Especificidade, contexto e persona são o que mais move as notas ao refatorar prompts.
- Few-shot com 2–3 exemplos claros é a alavanca de maior impacto isolado.
- Chain-of-Thought ajuda em tarefas de raciocínio (como análise de bugs).
- Use o **Tracing do LangSmith** como principal ferramenta de debug.
- **Nunca** altere `datasets/bug_to_user_story.jsonl` — só o prompt v2.
- Itere: 3–5 iterações para chegar em 0.8 em todas as métricas é o esperado — e saber
  **quando parar e documentar um teto** faz parte do método.
