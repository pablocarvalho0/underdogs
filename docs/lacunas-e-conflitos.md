# Lacunas, hipóteses e conflitos (17/10, 14h40)

O que **ainda não sabemos**, o que é **hipótese nossa**, o que **parece errado** nos dados e o que
**conflita** entre fontes e documentos. Complementa o `HIPOTESES.md`: lá fica a regra, aqui fica a
dúvida. Todo número foi medido por script no data pack (01 + 06), não estimado.

**Como usar.** Cada item tem impacto, quem resolve e o próximo passo. Quando um item for resolvido,
ele sai daqui e vira R-xx, P-xx ou correção no documento certo.

| Prefixo | Significa |
| :--- | :--- |
| **N-** | Não sabemos: falta informação de fora (Helena, comercial, Ponte, Orbe, organização) |
| **H-** | Hipótese nossa ainda não confirmada |
| **E-** | Parece errado ou estranho nos dados |
| **C-** | Conflito entre fontes, documentos ou código |
| **X-** | Pendência do processo (decisão do time ou tarefa fora do código) |

Impacto: **SET** muda número de setembro · **OUT** muda o fechamento de outubro · **NOTA** muda a
correção automática · **PITCH** é argumento para o pitch · **—** sem efeito em número.

---

## 0. O que chegou no Slack depois das 13h50

Já registrado no `HIPOTESES.md` nesta mesma branch:

| Hora | Resposta | Efeito |
| :--- | :--- | :--- |
| 14h08 | Bandeira não muda taxa; a Orbe às vezes troca a bandeira no estorno; não contestar, não abrir pendência | **R-50**. Fecha a Q-05 e confirma a D-04 |
| 14h10 | Estorno ou reversão no ajuste que aponta para transação ausente: entra pelo valor que veio e vira pendência para a Helena pedir a original | **R-51**. Fecha a Q-06 e confirma a D-02 |
| 14h11 | Rastro auditável: rastro também de divergências e da nota da Ponte, **registro de cada execução** (arquivos, linhas, data e hora) e **regra aplicada em cada linha** | **L-10**. Fecha a Q-07. **Requisito novo para o Extra:** ver X-03 |

Continua sem resposta: **Q-04** (ajuste da Ponte é o spread inteiro ou a nossa parte?), de 12h04.

---

## 1. O que não sabemos (informação faltante)

