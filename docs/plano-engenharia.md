# Plano de engenharia — fechamento set/2026 Tarvo

> **Superado em parte (17/10 14h16).** Só a §2 (arquitetura e contrato) continua valendo. Ver `docs/00-COMECE-AQUI.md`.

Rascunho v0 (17/10, 13h20). Decisões marcadas **[D-xx]** estão abertas; perguntas ao
financeiro marcadas **[F-xx]**. Todo número citado aqui foi medido no data pack
nesta sessão, não estimado.

## 0. Relógio

| Quando | O quê |
| :--- | :--- |
| até 13h45 | Fechar decisões D-xx; **enviar F-01..F-10 no #tarvo-financeiro** (atende até 17h30) |
| 13h45–14h15 | **Fase 0a (serial):** contrato congelado — `model.py`, assinaturas, `premissas.py` |
| 14h15–15h00 | **Fase 0b (Pablo)** cadastro + writer · devs já codam a trilha contra o contrato |
| 15h30 | Checkpoint 2: comissão de checkout com rastro saindo (nível mínimo) |
| 14h15–17h00 | **Fase 1 (paralela):** trilhas A, B, C |
| 17h00 | Code freeze das trilhas. Respostas do financeiro que chegarem depois viram flag em `premissas.py`, não código |
| 17h00–17h45 | **Fase 2 (serial):** integração, invariantes, `npm test`, `validate` |
| 17h45–18h20 | README, HIPOTESES, MOMENTOS, export de PROMPTS. Push final 18h20 |
| 18h30–19h00 | Pitch |

## 1. O que os dados mostram (fatos medidos)

**Orbe (1.943 linhas):** 1.840 VENDA, 59 ESTORNO, 38 ANTECIPACAO, 6 REVERSAO
ANTECIPACAO. Sem CNPJ: só `cod_estabelecimento` (22 ECs). `valor_taxa` bate com
`valor_bruto × taxa_aplicada` em 100% das linhas. Nomes inconsistentes para o mesmo EC
("Mundo Aberto" / "MUNDO ABERTO INTERCAMBIO").

**Taxas (aba "Taxas vigentes", 25 lojistas):**
- Percentual em dois formatos (`0.0149` e `'1,49%'`); CNPJ às vezes inteiro sem zero à
  esquerda (`3229837000103`).
- **Bridge tem duas linhas** — crédito à vista 2,59% até 14/09 e 2,19% a partir de 15/09.
- **3 ECs da Orbe sem EC na planilha:** Kiwi (`1038867654`), Horizonte Viagens
  (`1043396662`), e `1043300981 HORIZONTE INTERCAMBIO`. As taxas aplicadas deste último
  batem exatamente com "Novo Horizonte Intercambio" — mas casar por nome é o erro que o
  case avisa.
- **Atlas Idiomas (`1076801732`, 57 linhas) não está na aba vigente.** Só aparece na aba
  "ANTIGO 2025 - nao usar". Taxas aplicadas (3,49/3,99/4,49) não batem com nenhuma tabela.
- Spread de remessa: vazio = "padrão" (valor não escrito); Canguru literalmente `'padrão'`.
- Globo Trotter inativo desde jul/26; Casa do Estudante tem comentário "condição especial".

**Divergências de checkout já visíveis (prévia, sem Atlas/Horizonte Intercâmbio):** 92
linhas, quase todas da **Rota Global**: a Orbe cobra 2,99/3,49/4,09, que são as taxas da
tabela de 2025, contra 2,49/2,99/3,59 contratadas. Cerca de R$ 1,6 mil a mais. Mais 5
vendas da Bridge depois de 15/09 ainda cobradas a 2,59. **Causa raiz candidata para o
pitch:** cadastro da Orbe desatualizado em relação à planilha.

**Ponte (anexo do .eml):** 233 operações (o rodapé diz 233; spread total R$ 78.073,59 bate
com a soma). O loader atual devolve 235 porque **lê as 2 linhas de rodapé como operação**.
- `PC-0926-0162` duplicada; a segunda cópia tem a observação "reprocessada".
- **4 spreads negativos** (−R$ 1.834,05), todos com "Taxa travada no pedido (D-1)" e
  `Spread Estimado (D-1)` positivo.
