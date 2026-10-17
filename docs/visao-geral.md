# Visão geral da solução: fechamento de setembro/2026 da Tarvo

> Documento de orientação. Define **como pensamos o problema** antes de construir. Se o código divergir deste documento, um dos dois está errado e precisa ser corrigido.

---

## 1. O problema em uma frase

O fechamento da Tarvo leva 8 dias úteis porque cada fonte é um arquivo diferente, em formato diferente, conferido à mão, e porque **parte das regras só existe na cabeça de uma pessoa**.

O cliente pediu: *"um agente que feche o mês para a gente"*.
Nossa leitura: o que ele precisa é de um fechamento **rastreável**, que **separa o que é cálculo do que é decisão humana**.

---

## 2. O negócio, em um desenho

```
CHECKOUT (cartão / Pix)
 aluno ──paga──▶ Orbe (adquirente) ──repassa──▶ TARVO ──repassa líquido──▶ lojista
                                                  │
                          Tarvo ganha: MDR + taxa de antecipação

REMESSA (pagamento a escola no exterior)
 lojista ──paga em R$──▶ TARVO ──opera com──▶ Ponte Câmbio ──paga──▶ escola no exterior
                                                  │
                          Tarvo ganha: participação no spread
```

| Linha | Fonte de dados | Sai como |
|---|---|---|
| CHECKOUT | `01_orbe_relatorio_comissoes` (uma linha por transação) | comissão por lojista |
| REMESSA | `03_email_ponte_cambio` (relatório anexo no e-mail) | comissão por lojista |
| Taxas contratadas | `02_tabela_taxas_contratadas.xlsx` (mantida à mão) | referência para divergências |
| Bancos | `05a` Aurora (CSV), `05b` Meridiano (OFX) | lançamentos classificados |
| Plano de contas | `04_plano_de_contas_fenix_erp` | destino da classificação |

---

## 3. Princípios (as regras do nosso jogo)

1. **Perguntar antes de assumir.** Regra de negócio que não está nos arquivos vira pergunta ao financeiro. Se não houver resposta, vira premissa escrita em `HIPOTESES.md`.
2. **Ler os arquivos como vêm.** Sem limpeza manual prévia. A solução faz a padronização.
3. **Padronizar formato, não decidir sentido.** Veja a seção 4.
4. **Todo número tem rastro.** Cada valor de saída aponta para as linhas de origem, e a soma das linhas fecha com o total.
5. **Nunca ajustar para forçar o total.** Se não fecha, ou a regra está errada (corrigimos a regra) ou o dado precisa de uma pessoa (vira pendência).
6. **Alarme falso conta contra.** Na dúvida, pendência é melhor que divergência inventada.
7. **Mínimo certo vale mais que extra errado.** Ordem de entrega: checkout com rastro → alvo completo → extras.

---

## 4. Dois tipos de limpeza

```
LIMPEZA DE FORMATO (a solução faz)      LIMPEZA DE SENTIDO (a solução NÃO decide)
──────────────────────────────────      ─────────────────────────────────────────
vírgula decimal → ponto                 "Escola X" é o mesmo lojista que "ESCOLA X LTDA"?
data pt-BR → AAAA-MM-DD                 taxa diferente da contratada: erro ou exceção negociada?
encoding (cp1252 / utf-8)               spread negativo: aceitar ou rejeitar?
CSV / OFX / EML / XLSX → tabelas        operação repetida no e-mail da Ponte: duplicata ou legítima?
CNPJ só com 14 dígitos                  
            │                                            │
     determinístico                          vira PENDÊNCIA (motivo + quem decide)
```

**Atenção ao casamento de nomes:** aceitar correspondência aproximada "que parece boa" é erro explicitamente citado no case. Só casamos por chave exata (ex.: CNPJ, código do estabelecimento) ou por regra confirmada. O resto vai para pendência.

---

## 5. Fluxo geral

```
 ┌───────────────────────┐
 │ 0. PERGUNTAR          │  financeiro responde regras não escritas
 │    HIPOTESES.md       │  (o que não for respondido vira premissa escrita)
 └──────────┬────────────┘
            ▼
 ┌───────────────────────┐
 │ 1. LER + PADRONIZAR   │  só formato: números, datas, encoding, CNPJ
 │    (formato)          │  cada linha mantém a referência de origem
 └──────────┬────────────┘
            ▼
 ┌───────────────────────┐
 │ 2. APLICAR REGRAS     │  confirmadas ou assumidas (e escritas)
 │                       │  comissão · divergência · nota · classificação
 └──────────┬────────────┘
            ▼
 ┌───────────────────────┐        falha
 │ 3. CONFERIR           │ ─────────────┐
 │  soma saída = soma    │              ▼
 │  das linhas de origem │     regra errada? → corrige a regra
 └──────────┬────────────┘     dado ambíguo? → PENDÊNCIA
            ▼
 ┌───────────────────────┐
 │ 4. SAÍDAS em saida/   │  6 CSVs no formato fixo do case
 └───────────────────────┘

 Exceção em QUALQUER etapa ──▶ pendencias.csv (motivo + quem decide)
```

O **rastro não é uma etapa final**: ele é carregado desde o passo 1. Reconstruir rastro no fim é a forma mais comum de acabar com total que não fecha.

---

## 6. Onde a IA atua e onde não atua

> **Plano inicial, superado na entrega.** Na versão entregue **não há IA no pipeline**: as 184 classificações saem por regra (`metodo=REGRA`), a extração do e-mail da Ponte é por código e os textos de nota e pendência são modelos fixos (P-18 do `HIPOTESES.md`, README §3). A IA atuou só no desenvolvimento e na conferência (`PROMPTS/`). A tabela abaixo fica como registro do plano.