| ID | O que falta | O que já sabemos | Impacto | Quem resolve | Próximo passo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| N-01 | **Taxa e contrato da Atlas Idiomas** | Sem contrato na aba vigente (R-06). A aba 2025 tem CNPJ 39.566.044/0001-19 e taxas (débito 1,69; à vista 2,99; parcelado 3,49, numa faixa só; Pix 0,99), mas não vale. A Orbe aplicou outras (débito 1,99; à vista 3,49; parcelado 3,99/4,49; Pix 0,99) | OUT: setembro entra junto com o mês da confirmação (R-07). Hoje: R$ 7.876,05 sem faturar | Comercial | Só pendência. Guardar as 57 linhas para recalcular (E6 do plano) |
| N-02 | **Quem pagou o Pix de R$ 7.350 (Aurora L50)** | O histórico traz um CNPJ: **38.686.002/0001-80**. Não está na planilha nem no relatório da Ponte | SET: conta 1.1.09.002 + pendência (R-32) | Helena | Pôr o CNPJ no motivo da pendência. É a pista que falta para identificar |
| N-03 | **Motivo da devolução de Pix de R$ 12.400 da Mundo Aberto (L65, 23/09)** | Não bate com nenhum repasse à Mundo Aberto (R$ 48.714,59 em 09/09 e R$ 88.746,05 em 24/09). Chegou **antes** do repasse de 24/09, então não é o repasse inteiro voltando | SET: conta 2.1.01.001 (P-04) + pendência | Helena | Pôr os dois repasses no motivo da pendência |
| N-04 | **Quanto a Ponte vai pagar em 06/10** | O e-mail diz "50% do spread realizado". O total do relatório (R$ 78.073,59, 233 linhas) **inclui a duplicata e os negativos**: 50% dele são R$ 39.036,80. A nossa nota é de R$ 39.543,45 | SET: pendência de acompanhamento (R-39). Ver **C-03** | Helena | A pendência deve trazer os dois valores e a diferença explicada |
| N-05 | **Valor do ajuste da Ponte em outubro** (Q-04) | É linha nova, "AJUSTE REF PC-…" (R-18). Não sabemos se o `Spread R$` é o spread inteiro (abate 50%) ou já a nossa parte (abate 100%) | OUT | Helena | Acompanhar o thread [T44]. Até lá, flag em `premissas.py` com default "spread inteiro" e pendência quando aparecer |
| N-06 | **Por que a Orbe passou a cobrar +0,50 p.p. no crédito da Rota a partir de 12/09** | À vista 2,49→2,99, 2–6x 2,99→3,49, 7–12x 3,59→4,09. Débito (1,49) e Pix (0,89) não mudaram. O contrato não mudou (R-22) | — nos números (é divergência de qualquer jeito). PITCH | Helena/Orbe | Citar o padrão "+0,50 p.p. no crédito desde 12/09" na contestação |
| N-07 | **A Mundo Aberto pagou spread a mais também em julho e agosto?** | O contrato é de 1,20% desde julho (R-22). Em setembro, as 23 operações saíram com ~1,50%. Só temos setembro | OUT e PITCH: dinheiro possivelmente maior que R$ 1.418,85 | Helena | Candidata a pergunta (§6) |
| N-08 | **A Orbe e a Ponte vão continuar cobrando errado em outubro?** | Ninguém as avisa (R-49). A isenção da Casa vai até dezembro | OUT e PITCH: sem aviso, a devolução da Casa se repete (~R$ 15 mil/mês) e a divergência da Rota e da Mundo Aberto também | Comercial/Helena | O rascunho de contestação deve pedir a correção do cadastro, além do ressarcimento |
| N-09 | **Saldo inicial do Meridiano** | O OFX só traz `LEDGERBAL` (R$ 1.320.453,26). O saldo inicial implícito é R$ 204.118,03. Não há como conferir contra o fechamento de agosto | SET: o invariante de saldo do Meridiano só fecha pelo saldo implícito | — | Declarar no invariante que o saldo inicial é derivado |
| N-10 | **Competência dos DARFs de IRRF, PIS e COFINS** | Folha, ISS, INSS e FGTS trazem "08/2026" no histórico. Os três DARFs (L57, L86, L87: R$ 22.104,35, R$ 9.811,20 e R$ 45.282,46) **não trazem mês**. A R-30 fala em "DARFs de agosto" | SET: baixa de passivo (2.1.03.00x) × despesa | Helena (critério já dado) | Ver **H-03** |
| N-11 | **Custo da conta garantida** | O Aurora fica negativo de 09/09 a 30/09 (mínimo de −R$ 2.289.532,94 em 24/09), e **não há juros nem IOF** no extrato de setembro | — em setembro. OUT: provavelmente cai no início de outubro. PITCH: adiantar repasse custa dinheiro e não aparece no mês | Helena | Registrar como limitação conhecida, não como pendência |
| N-12 | **IOF s/ operação de crédito no Meridiano** (26/09, R$ 48,21) | O Meridiano não fica negativo em nenhum dia, e não há operação de crédito visível | SET: conta 4.3.01 (sem dúvida de conta) | — | Só registro |
| N-13 | **Que remessa o Pix de R$ 18.240 vai pagar** | É de uma remessa que sai em outubro (R-34) | OUT: casar com a operação quando ela aparecer | — | Acompanhamento em outubro, sem pendência em setembro (P-12) |
| N-14 | **Crédito dos R$ 300 mil (L92) no Meridiano em 01/10** | As outras 3 transferências (350, 420 e 380 mil) chegaram no mesmo dia | OUT | — | Pendência de acompanhamento (P-11) |
| N-15 | **O que a suíte caixa-preta espera** | Ninguém pode ler (diretiva 0). O `COMECE-AQUI` registra `1 failed`. Foi escrita **antes** das respostas do financeiro | NOTA: pode codificar regra antiga | Humano do time | Triagem humana quando falhar (plano §4.2). Vale a regra da Helena |

---

## 2. Hipóteses nossas ainda não confirmadas

Premissas do `HIPOTESES.md` que seguem como **proposta**, mais hipóteses implícitas no código ou
no plano que ainda não estavam escritas em lugar nenhum.

