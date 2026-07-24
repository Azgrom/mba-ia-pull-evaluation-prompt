# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

## Objetivo

Você deve entregar um software capaz de:

1. **Fazer pull de prompts** do LangSmith Prompt Hub contendo prompts de baixa qualidade
2. **Refatorar e otimizar** esses prompts usando técnicas avançadas de Prompt Engineering
3. **Fazer push dos prompts otimizados** de volta ao LangSmith
4. **Avaliar a qualidade** através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
5. **Atingir pontuação mínima** de 0.8 (80%) em todas as métricas de avaliação

---

## Exemplo no CLI

**Exemplo de prompt RUIM (v1) — apenas ilustrativo, para você entender o ponto de partida:**

```
==================================================
Prompt: {seu_username}/bug_to_user_story_v1
==================================================

Métricas Derivadas:
  - Helpfulness: 0.45 ✗
  - Correctness: 0.52 ✗

Métricas Base:
  - F1-Score: 0.48 ✗
  - Clarity: 0.50 ✗
  - Precision: 0.46 ✗

❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.8: helpfulness, correctness, f1_score, clarity, precision
```

**Exemplo de prompt OTIMIZADO (v2) — seu objetivo é chegar aqui:**

```bash
# Após refatorar os prompts e fazer push
python src/push_prompts.py

# Executar avaliação
python src/evaluate.py

Executando avaliação dos prompts...
==================================================
Prompt: {seu_username}/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.96 ✓

Métricas Base:
  - F1-Score: 0.93 ✓
  - Clarity: 0.95 ✓
  - Precision: 0.92 ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

---

## Tecnologias obrigatórias

- **Linguagem:** Python 3.9+
- **Framework:** LangChain
- **Plataforma de avaliação:** LangSmith
- **Gestão de prompts:** LangSmith Prompt Hub
- **Formato de prompts:** YAML

---

## Pacotes recomendados

```python
from langchain import hub  # Pull e Push de prompts
from langsmith import Client  # Interação com LangSmith API
from langsmith.evaluation import evaluate  # Avaliação de prompts
from langchain_openai import ChatOpenAI  # LLM OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI  # LLM Gemini
```

---

## OpenAI

- Crie uma **API Key** da OpenAI: https://platform.openai.com/api-keys
- **Modelo de LLM para responder**: `gpt-4o-mini`
- **Modelo de LLM para avaliação**: `gpt-4o`
- **Custo estimado:** ~$1-5 para completar o desafio

## Gemini (modelo free)

- Crie uma **API Key** da Google: https://aistudio.google.com/app/apikey
- **Modelo de LLM para responder**: `gemini-2.5-flash`
- **Modelo de LLM para avaliação**: `gemini-2.5-flash`
- **Limite:** 15 req/min, 1500 req/dia

---

## Requisitos

### 1. Pull do Prompt inicial do LangSmith

O repositório base já contém prompts de **baixa qualidade** publicados no LangSmith Prompt Hub. Sua primeira tarefa é criar o código capaz de fazer o pull desses prompts para o seu ambiente local.

**Tarefas:**

1. Configurar suas credenciais do LangSmith no arquivo `.env` (conforme o arquivo `.env.example`)
2. Implementar o script `src/pull_prompts.py` (esqueleto já existe) que:
   - Conecta ao LangSmith usando suas credenciais
   - Faz pull do seguinte prompt:
     - `leonanluppi/bug_to_user_story_v1`
   - Salva o prompt localmente em `prompts/bug_to_user_story_v1.yml`

---

### 2. Otimização do Prompt

Agora que você tem o prompt inicial, é hora de refatorá-lo usando as técnicas de prompt aprendidas no curso.

**Tarefas:**

1. Analisar o prompt em `prompts/bug_to_user_story_v1.yml`
2. Criar um novo arquivo `prompts/bug_to_user_story_v2.yml` com suas versões otimizadas
3. Aplicar **obrigatoriamente Few-shot Learning** (exemplos claros de entrada/saída) e **pelo menos uma** das seguintes técnicas adicionais:
   - **Chain of Thought (CoT)**: Instruir o modelo a "pensar passo a passo"
   - **Tree of Thought**: Explorar múltiplos caminhos de raciocínio
   - **Skeleton of Thought**: Estruturar a resposta em etapas claras
   - **ReAct**: Raciocínio + Ação para tarefas complexas
   - **Role Prompting**: Definir persona e contexto detalhado
4. Documentar no `README.md` quais técnicas você escolheu e por quê

**Requisitos do prompt otimizado:**

- Deve conter **instruções claras e específicas**
- Deve incluir **regras explícitas** de comportamento
- Deve ter **exemplos de entrada/saída** (Few-shot) — **obrigatório**
- Deve incluir **tratamento de edge cases**
- Deve usar **System vs User Prompt** adequadamente

---

### 3. Push e Avaliação

Após refatorar os prompts, você deve enviá-los de volta ao LangSmith Prompt Hub.

**Tarefas:**

1. Implementar o script `src/push_prompts.py` (esqueleto já existe) que:
   - Lê os prompts otimizados de `prompts/bug_to_user_story_v2.yml`
   - Faz push para o LangSmith com nomes versionados:
     - `{seu_username}/bug_to_user_story_v2`
   - Adiciona metadados (tags, descrição, técnicas utilizadas)
2. Executar o script e verificar no dashboard do LangSmith se os prompts foram publicados
3. Deixá-lo público

---

### 4. Iteração

- Espera-se 3-5 iterações.
- Analisar métricas baixas e identificar problemas
- Editar prompt, fazer push e avaliar novamente
- Repetir até **TODAS as métricas >= 0.8**

### Critério de Aprovação:

```
- Helpfulness >= 0.8
- Correctness >= 0.8
- F1-Score >= 0.8
- Clarity >= 0.8
- Precision >= 0.8

