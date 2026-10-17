# Plano de construção — do estado atual até a entrega (v2, 17/10 14h30)

Substitui o `docs/plano-engenharia.md` (v0, 13h20) no que é organização, cronograma e critério de
pronto. A arquitetura e o contrato da v0 continuam valendo (§5). As regras estão no `HIPOTESES.md`
da `main`, e os IDs citados aqui (R-xx, P-xx, D-xx, Q-xx, L-xx) são os de lá. Os documentos
`docs/tasks/*.md` (PR #13) são reaproveitados como especificação das trilhas (§4.1).

**Meta: entregar o nível Extra sem arriscar o Mínimo.** O desafio diz: "É melhor entregar o nível
mínimo certo do que o nível extra com números que não fecham". Por isso há **portões** (§6): só se
avança de nível quando os números do nível atual batem com o controle independente.

---

## 1. Onde estamos (14h30)

| Peça | Estado | Observação |
| :--- | :--- | :--- |
| Contrato (`core/model.py`, `writer.py`, `pipeline.py`) | ✅ `main` | O writer recusa linha cujo valor ≠ Σ componentes. O rastro sai por construção |
| Cadastro (`core/cadastro.py`) | ✅ `main` | Taxa em pontos percentuais, vigência e alias de EC. Não filtra lojista INATIVO |
| Loaders | ⚠️ `main` | **Nome de arquivo fixo de setembro** (o 06 é ignorado). A Orbe vira `float` e um valor ilegível vira 0 sem aviso |
| CLI `npm run run` | ⚠️ | Não recebe a pasta do mês |
| Trilhas A, B e C | ❌ stubs | Especificação pronta em `docs/tasks/` (PR #13) |
| `premissas.py` | ⚠️ | Defaults da v0. O "serial" do Pablo atualiza |
| Painel + GitHub Pages | ✅ `main` | |
| `HIPOTESES.md` | ✅ `main` (PR #10) | D-01..D-06 com recomendação, à espera do ok do time |
| README, PROMPTS, MOMENTOS, pitch | 🔄 / ❌ | Ninguém está cuidando disso agora |

Prazos: **checkpoint 2 às 16h00**, **financeiro até 17h45**, **repositório às 18h30**,
**pitch às 19h00**.

---

## 2. Como nos organizar: por função, não por módulo de código

### 2.1 Por que não "Dev 1 = checkout, Dev 2 = remessa + extratos"

| Problema da divisão por trilha | Consequência às 17h |
| :--- | :--- |
| **75% da nota não é código.** Causa raiz 15%, hipóteses 10%, perguntas 10%, comunicação 10%, uso de IA 20% e tempo 10%. Os números são 25% | Três pessoas codando até as 17h deixam pitch, README, PROMPTS e MOMENTOS para a última hora |
| O código restante é pequeno: três trilhas de algumas centenas de linhas, com a especificação já escrita | Com IA, uma pessoa orquestrando sessões paralelas faz tudo. Três pessoas com três sessões sem contexto comum geram três leituras diferentes da mesma regra (arredondamento, unidade, componente) |
| O Pablo já é gargalo: faz o serial, revisa 3 PRs, integra e é o único que aprova a `main` | A integração cai na janela 17h00–17h45, junto com o fim do atendimento do financeiro |
| Ninguém fica responsável por **conferir** | Os números (25%) dependem de comparar a saída com algo independente. Alarme falso conta contra, e quem escreveu o código não é quem melhor acha o erro dele |
| Entrar no contrato agora custa caro (ler `model.py`, `cadastro.py`, HIPOTESES…) | A pessoa perde de 30 a 45 minutos antes de produzir |

A divisão por trilha faria sentido com três pessoas já dentro do código e uma especificação
instável. Não é o nosso caso. A especificação está estável (HIPOTESES + tasks) e o código cabe
numa pessoa com IA.

### 2.2 Três papéis

| Papel | Dono do quê | Sugestão de quem |
| :--- | :--- | :--- |
| **Construção** | Tudo em `src/`: o serial, as 3 trilhas (como sessões paralelas de IA, cada uma com a sua task), a integração, os extras de código e os merges na `main` | **Pablo**: é o mantenedor, escreveu o contrato e o serial, e o PR #13 já prevê worktrees para sessões paralelas |
| **Verificação e regras** | Controle independente (não importa nada de `src/`), conferência de cada PR, triagem humana da suíte caixa-preta, `HIPOTESES.md`, canal do Slack, ensaio de outubro | **puerari-dev**: fez a prévia independente e o HIPOTESES, e conhece as regras linha a linha |
| **Narrativa e entrega** | Causa raiz, pitch, README para quem não é técnico, checkpoint 2, export dos PROMPTS de todos, curadoria dos MOMENTOS, envio às 18h30 e às 19h00 | **Terceira pessoa** do time |

Com só duas pessoas ativas, Verificação e Narrativa ficam com a mesma pessoa, e a ordem de corte
da §9 passa a valer mais cedo.

**Plano B:** se o G1 não passar às 16h00, a Verificação para o que estiver fazendo e assume a
trilha C (a mais independente), seguindo `docs/tasks/dev2-remessa-extratos.md`. A Narrativa não
para em nenhum caso.

### 2.3 Por que isso também é melhor para a nota de "Uso de IA" (20%)

Cada pessoa deixa nos PROMPTS um tipo diferente de direção da IA:
- a Construção especifica tarefas e revisa diffs de sessões paralelas;
- a Verificação pega a IA errando, porque compara com o controle e confere caso a caso;
- a Narrativa pede rascunhos e corrige para a linguagem do financeiro.

É exatamente o que a banca diz procurar: "dirige a IA, verifica o que ela entrega e corrige
quando ela erra".

---

## 3. O que "Extra" significa para nós

| Requisito do desafio | Como entregamos | Papel |
| :--- | :--- | :--- |
| Rastro completo de todos os números | Toda linha com valor, **inclusive pendências e notas**, sai com componentes. O writer recusa se não fechar | Construção |
| Pendências explicadas | Uma por contraparte e por lojista (P-13), com valor rastreado, motivo em linguagem do financeiro e `quem_decide`. Mais um rascunho de e-mail de contestação por contraparte (R-37) | Construção (código) + Verificação (texto dos motivos) |
| Roda em outubro sem retrabalho | Descoberta de arquivos pelo cabeçalho (D-01); conferência de layout que **avisa, sem quebrar** (R-42); condição comercial como dado com vigência e aprovador (P-03); ensaio com uma pasta de outubro simulada | Construção + Verificação (ensaio) |

---

## 4. O que cada papel faz

### 4.1 Construção

**Serial (14h30–15h15).** É o que bloqueia as trilhas. O mínimo que precisa estar na `main`:
- **Entrada por descoberta (D-01).** O papel de cada arquivo sai do cabeçalho. Todos os
  arquivos da Orbe da pasta são concatenados (01 + 06), com `arquivo_origem` por linha. `id`
  repetido segue a P-14. Papel ausente ou arquivo desconhecido vira pendência
  `FONTE_AUSENTE`/`ARQUIVO_DESCONHECIDO`, e o resto fecha (R-42).
- Loader da Orbe em **`Decimal` a partir do texto cru**. Valor ilegível vira pendência, não 0.
- Cadastro sem lojista INATIVO (Globo Trotter). Transação de inativo vira pendência.
- `premissas.py` como descrito nas tasks:
  - aliases (R-05), isenções com vigência (R-08, R-44) e Atlas (R-06, D-03);
  - spread padrão de 1,5 (R-12), duplicata contada uma vez (R-13), negativo fora (R-14);
  - tolerância de 0,01 p.p. (P-01) e taxa em pontos percentuais (P-09).
- `core/pendencias.py` (helper da task).
- `npm run run -- --input <pasta> --output <pasta>`, e o `status` usando a descoberta.
- `tests/test_controle_setembro.py` com os números de **01 + 06** (§7). As tasks ainda citam
  R$ 207.039,73, que é o valor sem o 06. **Corrigir para R$ 203.735,34.**

**Trilhas (15h15–16h45).** São três sessões paralelas de IA, em worktrees, com as tasks como
prompt: `dev1-checkout.md` e `dev2-remessa-extratos.md` (dividida em B e C). Ajustes nas tasks:
- o controle passa a ser o de 01 + 06;
- a Atlas fica conforme a D-03 decidida no alinhamento;
- valem as pendências esperadas e as **não-pendências** da §8.

Ordem dos merges: A (G1), depois B, depois C.

**Integração (16h45–17h15):** `run`, `validate`, `npm test` e `test_controle`. A triagem da
caixa-preta é com a Verificação (§4.2).

**Extras de código (17h15–17h45), por ordem de valor:**
- E2: rascunhos de e-mail de contestação a partir de `pendencias.csv`, em `saida/rascunhos/`;
- E5: IA no resíduo dos extratos, com cache, como já está na task C;
- E6: colunas extras nas pendências, para outubro recalcular a Atlas (R-07).

**17h45: congelamento do código.**

### 4.2 Verificação e regras

**Kit de conferência (14h30–15h30).** Fica pronto antes do primeiro PR de trilha:
- `scripts/controle/controle_independente.py`. É a prévia que já existe, versionada. Não
  importa nada de `src/`. Gera `controle/esperado/*.csv` com as chaves e os valores
  esperados de cada saída (comissões, divergências, notas e lançamentos) e a lista de
  pendências esperadas.
- `scripts/controle/comparar.py saida/ controle/esperado/`. Lista três coisas:
  - **faltando**: o esperado não saiu;
  - **sobrando**: saiu algo não esperado, possível **alarme falso**;
  - **valor diferente**, com a diferença.
- Casos calculados à mão, para pegar o erro que as duas implementações cometeriam juntas:
  - 3 da Rota: à vista, 2–6x e estorno;
  - o estorno de agosto da Casa (`TX88445133`);
  - uma reversão do 06;
  - uma operação da Mundo Aberto;
  - uma operação negativa.

**Conferência de cada PR (15h30–17h15).** Para cada trilha: rodar o branch, rodar `comparar.py`
e comentar no PR "conferido" com o relatório, ou a lista do que não bate. **O Pablo só faz o
merge com esse comentário.** Diferença sem explicação não se ajusta no código: se investiga
(regra das tasks).

**Triagem humana da caixa-preta.** Os testes foram escritos antes das respostas do financeiro e
podem codificar regra antiga. Quando falharem:
1. um humano lê a asserção (a IA não lê; diretiva 0 do `CLAUDE.md`);
2. compara com o `HIPOTESES.md`;
3. decide se o problema está no teste ou no código;
4. registra a decisão no PR.

A regra da Helena vale mais que o teste.

**Regras e canal (contínuo até 17h45):**
- acompanhar as Q-04..Q-07 e as perguntas da §11 que o time decidir mandar;
- resposta nova vira R-xx no `HIPOTESES.md` e é avisada à Construção, que muda a flag;
- registrar momento de MOMENTOS sempre que a IA errar e alguém pegar.

**Ensaio de outubro (17h00–17h30):**
- copiar a pasta renomeando os arquivos para `*_out2026`;
- tirar o 06;
- trocar a ordem de uma coluna do Aurora;
- rodar.

O esperado é que não quebre e avise. O print entra no pitch.

**Conferência final (17h45–18h15):** `comparar.py` sobre o `saida/` final, e **clone limpo**
numa pasta nova seguindo só o README.

### 4.3 Narrativa e entrega

**14h30–16h00**
- **Causa raiz** (§10) em linguagem do financeiro, com o valor de cada causa. Vai para o README e para o pitch.
- **Esqueleto do pitch**, já com os números de controle (§7). Eles não dependem do código, e se mudarem é só trocar.
- **Seções do README para não técnicos:** o que a solução faz, como a analista roda em outubro, onde mexer quando mudar uma condição e o que ela **não** faz.
- **Às 16h00, checkpoint 2:** mensagem privada ao organizador, começando com "Underdogs". Conteúdo pedido: o que roda de ponta a ponta, o que mudou no plano, o que vai ser cortado, o maior risco e em que a banca pode ajudar.

**16h00–17h45:** slides do pitch, cobrindo os 7 pontos pedidos:

| Ponto pedido | Conteúdo |
| :--- | :--- |
| O que está quebrado e por quê | §10 |
| O que a solução faz | Fluxo de 1 slide: pasta do mês → 6 arquivos → pendências com dono |
| Dinheiro em jogo | Divergências R$ 1.576,23 + R$ 1.418,85; devolução da Casa R$ 15.396,77; Atlas R$ 7.876,05 sem faturar; negativos −R$ 1.834,05; o 06 mudando R$ 3.304,39 |
| Como a analista usa em outubro | Roteiro de 5 passos + print do ensaio |
| Onde a IA atua e onde não atua | Regras decidem; a IA só sugere no resíduo; o humano aprova; números nunca saem de IA |
| Onde falha e o que acontece | Layout novo, arquivo faltando, lojista sem contrato: avisa, fecha o resto, gera pendência |
| Mais um mês | Pendências que passam de mês, aba de condições especiais, conciliação Orbe × banco parcela a parcela |

**17h45–18h25**
- **PROMPTS:** cada pessoa exporta **todas** as sessões, de construção e de preparação, para `PROMPTS/<pessoa>/`. Pode ser o `/export` do Claude Code ou o `.jsonl` bruto de `~/.claude/projects/`. Tirar chave de API (`grep -r "sk-ant"`) e dado pessoal; fora isso, não editar.
- **MOMENTOS:** escolher de 2 a 4 entre os candidatos e os novos da tarde. Pelo menos um tem que ser erro da IA.
- **README final.**
- **18h25:** confirmar com a Construção que o merge final entrou e que o repositório está público. **Mandar o link por e-mail (L-06).**

**18h30–19h00:** fechar o PDF do pitch com os números do `saida/` final e mandar por e-mail até
19h00.

---

## 5. Arquitetura (mantida) e ajustes no contrato

```
pasta do mês ──► entrada (descobre papéis pelo cabeçalho, confere layout, avisa)
             ──► cadastro (planilha + aliases + condições comerciais com vigência)
             ──► trilha A checkout │ trilha B remessa │ trilha C extratos   (paralelas)
             ──► pendências (contraparte × lojista) + alertas
             ──► writer (6 CSVs, assert do rastro) ──► invariantes ──► painel
```

Ajustes que o serial faz no contrato:
1. `dados.orbe` com a coluna `arquivo_origem`;
2. valores em `Decimal` desde o texto;
3. `--input/--output` na CLI;
4. fonte ausente vira pendência, não exceção.

Esquema de `id_saida` (v0, mantido): `COM-CHK-<cnpj>`, `COM-REM-<cnpj>`,
`DIV-CHK-<id_transacao>`, `DIV-REM-<nº>`, `NF-CHK-<cnpj>`, `NF-REM-<cnpj ponte>`,
`LAN-AUR-L<n>`, `LAN-MER-<fitid>`, `PEN-<trilha>-<chave>`.

`taxa_*_pct` em pontos percentuais (`2.69`, P-09). O `Spread %` da Ponte vem em fração: ×100 na
saída.

---

## 6. Portões

| Portão | Hora | Critério (conferido pela Verificação com `comparar.py`) | Se falhar |
| :--- | :--- | :--- | :--- |
| **G1 Mínimo** | 16h00 | `comissoes_por_lojista` CHECKOUT bate **lojista a lojista**, o rastro fecha e o `validate` passa | Plano B (§2.2). O checkpoint 2 relata como está |
| **G2 Alvo** | 16h45 | Remessa, divergências, notas e 184 lançamentos batem; nada sobrando | Cortar os extras de baixo para cima (§9) |
| **G3 Extra** | 17h40 | Pendências da §8 completas e sem sobra, invariantes em zero, ensaio de outubro sem quebrar | Entregar o G2 e registrar no README o que ficou de fora |

---

## 7. Números de controle (01 + 06)

| Saída | Esperado |
| :--- | ---: |
| Comissão CHECKOUT, 21 lojistas (Casa −5,50; sem Atlas) | **R$ 203.735,34** |
| Notas CHECKOUT (20 lojistas com comissão > 0) | Σ R$ 203.740,84 |
| Divergências CHECKOUT, 92 linhas (Rota 299,62 + 539,26 + 707,40; Bridge 29,95) | R$ 1.576,23 |
| Comissão REMESSA, 228 operações | **R$ 39.543,45** |
| Nota REMESSA (Ponte Câmbio, 75374179000146) | R$ 39.543,45 |
| Divergência REMESSA, Mundo Aberto, 23 operações | R$ 1.418,85 |
| Lançamentos classificados | 184 (84 Aurora + 100 Meridiano) |

Por lojista, a §5 do `HIPOTESES.md` traz a tabela antes e depois do 06. Uma diferença de 1
centavo quase sempre é arredondamento: float, soma antes de arredondar, ou negativo arredondado
para o lado errado.

---

## 8. Pendências esperadas em setembro (e o que **não** é pendência)

| Tipo | Chave | Valor | Quem decide |
| :--- | :--- | ---: | :--- |
| Lojista sem contrato (não faturar) | Atlas, 57 linhas | 7.876,05 | Comercial |
| Devolução ao lojista | Casa, 118 linhas | 15.396,77 | Helena + Comercial |
| Nota não emitida (comissão negativa) | Casa, `TX88445133` | −5,50 | Helena |
| Divergência a contestar com a Orbe e ressarcir | Rota, 87 linhas | 1.546,28 | Helena |
| Divergência a contestar com a Orbe e ressarcir | Bridge, 5 linhas | 29,95 | Helena |
| Alerta de antecipação acima das vendas | Atlas, pico em 15/09 | 124.235,32 | Helena + Comercial |
| Spread negativo a contestar | Ponte, 4 operações | −1.834,05 (até o contrato: −3.565,98) | Helena → Ponte |
| Operação duplicada no relatório | Ponte, `PC-0926-0162` | spread da cópia | Ponte |
| Spread acima do contrato | Mundo Aberto, 23 operações | 1.418,85 | Helena → Ponte |
| Acompanhamento: repasse da Ponte em outubro | Nota REMESSA | 39.543,45 | Helena |
| Crédito sem identificação | Aurora L50 | 7.350,00 | Helena |
| Devolução de Pix, motivo desconhecido | Aurora L65 | 12.400,00 | Helena |
| Acompanhamento: crédito no Meridiano em 01/10 | Aurora L92 | 300.000,00 | Helena |

**Não geram pendência**, porque seriam alarme falso (L-04):
- bandeira divergente nos estornos (D-04);
- o Pix de R$ 18.240 (R-34);
- os aliases confirmados;
- os estornos de agosto (R-03);
- as ressalvas da Ponte (R-15).

---

## 9. Riscos e ordem de corte

| Risco | Mitigação |
| :--- | :--- |
| A Construção vira gargalo | As trilhas rodam em sessões paralelas a partir das tasks. Plano B às 16h00 (§2.2). A Verificação libera o merge com o "conferido", e o Pablo não precisa revisar número |
| O serial atrasa | As trilhas começam lendo `dados.orbe` como está hoje. Quando o serial cai, só ganham as 14 linhas do 06, e o G1 é conferido de novo |
| Centavos | `Decimal` desde o texto, `brl()` por linha, conferência lojista a lojista |
| A caixa-preta falha por regra antiga | Triagem humana (§4.2). Não se "conserta" código para passar em teste errado |
| Conflito de merge | Uma trilha = um arquivo. `premissas.py`, `entrada.py` e `pendencias.py` só pelo serial |
| Atendimento termina às 17h45 | Pergunta nova só até 17h15. Depois disso, assumir e escrever no HIPOTESES |
| Tempo | **Ordem de corte:** E5 → E6 → ensaio de outubro → E2 → painel. **Nunca cortar:** descoberta de arquivos (sem ela o 06 some), as 3 trilhas, o formato, o README rodando do zero, os PROMPTS, os MOMENTOS e o pitch |

---

## 10. Causa raiz (para o README e o pitch)

1. **Não existe chave comum entre as fontes.**
   - A Orbe identifica o lojista por EC, a Ponte por CNPJ e os bancos pelo nome truncado.
   - A ponte entre eles é uma planilha à mão: faltam 3 ECs, o CNPJ aparece em 3 formatos e uma condição especial está escondida num comentário de célula.
2. **A condição comercial não chega a quem cobra (R-49).** Resultado em setembro:
   - Rota: R$ 1.546,28;
   - Bridge: R$ 29,95;
   - Mundo Aberto: R$ 1.418,85;
   - Casa: R$ 15.396,77 a devolver.

   Hoje isso só aparece quando o lojista reclama.
3. **A regra só existe na cabeça da Helena.** Pelas palavras dela: "Quase tudo que vocês
   descobriram aqui estava só na minha cabeça". Agora é dado versionado, com fonte e aprovador.
4. **A conferência é por fonte, nunca cruzada.** A duplicata e os negativos da Ponte passam
   porque ninguém compara o relatório com as TEDs do Meridiano. Nós comparamos: 21 de 21.
5. **Arquivo novo ou atrasado quebra o processo.** O 06 chegou depois do relatório e muda
   R$ 3.304,39 em 7 notas. Um processo que lê um nome fixo erra em silêncio.

---

## 11. Perguntas que ainda valem a pena (em revisão pelo time)

O canal já respondeu quase tudo de setembro. Pergunta vaga recebe resposta vaga, e repetir o que
já foi respondido conta contra. A lista é curta, e cada pergunta diz o que destrava.

### 11.1 Para a organização do hackathon — `[Logística]`
| ID | Mensagem proposta | O que destrava |
| :--- | :--- | :--- |
| O-1 (Q-02) | "[Logística] Underdogs: no `rastro.csv`, para valores da Ponte, o `arquivo_origem` deve ser o `.eml` do pacote (`03_email_ponte_cambio_relatorio_set2026.eml`) ou o nome do anexo (`PonteCambio_Relatorio_TARVO_092026.xlsx`)? O `ref_origem` é o Nº Operação nos dois casos." | Correção automática do rastro da remessa |
| O-2 | "[Logística] Underdogs: a Helena disse que alguns itens podem ou não ser listados: a devolução da Casa em `divergencias_taxa.csv`, a Atlas com 0,00 em `comissoes_por_lojista.csv` e os spreads negativos em `divergencias_taxa.csv`. Na correção automática, incluir esses itens conta como alarme falso ou é neutro? Hoje deixamos os três só em `pendencias.csv`." | P-06, P-07 e D-03 sem perder ponto por alarme falso |
| O-3 | "[Logística] Underdogs: a correção casa as linhas pelo `cnpj`/`ref_origem` (e `linha_negocio`), e o `id_saida` é livre? Usamos `COM-CHK-<cnpj>`, `DIV-CHK-<id_transacao>` etc." | Confirma que o padrão de `id_saida` não atrapalha a correção |

Acompanhar sem perguntar de novo: **Q-07** (estrutura do rastro), da Turma do Barulho.

### 11.2 Para o financeiro da Tarvo — `[Financeiro]`, Helena até 17h45
| ID | Mensagem proposta | O que destrava |
| :--- | :--- | :--- |
| T-1 | "[Financeiro] Underdogs: no fechamento de outubro, como vocês dão baixa numa pendência de um mês para o outro? Exemplo: a Atlas fica pendente em setembro e, quando o comercial confirmar a taxa, setembro entra junto com o mês seguinte. Propomos que a analista marque `status=resolvida` e a decisão numa coluna do `pendencias.csv` do mês anterior, e que o agente de outubro leia esse arquivo e só reabra o que continua aberto. Funciona para vocês, ou a baixa acontece em outro lugar, como a aba de controle da planilha?" | E6 e o roteiro de outubro do pitch |
| T-2 | "[Financeiro] Underdogs: hoje a isenção da Casa está só num comentário da Bia na célula A13 da planilha, e nem a Orbe ficou sabendo. Para outubro em diante, propomos uma aba 'Condições especiais' na mesma planilha (lojista, linha, condição, de, até, quem aprovou), preenchida pela Bia depois do ok do comercial, e o agente lê essa aba. Vocês adotariam? Se não, onde a condição especial deveria ficar registrada?" | P-03 com dono no cliente; responde à causa raiz 2 |

Acompanhar sem perguntar de novo: **Q-04** (valor do ajuste da Ponte), **Q-05** (bandeira) e
**Q-06** (id repetido e estorno órfão no ajuste da Orbe). Resposta que chegar muda flag em
`premissas.py`, não código.

**Não perguntar:**
- se os números ou as contas estão certos: a Helena não valida nenhum dos dois (R-48);
- nada que o `HIPOTESES.md` já cita com link;
- a unidade da taxa, que o time decidiu em 2.69 (P-09).

---

## 12. Linha do tempo

| Hora | Construção | Verificação e regras | Narrativa e entrega |
| :--- | :--- | :--- | :--- |
| 14h30–14h40 | **Alinhamento (todos):** papéis, D-01..D-06 (sobretudo a D-03), merge do #12, do #13 e deste plano | | |
| 14h40–15h15 | Serial | Kit de conferência | Causa raiz + esqueleto do pitch |
| 15h15–16h00 | Trilhas A, B e C em paralelo | Kit pronto; casos à mão | README para não técnicos |
| **16h00** | **G1** (checkout) | Confere o G1 | **Checkpoint 2** |
| 16h00–16h45 | Trilhas B e C | Confere cada PR | Slides do pitch |
| **16h45** | **G2** | Confere o G2 | |
| 16h45–17h15 | Integração + caixa-preta | Triagem humana da caixa-preta | Slides |
| 17h15–17h45 | Extras de código | Ensaio de outubro; última pergunta até 17h15 | Slides + roteiro de outubro |
| **17h45** | **Congelamento do código**, `saida/` final | Conferência final + clone limpo | PROMPTS (todos exportam) + MOMENTOS |
| 18h15–18h25 | Merge final na `main` | Confirma "conferido" final | README final, **e-mail com o repositório** |
| 18h30–19h00 | Pitch (todos) | Pitch (todos) | **PDF por e-mail até 19h00** |
