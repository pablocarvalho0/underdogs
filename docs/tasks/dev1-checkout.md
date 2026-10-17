# Task Dev 1 — Trilha A: Checkout

**Branch:** `feat/trilha-checkout`, a partir da `main` depois do merge do serial (Pablo avisa).
**Arquivo seu:** `src/trilhas/checkout.py` (e módulos novos em `src/trilhas/checkout_*.py`, se quiser).
**Freeze:** PR aberto até **17h00**. Checkpoint opcional às 16h: comissão por lojista saindo com rastro.
**Revisor:** Pablo. Cada regra abaixo tem ID; cite o ID no comentário do código onde ela é aplicada.

Leia antes, nesta ordem: `CLAUDE.md` (diretiva 0 e §5), `HIPOTESES.md` §2.1, §2.3, §2.4, §3 e §5, `src/core/model.py`, `src/core/cadastro.py`, `src/premissas.py`.

## Proibições

- **Não leia nem altere** `tests/test_blackbox_immutable.py` e `tests/fixtures/blackbox/`. Só rode `npm test`.
- O gabarito da suíte roda com um **data pack sintético** (outros CNPJs, outros volumes). Nada fixo para setembro: nenhum CNPJ, EC, data ou total escrito no código. Tudo vem do cadastro e do `premissas.py`.
- Nada de casar lojista por nome. EC → lojista só pelo `Cadastro.lojista_por_ec` (que já aplica os aliases).
- Coluna ausente ou linha estranha não derruba a trilha: vira pendência (R-42).

## Contrato

```python
def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha
```

- Entrada: `dados.orbe`, com as colunas `id_transacao, data_movimento, cod_estabelecimento, nome_estabelecimento, tipo_lancamento, modalidade, qtd_parcelas, bandeira, valor_bruto, taxa_aplicada_pct, valor_taxa, valor_liquido, id_referencia, data_venda_original`.
- `tipo_lancamento`: `VENDA`, `ESTORNO`, `ANTECIPACAO`, `REVERSAO ANTECIPACAO`.
- Toda linha de saída é criada com `LinhaSaida.somando(...)`, e os componentes são linhas do Orbe: `Componente(ARQ_ORBE, id_transacao, valor)`. O writer recusa escrever se a soma não fechar.
- Dinheiro sempre em `Decimal`, arredondado por linha com `brl()` (half-up, inclusive no negativo), e só **depois** somado (R-02).

### O que o serial entrega (já vai estar na `main`)

- `premissas.aliases_ec` com os 3 aliases confirmados (R-05).
- `premissas.isencoes_checkout`: lista de `Isencao(cnpj, inicio, fim, aprovador, fonte)`. É a isenção da Casa (R-08, P-03). Use-a; não escreva a Casa no código.
- `premissas.sem_contrato_lista_zero` (P-02) e `premissas.taxa_saida_em_pp` (P-09).
- `src/core/pendencias.py`:
  ```python
  def pendencia(trilha, chave, tipo, componentes, motivo, quem_decide) -> LinhaSaida
  ```
  Gera `id_saida = PEN-<trilha>-<chave>` e `ref_origem` com os refs juntados por `|`. Use `trilha="CHK"`. **Uma pendência por contraparte e por lojista** (R-37, P-13), nunca uma por transação.

## Regras

**1. Comissão por linha (R-01, R-03, R-04).**
- `VENDA`: `+brl(valor_bruto × taxa_contratada / 100)`, com a taxa vigente em `data_movimento` para a modalidade e as parcelas da linha. Use `cadastro.taxa_contratada_pct(cnpj, modalidade, qtd_parcelas, data)`. **Não use `valor_taxa`.**
- `ESTORNO`: negativo. A taxa é a vigente na **`data_venda_original`**; modalidade e parcelas vêm da linha do estorno. Isso vale também para estorno de venda de agosto, que abate setembro.
- `ANTECIPACAO`: taxa da coluna Antecipação (modalidade `ANTECIPACAO`), na mesma comissão do lojista.
- `REVERSAO ANTECIPACAO`: anula exatamente a comissão da antecipação apontada por `id_referencia` (valor negativo igual).
- Isenção (R-08): lojista com `Isencao` vigente na data da venda (para estorno, na data da venda original) tem comissão 0. Estorno de venda anterior à isenção segue a taxa da venda. Exemplo real: `TX88445133`, venda de 21/08 a 1,49%.