MÉDIA das 5 métricas >= 0.8
```

**IMPORTANTE:** TODAS as 5 métricas devem estar >= 0.8, não apenas a média!

### 5. Testes de Validação

**O que você deve fazer:** Edite o arquivo `tests/test_prompts.py` e implemente, no mínimo, os 6 testes abaixo usando `pytest`:

- `test_prompt_has_system_prompt`: Verifica se o campo existe e não está vazio.
- `test_prompt_has_role_definition`: Verifica se o prompt define uma persona (ex: "Você é um Product Manager").
- `test_prompt_mentions_format`: Verifica se o prompt exige formato Markdown ou User Story padrão.
- `test_prompt_has_few_shot_examples`: Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot).
- `test_prompt_no_todos`: Garante que você não esqueceu nenhum `[TODO]` no texto.
- `test_minimum_techniques`: Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas.

**Como validar:**

```bash
pytest tests/test_prompts.py
```

---

## Estrutura obrigatória do projeto

Faça um fork do repositório base: **[Clique aqui para o template](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt)**

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Sua documentação do processo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (já incluso)
│   └── bug_to_user_story_v2.yml  # Seu prompt otimizado (criar)
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs (já incluso)
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith (implementar)
│   ├── push_prompts.py       # Push ao LangSmith (implementar)
│   ├── evaluate.py           # Avaliação automática (pronto)
│   ├── metrics.py            # 5 métricas implementadas (pronto)
│   └── utils.py              # Funções auxiliares (pronto)
│
├── tests/
│   └── test_prompts.py       # Testes de validação (implementar)
```

**O que você deve implementar:**

- `prompts/bug_to_user_story_v2.yml` — Criar do zero com seu prompt otimizado
- `src/pull_prompts.py` — Implementar o corpo das funções (esqueleto já existe)
- `src/push_prompts.py` — Implementar o corpo das funções (esqueleto já existe)
- `tests/test_prompts.py` — Implementar os 6 testes de validação (esqueleto já existe)
- `README.md` — Documentar seu processo de otimização