A maior parte do fechamento é **determinística** (leitura, cálculo, soma, comparação). A IA entra onde há texto livre ou onde o resultado é texto para humano.

| Tarefa | Quem faz | Por quê |
|---|---|---|
| Ler e padronizar arquivos | REGRA (código) | formato é previsível |
| Calcular comissão e divergência | REGRA (código) | aritmética sobre regra definida |
| Conferir totais contra o rastro | REGRA (código) | verificação tem que ser reprodutível |
| Classificar linhas de extrato no plano de contas | REGRA primeiro; IA para o que a regra não cobre | descrição bancária é texto livre |
| Extrair dados do e-mail da Ponte | REGRA/IA, conferido por soma | formato de e-mail pode variar |
| Redigir `discriminacao` das notas e explicar pendências | IA | texto para humano |
| Decidir exceções de negócio | HUMANO | regra não escrita |
| **Construir a solução** | IA dirigida por nós, **verificada por nós** | 20% da avaliação é como dirigimos a IA |

A coluna `metodo` (REGRA / IA / HUMANO) e a `confianca` (0 a 1) nos lançamentos classificados tornam essa divisão visível no resultado.

**Regra de ouro:** a IA nunca decide valor em reais sozinha. Ela propõe, o código confere, o humano decide o que é ambíguo.

---

## 7. Entregas e como cada uma se liga ao rastro

| Saída (`saida/`) | O que responde | Origem do rastro |
|---|---|---|
| `comissoes_por_lojista.csv` | quanto a Tarvo ganhou de cada lojista, por linha de negócio | transações Orbe / operações Ponte |
| `divergencias_taxa.csv` | onde a taxa aplicada difere da contratada, em R$ | `id_transacao` / Nº Operação |
| `notas_a_emitir.csv` | para quem, de qual linha e de quanto emitir nota | comissões agregadas |
| `lancamentos_classificados.csv` | cada linha dos extratos no plano de contas | linha `L10, L11…` (Aurora) / `FITID` (Meridiano) |
| `pendencias.csv` | o que exige pessoa, com motivo e responsável | linha que gerou a dúvida |
| `rastro.csv` | liga cada `id_saida` às linhas de origem | soma de `valor` por `id_saida` = número reportado |

---

## 8. FATOS, HIPÓTESES e PERGUNTAS

### Fatos (estão nos arquivos ou nas instruções)
- A Tarvo tem duas linhas de negócio: checkout (Orbe) e remessas (Ponte Câmbio). *(instruções)*
- O relatório da Orbe traz uma linha por transação, incluindo vendas, estornos, antecipações e reversões, com a taxa que a Orbe aplicou. *(`LEIA-ME.md`; colunas `tipo_lancamento`, `taxa_aplicada_pct`, `valor_taxa`, `id_referencia`)*
- As taxas contratadas ficam numa planilha mantida à mão. *(`LEIA-ME.md`)*
- Os formatos chegam como cada sistema exporta: pt-BR, `;`, nomes inconsistentes. *(`LEIA-ME.md`)*
- O plano de contas está em cp1252; Orbe e Aurora estão em utf-8. *(metadados dos arquivos)*
- A solução precisa rodar de novo em outubro com arquivos novos no mesmo formato. *(`LEIA-ME.md`)*

### Hipóteses (prováveis, **não confirmadas**)
- A Tarvo fica com 50% do spread nas remessas. *(informação de partida, a confirmar na planilha de taxas e com o financeiro)*
- Estornos e reversões da Orbe devem reduzir a comissão do mês. *(a confirmar: no mês do estorno ou no mês da venda original?)*
- O CNPJ é a chave para ligar lojista entre as fontes. *(confirmado: a Orbe não traz CNPJ; a ligação é EC → CNPJ pela planilha de taxas, R-05)*

### Perguntas para o financeiro (a refinar com os dados abertos)
1. Como tratar estornos e reversões: abatem a comissão do mês do estorno ou da venda original?
2. Taxa aplicada diferente da contratada: há exceções negociadas fora da planilha?
3. Remessa com spread negativo: aceita, rejeita ou escala para alguém?
4. Operação repetida no e-mail da Ponte: qual é a regra para decidir que é duplicata?
5. A nota fiscal é emitida sobre a comissão da Tarvo, ou sobre o valor movimentado? Uma nota por lojista e linha de negócio?
6. Quem decide cada tipo de pendência (financeiro, fiscal, comercial)?

---

## 9. Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Total bonito que não fecha com as linhas de origem | conferência automática soma(rastro) = saída, antes de gravar |
| Casamento aproximado de nomes gerando correspondência errada | só chave exata ou regra confirmada; o resto vira pendência |
| IA escolhendo regra de negócio sozinha | regra ambígua vira pergunta ou premissa escrita |
| Alarme falso de divergência | divergência só quando a regra de taxa estiver clara; dúvida vira pendência |
| Gastar a tarde no extra e perder o mínimo | ordem fixa: mínimo → alvo → extra |
| Solução que só funciona para setembro | nada de valores fixos por lojista ou mês no código; configurações em arquivo |

---

## 10. Ordem de construção

1. **Mínimo:** comissão de checkout por lojista, com rastro e conferência de soma.
2. **Alvo:** comissão de remessa, divergências de taxa, notas a emitir, lançamentos classificados, pendências.
3. **Extra:** rastro completo em todas as saídas, pendências explicadas, execução em outubro sem retrabalho.

Cada nível só começa quando o anterior fecha. Os números do nível mínimo precisam estar certos antes de qualquer outra coisa.