- 16 "APROVADO C/ RESSALVA" (o e-mail diz que liquidam normalmente).
- 6 operações contratadas em 30/09 e liquidadas em outubro.
- **Mundo Aberto: contratado 1,2% (negociado em jul/26), Ponte aplicou 1,5%** nas 23
  operações. É uma divergência de REMESSA.
- Demais lojistas: spread aplicado bate com o contratado; os sem valor rodam a ~1,5%.

**Aurora (84 lançamentos reais, L9–L92):** o loader incluía `SALDO ANTERIOR` (L8) e 3 linhas de
rodapé (L93–L95) com valor 0 — precisam sair. Padrões claros: TED Orbe, PIX ENVIADO
lojista (repasse), transferência p/ Meridiano, folha, impostos, tarifas. Ambíguos:
`L50 PIX RECEBIDO ... SEM IDENTIFICACAO` (R$ 7.350) e `L65 DEVOLUCAO PIX - MUNDO
ABERTO` (R$ 12.400).

**Meridiano (100 lançamentos):** PIX RECEB de lojistas (recursos de remessa), TED
ENVIADA PONTE (liquidação), TED da própria Tarvo, CDB, tarifas, IOF. **Armadilha:**
"PIX RECEB PONTE AEREA..." é o lojista Ponte Aérea Estudantil, não a Ponte Câmbio.
`TED RECEB PONTE ... REPASSE COMISSAO 08/2026` (R$ 61.884,12) é receita de agosto
recebida em setembro.

## 2. Arquitetura — o rastro é construído, não reconstruído

Ideia central: **nenhuma linha de saída existe sem os componentes que a somam.** Toda
trilha devolve `LinhaSaida` com `componentes`. O writer recusa escrever se
`Σ componentes ≠ valor` — o arquivo `rastro.csv` sai como subproduto e não tem como
divergir.

```
src/
  premissas.py          # flags H-xx (uma por hipótese) + aliases explícitos de EC
  core/model.py         # Componente, LinhaSaida, Pendencia, ResultadoTrilha   (Fase 0a)
  core/cadastro.py      # Lojista, resolve EC→lojista, taxa vigente por data    (Fase 0b)
  core/writer.py        # 6 CSVs + rastro, formato fixo, assert de soma         (Fase 0b)
  core/pipeline.py      # run_pipeline(input_dir, output_dir) junta as trilhas  (Fase 2)
  trilhas/checkout.py   # Trilha A
  trilhas/remessa.py    # Trilha B
  trilhas/extratos.py   # Trilha C
```

Contrato (Fase 0a):

```python
@dataclass(frozen=True)
class Componente:
    arquivo_origem: str      # nome do arquivo do data pack
    ref_origem: str          # id_transacao | Nº Operação | L10 | FITID
    valor: Decimal

@dataclass
class LinhaSaida:
    arquivo: str             # "comissoes_por_lojista.csv" etc.
    id_saida: str
    campos: dict[str, object]
    valor: Decimal | None    # número rastreado da linha (None = sem número)
    componentes: list[Componente]

@dataclass
class ResultadoTrilha:
    linhas: list[LinhaSaida]          # inclui pendências
    conservacao: dict[str, Decimal]   # invariantes da trilha (ver §4)

def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha
```

Restrições que valem para todos:
- `run_pipeline(input_dir, output_dir)` é a assinatura usada pela suíte caixa-preta: os
  loaders precisam aceitar o caminho de `input_dir`, não só o default do `config.py`.
- **Respostas do financeiro mudam flag, não código.** Cada hipótese é um campo de
  `Premissas` com o default escolhido em D-03; a resposta troca o valor e registra no
  HIPOTESES.md.
- Nada de casamento aproximado de nomes. Alias de EC só entra em `premissas.py` com
  justificativa e vira pendência até o financeiro confirmar.