**O que já vem pronto (não alterar):**

- `src/evaluate.py` — Script de avaliação completo
- `src/metrics.py` — 5 métricas implementadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
- `src/utils.py` — Funções auxiliares
- `datasets/bug_to_user_story.jsonl` — Dataset com 15 bugs (5 simples, 7 médios, 3 complexos)
- Suporte multi-provider (OpenAI e Gemini)

## Repositórios úteis

- [Repositório boilerplate do desafio](https://github.com/devfullcycle/mba-ia-prompt-engineering)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

## Como Executar

### Pré-requisitos

- Python 3.9+ (ou Docker, como alternativa — veja a Opção B abaixo)
- Conta no [LangSmith](https://smith.langchain.com/) com uma API Key
- Uma API Key de LLM: OpenAI (`OPENAI_API_KEY`) ou Google Gemini (`GOOGLE_API_KEY`)

### 1. Configurar variáveis de ambiente

Copie o template e preencha com suas credenciais reais — o `.env` fica fora do controle de versão, nunca coloque chaves reais no `.env.example`:

```bash
cp .env.example .env
```

Edite o `.env` com:

- `LANGSMITH_API_KEY` — chave da API do LangSmith
- `LANGSMITH_PROJECT` — nome do projeto no LangSmith (usado para nomear o dataset de avaliação e o dashboard)
- `USERNAME_LANGSMITH_HUB` — seu username no Prompt Hub (publique qualquer prompt, abra-o e clique no ícone de cadeado para descobrir)
- `LLM_PROVIDER` — `openai` ou `google`
- `LLM_MODEL` — modelo usado para gerar as respostas (ex.: `gpt-4o-mini` ou `gemini-2.5-flash`)
- `EVAL_MODEL` — modelo usado como juiz nas 5 métricas (ex.: `gpt-4o` ou `gemini-2.5-flash`)
- `OPENAI_API_KEY` (obrigatório se `LLM_PROVIDER=openai`) ou `GOOGLE_API_KEY` (obrigatório se `LLM_PROVIDER=google`)

### 2. Instalar dependências

**Opção A — virtualenv:**

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Opção B — Docker:**

```bash
docker build -t langchain-prompt-optimization .
docker run --env-file .env prompt-opt
```

O comando padrão da imagem executa `python src/evaluate.py`. Para rodar outro script (pull, push ou os testes), sobrescreva o comando do container:

```bash
docker run --env-file .env prompt-opt python src/push_prompts.py
```

### 3. Executar o pipeline, fase a fase

```bash
# 1. Pull do prompt v1 (baixa qualidade) do LangSmith Hub
python src/pull_prompts.py

# 2. Editar manualmente prompts/bug_to_user_story_v2.yml aplicando as técnicas escolhidas

# 3. Validar a estrutura do prompt localmente (ver seção 4 abaixo)
pytest tests/test_prompts.py -v

# 4. Push do prompt v2 (otimizado) para o LangSmith Hub, como público
python src/push_prompts.py

# 5. Avaliar o prompt v2 publicado contra o dataset de 15 exemplos
python src/evaluate.py
```

Repita os passos 2-5 até que as 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision) fiquem `>= 0.8`. `evaluate.py` sempre avalia o prompt v2 **já publicado no Hub** — um `push_prompts.py` bem-sucedido é pré-requisito para cada rodada de avaliação; ele nunca lê o YAML local nem avalia a v1.

### 4. Executar os testes unitários

Os testes em `tests/test_prompts.py` validam a **estrutura** de `prompts/bug_to_user_story_v2.yml` (persona, formato de User Story, few-shot, ausência de `TODO`, mínimo de técnicas) — são locais, rápidos e não fazem nenhuma chamada de rede ou de LLM. Rode-os sempre antes de um `push_prompts.py`, já que `push_prompts.py` aplica o mesmo gate de validação (`utils.validate_prompt_structure`) e recusa publicar um prompt inválido.

**Com virtualenv ativado:**

```bash
pytest tests/test_prompts.py -v
```

**Rodando um teste específico:**

```bash
pytest tests/test_prompts.py -v -k test_prompt_has_few_shot_examples
```

**Via Docker** (sem precisar instalar Python/dependências localmente):

```bash
docker run --rm -v "$PWD":/app -w /app prompt-opt pytest tests/test_prompts.py -v
```

Saída esperada quando tudo passa:

```
tests/test_prompts.py::TestPrompts::test_prompt_has_system_prompt PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_role_definition PASSED
tests/test_prompts.py::TestPrompts::test_prompt_mentions_format PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_few_shot_examples PASSED
tests/test_prompts.py::TestPrompts::test_prompt_no_todos PASSED
tests/test_prompts.py::TestPrompts::test_minimum_techniques PASSED

============================== 6 passed in 0.08s ===============================
```

---

## Resultados da Otimização (Iterações 3–4 → v3)

**Status: REPROVADO.** Na iteração 3, `f1_score` fica em ~0.77 (abaixo do mínimo de 0.80) e as outras quatro passam — mas `precision` fica na corda bamba (~0.81–0.84 conforme a execução). O melhor estado *prompt-only* medido é 3/5 métricas (4/5 numa execução de precisão sortuda); ver a subseção **v3 — revert isolado e o teto estrutural** abaixo.

Commit avaliado no Hub: `azgrom/bug_to_user_story_v2` (`0b9b9235`).

### Técnicas aplicadas

| Técnica | Como aparece no prompt |
|---|---|
| Role Prompting | Persona de Product Owner sênior, mais uma regra de *polaridade de persona*: quando o ator afetado é um processo de backend ou uma regra de integridade do sistema, a User Story abre com `Como o sistema…` (o corpus faz isso em 3 dos 15 exemplos). |
| Chain-of-Thought | Cadeia comprimida em uma linha — identificar ator, extrair fatos afirmados, selecionar o tier, redigir. A versão anterior tinha quatro passos numerados que duplicavam o contrato de saída. |
| Few-shot Learning | Três exemplares completos, um por tier (simples 8 linhas, médio 14, complexo 88), calibrados contra o tamanho medido das referências. |

### Métricas

Duas medições do **mesmo** commit publicado, com os mesmos modelos e `temperature=0`:

| Métrica | Execução reportada (iteração 2) | Diagnóstico do mesmo prompt (mesmo dia) |
|---|---|---|
| F1-Score | 0.90 ✓ | 0.79 |
| Clarity | 0.80 ✗ | 0.87 |
| Precision | 0.73 ✗ | 0.83 |

À época, a divergência de ~±0.10 entre essas duas medições parecia maior que o efeito pretendido pelas edições — sugerindo que o ruído do juiz dominava o sinal. **Medições posteriores refutaram essa leitura no nível agregado**: três execuções idênticas deram F1 estável em 0.76–0.77 (amplitude 0.01), e os benchmarks v2/v3 no mesmo instrumento puseram a oscilação agregada em ~±0.02. O valor de 0.90 acima foi uma execução atípica; o que oscila ±0.10 é a nota *por exemplo*, que se dilui na média de 15 exemplos. O agregado, portanto, é confiável a duas casas e o teto de F1 ~0.77 é **real, não ruído** (ver a subseção **v3** e o retrospecto `spdd/analysis/GGQPA-XXX-202607240930-[Analysis]-v2-iteration-benchmark-retrospective.md`).

Comparando prompt antigo e prompt novo **no mesmo instrumento** (diagnóstico vs. execução oficial):

| Métrica | v2 anterior | v2 remediado | Δ |
|---|---|---|---|
| F1-Score | 0.789 | 0.773 | −0.016 |
| Clarity | 0.870 | 0.867 | −0.003 |
| Precision | 0.834 | 0.839 | +0.005 |

O agregado praticamente não se moveu. A atribuição por tier mostra por quê — dois efeitos grandes e opostos se cancelaram:

| Tier | F1 antes | F1 depois | Δ |
|---|---|---|---|
| Simples (1-5) | 0.870 | 0.728 | **−0.142** |
| Médio (6-12) | 0.749 | 0.753 | +0.004 |
| Complexo (13-15) | 0.750 | 0.897 | **+0.147** |

O ganho no tier complexo veio de adicionar `=== USER STORY PRINCIPAL ===`, as sub-seções e a escala que faltavam — as respostas anteriores estavam de 1.626 a 3.576 caracteres abaixo das referências. A perda no tier simples é o alvo da próxima iteração.

### Evidência estrutural (determinística, sem chamadas de LLM)

`scripts/diagnose_v2.py` compara cada resposta gerada com sua referência. Contra o prompt anterior:

- **6 exemplos com tier errado** — 3 e 4 (simples→médio); 6, 7, 8 e 10 (médio→complexo). A análise previa apenas o exemplo 8.
- **Banners `===` fora do tier complexo** nos exemplos 6, 7, 8 e 10.
- **Polaridade de persona divergente** exatamente nos exemplos 6, 8 e 11 — os três que a referência abre com `Como o sistema`.
- **Nenhum vazamento de preâmbulo** em nenhum dos 15 exemplos, o que descartou empiricamente a oitava mudança planejada.

Linha de base completa em `spdd/analysis/diagnostics/iteration-2-baseline.md`.

### Restrições deliberadamente não exercidas

- **`EVAL_MODEL` não foi alterado** (permanece `gpt-4o`). Trocá-lo mudaria o instrumento de medição, não o artefato sob teste, e tornaria os resultados incomparáveis entre iterações.
- **`LLM_MODEL` não foi promovido** de `gpt-4o-mini` para `gpt-4o`. É provavelmente a mudança isolada com maior chance de cruzar os cinco limiares, e é justamente por isso que foi descartada: uma aprovação obtida assim não demonstraria nada sobre o prompt, e ainda faria sujeito e juiz serem o mesmo modelo, introduzindo viés de auto-preferência.

### Assimetria sujeito/juiz

O prompt é executado por `gpt-4o-mini` e avaliado por `gpt-4o`. Não há viés de auto-preferência, mas o juiz detecta com confiabilidade desvios estruturais e de volume que o sujeito não evita com a mesma confiabilidade. Por isso a densidade condicional do prompt é ela própria um modo de falha: cada ramificação é um ponto onde o modelo mais fraco desvia.

### v3 — revert isolado e o teto estrutural

A iteração seguinte (que tornou o segundo grupo de critérios do tier médio *quase automático*) foi medida como uma **regressão**: não moveu o F1 e ainda derrubou a precisão de ~0.84 para ~0.81, quebrando a `correctness` junto. O `prompts/bug_to_user_story_v3.yml` reverte **exatamente essa regra** (segundo grupo volta a ser condicional) e **nada mais** — um experimento de variável única, para isolar o efeito.

Benchmark local (mesma execução, mesma pontuação de `evaluate.py`, prompts do YAML local, sem push — `scripts/benchmark_v2_v3.py`):

| Métrica | v2 (atual) | v3 (revert isolado) | Δ atribuível | Passa? |
|---|---|---|---|---|
| F1-Score | 0.754 | 0.740 | −0.014 | ✗ (ambos) |
| Clarity | 0.873 | 0.867 | −0.007 | ✓ |
| **Precision** | 0.788 | **0.809** | **+0.021** | v2 ✗ → **v3 ✓** |
| Helpfulness | 0.831 | 0.838 | +0.007 | ✓ |
| Correctness | 0.771 | 0.774 | +0.003 | ✗ (ambos) |

A mudança fez o previsto: **a precisão se recuperou (+0.021) e voltou a passar**. v3 é o melhor artefato *prompt-only* — passa em `clarity`, `precision` e `helpfulness` (3/5).

**Por que 5/5 é inalcançável só com o prompt — e é aritmética, não redação:**

- **F1** está no teto de *recall* (~0.70 na metade de recall do juiz). Nenhuma edição o move: adicionar conteúdo levanta o recall e, na mesma medida, a superfície que a metade de precisão do F1 penaliza — as duas metades se cancelam na média harmônica.
- **Correctness é uma falha *dependente*.** `correctness = (f1 + precision) / 2`. Com F1 preso em ~0.74–0.77, a `correctness` exigiria **precision ≥ 0.85** só para chegar a 0.80 — e a precisão satura em ~0.81–0.84. Ela falha *porque* o F1 falha, não por causa do prompt.

Duas das cinco métricas estão, portanto, fora do alcance do trabalho de prompt: uma é o muro (F1), a outra está acorrentada ao muro (correctness).

**Refino sobre o ruído do juiz:** entre execuções idênticas, o agregado oscila ~±0.02 na precisão (v2 mediu 0.812 e 0.788 em duas execuções), não os ±0.01 que uma leitura anterior sugeria. A `precision` passando (0.80–0.81) fica, portanto, na corda bamba — parte do 3/5 depende da sorte da execução. Relatório por exemplo em `spdd/analysis/diagnostics/benchmark-v2-vs-v3.md`.

**Conclusão honesta:** com `LLM_MODEL=gpt-4o-mini`, o teto *prompt-only* é 3/5 métricas (4/5 numa execução de precisão sortuda). A única alavanca com folga real para cruzar os cinco limiares é promover o modelo sujeito para `gpt-4o` — deliberadamente fora de escopo (ver *Restrições deliberadamente não exercidas*), porque otimizaria o runtime, não o prompt.

---

## Entregável

**1. Repositório público no GitHub** (fork do repositório base) contendo:

- Todo o código-fonte implementado
- Arquivo `prompts/bug_to_user_story_v2.yml` 100% preenchido e funcional
- Arquivo `README.md` atualizado

**2. README.md deve conter:**

**A) Seção "Técnicas Aplicadas (Fase 2)":**

