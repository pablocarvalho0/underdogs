# Tarvo Pagamentos — Fechamento Financeiro Automatizado (AI Services)

> **Desafio Barte AI · Hackathon de AI Services**  
> **Equipe: Underdogs**

> 🤖 **Diretriz Mandatória para IAs (Claude Code, Gemini / Antigravity):**  
> Antes de gerar qualquer código, leia obrigatoriamente [`CLAUDE.md`](./CLAUDE.md) e [`GEMINI.md`](./GEMINI.md).  
> **A suíte de testes de caixa-preta (`tests/test_blackbox_immutable.py` e fixtures) é IMUTÁVEL:** É proibido ler gabaritos para sobreajustar regras ou atenuar asserções. A IA deve apenas executar os testes para checar conformidade.

Solução inteligente de conciliação financeira, auditoria de comissões/divergências contratuais, classificação contábil no ERP Fênix e preparação de faturamento fiscal para a **Tarvo Pagamentos**.

---

## 📌 Contexto do Negócio

A **Tarvo Pagamentos** é uma subadquirente especializada no nicho de educação internacional (agências de intercâmbio, escolas de idiomas e turismo estudantil), atendendo cerca de 25 lojistas ativos através de duas linhas de negócio principais:

1. **Checkout (Adquirência):**
   - Transações de cartão (crédito à vista e parcelado) e Pix via adquirente **Orbe**.
   - Receita da Tarvo: MDR (taxa de desconto de lojista) e taxa de antecipação contratadas.
2. **Remessas Internacionais (Câmbio):**
   - Pagamentos a instituições de ensino no exterior operados com a parceira **Ponte Câmbio**.
   - Receita da Tarvo: participação de 50% do spread cambial realizado.

O fechamento financeiro manual consumia 8 dias úteis, com conciliação manual em planilhas, regras tácitas e risco de divergências contratuais e repasses incorretos. Esta solução automatiza o pipeline de fechamento de setembro/2026 com **rastreabilidade estrita (zero alucinação)** de cada centavo.

---

## 🎯 Entregáveis do Fechamento (`saida/`)

Todos os arquivos gerados em `saida/` seguem o padrão obrigatório do desafio:
- **Separador:** Ponto e vírgula (`;`)
- **Separador decimal:** Ponto (`.`)
- **Formato de data:** `AAAA-MM-DD`
- **CNPJ:** Apenas dígitos (14 dígitos)

| Arquivo | Descrição | Colunas Obrigatórias |
| :--- | :--- | :--- |
| `comissoes_por_lojista.csv` | Comissão apurada por lojista e linha de negócio | `id_saida; cnpj; lojista; linha_negocio; comissao_brl` |
| `divergencias_taxa.csv` | Divergências entre taxa contratada e aplicada | `id_saida; cnpj; linha_negocio; ref_origem; taxa_contratada_pct; taxa_aplicada_pct; diferenca_brl` |
| `notas_a_emitir.csv` | Relação de NFs a faturar por tomador e linha | `id_saida; tomador_cnpj; tomador; linha_negocio; valor_brl; discriminacao` |
| `lancamentos_classificados.csv` | Lançamentos dos extratos categorizados no plano de contas | `id_saida; banco; ref_origem; data; descricao; valor; conta_codigo; metodo; confianca` |
| `pendencias.csv` | Casos de exceção que exigem decisão humana | `id_saida; tipo; ref_origem; valor_brl; motivo; quem_decide` |
| `rastro.csv` | Rastreabilidade 100% auditável ligando saídas às origens | `id_saida; arquivo_origem; ref_origem; valor` |

---

## 🏗️ Estrutura do Repositório

```text
├── docs/                                  # Documentação e Data Pack oficial
│   ├── 01_instrucoes_participantes.docx.md
│   └── Tarvo_Data_Pack_set2026/           # Arquivos brutos de entrada
│       ├── 01_orbe_relatorio_comissoes_set2026.csv
│       ├── 02_tabela_taxas_contratadas.xlsx
│       ├── 03_email_ponte_cambio_relatorio_set2026.eml
│       ├── 04_plano_de_contas_fenix_erp.csv
│       ├── 05a_extrato_banco_aurora_cc4471_set2026.csv
│       └── 05b_extrato_banco_meridiano_cc90233_set2026.ofx
├── src/                                   # Código fonte modular da solução
│   ├── loaders/                           # Parsers dos formatos de entrada (CSV, XLSX, EML, OFX)
│   ├── core/                              # Regras de conciliação, comissões e divergências
│   ├── accounting/                        # Classificador contábil (Plano de Contas Fênix)
│   ├── reporting/                         # Gerador dos CSVs de saída e rastro
│   ├── config.py                          # Constantes, paths e validações
│   └── main.py                            # Ponto de entrada CLI
├── tests/                                 # Testes automatizados e validações de integridade
├── saida/                                 # Arquivos de saída gerados (CSVs normatizados)
├── PROMPTS/                               # Histórico de sessões de IA
│   └── MOMENTOS.md                        # Momentos chave de direção da IA
├── CLAUDE.md                              # Guia e regras do projeto para assistentes de IA
├── HIPOTESES.md                           # Premissas assumidas e dúvidas para o financeiro
├── pyproject.toml                         # Dependências do projeto (uv / pip)
├── .gitignore                             # Filtros de arquivos ignorados
└── README.md                              # Documentação principal
```