**2. `comissoes_por_lojista.csv`.** Uma linha por lojista: `id_saida = COM-CHK-<cnpj>`, `linha_negocio = CHECKOUT`, componentes = as comissões por linha dele.
- Lojista sem contrato vigente (Atlas, R-06): sem taxa, a linha sai com `0.00` se `sem_contrato_lista_zero` (P-02). Se a flag estiver desligada, fica só na pendência.

**3. `divergencias_taxa.csv` (R-20..R-22, R-24).** Uma linha por transação em que a taxa aplicada pela Orbe ≠ a contratada.
- `id_saida = DIV-CHK-<id_transacao>`, `ref_origem = id_transacao`, `diferenca_brl = brl(valor_bruto × (aplicada − contratada) / 100)`. O estorno de transação divergente entra negativo (R-21).
- Compare **taxa com taxa**. Centavo de truncamento da Orbe não é divergência.
- **Não** é divergência: lojista sem taxa contratada (é pendência), lojista isento (é devolução, P-06).
- Taxas na saída em pontos percentuais (`2.49`) se `taxa_saida_em_pp`.

**4. `notas_a_emitir.csv` (R-26, R-28).** Uma nota por lojista: `id_saida = NF-CHK-<cnpj>`, `tomador_cnpj = cnpj`, `linha_negocio = CHECKOUT`, componentes iguais aos da comissão.
- Comissão ≤ 0 não emite: vira pendência para a Helena.
- `discriminacao` simples, com o serviço e a competência (ex.: `Intermediação de pagamentos (MDR e antecipação) - competência 2026-09`). A competência vem dos dados, não é texto fixo.

**5. Pendências (`trilha="CHK"`).**

| Caso | Componentes | Quem decide |
| :--- | :--- | :--- |
| Lojista sem contrato vigente (Atlas): o que a Orbe cobrou, sem faturar (R-06, R-07) | `valor_taxa` das linhas | Comercial |
| EC sem lojista no cadastro | `valor_taxa` das linhas | Comercial |
| Devolução ao lojista isento: o que a Orbe descontou durante a isenção (R-09) | `valor_taxa` das linhas isentas | Helena + Comercial |
| Comissão ≤ 0, sem nota (R-26) | comissões | Helena |
| Contestação com a Orbe por lojista: soma das divergências (R-25, R-37) | `diferenca_brl` | Helena (Orbe) |
| Parcelado acima de 12x (R-10) | linha | Comercial |
| Alerta de antecipação (R-41, P-08): lojista sem venda antes do mês cuja antecipação acumulada supera as vendas acumuladas em algum dia; citar o pico e as reversões | antecipações | Helena + Comercial |

`motivo` em uma frase que a Helena entenda sem abrir o código.

**6. Invariante (`conservacao`).** Cada linha do Orbe aparece em **exatamente um** destino: componente de comissão ou pendência de lojista não faturado. Registre `conservacao["linhas_orbe"] = total − usadas` (tem que dar 0) e qualquer outra conta que prove que nada sumiu.

## Pronto quando

1. Os números de setembro batem com a prévia do `HIPOTESES.md` §5:

   | Item | Valor |
   | :--- | ---: |
   | Comissão de checkout, 21 lojistas sem a Atlas | **R$ 207.039,73** |
   | Casa do Estudante: comissão | −R$ 5,50, sem nota + pendência |
   | Casa do Estudante: devolução (118 linhas) | R$ 15.396,77 |
   | Atlas: cobrado pela Orbe, sem faturar (57 linhas) | R$ 7.876,05 |
   | Divergências (92 linhas) | R$ 1.576,23 |
   | · Rota Global (à vista, 2–6x e 7–12x, desde 12/09) | 299,62 + 539,26 + 707,40 |
   | · Bridge, à vista 2,19→2,59 (5 vendas de 15 a 18/09) | R$ 29,95 |

   O serial deixa esse controle automatizado em `tests/test_controle_setembro.py` (rode com `npm run test:all`). Se não bater, investigue antes de abrir o PR. Diferença sem explicação **não** se ajusta no código.
2. Três transações da Rota calculadas na mão, no comentário do PR: venda, estorno e parcelado.
3. `npm test`, `.venv/bin/ruff check src` e `.venv/bin/mypy src` rodados, com a saída colada no PR. A suíte caixa-preta só passa por inteiro com as três trilhas; diga no PR qual asserção falha e se ela é da sua trilha.
4. Premissa nova que você tiver que assumir: pare e mande para o Pablo, que decide e põe no `HIPOTESES.md`.