- Esquema de `id_saida`: `COM-CHK-<cnpj>`, `COM-REM-<cnpj>`, `DIV-CHK-<id_transacao>`,
  `DIV-REM-<nº operação>`, `NF-CHK-<cnpj>`, `NF-REM-<cnpj ponte>`,
  `LAN-AUR-L<n>`, `LAN-MER-<fitid>`, `PEN-<trilha>-<ref>`.

## 3. Fase 0 — base serial

**0a. Contrato (30 min, um só autor):** `model.py`, `premissas.py` com as flags vazias
e os defaults, stubs das 3 trilhas devolvendo `ResultadoTrilha([] , {})`, pipeline que
chama os três. Merge em `main` → os devs fazem branch daqui. **É a única parte que
realmente bloqueia.**

**0b. Fundação (45 min, em paralelo com o início das trilhas):**
- Correção dos loaders: rodapé da Ponte, saldo/rodapé do Aurora, `input_dir`.
- `cadastro.py`: normalização de % e CNPJ, vigência (Bridge), resolução EC→lojista com
  aliases explícitos, spread padrão.
- `writer.py`: formato (`;`, ponto decimal, AAAA-MM-DD, CNPJ 14 dígitos), assert de soma
  do rastro, `pendencias.csv`.

Enquanto a 0b não fica pronta, as trilhas usam o loader direto e um `Cadastro` falso de
2–3 lojistas. Integrar depois é trocar o import.

## 4. Fase 1 — trilhas paralelas

Cada trilha entrega as linhas dela **e um invariante de conservação** que prova que
nada sumiu: tudo o que entrou ou está numa saída, ou está numa pendência.

### Trilha A — Checkout (nível mínimo + alvo; é o maior peso da nota)
- Comissão CHECKOUT por lojista: base conforme D-03/F-01; antecipação e reversão
  entram; estorno conforme F-04.
- Divergência por transação: taxa contratada vigente na data × aplicada,
  `diferenca_brl = valor_bruto × (aplicada − contratada)`. Só onde **existe** taxa
  contratada — lojista sem taxa vira pendência, não divergência (alarme falso conta
  contra).
- NF CHECKOUT por lojista (F-08).
- Pendências: Atlas sem taxa, alias não confirmado, estorno de venda de agosto (se F-04
  não responder).
- **Invariante:** `Σ valor_taxa (1.943 linhas) = Σ comissões + Σ pendências`.
- Verificação manual: Rota Global, 3 transações calculadas na mão.

### Trilha B — Remessa
- Deduplicar `PC-0926-0162` (manter 1, a cópia vira pendência).
- Spread negativo → pendência (quem decide: Ponte Câmbio / Financeiro), fora da
  comissão até decidir (D-05).
- Comissão REMESSA por lojista = 50% × spread realizado.
- Divergência de spread contratado × aplicado (Mundo Aberto), fórmula conforme F-07.
- NF REMESSA contra a Ponte Câmbio (CNPJ 75374179000146) pelo total do repasse.
- **Invariante:** `Σ Spread R$ = 78.073,59 = Σ incluído + Σ pendente + Σ duplicata`.

### Trilha C — Extratos
- Tabela de regras (regex sobre a descrição → conta analítica que `ACEITA_LANCTO=S`),
  `metodo=REGRA`, `confianca=1`.
- Resíduo → D-02 (IA ou HUMANO). Os dois ambíguos já conhecidos (L50, L65) viram
  pendência de qualquer forma.
- Armadilha Ponte Aérea × Ponte Câmbio: a regra mais específica vem primeiro.
- **Invariante:** 84 + 100 lançamentos de entrada = lançamentos classificados; saldo
  inicial + Σ = saldo final no Aurora.

## 5. Fase 2 — integração (serial)

Pipeline junta as trilhas → writer → `validate` → `npm test`. Conferir as 3 invariantes
impressas no `run`. Qualquer falha é corrigida na trilha, não no integrador.

## 6. Perguntas ao financeiro (mandar todas numa mensagem, já)

