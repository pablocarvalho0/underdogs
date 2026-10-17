# Hipóteses, premissas e respostas do financeiro

> **Versão de 17/10, 13h50.** Reescrita a partir de todas as respostas do financeiro da Tarvo
> (assinadas "Helena, financeiro da Tarvo") no canal
> [#duvidas-hackathon-ai](https://bartehackathonai.slack.com/archives/C0CA0S5D37B) até 13h50.
> Inclui o arquivo `06_orbe_ajustes_tardios_set2026.csv`, que chegou às 13h10. Consolida os PRs
> #7 (respostas do financeiro e arquivo 06) e #8 (releitura do canal inteiro).
> O canal é compartilhado entre os times ("queremos que todos tenham o mesmo contexto"), então as
> respostas valem para todos. A versão anterior (H-01..H-07) está mapeada na §6.

**Como ler**

| Marca | Significa | Quem aprova |
| :--- | :--- | :--- |
| **Fato** | Medido nos arquivos do data pack por script, ou escrito num documento do case | — |
| **R-xx** | Regra respondida pelo financeiro no canal (link `[Tn]` para o thread) | Regra de fechamento: Helena. Taxa e condição comercial: comercial, registrada pela Helena [T23] |
| **P-xx** | Premissa nossa: decisão que a Helena delegou ("o critério é de vocês, escrevam no HIPOTESES.md") ou que ninguém respondeu | Time Underdogs |
| **Q-xx** | Pergunta ainda sem resposta no canal | — |

---

## 1. Fatos do data pack (medidos)

**Orbe (`01_...csv`)**
- 1.943 linhas: 1.840 `VENDA`, 59 `ESTORNO`, 38 `ANTECIPACAO`, 6 `REVERSAO ANTECIPACAO`.
- 22 ECs e 31 grafias de nome. A Mundo Aberto aparece de 3 jeitos. **Não traz CNPJ.**
- `valor_taxa` é `valor_bruto × taxa_aplicada_pct` **truncado** no centavo, em 100% das linhas.
- Estornos: 50 apontam (`id_referencia`) para vendas do próprio arquivo, todos integrais, com a mesma taxa e o mesmo EC; 9 apontam para vendas de agosto. As 6 reversões apontam para antecipações do mês, pelo valor integral.
- A bandeira do estorno é diferente da bandeira da venda em 39 dos 50 casos. Não importa, porque nenhuma taxa depende da bandeira.

**Orbe, ajustes tardios (`06_orbe_ajustes_tardios_set2026.csv`, chegou às 13h10 de 17/10 [T43])**
- O cabeçalho é **idêntico** ao do 01, com a mesma codificação, separador e formato de data. São 14 linhas, todas com `data_movimento` = 30/09/2026: 10 `ESTORNO`, 3 `REVERSAO ANTECIPACAO` e 1 `VENDA`.
- Nenhum `id_transacao` repete o 01. Os ids continuam a sequência do 01 (o maior TX do 01 é 88446959; o menor do 06 é 88446992).
- Os 10 estornos apontam para vendas de setembro do 01. Todos são integrais, com mesmo EC, modalidade, parcelas, taxa e data da venda. Nenhuma dessas vendas já tinha estorno no 01.
- As 3 reversões anulam por inteiro antecipações do 01: Oxford em 22/09 e 29/09, e Maple em 24/09.
- A venda é da Kiwi (`TX88447225`): R$ 5.480,00, 3x, 3,19%, a mesma taxa das outras 24 vendas parceladas da Kiwi no mês.
- `valor_taxa` também vem truncado, e `valor_liquido` = bruto − taxa em todas as linhas.
- A bandeira do estorno difere da bandeira da venda em 7 dos 10 estornos. Mesmo caso do 01: não muda nenhuma taxa (ver Q-05).

**Planilha de taxas (`02_...xlsx`)**
- Aba "Taxas vigentes": 25 linhas, 24 CNPJs. A Bridge tem 2 linhas: crédito à vista 2,59% até 14/09 e 2,19% a partir de 15/09.
- Kiwi, Horizonte Viagens e Novo Horizonte estão sem EC.
- Percentual ora como número (`0.0149`), ora como texto (`'1,49%'`). CNPJ em 3 formatos, e dois perderam o zero à esquerda (Fluente, Campus Global).
- Spread em branco ou `'padrão'`.
- **Comentário na célula A13 (Casa do Estudante), autora Bia: "conversar com Diego (comercial) sobre condição especial".**
- Linha da Globo Trotter **tachada** ("INATIVO desde jul/26").
- Aba "ANTIGO 2025 - nao usar": é onde aparece a Atlas Idiomas (CNPJ 39.566.044/0001-19).

**Ponte (`03_...eml` → anexo `PonteCambio_Relatorio_TARVO_092026.xlsx`)**
- Cabeçalho na linha 5. São 233 linhas de operação mais 2 linhas de total no rodapé.
- `PC-0926-0162` aparece 2× (a 2ª diz "reprocessada"), então são **232 operações**. O rodapé (233 / R$ 78.073,59) conta a duplicata.
- 4 spreads negativos (−R$ 1.834,05), todos "Taxa travada no pedido (D-1)". 16 "APROVADO C/ RESSALVA". 6 operações contratadas em 30/09 liquidam em 01/10.
- `Spread %` = (Taxa Cliente − PTAX) / PTAX, com ruído de ±0,002 p.p. em torno do contratado.
- CNPJ em 2 formatos. Nome cortado em 20 caracteres.

**Aurora (`05a_...csv`)**
- L1–L7 são cabeçalho, L8 é o saldo anterior, **84 lançamentos de L9 a L92**, e L93–L95 são rodapé.
- O saldo fecha linha a linha e fica negativo de 09/09 em diante (mínimo −R$ 2.289.532,94 em 24/09).

**Meridiano (`05b_...ofx`)**
- 100 transações, FITID único, codificação cp1252.

**Plano de contas (`04_...csv`)**
- 52 contas, 32 com `ACEITA_LANCTO=S`, codificação ISO-8859-1.

**Cruzamentos entre fontes**
- As 21 TEDs Meridiano→Ponte batem ao centavo com Σ(`Valor R$` + `IOF R$`) das operações contratadas no dia. A TED de 22/09 paga a `PC-0926-0162` **uma vez só**.
- 63 dos 64 Pix de lojistas no Meridiano batem com Σ(`Valor R$` + `IOF R$`) das operações dos 7 dias seguintes. O 64º (R$ 18.240,00) é explicado na R-34.
- As 4 transferências Aurora→Meridiano somam R$ 1,45 mi, e só 3 chegam ao Meridiano em setembro (ver R-33).

---

## 2. Regras confirmadas pelo financeiro

### 2.1 Comissão de checkout
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-01 | Comissão = `valor_bruto × taxa contratada`, linha a linha, **e não o `valor_taxa`** da Orbe. É a taxa inteira, sem desconto de custo da Orbe. | [T1] [T15] |
| R-02 | Arredondamento comum ao centavo: meio centavo para cima, e no negativo também (−0,005 → −0,01). **Por linha, depois soma.** A Orbe trunca; nós não. | [T9] |
| R-03 | Estorno abate a comissão **no mês do estorno**, inclusive o de venda de agosto (agosto não reabre). A taxa é a contratada vigente **na data da venda original**; a faixa (modalidade e parcelas) vem da linha do estorno. | [T2] [T33] |
| R-04 | Antecipação entra na comissão do lojista, na mesma nota. A reversão anula só a taxa da antecipação que ela reverte. | [T5] [T15] |
| R-05 | EC→lojista: `1043300981` = Novo Horizonte Intercâmbio; `1043396662` = Horizonte Viagens (são empresas diferentes); `1038867654` = Kiwi Experience. CNPJ e taxas estão nas linhas delas na aba vigente. | [T4] |
| R-06 | **Atlas Idiomas** (`1076801732`) não tem contrato na aba vigente e começou em 10/09: **não fatura** até o comercial confirmar a taxa. O CNPJ da aba 2025 pode ser usado só para identificar; a taxa daquela aba não vale. O repasse continua normal. | [T4] [T34] [T29] |
| R-07 | Quando o comercial confirmar a taxa da Atlas, ela vale desde 10/09, e **setembro é faturado junto com o mês seguinte**. O fechamento seguinte precisa puxar as linhas pendentes. | [T20] |
| R-08 | **Casa do Estudante** (`1018325654`) tem **tarifa zerada no checkout de set a dez/2026**, em MDR e antecipação, por concessão do comercial. Vale para venda a partir de 01/09. Estorno de venda anterior segue a taxa da venda (ex.: `TX88445133`, venda de 21/08, 1,49%). Para a antecipação, vale a data da antecipação (R-44). A remessa segue normal. | [T7] [T35] [T17] |
| R-09 | O que a Orbe cobrou da Casa durante a isenção é **devolução ao lojista**, paga pela Tarvo. Não é divergência de contrato e não entra na cobrança da Orbe. O valor é o descontado de fato (`valor_taxa`). Vira pendência para Helena e comercial, com o total e o detalhe por transação. | [T17] [T26] [T36] [T39] |
| R-10 | A Tarvo não vende acima de 12x. Se aparecer, é pendência. | [T28] |
| R-43 | **Ajuste tardio da Orbe** chega num arquivo à parte, no mesmo formato do 01, e só quando a Orbe tem ajuste (não é todo mês). Se chegar **antes** da aprovação do fechamento, entra no mês do movimento: é o caso do 06, que entra em setembro. Se chegar **depois** da aprovação, entra no mês seguinte. Consequência: a entrada tem que ler **todos** os arquivos da Orbe da pasta do mês, e não um nome fixo. | [T40] [T43] |
| R-44 | Isenção da Casa na **antecipação**: vale a data da antecipação, não a das vendas antecipadas. Antecipação feita em setembro é isenta, e não é preciso procurar as vendas de origem. | [T41] |

### 2.2 Comissão de remessa
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-11 | Comissão = **50% do `Spread R$` realizado**, e não do contratado. É calculada por operação, com o arredondamento da R-02 (50% de 262,01 = 131,01). | [T6] [T9] |
| R-12 | Spread em branco ou "padrão" é **1,5% sobre a PTAX de referência**. | [T6] |
| R-13 | O Nº de operação é único: operação repetida **conta uma vez**, e a repetição entra na lista para a Ponte corrigir o relatório. | [T6] [T13] |
| R-14 | Spread negativo ("taxa travada D-1") **não é aceito**: a trava vale 2 horas e já tinha vencido. Fica fora da comissão e da nota. Vira pendência de contestação com **dois valores**: o spread do relatório e a diferença até o spread do contrato (ex.: `PC-0926-0210`: −R$ 687,52 e −R$ 1.351,87). Os dois números do exemplo são cálculo do time que perguntou; a Helena confirmou a regra, não os valores (R-48). | [T6] [T32] |
| R-15 | "APROVADO C/ RESSALVA" não muda nada. | [T6] |
| R-16 | A competência é a **data de contratação**. | [T6] |
| R-17 | Mundo Aberto: a comissão e a nota saem **pelo realizado**, com o excesso sobre 1,20% incluído. A contestação é um processo à parte. Se a Ponte devolver, a nossa metade sai no mês do ajuste. Não presumir que a Ponte vai descontar algo do repasse. | [T11] [T12] |
| R-18 | Ajuste de contestação (de outubro em diante) chega como **linha nova**, com Nº próprio, `Spread R$` negativo e Observação "AJUSTE REF PC-…". Entra no mês em que aparece e abate a participação dentro da nota única. O rastro aponta para a operação original. Não há nenhum em setembro. Se o `Spread R$` do ajuste é o spread inteiro ou já a nossa parte está em aberto (Q-04). | [T31] |
| R-19 | Operação de CNPJ fora da planilha: calcular a nossa metade mesmo assim e abrir pendência de cadastro para o comercial. Não aconteceu em setembro. **A rigor é premissa**: a proposta foi de um time e a Helena respondeu "o tratamento que vocês propuseram é razoável. Registrem como premissa." Mantida aqui com o mesmo ID porque as tasks já a citam. | [T18] |

### 2.3 Divergências de taxa
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-20 | Divergência = **taxa** aplicada ≠ contratada. O valor é `valor_bruto × (aplicada − contratada)`. Centavo de truncamento da Orbe não é divergência. | [T9] |
| R-21 | É listada transação por transação. O estorno de uma venda com taxa errada entra com valor negativo. Da Orbe só se cobra a diferença líquida. | [T17] [T33] |
| R-22 | **O que decide é o contrato, não o aviso.** São divergência: Bridge (aditivo de 2,19% desde 15/09), Mundo Aberto (1,20% desde julho) e Rota (o contrato não mudou). O lojista é ressarcido e a Helena contesta com a Orbe ou a Ponte. A Casa **não** é divergência (R-09). | [T32] [T7] |
| R-23 | Na remessa, divergência é o **lojista** pagar spread diferente do contratado. O valor é **cheio**, não a nossa metade. A tolerância é decisão nossa (P-01). Spread negativo não é divergência (R-14); pode ser listado, desde que marcado como outra natureza. | [T8] [T17] [T16] |
| R-24 | Orbe cobrando abaixo do contrato também é divergência, decidida caso a caso. Não ocorreu em setembro. | [T17] |
| R-25 | Divergência não vai automática para cobrança: a Helena decide caso a caso, com transação e valor. | [T1] |
| R-49 | Ninguém avisa a Orbe nem a Ponte de condição nova: "O comercial fecha e, quando lembra, manda um e-mail para a Orbe ou a Ponte. A Bridge foi avisada alguns dias depois de 15/09, e a Casa do Estudante e a Mundo Aberto não foram avisadas." Contexto da R-22: o aviso não muda quem deve. | [T22] |

### 2.4 Notas fiscais
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-26 | Checkout: **uma nota por lojista por mês**, no valor da comissão pela taxa contratada (com a antecipação). Comissão **zero ou negativa não emite**: vira pendência para a Helena e não passa automaticamente para o mês seguinte. | [T5] |
| R-27 | Remessa: **uma nota só, com a Ponte Câmbio como tomadora** (75.374.179/0001-46), pelo total da participação no mês. Não há nota por lojista. | [T5] |
| R-28 | Discriminação sem texto padrão: algo simples com o serviço e a competência. | [T5] |
| R-45 | A nota de checkout **não gera cobrança nova**: "A Orbe já liquida o líquido: a taxa é descontada na hora em que ela paga [...]. A nota só documenta a taxa que já foi descontada e não gera cobrança nova. Por isso, quando a Orbe cobra a mais, o lojista já recebeu a menos e eu preciso devolver." | [T25] |

### 2.5 Extratos e plano de contas
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-29 | `conta_codigo` é a **contrapartida** do movimento no banco. Se o valor já estava registrado, o movimento baixa a conta onde ele estava; o resto vai para a natureza (receita ou despesa). | [T10] [T28] [T29] |
| R-30 | Já estavam registrados: folha, ISS, INSS, FGTS e DARFs **de agosto** (provisionados) e o repasse da Ponte de 04/09 (comissão de agosto a receber). Nada mais: tarifas, aluguel, cloud, assinaturas e serviços entram como despesa do mês. | [T7] [T10] [T21] |
| R-31 | A provisão de folha e impostos de setembro fica **fora** do nosso fechamento (é da contabilidade). Classificamos só o que passou nos extratos. | [T36] |
| R-32 | Pix de R$ 7.350 sem identificação (L50): **não é receita** até alguém identificar. A devolução de Pix da Mundo Aberto, R$ 12.400 (L65), é um repasse que voltou, motivo ainda desconhecido; servem a 2.1.01.001 ou a 2.1.01.002 (P-04). | [T7] [T21] |
| R-33 | A transferência de R$ 300 mil de 30/09 (L92) cai no Meridiano em 01/10. | [T7] |
| R-34 | O Pix de R$ 18.240 da Ponte Aérea (`MRD2026090425`) é dinheiro de uma remessa que sai em outubro. A Ponte Aérea Estudantil é lojista, não tem relação com a Ponte Câmbio. Fica em recursos para remessas. | [T17] [T18] [T42] |
| R-35 | O saldo negativo do Aurora é a **conta garantida**, usada para pagar lojistas antes de a Orbe liquidar. A Orbe deposita tudo no Aurora: débito e Pix em D+1, crédito e parcelado ao longo dos meses. Conciliar Orbe × banco parcela por parcela fica fora deste fechamento. | [T14] |
| R-36 | O repasse ao lojista é 2× no mês (~10 e ~24), do que a Orbe já liquidou. Às vezes a Bia antecipa pela conta garantida, sem regra nem limite. O repasse à Atlas continua. | [T25] [T27] [T29] |

### 2.6 Pendências, contestação e governança
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| R-37 | Uma pendência **por contraparte e por lojista**, com o detalhe das transações. Ela vira o **rascunho de e-mail de contestação** por contraparte, que a Helena revisa e envia. | [T22] [T28] |
| R-38 | A contestação com a Ponte ainda não foi aberta; considerar que estamos dentro do prazo. Manter como pendência de contestação, com valor e operações. | [T13] |
| R-39 | "Conferir a TED da Ponte quando cair" é pendência de acompanhamento válida e fica com a Helena. Pendência de acompanhamento **não é alarme falso**. | [T12] [T30] |
| R-40 | Quem decide: **taxa, cadastro e contrato, o comercial** (a Bia mantém a planilha, mas não decide taxa). **Regra de fechamento e liberação, a Helena.** Registrar quem aprovou cada regra e quando. | [T23] [T28] [T37] |
| R-41 | Antecipação acima das vendas vira **alerta** para Helena e comercial e não muda nenhum número. O critério é nosso (P-08). | [T17] [T32] [T36] [T38] |
| R-42 | Todo mês a estrutura é a mesma, mas arquivo pode atrasar, a Orbe pode mandar ajuste depois do relatório e parceiro já mudou layout sem avisar. **A solução deve avisar, não quebrar em silêncio.** Se faltar uma fonte, fecha o que não depende dela, marca o provisório e explica o bloqueio. Quem libera é a Helena (taxa e cadastro passam antes pelo comercial). | [T37] |
| R-46 | Retorno da contestação: "A Ponte responde por e-mail e manda o ajuste no relatório do mês seguinte, como crédito ou débito. Eu confiro e registro no fechamento do mês em que o ajuste aparece." Complementa a R-18. | [T25] |
| R-47 | Caso que nenhuma regra cobre: "Para o que aparecer fora disso, me digam como vocês tratariam e por quê." O agente propõe o tratamento com o motivo e gera pendência; não decide sozinho. | [T6] |
| R-48 | **A Helena não valida número nem conta contábil.** "Número eu não valido. Quem fecha é você, e a banca vai olhar o rastro." [T12]; "Conta por conta eu não valido." [T28] [T29]; "Os números eu não confiro." [T35]. Tabela de contas proposta por time no canal (TED da Orbe → 1.1.03.001, Pix ao lojista → 2.1.01.001 etc.) é **proposta**, não regra: confirmado é só o critério da contrapartida (R-29). Os lançamentos propostos na thread [T7] depois da resposta dela também ficaram sem resposta. | [T7] [T12] [T28] [T29] [T35] |

**Contexto do processo atual** [T25], útil para o pitch e não para o código: a Bia cuida do
checkout e da planilha de taxas, o Caio cuida dos bancos e das remessas, e a Helena confere,
decide as exceções e fala com comercial, Orbe e Ponte. O fechamento leva uns 3 dias de comissão
de checkout (metade manual, metade retrabalho por planilha desatualizada), uns 2 de remessa
(a maior parte espera), uns 2 de classificação de extrato (quase tudo manual), e o último dia é
das notas e da revisão. A conclusão de cada etapa é marcada com "ok" e data numa aba de controle
da planilha. Nas palavras dela: "Quase tudo que vocês já descobriram aqui no canal estava só na
minha cabeça".

### 2.7 Logística do hackathon
| ID | Regra | Fonte |
| :--- | :--- | :--- |
| L-01 | Canal único `#duvidas-hackathon-ai`: começar com `[Financeiro]` ou `[Logística]` e o nome do time, uma pergunta por thread. | [T24] |
| L-02 | **A solução tem que rodar**: recebe a pasta (ou upload) do mês, não tem nada fixo para setembro, roda com um comando e gera os 6 CSVs. O README diz como rodar e onde configurar a chave de API. A banca roda com os arquivos do case, **inclusive os que chegarem durante o dia**, e compara com o `saida/` entregue. **O fechamento das 18h30 tem que considerar o 06.** | [T19] [T30] [T43] |
| L-03 | Não vai ter pacote de outubro. O `saida/` tem só setembro. | [T30] |
| L-04 | `pendencias.csv`: vários `ref_origem` separados por `|` valem; `quem_decide` é texto livre, coerente com o canal. **Alarme falso é marcar divergência onde não existe.** | [T30] |
| L-05 | Um repositório por time, com tudo dentro. | [T3] |
| L-06 | Agenda: 11h45 checkpoint 1 (opcional, passou), **16h00 checkpoint 2** (opcional), **17h45 fim do atendimento do financeiro**, **18h30 link do repositório por e-mail**, **19h00 link do pitch por e-mail**, 19h30 finalistas, 20h30 premiação. O checkpoint 2 pede: o que roda de ponta a ponta, o que mudou no plano, o que vai ser cortado, o maior risco e em que a banca pode ajudar. Uma pessoa do time manda por mensagem privada ao organizador, começando com o nome do time. | [T24] |
| L-07 | Chave de API: "quem quiser enviar sua chave de API junto do desenvolvimento para testarmos, ok. lembrem-se de limitar o uso dela". Opcional; o README diz onde configurá-la (L-02). | [T45] |
| L-08 | O repositório entregue tem "código, `saida/`, `PROMPTS/`, `HIPOTESES.md` e um `README.md` que rode a solução do zero". Parte em plataforma online vai como link no README, com instruções de teste. "A regra das 18h30 vale para tudo: o que mudar depois não conta." Detalha a L-05. | [T3] |
| L-09 | O canal `#tarvo-financeiro` do documento do desafio **não existe**. "podem enviar aqui. explicitem na thread de duvida se é tarvo ou hackaton." | [T1] |

---

## 3. Premissas nossas (decisões delegadas ou sem resposta)

Status: **proposta**, a confirmar pelo time no PR, menos onde está marcado **decidida**.

| ID | Premissa | Por quê | Fonte da delegação |
| :--- | :--- | :--- | :--- |
| P-01 | Na remessa, \|`Spread %` − contratado\| **< 0,01 p.p. é ruído**, não divergência. | O ruído observado é ±0,002 p.p.; a menor divergência real de setembro (Mundo Aberto) é +0,30 p.p. Assim não sai alarme de centavo e não passa diferença de verdade. | [T8] |
| P-02 | **Decidida pelo time (17/10, PR #16, D-03 (a)).** A Atlas **não aparece** em `comissoes_por_lojista.csv`: sem taxa na aba vigente, não há comissão a calcular, e ela não fatura até o comercial confirmar (R-06). As 57 transações (R$ 7.876,05 cobrados pela Orbe) ficam fora da comissão e da nota. **No nível Mínimo** elas só aparecem na contagem de conservação do `run` (`checkout.sem_contrato_1076801732: 57`); **no Alvo** viram uma pendência para o Comercial em `pendencias.csv`, com as 57 transações no rastro. Não gera divergência. | É o que a Helena respondeu no canal: "não fatura até o comercial confirmar a taxa" (R-06) e "setembro é faturado junto com o mês seguinte" (R-07). Uma linha 0,00 com 57 componentes somando zero seria artificial. A pendência é o que o fechamento de outubro vai puxar (R-07). | [T4] [T20] [T34] |
| P-03 | Condição comercial fora da planilha (a isenção da Casa) fica em **configuração com vigência e aprovador**, nunca no código. | Rodar em outubro sem mexer em código. A isenção vale até 31/12. | [T23] [T37] |
| P-04 | Devolução de Pix da Mundo Aberto (L65) → **2.1.01.001** (o repasse volta a ser devido), com pendência pelo motivo. | Qualquer das duas serve; mantemos o mesmo critério. | [T21] |
| P-05 | O valor da divergência da Mundo Aberto vem de `Spread %` × `Valor ME` × `PTAX` (R$ 1.418,85), e não da proporção do `Spread R$` (R$ 1.418,88). | Mesma fórmula da R-20: base × diferença de taxa. | [T28] |
| P-06 | A isenção da Casa **não** entra em `divergencias_taxa.csv`; fica só na pendência, com detalhe por transação no rastro. | Evita misturar com divergência de contrato (R-09). Listar é opcional. | [T36] |
| P-07 | Spreads negativos **não** entram em `divergencias_taxa.csv`; ficam só na pendência de contestação. | O lojista não pagou a mais (R-23). | [T16] |
| P-08 | Alerta de antecipação: lojista **sem venda antes do mês** cuja antecipação acumulada supera as vendas acumuladas em algum dia do mês (o **pico**), citando as reversões. Em setembro acende só para a Atlas (pico em 15/09: R$ 179.592,82 antecipados contra R$ 55.357,50 vendidos). | Antecipação é sobre a agenda inteira, então comparar com as vendas do mês acende lojista demais. O que preocupa é lojista novo antecipando alto. | [T32] [T38] |
| P-09 | **Decidida pelo time (17/10 13h40).** `taxa_contratada_pct` e `taxa_aplicada_pct` em **pontos percentuais** (`2.69`). Internamente o cálculo usa fração; a conversão é feita só na gravação do CSV. | É a unidade da coluna `taxa_aplicada_pct` da Orbe, e a Orbe manda todo mês no mesmo modelo (o 06 confirma). Não muda nenhum valor em R$. | — |
| P-10 | `arquivo_origem` no rastro é o nome do arquivo do data pack. Para a Ponte, o `.eml` (`03_email_ponte_cambio_relatorio_set2026.eml`), com `ref_origem` = Nº Operação. | É o arquivo que chega no pacote; o xlsx é extraído dele. Ver Q-02. | — |
| P-11 | Transferência de R$ 300 mil (L92) → 1.1.09.001, com pendência de acompanhamento: confirmar o crédito no Meridiano em 01/10. | R-33 + R-39. | — |
| P-12 | Pix de R$ 18.240 (`MRD2026090425`) → 2.1.02.001. Não é pendência de decisão, porque a R-34 explica; no máximo acompanhamento até a operação de outubro. | R-34. | — |
| P-13 | Pendência é **uma por contraparte e por lojista**, com os `ref_origem` separados por `|`. | R-37 + L-04. | — |
| P-14 | Ajuste da Orbe com `id_transacao` que **já existe** em outro arquivo da Orbe do mês: se a linha for idêntica, conta uma vez. Se for diferente, **vale a versão do ajuste**, e uma pendência para a Helena mostra as duas linhas e o efeito na comissão e na divergência. A linha substituída não entra no rastro. | É a informação mais recente da fonte, e a Helena vê a troca antes de liberar. A duplicata idêntica segue a lógica da R-13. Não aconteceu em setembro. | [T40] |
| P-15 | **Fonte: briefing interno (áudio de 17/10, transcrição em `docs/audios/briefing-transcricao.txt`).** O sistema recebe um data pack no formato do template e gera os 6 arquivos de `saida/`. Tem de rodar com **outro data pack** sem mudar código: nada de nome de arquivo, CNPJ, data ou total de setembro fixo. | Fala do briefing: "um sistema que você vai enviar os dados que estão no template [...] e com esses dados vai sair num output padronizado". Reforça a recomendação (a) da D-01 e a regra das tasks sobre o data pack sintético da suíte. **Inferência nossa** a partir da fala: o áudio não diz "outro mês" explicitamente. | Briefing interno |
| P-16 | **Fonte: briefing interno (áudio de 17/10).** O sistema **detecta e registra** divergências e pendências, mas não as resolve: a decisão fica com o time (o `quem_decide` de cada linha). Não implementamos heurística de resolução. | Fala do briefing: "depois disso, o resto do time vai pensar o que fazer com essas pendências e divergências". É consistente com a regra 3 do `CLAUDE.md` e corta escopo antes do prazo das 18h30. | Briefing interno |

---

## 4. Perguntas abertas (ainda não respondidas no canal)

| ID | Para | Pergunta | O que destrava |
| :--- | :--- | :--- | :--- |
| Q-02 | `[Logística]` | No `rastro.csv`, qual `arquivo_origem` usar para valores da Ponte: o `.eml` do pacote ou o xlsx anexado? **Não enviada.** | A correção automática do `rastro.csv` (P-10) |
| Q-04 | Desbravadores, 12h04 [T44] | No ajuste da Ponte ("AJUSTE REF PC-…"), o `Spread R$` negativo é o spread inteiro (a nossa parte cai 50% dele) ou já a nossa parte (cai 100%)? Ex.: devolução de R$ 235,74 da `PC-0926-0434`. | A R-18 de outubro em diante. Não afeta setembro |
| Q-05 | Turma do Barulho, 13h35 [T46] | 7 estornos do 06 têm bandeira diferente da venda referenciada. Mantém o vínculo, abate pela taxa da venda e registra a divergência de bandeira para a Orbe corrigir? | Se a bandeira divergente vira pendência para a Orbe. Não muda nenhum valor (nenhuma taxa depende da bandeira) |
| Q-06 | Desbravadores, 13h36 [T47] | (1) Mesmo `id_transacao` no relatório e no ajuste, com valores iguais ou diferentes. (2) Estorno ou reversão no ajuste que aponta para transação do mês que **não está** em nenhum arquivo da Orbe. | (1) já coberto pela P-14. (2) Hoje não há regra: não acontece em setembro |
| Q-07 | Turma do Barulho, 13h48 [T48] | Estrutura de rastro desejada e padrão para ser auditável pela Tarvo e pela Barte. | Pode mudar o formato do `rastro.csv`, se a resposta for além do §4 do `CLAUDE.md` |

As 3 perguntas da versão anterior deste arquivo **não chegaram a ser enviadas**. Todas foram respondidas no canal por perguntas de outros times (ver §6). Duas perguntas da versão de 13h25 também saíram da lista: a Q-01 (unidade da taxa) foi decidida pelo time (P-09), e a Q-03 (ajuste da Orbe) foi respondida pela R-43. Das perguntas do PR #8, a de ajuste da Orbe e a de isenção da Casa na antecipação foram respondidas antes das 13h40 (R-43 e R-44); só a do ajuste da Ponte segue aberta (Q-04). As Q-04..Q-07 são de outros times; acompanhamos as respostas.


### 4.1 Decisões internas do time (antes das trilhas)

Não são perguntas para o canal: são escolhas nossas, levantadas na consolidação dos PRs #7 e #8. Cada uma traz uma recomendação; quando o time decidir, ela vira P-xx (ou ajuste de uma P existente) e sai daqui.

| ID | Decisão | Opções | Recomendação e por quê |
| :--- | :--- | :--- | :--- |
| D-01 | Como a entrada acha os arquivos do mês. Hoje `src/config.py` usa o nome fixo de setembro: o 06 é ignorado (checkout R$ 3.304,39 acima do certo) e outubro quebra (L-02). | (a) papel pelo **cabeçalho**, com o prefixo `01_`/`06_` como desempate; (b) só pelo prefixo numérico; (c) glob pelo nome do parceiro | **(a)**. A suíte caixa-preta roda com um data pack sintético, cujos nomes de arquivo não conhecemos. Todos os arquivos da Orbe são concatenados com `arquivo_origem` por linha. Papel faltando ou arquivo desconhecido gera pendência (R-42). |
| D-02 | Estorno ou reversão no ajuste que aponta para transação do mês que **não está** em nenhum arquivo da Orbe (Q-06, parte 2). | (a) abate e gera pendência; (b) não abate, só gera pendência; (c) esperar a resposta da Helena | **(a)**. A linha do estorno já traz modalidade, parcelas e `data_venda_original`, que é tudo de que a R-03 precisa. É o mesmo mecanismo dos 9 estornos de agosto. A pendência diz "venda original não veio". |
| D-03 | Atlas na `comissoes_por_lojista.csv` (P-02). | (a) não aparece, fica só na pendência; (b) aparece com 0,00 | **(a)**. A Helena disse que a Atlas não fatura. Uma linha 0,00 com 57 componentes somando zero é artificial, e a L-04 diz que alarme falso conta contra. A pendência carrega o detalhe e os R$ 7.876,05. **Decidida: (a)**, registrada na P-02 (17/10, PR #16). |
| D-04 | Bandeira do estorno diferente da venda (7 de 10 no 06, 39 de 50 no 01; Q-05). | (a) só registro aqui; (b) pendência informativa para a Orbe | **(a)**. Nenhuma taxa depende da bandeira, e a frequência indica ruído do dado. Pendência aqui seria alarme falso (L-04). |
| D-05 | Status das premissas P-01..P-08 e P-10..P-14, que ainda estão como **proposta**. | Confirmar em bloco ou contestar uma a uma | Confirmar em bloco, menos a P-02 (depende da D-03). As tasks das trilhas já foram escritas em cima delas. |
| D-06 | Destino dos PRs #7 e #8. | Fechar os dois quando este for mergeado | Fechar. Todo o conteúdo deles está aqui, e o log da §7 registra o que mudou de ID. |

---

## 5. Prévia independente dos números de setembro (para controle)

Calculada por um script de exploração, fora do `src/`, aplicando as regras acima aos arquivos **01 + 06** da Orbe. **A implementação das trilhas tem que chegar aos mesmos valores.** Se não chegar, alguém errou, e vale investigar antes de entregar.

| Item | Valor | Regras |
| :--- | ---: | :--- |
| Comissão de checkout, 21 lojistas (sem Atlas), com o 06 | **R$ 203.735,34** | R-01..R-08, R-43 |
| · sem o 06, só para comparar | R$ 207.039,73 | |
| Casa do Estudante: comissão do mês (só o estorno `TX88445133`) | −R$ 5,50 → sem nota, pendência | R-08, R-26 |
| Casa do Estudante: devolução ao lojista (118 linhas isentas) | R$ 15.396,77 | R-09 |
| Atlas: o que a Orbe cobrou e não será faturado (57 linhas) | R$ 7.876,05 | R-06 |
| Divergências de checkout (contrato): 92 linhas | R$ 1.576,23 | R-20..R-22 |
| · Rota Global, crédito à vista 2,49% → 2,99% (desde 12/09) | R$ 299,62 | |
| · Rota Global, 2–6x 2,99% → 3,49% (desde 12/09) | R$ 539,26 | |
| · Rota Global, 7–12x 3,59% → 4,09% (desde 12/09) | R$ 707,40 | |
| · Bridge, crédito à vista 2,19% → 2,59% (5 vendas de 15 a 18/09) | R$ 29,95 | |
| Comissão de remessa: 228 operações (232 − 4 negativas) → uma nota para a Ponte | **R$ 39.543,45** | R-11..R-17 |
| Divergência de remessa: Mundo Aberto, 23 operações (valor cheio) | R$ 1.418,85 | R-23, P-01, P-05 |
| Spreads negativos: pelo relatório / pela diferença até o contrato | −R$ 1.834,05 / −R$ 3.565,98 | R-14 |

Na Rota, o débito (1,49%) e o Pix (0,89%) foram cobrados certo o mês inteiro. A diferença é só no crédito, a partir de 12/09.

**O que o 06 muda (−R$ 3.304,39 no checkout).** Muda só a comissão de 7 lojistas. Divergências, Casa, Atlas e remessa ficam iguais: nenhuma linha do 06 é de Rota, Bridge à vista, Casa ou Atlas, e as taxas aplicadas batem com o contrato.

| Lojista | Linhas do 06 | Comissão sem o 06 | Com o 06 | Diferença |
| :--- | :--- | ---: | ---: | ---: |
| Oxford Prep | 2 estornos e 2 reversões de antecipação | 16.077,90 | 13.845,71 | −2.232,19 |
| Maple Study | 2 estornos e 1 reversão | 15.010,78 | 14.165,77 | −845,01 |
| EduAbroad | 2 estornos | 12.070,17 | 11.858,16 | −212,01 |
| Bridge | 2 estornos | 11.916,02 | 11.769,74 | −146,28 |
| Dublin Hub | 1 estorno | 11.906,08 | 11.876,37 | −29,71 |
| Mundo Aberto | 1 estorno | 18.522,09 | 18.508,09 | −14,00 |
| Kiwi | 1 venda | 10.711,41 | 10.886,22 | +174,81 |

Todas as 7 notas de checkout mudam de valor, e nenhuma fica zerada ou negativa.

---

## 6. O que aconteceu com as hipóteses e perguntas anteriores

| Antes | Situação agora |
| :--- | :--- |
| H-01 estorno reverte a comissão | **Confirmada**, com detalhe: taxa da data da venda e mês do estorno (R-03) |
| H-02 divergência por modalidade/bandeira | **Ajustada**: não há taxa por bandeira. A chave é lojista × modalidade × faixa de parcelas × data da venda (R-20, R-21). A remessa precisa de tolerância (P-01) |
| H-03 nota de checkout contra o lojista pela receita | **Confirmada**, pela taxa contratada (R-26) |
| H-04 nota de remessa contra a Ponte | **Confirmada** (R-27) |
| H-05 duplicata só como pendência | **Substituída**: conta uma vez e entra na lista para a Ponte (R-13) |
| H-06 spread negativo como pendência | **Confirmada**: fora da comissão, pendência com os dois valores (R-14) |
| H-07 conciliar repasses do Aurora com o líquido das vendas | **Descartada**: a Helena disse que não precisa neste fechamento (R-35) |
| Plano F-01..F-10 (`docs/plano-engenharia.md`) | F-01 → R-01; F-02 → R-06; F-03 → R-05; F-04 → R-03; F-05 → R-04; F-06 → R-12; F-07 → R-17, R-23; F-08 → R-26; F-09 → R-14; F-10 → R-16 |

---

## 7. Log de decisões

- **17/10 08:30** — Repositório criado com proteção de branch e aprovação por PR.
- **17/10 08:35** — Arquitetura com `rastro.csv` nativo.
- **17/10 13:25** — Reescrita a partir das respostas do financeiro no canal (R-01..R-42), com premissas propostas (P-01..P-13), perguntas abertas (Q-01..Q-03) e prévia de controle (§5).
- **17/10 13:40** — Entrou o `06_orbe_ajustes_tardios_set2026.csv` (fatos na §1, R-43, R-44, P-14, §5 recalculada). P-09 decidida: 2.69. Q-01 e Q-03 saíram da lista.
- **17/10 13:50** — Consolidação dos PRs #7 e #8. Do #8 entraram, renumerados para não colidir com o #7: R-45..R-49 (no #8 eram R-43..R-47), a agenda completa na L-06, L-07..L-09 (no #8, L-08, L-11, L-10), Q-04 (no #8, Q-06), o contexto do processo e as ressalvas na R-14 e na R-19. Saíram do #8 a L-07 (o 06 já está no data pack) e as Q-04/Q-05 dele (respondidas: R-43, R-44). Entraram as Q-05..Q-07, de threads posteriores. Links [T40]..[T43] seguem a numeração do #7; [T44]..[T48] são novos.

- **17/10 14:15** — Briefing interno em áudio transcrito (faster-whisper large-v3, 36 s). Entraram a P-15 (entrada reprocessável com outro data pack, reforça a D-01 (a)) e a P-16 (o sistema registra pendências e divergências, mas não as resolve).
- **17/10 15:10** — Nível Mínimo implementado (PR #16): comissão de checkout por lojista com rastro, conferida contra a §5 (R$ 203.735,34 em 21 lojistas). D-03 decidida como (a): a Atlas fica fora da comissão e a pendência dela entra no Alvo (P-02 reescrita).

---

## Fontes (threads do canal)

[T1]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792191465288839 "Fox AI: base da comissão (16/10 20h)"
[T2]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792191877776469 "MN AI: estorno de venda de agosto (16/10 20h04)"
[T3]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792192104351419 "MN AI: um repositório por time (16/10 20h08)"
[T4]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792192601377449 "Fox AI: 4 ECs fora da planilha (16/10 20h16)"
[T5]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792193219408319 "MN AI: regra das notas (16/10 20h26)"
[T6]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792193429257939 "MN AI: lógica da remessa (16/10 20h30)"
[T7]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792193803331999 "Participante: Rota, Casa, competência, créditos sem origem (16/10 20h36)"
[T8]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792194771073879 "Fox AI: divergência de remessa e tolerância (16/10 20h52)"
[T9]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792195651974369 "Fox AI: arredondamento (16/10 21h07)"
[T10]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792195685607029 "Fox AI: critério do plano de contas (16/10 21h08)"
[T11]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792196203351619 "Participante: nota pelo realizado na Mundo Aberto (16/10 21h16)"
[T12]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792198608227769 "Participante: tratamento da remessa (16/10 21h56)"
[T13]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792199088314709 "Insper AI: prazo de contestação (16/10 22h04)"
[T14]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792199352656099 "Insper AI: Aurora e liquidação da Orbe (16/10 22h09)"
[T15]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792200039150939 "Fox AI: 3 confirmações de checkout (16/10 22h20)"
[T16]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792237413528249 "MN AI: spread negativo × divergência (17/10 08h43)"
[T17]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792238981638289 "Participante: 7 perguntas (17/10 09h09)"
[T18]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792239424862549 "Desbravadores: Pix de R$ 18.240 e CNPJ fora da planilha (17/10 09h17)"
[T19]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792239664713999 "Organização: a solução precisa rodar (17/10 09h21)"
[T20]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792239661809489 "MN AI: Atlas em outubro (17/10 09h21)"
[T21]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792240196919929 "Desbravadores: devolução de Pix e provisões (17/10 09h29)"
[T22]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792240392972619 "MN AI: avisos e rascunho de contestação (17/10 09h33)"
[T23]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792240517567649 "MN AI: quem aprova regra (17/10 09h35)"
[T24]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792243684049629 "Organização: novos horários e checkpoints (17/10 10h28)"
[T25]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792243935921379 "Turma do Barulho: como o financeiro trabalha (17/10 10h32)"
[T26]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792245024407259 "Fox AI: Casa do Estudante (17/10 10h50)"
[T27]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792245351838949 "Turma do Barulho: repasse e conta garantida (17/10 10h55)"
[T28]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792245368683109 "Casa Barton: pendências, contas, 13x (17/10 10h56)"
[T29]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792245682730949 "Participante: contas do dia a dia e repasse da Atlas (17/10 11h01)"
[T30]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792245893941999 "Organização: outubro, saída e pendências (17/10 11h04)"
[T31]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792246021501709 "Desbravadores: ajuste de contestação da Ponte (17/10 11h07)"
[T32]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792246576200269 "Participante: contrato × aviso, alerta, spread negativo (17/10 11h16)"
[T33]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792246994695489 "Southlands: 5 regras gerais (17/10 11h23)"
[T34]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792247204388409 "Prime: Atlas (17/10 11h26)"
[T35]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792247223569669 "Prime: data-base da isenção da Casa (17/10 11h27)"
[T36]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792248442468319 "Datarmos: Casa, provisão, alerta (17/10 11h47)"
[T37]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792250828101959 "Turma do Barulho: mudanças de mês a mês (17/10 12h27)"
[T38]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792251374757469 "Fox AI: alerta da Atlas pelo pico (17/10 12h36)"
[T39]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792251861625499 "Participante: devolução pelo valor descontado (17/10 12h44)"
[T40]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792253999043339 "Participante: ajustes tardios da Orbe (17/10 13h20)"
[T41]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792253993517819 "Participante: isenção da Casa na antecipação (17/10 13h20)"
[T42]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792253934475539 "Dogshow: Pix de R$ 18.240 (17/10 13h19)"
[T43]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792253401618969 "Organização: chegou o arquivo 06 (17/10 13h10)"
[T44]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792249449403979 "Desbravadores: valor do ajuste da Ponte (17/10 12h04, sem resposta)"
[T45]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792250704054669 "Organização: chave de API (17/10 12h25)"
[T46]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792254957589749 "Turma do Barulho: bandeira divergente nos estornos do 06 (17/10 13h35, sem resposta)"
[T47]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792254985999379 "Desbravadores: id repetido e estorno órfão no ajuste da Orbe (17/10 13h36, sem resposta)"
[T48]: https://bartehackathonai.slack.com/archives/C0CA0S5D37B/p1792255687788519 "Turma do Barulho: estrutura do rastro (17/10 13h48, sem resposta)"
