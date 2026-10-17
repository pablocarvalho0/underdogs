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
│   ├── 00-COMECE-AQUI.md                  # Mapa: onde estamos e qual documento manda em quê
│   ├── 01_instrucoes_participantes.docx.md
│   └── Tarvo_Data_Pack_set2026/           # Arquivos brutos de entrada (01 a 06)
├── src/                                   # Código fonte modular da solução
│   ├── loaders/                           # Parsers dos formatos de entrada (CSV, XLSX, EML, OFX)
│   ├── core/                              # Contrato (model), cadastro, entrada, writer, pipeline
│   ├── trilhas/                           # checkout.py, remessa.py, extratos.py: regras de negócio
│   ├── validators/                        # Conferência do esquema dos 6 CSVs
│   ├── premissas.py                       # Regras e premissas como configuração
│   ├── config.py                          # Constantes e caminhos
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
npm run run
```

Para rodar outro mês, aponte a pasta do data pack (os nomes dos arquivos não importam: o papel de
cada um é reconhecido pelo conteúdo, e **todos** os arquivos da Orbe da pasta entram, inclusive
ajustes tardios):
```bash
npm run run -- --input caminho/da/pasta_do_mes --output saida
```
Se faltar uma fonte ou aparecer um arquivo com layout desconhecido, a execução não para: o terminal
mostra o aviso, ele vira uma linha em `saida/pendencias.csv` e o restante fecha normalmente.

Para ver numa página só as entradas, o resultado esperado e o que o pipeline gerou, abra
[`conferencia/index.html`](conferencia/index.html) no navegador. Ela já vem gerada; para regerar:
```bash
npm run conferencia
```
A página roda o pipeline do zero, compara cada total e cada pendência com
`controle/esperado_setembro.json` (a prévia independente do HIPOTESES.md §5), mostra os
invariantes e diz se o `saida/` versionado é idêntico à execução. Clicando num `id_saida`, ela
mostra as linhas de origem que somam aquele número.

Para conferir os números de setembro contra o controle independente (HIPOTESES.md §5):
```bash
.venv/bin/python -m pytest tests/test_controle_setembro.py -q
```

Para validar a integridade dos arquivos gerados contra o esquema oficial:
```bash
npm run validate
```

### Painel visual
Para ver input, processamento e output do pipeline numa página só:
```bash
npm run report
```
Depois abra `painel/index.html` no navegador. O pipeline roda num diretório temporário (não grava em `saida/`) e `painel/` não é versionado.

### 5. Executar a Suíte de Testes Caixa-Preta (Imutável)
Funciona de forma idêntica em **Linux**, **Arch Linux** e **Windows 11**:
```bash
npm test
```

> `npm test` não usa jest: o `package.json` é só um atalho que chama o pytest da `.venv`. Detalhes e o que não fazer em [`CLAUDE.md` §5](./CLAUDE.md).

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

## 🤝 Como Contribuir (Fluxo de Trabalho)

Todo trabalho segue o mesmo ciclo: **branch nova → código → PR → revisão do `@pablocarvalho0` → merge → atualizar a `main` local → próxima tarefa.**

### 1. Planeje antes de abrir a branch
Cada branch resolve **uma tarefa planejada e delimitada** (ex.: "parser do OFX do Meridiano", "cálculo de comissão do Checkout"). Se a tarefa não cabe em uma frase, quebre em mais de uma branch. PR pequeno é revisado e mergeado rápido; PR grande trava o time.

### 2. Parta da `main` atualizada e crie a branch
```bash
git switch main
git pull
git switch -c feat/nome-da-tarefa
```
Prefixos: `feat/` (funcionalidade), `fix/` (correção), `docs/` (documentação), `chore/` (ferramental).

### 3. Code na sua branch
- Commits pequenos e com mensagem que diga **o que** e **por quê**.
- Rode `npm test` antes de subir. Teste falhando que você não consegue explicar vai na descrição do PR, não é escondido.
- Premissa nova de regra de negócio vai em [`HIPOTESES.md`](./HIPOTESES.md); decisão relevante tomada com IA vai em [`PROMPTS/MOMENTOS.md`](./PROMPTS/MOMENTOS.md).

### 4. Suba e abra o Pull Request
```bash
git push -u origin feat/nome-da-tarefa
```
Abra o PR contra a `main` no GitHub (ou `gh pr create --base main`). Na descrição: o que muda, por quê, e como você verificou (resultado do `npm test`).

### 5. Revisão e merge
O `@pablocarvalho0` revisa o PR. Se pedir ajuste, faça novos commits na **mesma branch** e dê `git push` — o PR atualiza sozinho. Depois de aprovado, **o próprio mantenedor faz o merge** na `main`; você não precisa fazer nada nessa etapa.

### 6. Depois do merge: atualize sua `main` local
```bash
git switch main
git pull
git branch -d feat/nome-da-tarefa
```
Pronto: sua `main` está igual à do GitHub. Volte ao passo 1 para a próxima tarefa.

> **Branch em andamento enquanto outro PR foi mergeado?** Traga as novidades da `main` para a sua branch antes de continuar:
> ```bash
> git switch feat/minha-tarefa
> git fetch origin
> git rebase origin/main
> ```
> Se houver conflito, resolva, `git add` nos arquivos e `git rebase --continue`. Depois do rebase, o push precisa de `git push --force-with-lease`.


---

## ⚠️ Limitações Conhecidas e Premissas

- **Transações da Ponte Câmbio:** O anexo `.xlsx` dentro do arquivo `.eml` é extraído programaticamente pelo parser sem necessidade de manipulação manual.
- **Transações com status "APROVADO C/ RESSALVA":** seguem para liquidação e não mudam nenhum cálculo (R-15 do `HIPOTESES.md`).
- **Identificação de lojista no checkout e na remessa:** nunca por nome. Orbe pelo EC, Ponte pelo CNPJ, ambos resolvidos pela planilha de taxas e pelos aliases confirmados pelo financeiro (R-05). O que não casa vira pendência.
- **Exceção, nos extratos:** o banco não traz CNPJ no Pix enviado, só o nome truncado do destinatário. O Pix enviado é tratado como repasse ao lojista quando esse nome truncado é o **começo** do nome de um lojista (planilha, Orbe ou Ponte), depois de tirar acentos e pontuação. Não há similaridade aproximada, mas um nome curto pode casar com o lojista errado. Isso muda só a conta contábil (2.1.01.001), nunca uma comissão.
- **Saldo inicial do Meridiano:** o OFX só traz o saldo final; o inicial (R$ 204.118,03) é derivado dele e não tem conferência independente.
- **O que não aparece em nenhum arquivo:** o custo da Orbe para a Tarvo e os juros e o IOF da conta garantida. A comissão é a taxa contratada inteira (R-01); esses custos ficam fora do fechamento.
- **Suíte caixa-preta (`npm test`):** falha em um valor (CNPJ 22222222000122: gerado 43,80, esperado 53,80). Duas implementações independentes chegam a 43,80 seguindo as respostas da Helena; a suíte foi escrita antes delas. Não foi lida nem alterada (`CLAUDE.md` §0).
- Veja detalhes completos em [`HIPOTESES.md`](./HIPOTESES.md).
