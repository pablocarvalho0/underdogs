# CLAUDE.md — Guia de Desenvolvimento & Instruções do Projeto

Este documento orienta assistentes de IA (Claude Code, Cursor, Copilot, Antigravity) e desenvolvedores que trabalham no projeto **Tarvo Fechamento Financeiro** da equipe **Underdogs**.

---

## 🚫 0. DIRETIVA MANDATÓRIA E INEGOCIÁVEL PARA QUALQUER IA: SUÍTE DE TESTES IMUTÁVEL

> **ATENÇÃO MÁXIMA PARA QUALQUER AGENTE DE IA (CLAUDE, CURSOR, COPILOT, GEMINI, ANTIGRAVITY):**
>
> 1. **NÃO LEIA NEM INSPECIONE O ARQUIVO DE TESTE:** É terminantemente proibido ler `tests/test_blackbox_immutable.py` ou os gabaritos em `tests/fixtures/blackbox/` para "adaptar", "sobreajustar" (overfit) ou contornar as regras do código para fazê-lo passar nos testes.
> 2. **NÃO ALTERE, NÃO AFROUXE E NÃO REMOVA TESTES:** O arquivo `tests/test_blackbox_immutable.py` e todos os arquivos em `tests/fixtures/blackbox/` são **IMUTÁVEIS**. Nenhuma asserção pode ser modificada, comentada ou atenuada.
> 3. **PAPEL EXCLUSIVO DA IA:** Seu único papel é desenvolver a lógica pura de negócio dentro do diretório `src/` a partir dos documentos de especificação em `docs/`.
> 4. **ÚNICO USO PERMITIDO:** A IA está autorizada única e exclusivamente a **EXECUTAR O COMANDO DE TESTES** (`npm test` — ver seção 5 antes de rodar qualquer variante) para verificar se a sua implementação em `src/` atende aos contratos exigidos pelo cliente.

---

## 🎯 1. Visão Geral do Projeto

A **Tarvo Pagamentos** é uma subadquirente de nicho focada no mercado de educação internacional (~25 lojistas ativos). O projeto consiste em construir uma solução automatizada de fechamento financeiro para o mês de **setembro/2026** baseada nos arquivos brutos do cliente em `docs/Tarvo_Data_Pack_set2026/`.

### Linhas de Negócio da Tarvo
1. **Checkout (Adquirência):**
   - Transações de cartão (crédito à vista e parcelado) e Pix via adquirente **Orbe**.
   - Receita Tarvo: MDR contratado do lojista + taxa de antecipação contratada.
2. **Remessas Internacionais (Câmbio):**
   - Pagamentos a instituições de ensino no exterior operados via **Ponte Câmbio**.
   - Receita Tarvo: repasse de 50% (cinquenta por cento) do spread realizado.

---

## ⚠️ 2. Regras de Ouro e Princípios Invioláveis

1. **Rastreabilidade Total (`rastro.csv`):**
   - **TODO NÚMERO NA SAÍDA DEVE APONTAR PARA A LINHA DE ORIGEM.**
   - Total que não fecha com a soma das linhas de origem conta como **número inventado (alucinação)**.
   - Cada linha em `comissoes_por_lojista.csv`, `divergencias_taxa.csv`, `notas_a_emitir.csv`, etc., deve ter seus componentes rastreados em `rastro.csv` com `id_saida`, `arquivo_origem`, `ref_origem` e `valor`.

2. **Consumo de Arquivos Brutos:**
   - A solução consome os arquivos como vêm no data pack, sem limpeza prévia manual.
   - O e-mail da Ponte Câmbio (`.eml`) deve ter seu anexo extraído programaticamente.
   - O extrato OFX do Meridiano deve ser parseado programaticamente.

3. **Exceções são Pendências, não Bugs Silenciados:**
   - Casos com dados conflitantes, spread negativo não explicado ou lojistas não localizados **NÃO** devem ser descartados silenciosamente nem forçados com heurísticas arbitrárias.
   - Devem ser registrados em `saida/pendencias.csv` com o motivo claro e a indicação de quem decide (ex: `Lojista`, `Ponte Câmbio`, `Financeiro Tarvo`).

4. **Separação Rígida entre Fato e Premissa:**
   - Qualquer suposição não explícita na documentação oficial deve ser documentada em `HIPOTESES.md`.
   - Se uma regra puder ser esclarecida com o financeiro no canal `#tarvo-financeiro`, a pergunta deve ser formulada primeiro.

5. **Formato Obrigatório de Saída em `saida/`:**
   - Separador de colunas: `;`
   - Separador decimal: `.` (ponto)
   - Formato de data: `AAAA-MM-DD`
   - Formato de CNPJ: 14 dígitos numéricos (apenas dígitos, sem formatação `.`, `/`, `-`)

---

## 📂 3. Dados de Entrada (`docs/Tarvo_Data_Pack_set2026/`)

| Arquivo | Origem | Conteúdo Chave |
| :--- | :--- | :--- |
| `01_orbe_relatorio_comissoes_set2026.csv` | Orbe Adquirente | `id_transacao`, `data_movimento`, `cod_estabelecimento`, `nome_estabelecimento`, `tipo_lancamento`, `modalidade`, `qtd_parcelas`, `bandeira`, `valor_bruto`, `taxa_aplicada_pct`, `valor_taxa`, `valor_liquido` |
| `02_tabela_taxas_contratadas.xlsx` | Financeiro Tarvo | Taxas negociadas por lojista (MDR por modalidade, taxa de antecipação, spread de remessa) |
| `03_email_ponte_cambio_relatorio_set2026.eml` | Ponte Câmbio | E-mail contendo anexo `PonteCambio_Relatorio_TARVO_092026.xlsx` com operações de remessa, spread e repasse de 50% |
| `04_plano_de_contas_fenix_erp.csv` | ERP Fênix | `COD_CONTA`, `DESCRICAO`, `TIPO`, `NATUREZA`, `ACEITA_LANCTO`, `COD_SUPERIOR` |
| `05a_extrato_banco_aurora_cc4471_set2026.csv` | Internet Banking | Conta corrente principal de movimentação e repasses |
| `05b_extrato_banco_meridiano_cc90233_set2026.ofx` | Internet Banking | Conta corrente usada nas operações de remessas internacionais |