- Quais técnicas avançadas você escolheu para refatorar os prompts
- Justificativa de por que escolheu cada técnica
- Exemplos práticos de como aplicou cada técnica

**B) Seção "Resultados Finais":**

- Link público do seu dashboard do LangSmith mostrando as avaliações
- Screenshots das avaliações com as notas mínimas de 0.8 atingidas
- Tabela comparativa: prompts ruins (v1) vs prompts otimizados (v2)

**C) Seção "Como Executar":**

- Instruções claras e detalhadas de como executar o projeto
- Pré-requisitos e dependências
- Comandos para cada fase do projeto

**3. Evidências no LangSmith:**

- Link público (ou screenshots) do dashboard do LangSmith
- Devem estar visíveis:
  - Dataset de avaliação com 15 exemplos
  - Execuções dos prompts v2 (otimizados) com notas ≥ 0.8
  - Tracing detalhado de pelo menos 3 exemplos

---

## Dicas Finais

- **Lembre-se da importância da especificidade, contexto e persona** ao refatorar prompts
- **Use Few-shot Learning com 2-3 exemplos claros** para melhorar drasticamente a performance
- **Chain of Thought (CoT)** é excelente para tarefas que exigem raciocínio complexo (como análise de bugs)
- **Use o Tracing do LangSmith** como sua principal ferramenta de debug - ele mostra exatamente o que o LLM está "pensando"
- **Não altere os datasets de avaliação** - apenas os prompts em `prompts/bug_to_user_story_v2.yml`
- **Itere, itere, itere** - é normal precisar de 3-5 iterações para atingir 0.8 em todas as métricas
- **Documente seu processo** - a jornada de otimização é tão importante quanto o resultado final