| ID | Hipótese | Se estiver errada | Status |
| :--- | :--- | :--- | :--- |
| H-01 | P-01: tolerância de 0,01 p.p. no spread | Abaixo disso aparecem alarmes de centavo (o ruído é ±0,002). Acima, uma divergência real pequena passaria. Nenhum caso de setembro fica perto do limite | Proposta |
| H-02 | P-02 × D-03: a Atlas aparece com 0,00 em `comissoes_por_lojista`, ou não aparece | Alarme falso, ou lojista "sumido" na correção | **Em conflito** (C-02) |
| H-03 | Os DARFs sem mês no histórico (IRRF, PIS, COFINS) são **de agosto** e baixam passivo | Se forem de setembro, viram despesa: R$ 77.198,01 trocariam de conta | Implícita. Coerente com o vencimento (o dia 20/25 do mês seguinte) e com a R-30 |
| H-04 | P-05: divergência da Mundo Aberto = `Spread %` × `Valor ME` × `PTAX` (R$ 1.418,85), e não a proporção do `Spread R$` (R$ 1.418,88) | R$ 0,03 de diferença no total | Proposta |
| H-05 | P-06 e P-07: a Casa e os spreads negativos ficam **fora** de `divergencias_taxa.csv` | Se o gabarito os listar, perdemos linhas; se não listar e nós listarmos, é alarme falso | Proposta. Pergunta O-2 do plano |
| H-06 | P-08: o alerta de antecipação acende só para lojista novo, pelo pico (Atlas, R$ 124.235,32 de excedente em 15/09) | O critério é nosso (a Helena delegou). O risco é acender pouco | Proposta (aceita como "razoável" às 12h50) |
| H-07 | P-10: o `arquivo_origem` da Ponte é o `.eml` | A correção automática do rastro pode esperar o nome do xlsx | Proposta. Pergunta O-1 (Q-02) |
| H-08 | P-14: id repetido entre arquivos da Orbe → vale o ajuste, com pendência | Não ocorre em setembro | Proposta (a Helena delegou) |
| H-09 | O alerta e as pendências **não** contam como alarme falso | Pela L-04, só conta como alarme falso a divergência onde não existe. Pendência de acompanhamento não é alarme falso | Fundamentada na L-04 |
| H-10 | O valor da pendência de acompanhamento da Ponte é a **nossa nota** (R$ 39.543,45) | Talvez devesse ser o valor que a Ponte vai pagar (R$ 39.036,80). Ver C-03 | Implícita no plano |
| H-11 | `id_saida` livre: a correção casa as linhas por `cnpj`/`ref_origem` | Se casar por `id_saida`, o nosso padrão pode não bater | Pergunta O-3 do plano |
| H-12 | P-15: o data pack da banca segue o mesmo modelo, com outros nomes e valores | Se mudar o layout, a entrada tem que avisar, não quebrar (R-42) | Inferida do briefing |

---

## 3. O que parece errado ou estranho nos dados

| ID | Achado | Números | Tratamento hoje | Por que importa |
| :--- | :--- | :--- | :--- | :--- |
| E-01 | **Atlas: a Tarvo repassou bem mais do que a Atlas vendeu** | Primeira venda em 10/09. Vendas brutas no mês: **R$ 135.428,90** (líquido R$ 130.206,49). Antecipações: R$ 235.943,10, das quais R$ 108.712,14 foram revertidas (2 reversões). **Repasses do Aurora à Atlas: R$ 112.220,15 (10/09, L34) + R$ 137.081,62 (22/09, L60) = R$ 249.301,77**, ou **R$ 119.095,28 acima** do líquido das vendas do mês. O 2º repasse saiu **depois** da 1ª reversão (17/09) | Alerta P-08, que hoje só olha antecipação × vendas | É o maior risco de dinheiro do mês, e o processo não tem trava (R-36: "a Bia antecipa sem regra"). **Pôr os repasses no motivo do alerta.** Candidata a pergunta (§6) |
| E-02 | Atlas: as taxas da Orbe não batem com nenhuma tabela | 2025 + 0,50 p.p. no crédito, débito 1,99 (a aba 2025 tem 1,69) | Pendência de lojista sem contrato | Reforça a N-01: ninguém sabe que preço a Atlas está pagando |
| E-03 | **A Ponte soma a duplicata e os negativos nos próprios totais** | O rodapé e a aba "Resumo" dizem 233 operações e R$ 78.073,59. Isso inclui `PC-0926-0162` duas vezes (+R$ 821,88) e os 4 negativos (−R$ 1.834,05) | Duplicata conta uma vez (R-13); negativos fora (R-14) | Se a Ponte pagar pelo próprio total, paga R$ 506,65 a menos que a nossa nota (C-03) |
| E-04 | A Orbe não aplicou a isenção da Casa | 118 linhas cobradas em setembro, incluindo 4 antecipações (R$ 2.827,56 só de antecipação) | Devolução de R$ 15.396,77 (R-09) | Repete em outubro se ninguém avisar a Orbe (N-08) |
| E-05 | A Orbe aplicou a taxa antiga da Bridge por 4 dias | 5 vendas de 15 a 18/09 a 2,59% (o aditivo é de 2,19% desde 15/09) | Divergência de R$ 29,95 | A Bridge foi avisada "alguns dias depois" (R-49): mostra o atraso do aviso |
| E-06 | A Ponte cobra 1,50% da Mundo Aberto, quando o contrato é 1,20% | 23 operações, R$ 1.418,85 | Divergência de remessa + contestação | Provavelmente desde julho (N-07) |
| E-07 | Spreads negativos com "taxa travada D-1" | 4 operações, −R$ 1.834,05. O spread estimado em D-1 era positivo | Fora da comissão, pendência (R-14) | A trava vale 2h e já tinha vencido: a Ponte honrou uma cotação vencida |
| E-08 | Bandeira trocada nos estornos | 39 de 50 no 01 e 7 de 10 no 06 | Nada (R-50) | Resolvido: é comportamento conhecido da Orbe |
| E-09 | O Pix sem identificação traz CNPJ | L50: `PIX RECEBIDO 38686002000180 SEM IDENTIFICACAO` | Pendência (R-32) | "Sem identificação" é do banco; o CNPJ está no histórico (N-02) |
| E-10 | IOF de crédito numa conta que nunca ficou negativa | Meridiano, 26/09, R$ 48,21 | Conta 4.3.01 | Valor pequeno; só registro (N-12) |
| E-11 | O prazo de contestação do e-mail da Ponte já teria passado | O e-mail é de 02/10 e pede resposta "em até 5 dias úteis", ou seja, até 09/10. O fechamento é em 17/10 | Contestação como pendência | A Helena mandou considerar dentro do prazo (R-38). Ver C-04 |