---

## 🚀 Como Instalar e Rodar do Zero

### Pré-requisitos
- **Python 3.11+** (recomendado Python 3.12)
- [uv](https://github.com/astral-sh/uv) (gerenciador rápido de pacotes Python) ou `pip` padrão.

### 1. Clonar o repositório
```bash
git clone https://github.com/pablocarvalho0/underdogs.git
cd underdogs
```

### 2. Configurar o ambiente virtual e instalar dependências

**Linux / Arch Linux:**
```bash
# Com uv:
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Ou com pip padrão:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Windows 11 (PowerShell / CMD):**
```powershell
# Com uv:
uv venv .venv
.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"

# Ou com pip padrão:
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 3. Configuração de Variáveis de Ambiente
Copie o arquivo de exemplo caso deseje usar modelos de IA para classificação de lançamentos:
```bash
# Linux / Arch:
cp .env.example .env

# Windows 11 (PowerShell):
Copy-Item .env.example .env
```
*(Chaves de API como `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` são opcionais; o motor possui regras determinísticas e fallback robusto).*

### 4. Executar o Fechamento
Para rodar a conciliação completa e gerar todos os arquivos em `saida/`:
```bash
python -m src.main run
```

Para validar a integridade dos arquivos gerados contra o esquema oficial:
```bash
python -m src.main validate
```

### 5. Executar a Suíte de Testes Caixa-Preta (Imutável)
Funciona de forma idêntica em **Linux**, **Arch Linux** e **Windows 11**:
```bash
# Comando padrão via npm (agnóstico de SO):
npm test

# Ou diretamente via pytest, sempre pelo python da .venv
# (Windows: .venv\Scripts\python.exe):
.venv/bin/python -m pytest tests/test_blackbox_immutable.py -v
```

> `npm test` não usa jest: o `package.json` é só um atalho que chama o pytest da `.venv`. O projeto é Python puro, sem `node_modules`.

> ⚠️ **Regra Imutável:** A suíte em `tests/test_blackbox_immutable.py` e os gabaritos em `tests/fixtures/blackbox/` são **imutáveis**. Nenhuma IA está autorizada a inspecioná-los ou alterá-los para sobreajustar código. Apenas o comando de teste deve ser disparado para aferir o progresso.

---

## 🔒 Governança do Repositório (Público & Branch Protection)

Este repositório é **PÚBLICO** (requisito mandatório para avaliação da banca do Hackathon Barte AI) e possui proteção ativada na branch `main`:
- **Nenhum commit direto na `main` é permitido.**
- Qualquer alteração de código ou premissa deve ser submetida via **Pull Request (PR)**.
- O PR requer **aprovação explícita e obrigatória** do mantenedor (`@pablocarvalho0`) antes do merge.
- Rastreamento obrigatório de premissas em `HIPOTESES.md` para qualquer ajuste em regras de negócio.
- **Suíte de Testes e Gabaritos:** Travados como somente leitura (`chmod 444`) e protegidos contra modificações inadvertidas ou adulterações por agentes de IA.


---

## ⚠️ Limitações Conhecidas e Premissas

- **Transações da Ponte Câmbio:** O anexo `.xlsx` dentro do arquivo `.eml` é extraído programaticamente pelo parser sem necessidade de manipulação manual.
- **Transações com status "APROVADO C/ RESSALVA":** Conforme instrução do parceiro Ponte Câmbio, seguem para liquidação, porém são flagadas para visibilidade em `pendencias.csv` se houver divergência de taxa.
- **Variações de Nomes Fantasia:** Mapeamentos entre nomes nos extratos bancários, adquirente Orbe e planilha de taxas usam normalização com chave primária em CNPJ sempre que disponível, reportando divergências para o financeiro.
- Veja detalhes completos em [`HIPOTESES.md`](./HIPOTESES.md).