Formato: "[Underdogs] …", sempre com um caso concreto do arquivo.

- **F-01 Base da comissão.** Rota Global foi cobrada a 2,99% no crédito à vista (ex.
  linhas de 01/09), contrato 2,49%. A comissão da Tarvo é o que a Orbe cobrou ou o
  contratado, com a diferença devolvida ao lojista?
- **F-02 Atlas Idiomas** (EC 1076801732) não está na aba vigente. Qual taxa contratada?
  O CNPJ é o 39.566.044/0001-19 da aba antiga?
- **F-03** O EC 1043300981 "HORIZONTE INTERCAMBIO" é o Novo Horizonte Intercâmbio (CNPJ
  66.564.512/0001-99)? E o Kiwi (EC 1038867654) e o Horizonte Viagens (EC 1043396662)
  sem EC na planilha, confirmam?
- **F-04 Estorno de venda de agosto** (ex. TX88444848, venda de 22/08 estornada em
  01/09): abate a comissão de setembro? A Tarvo devolve o MDR inteiro?
- **F-05 Antecipação revertida** (AN88445093 reverte AN88445076 no dia seguinte): a
  receita de antecipação zera?
- **F-06 Spread "padrão"** (Canguru, Kiwi, Ponte Aérea, Bem-Vindo): é 1,5%?
- **F-07 Mundo Aberto:** contrato de 1,2% (jul/26), a Ponte aplicou 1,5% nas 23
  operações. A diferença é devolvida ao lojista? Em R$ = Valor R$ × 0,3%?
- **F-08 Notas de checkout:** uma NF por lojista com MDR + antecipação somados, ou
  separadas?
- **F-09 Spread negativo com taxa travada D-1** (PC-0926-0210, −R$ 687,52; estimado
  D-1 +R$ 587,97): o repasse usa o realizado, o estimado, ou contesta?
- **F-10 Competência:** operação contratada em 30/09 e liquidada em 01/10 (ex.
  PC-0926-0002) entra em setembro?

## 7. Organização do time (D-01, decidido)

| Quem | Durante a Fase 0 (Pablo no serial) | Fase 1 |
| :--- | :--- | :--- |
| **Pablo** | Fase 0a + 0b; dispara F-01..F-10 | Trilha B (remessa) + respostas do financeiro |
| **Dev 1** | Estuda a trilha A: hipóteses, 3 casos calculados na mão, invariante | Trilha A (checkout), branch `feat/trilha-checkout` |
| **Dev 2** | Estuda a trilha C: rascunho da tabela de regras, invariante | Trilha C (extratos), branch `feat/trilha-extratos` |

O estudo de cada dev precisa sair com três coisas escritas, para virar código direto
quando o contrato cair na `main`:
1. As hipóteses da trilha que ainda não estão em §6 — viram pergunta ou flag.
2. **Condições de controle:** o invariante de conservação da trilha (§4) e 3 casos
   reais calculados na mão, com o valor esperado — viram a verificação da trilha.
3. **Dev 1:** tabela EC → lojista → taxa vigente para os 22 ECs, marcando onde não há
   taxa ou EC. **Dev 2:** lista dos padrões de descrição dos dois extratos → conta
   analítica, marcando os que não têm regra óbvia.

Quando 0a estiver na `main`, cada dev faz `git pull` e rebase da própria branch. Merge
final na Fase 2, um PR por trilha, aprovado pelo Pablo.

## 8. Decisões de engenharia em aberto
- **D-02** IA em runtime na classificação dos extratos: sim (resíduo, com cache) ou não.
- **D-03** Default enquanto o financeiro não responde F-01 (comissão pela aplicada ou
  pela contratada).
- **D-04** Aritmética: `Decimal` com arredondamento por linha ou `float`.
- **D-05** Spread negativo e duplicata: fora da comissão até decidir, ou dentro.
- **D-06** Alias de EC sem confirmação (Kiwi, Horizonte Viagens, Horizonte
  Intercâmbio): entra calculado + pendência, ou fica fora.