---

## 4. Conflitos entre fontes, documentos e código

| ID | Conflito | Lado A | Lado B | Quem decide | Proposta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C-01 | Número de controle do checkout nas tasks | `docs/tasks/dev1-checkout.md`: **R$ 207.039,73** | `HIPOTESES.md` §5 e plano §7, com o 06: **R$ 203.735,34** | Pablo | Corrigir a task antes de virar prompt. O `test_controle_setembro.py` deve usar 01 + 06 |
| C-02 | Atlas em `comissoes_por_lojista` | P-02 e task dev1 (flag `sem_contrato_lista_zero`): aparece com 0,00 | D-03 (recomendação): não aparece, só na pendência | Time (alinhamento) | Decidir a D-03 e alinhar o default da flag. Pergunta O-2 do plano ajuda |
| C-03 | **Valor esperado do repasse da Ponte** | E-mail: "50% do spread realizado", e o relatório da Ponte soma tudo: R$ 39.036,80 | Nossa nota: R$ 39.543,45 (sem os negativos, R-14, e com a duplicata uma vez, R-13) | Helena | A pendência de acompanhamento leva os dois valores e a diferença de **R$ 506,65**. Ela se explica assim: metade dos negativos (+R$ 917,025), menos metade da duplicata (−R$ 410,94), mais o arredondamento por operação (+R$ 0,57). O total da Ponte foi arredondado no meio centavo |
| C-04 | Prazo de contestação | E-mail da Ponte: 5 dias úteis a partir de 02/10 | Helena: "considerar que estamos dentro do prazo" (R-38) | Helena (já decidiu) | Segue a Helena. Registrar no motivo que o prazo do e-mail é 09/10 |
| C-05 | Testes não-caixa-preta × plano | `tests/test_loaders.py` exige `valor_bruto` em **float64**. `tests/test_real_dataset_integrity.py` exige **1.943** linhas da Orbe | Plano: Orbe em `Decimal` e 01 + 06 concatenados (1.957) | Pablo | Esses testes não são imutáveis. Atualizar no PR do serial (ou concatenar na entrada, não no loader) |
| C-06 | "Rota cobrada pela tabela de 2025" | `docs/plano-engenharia.md` v0 | Dados: só o à vista e o 2–6x coincidem com 2025. O 7–12x (4,09) não existe na aba 2025, e o débito (1,49) e o Pix (0,89) seguem os atuais. O padrão é **+0,50 p.p. no crédito** desde 12/09 | — | A v0 já está superada (COMECE-AQUI §2). Não repetir no pitch |
| C-07 | "233 operações" | `docs/plano-engenharia.md` v0 | 232 operações + 1 repetição (R-13) | — | Superado. Cuidado no pitch |
| C-08 | Quem faz a remessa | `docs/tasks/dev2-remessa-extratos.md`: Dev 2 faz B e C | `docs/plano-construcao.md` v2: Construção faz tudo; Verificação confere | Pablo | Decidir no alinhamento (COMECE-AQUI §3.1) |
| C-09 | Exemplos de `quem_decide` | `CLAUDE.md` §2.3: "Lojista, Ponte Câmbio, Financeiro Tarvo" | `HIPOTESES.md`: Helena, Comercial, Ponte | — | Texto livre (L-04). Padronizar nos nomes do `HIPOTESES.md` |
| C-10 | R-19 está entre as regras, mas é premissa | `HIPOTESES.md` R-19 | A Helena: "Registrem como premissa" | — | Já anotado na própria R-19. Não ocorre em setembro |
| C-11 | Exemplo numérico da R-14 | −R$ 1.351,87 (`PC-0926-0210`, diferença até o contrato) | Cálculo de outro time; a Helena não valida número (R-48) | Verificação | Recalcular com o nosso controle antes de pôr na pendência |
| C-12 | Áudio do briefing no repositório público | `docs/audios/briefing.ogg` na `main` | Dado pessoal (voz) num repositório público | Pablo | Decidir se sai (COMECE-AQUI §3.4). As instruções permitem tirar dado pessoal dos PROMPTS |