---

## 📊 4. Especificação dos Arquivos de Saída (`saida/`)

1. **`comissoes_por_lojista.csv`**
   - Colunas: `id_saida; cnpj; lojista; linha_negocio; comissao_brl`
   - `linha_negocio`: `CHECKOUT` ou `REMESSA`
2. **`divergencias_taxa.csv`**
   - Colunas: `id_saida; cnpj; linha_negocio; ref_origem; taxa_contratada_pct; taxa_aplicada_pct; diferenca_brl`
3. **`notas_a_emitir.csv`**
   - Colunas: `id_saida; tomador_cnpj; tomador; linha_negocio; valor_brl; discriminacao`
4. **`lancamentos_classificados.csv`**
   - Colunas: `id_saida; banco; ref_origem; data; descricao; valor; conta_codigo; metodo; confianca`
   - `banco`: `AURORA` ou `MERIDIANO`
   - `ref_origem`: número da linha física no Aurora (ex: `L10`, `L11`) e `FITID` no Meridiano
   - `metodo`: `REGRA`, `IA` ou `HUMANO`
   - `confianca`: float de `0` a `1`
5. **`pendencias.csv`**
   - Colunas: `id_saida; tipo; ref_origem; valor_brl; motivo; quem_decide`
6. **`rastro.csv`**
   - Colunas: `id_saida; arquivo_origem; ref_origem; valor`
   - **Regra**: a soma de `valor` agrupado por `id_saida` deve bater com exatidão com o número reportado.

---

## 🛠️ 5. Comandos Frequentes

### Como os testes rodam aqui — é pytest, não jest

O projeto é **100% Python**. O `package.json` existe só como atalho
multiplataforma: `npm test` → `scripts/runner.js` → `.venv/bin/python -m pytest
tests/test_blackbox_immutable.py -v` (no Windows, `.venv\Scripts\python.exe`).
Não há jest, vitest, `node_modules` nem dependência npm.

- **Não** passar flags de jest/vitest (`--maxWorkers`, `--runInBand`, `--watch`,
  `--coverage`): o pytest não reconhece e falha.
- **Não** rodar `npm install`: não há nada para instalar.
- **Não** rodar `pytest` ou `python -m pytest` "pelado": pytest, pandas, ruff e
  mypy existem **só na `.venv`**. O python do sistema dá
  `ModuleNotFoundError: No module named 'pytest'`. Se precisar chamar direto,
  use o binário da venv: `.venv/bin/python -m ...`.
- `npm test` saindo com código 1 e `FAILED` é **teste falhando de verdade**,
  não erro de ambiente. Leia a mensagem do pytest em vez de trocar de runner.

### Comandos

```bash
# Suíte caixa-preta (comando padrão — o gabarito do desafio)
npm test

# Todos os testes (inclui parsers de dados reais)
npm run test:all

# Só os testes dos dados reais / loaders
npm run test:real

# Pipeline de conciliação, validação de saída e status
npm run run
npm run validate
npm run status

# Linters e checagem de tipos (sempre pelo binário da venv)
.venv/bin/ruff check src tests
.venv/bin/ruff format src tests
.venv/bin/mypy src
```

---

## 🤖 6. Orquestração: líder + subagents

A sessão principal (Opus) é o **líder**: lê a spec, quebra a tarefa grande em
fatias independentes e delega. Subagents de projeto em `.claude/agents/`:

- `implementador` (sonnet): implementa uma fatia em `src/`.
- `varredor` (haiku): localiza coisas em `src/` e `docs/`, read-only.

Protocolo do líder:

1. Decidir arquitetura e regras ambíguas **antes** de delegar; premissa nova vai para `HIPOTESES.md`.
2. Fatias sem arquivo em comum rodam em paralelo; com arquivo em comum, em sequência.
3. Cada prompt de subagent é autocontido: arquivos a criar/editar, contrato de
   entrada/saída (colunas, tipos), regra de negócio exata e critério de pronto.
   Subagent não vê esta conversa.
4. O líder revisa o diff de cada fatia e roda `npm test` no final. Subagent nunca
   lê os testes caixa-preta (diretiva 0).
5. Tarefa pequena ou de um arquivo só: o líder faz direto, sem delegar.

Skills do gstack (instaladas em `~/.claude/skills`): úteis aqui são `/investigate`
(teste falhando), `/review` (antes do PR) e `/ship`.

---

## 🔐 7. Governança e Git

- **O repositório no GitHub deve ser PÚBLICO** (exigência mandatória do regulamento oficial da Barte AI para envio e correção automática até 18h30 de 17/10).
- **Apenas mudanças aprovadas pelo usuário (`@pablocarvalho0`) podem entrar na branch `main`.**
- Trabalhe sempre em branches de funcionalidade (ex: `feat/orbe-loader`, `feat/reconciliation-engine`, `feat/export-csv`) e abra Pull Requests para aprovação do usuário.
- Mantenha `PROMPTS/MOMENTOS.md` atualizado com as decisões e interações críticas de IA.