---

## 5. Pendências do processo (não são código)

| ID | Pendência | Prazo | Dono |
| :--- | :--- | :--- | :--- |
| X-01 | Decidir D-01, D-03, D-05 e D-06 (D-02 e D-04 já confirmadas pela Helena) | Alinhamento | Time |
| X-02 | Revisar e decidir quais perguntas enviar (plano §11 + candidatas da §6 abaixo). **Pergunta nova só até 17h15** | 17h15 | puerari-dev |
| X-03 | **Requisito novo (L-10):** registro de cada execução (arquivos, linhas, data e hora) e a regra aplicada em cada linha (colunas extras, por exemplo `regra`, `taxa_contratada_usada`, `data_base`). Entra no Extra | Antes do G3 | Construção |
| X-04 | Corrigir o controle nas tasks e no `test_controle_setembro.py` para 01 + 06 (C-01) | Antes das trilhas | Pablo |
| X-05 | Atualizar os testes de loader que travam float e 1.943 linhas (C-05) | No serial | Pablo |
| X-06 | Motivos das pendências com as pistas que temos: CNPJ do L50, repasses da Mundo Aberto no L65, repasses da Atlas no alerta, os dois valores da Ponte | Antes do G3 | Verificação (texto) + Construção |
| X-07 | Checkpoint 2 (16h00): o que roda, o que mudou, o que corta, maior risco, onde a banca ajuda | 16h00 | Narrativa |
| X-08 | Export dos PROMPTS de todos e escolha de 2 a 4 MOMENTOS (pelo menos 1 erro da IA) | 18h15 | Narrativa |
| X-09 | Destino do áudio no repositório público (C-12) | Antes de 18h30 | Pablo |

---

## 6. Perguntas candidatas que saem desta investigação

Para revisão, junto com o §11 do plano. **Nenhuma foi enviada.**

| ID | Para | Pergunta | Por que vale a pena |
| :--- | :--- | :--- | :--- |
| T-3 | `[Financeiro]` | "Underdogs: a Atlas começou a vender em 10/09 e vendeu R$ 135,4 mil brutos no mês, mas recebeu R$ 249,3 mil em repasses (Pix de 10/09 e de 22/09). O segundo saiu depois da reversão de antecipação de 17/09. Isso foi uma antecipação da Bia pela conta garantida? Vocês querem que o alerta de antecipação traga também o total repassado contra o vendido?" | Muda o conteúdo do alerta e dá ao pitch o "dinheiro em risco" mais concreto do mês. Pergunta sobre fato, com números, sem pedir validação de número |
| T-4 | `[Financeiro]` | "Underdogs: o contrato da Mundo Aberto é de 1,20% de spread desde julho, e em setembro a Ponte cobrou ~1,50% nas 23 operações. Se aconteceu o mesmo em julho e agosto, a contestação com a Ponte deve pedir esses meses também, ou só setembro?" | Pode aumentar o valor a contestar e entra no rascunho de e-mail. A resposta pode ser "só setembro", mas a pergunta mostra a causa raiz |
| T-5 | `[Financeiro]` | "Underdogs: o e-mail da Ponte diz que o repasse é 50% do spread realizado, e o total do relatório (R$ 78.073,59) inclui a duplicata e os spreads negativos, dando R$ 39.036,80. A nossa nota sai em R$ 39.543,45. A nota vai pelo nosso valor e a diferença de R$ 506,65 entra na contestação, certo?" | Fecha a C-03 e define o texto da pendência de acompanhamento. Risco baixo: a R-14 e a R-27 já indicam a resposta |
