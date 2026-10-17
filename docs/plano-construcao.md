# Plano de construção — do estado atual até a entrega (v1, 17/10 14h20)

Substitui o `docs/plano-engenharia.md` (v0, 13h20) no que é cronograma, tarefas e critério de
pronto. A arquitetura e o contrato da v0 continuam valendo (§3). As regras de negócio estão no
`HIPOTESES.md` (versão do PR #10), e os IDs citados aqui (R-xx, P-xx, D-xx, Q-xx, L-xx) são os de lá.

**Meta: entregar o nível Extra sem arriscar o Mínimo.** O desafio diz: "É melhor entregar o nível
mínimo certo do que o nível extra com números que não fecham". Por isso o plano tem **portões**
(§5). Só se passa ao nível seguinte quando os números do nível atual batem com a prévia
independente.

---

## 1. Onde estamos (14h15)

| Peça | Estado | Observação |
| :--- | :--- | :--- |
| Contrato (`core/model.py`, `writer.py`, `pipeline.py`) | ✅ na `main` | O writer recusa linha cujo valor ≠ Σ componentes. O rastro sai por construção |
| Cadastro (`core/cadastro.py`) | ✅ na `main` | Taxa em pontos percentuais (`2.49`), vigência (Bridge) e alias de EC. Não filtra lojista INATIVO |
| Loaders | ⚠️ na `main` | **Nome de arquivo fixo de setembro** (o 06 é ignorado). A Orbe vira `float` e um valor ilegível vira 0 **sem aviso** |
| CLI `npm run run` | ⚠️ | Não recebe a pasta do mês: usa sempre `docs/Tarvo_Data_Pack_set2026` |
| Trilhas A, B e C | ❌ stubs | Devolvem `ResultadoTrilha` vazio |
| `premissas.py` | ⚠️ | Ainda com os defaults da v0: sem aliases, sem spread padrão, flags de remessa misturadas |
| Painel + GitHub Pages | ✅ na `main` | Regerado a cada push |
| `HIPOTESES.md` | 🔄 PR #10 aberto | Consolida o #7 e o #8. Decisões D-01..D-06 recomendadas |
| README, PROMPTS, MOMENTOS | 🔄 parcial | Faltam o export das sessões e a escolha final dos momentos |
| Pitch | ❌ | Envio até 19h00 |

Prazos: **checkpoint 2 às 16h00**, **financeiro até 17h45**, **repositório às 18h30** (o que
mudar depois não conta), **pitch às 19h00**.

---

## 2. O que "Extra" significa para nós, item a item

| Requisito do desafio | Como entregamos | Onde fica |
| :--- | :--- | :--- |
| Rastro completo de todos os números | Toda linha com valor, **incluindo pendências e notas**, sai com componentes. O writer recusa escrever se não fechar | `writer.py` (já existe) |
| Pendências explicadas | Uma por contraparte e por lojista (P-13), com valor rastreado, motivo em linguagem do financeiro e `quem_decide`. Mais o rascunho de e-mail de contestação por contraparte (R-37) | `pendencias.csv` + `saida/rascunhos/` |
| Roda em outubro sem retrabalho | (1) descobre os arquivos da pasta pelo cabeçalho (D-01); (2) confere o layout e **avisa em vez de quebrar** (R-42); (3) condição comercial é **dado com vigência e aprovador**, não código (P-03); (4) ensaio com uma pasta "outubro" simulada | `core/entrada.py`, `premissas.py`, `scripts/ensaio_outubro.py` |

Itens que pesam na nota além dos números:
- **Uso de IA (20%).** Há uma segunda implementação independente, que concorda ao centavo com
  o pipeline. Os transcripts vão completos para `PROMPTS/`. Os momentos são reais, incluindo
  erros da IA.
- **Causa raiz (15%).** O pitch e o README explicam *por que* o fechamento erra, com o número
  de cada causa (§9).
- **Tempo (10%).** Mandar o checkpoint 2 às 16h00 e entregar às 18h20, sem correria.

---

## 3. Arquitetura (mantida) e quatro ajustes no contrato

```
pasta do mês ──► entrada (descobre papéis pelo cabeçalho, confere layout, avisa)
             ──► cadastro (planilha + aliases + condições comerciais com vigência)
             ──► trilha A checkout │ trilha B remessa │ trilha C extratos   (paralelas)
             ──► pendências consolidadas (contraparte × lojista) + alertas
             ──► writer (6 CSVs, assert do rastro) ──► invariantes ──► painel
```

Ajustes no contrato. São da **W0** (§4) e precisam estar na `main` antes do meio das trilhas:

1. **`dados.orbe` com a coluna `arquivo_origem` por linha** e os arquivos 01 + 06 (+ qualquer
   outro com o cabeçalho da Orbe) concatenados. As trilhas usam essa coluna no `Componente`.
2. **Valores em `Decimal` a partir do texto cru**, nunca `float`. Valor ilegível vira
   **aviso/pendência**, e não 0.
3. **`run --input <pasta> --output <pasta>`**, com default para a pasta do data pack. A
   assinatura `run_pipeline(input_dir, output_dir)` não muda.
4. **Papel ausente ou arquivo desconhecido não derruba a execução.** Fecha o que não depende
   dele, gera pendência do tipo `FONTE_AUSENTE`/`ARQUIVO_DESCONHECIDO` e marca o resto como
   provisório (R-42).

Esquema de `id_saida` (v0, mantido): `COM-CHK-<cnpj>`, `COM-REM-<cnpj>`,
`DIV-CHK-<id_transacao>`, `DIV-REM-<nº>`, `NF-CHK-<cnpj>`, `NF-REM-75374179000146`,
`LAN-AUR-L<n>`, `LAN-MER-<fitid>`, `PEN-<trilha>-<tipo>-<chave>`.

Formato: `taxa_*_pct` em **pontos percentuais** (`2.69`, P-09). A Orbe já vem assim e o
cadastro já devolve assim. O `Spread %` da Ponte vem em fração e é multiplicado por 100 na saída.

---

## 4. Frentes de trabalho

Donos sugeridos (seguem a v0): **Pablo** = líder, W0, trilha B e integração. **Dev 1** =
trilha A. **Dev 2** = trilha C, depois documentação e pitch. Cada frente trabalha numa branch
própria e abre PR para o Pablo.

### W0 — Base serial (Pablo, 14h30–15h15) — bloqueia o fim das trilhas, não o começo
- Merge do PR #10 e fechamento do #7 e do #8 (D-06). Confirmar D-01..D-05 e as premissas em bloco.
- **Entrada por descoberta (D-01):** o papel de cada arquivo sai do cabeçalho; o prefixo `01_`/`06_` desempata.
  - Orbe: todo CSV com o cabeçalho da Orbe. Planilha de taxas: xlsx com a aba "Taxas vigentes". Ponte: `.eml` com anexo xlsx. Plano de contas: CSV com `COD_CONTA`. Aurora: CSV com o cabeçalho do banco. Meridiano: `.ofx`.
  - O `id_transacao` repetido entre arquivos segue a P-14.
- Loader da Orbe em `Decimal`, com `arquivo_origem` por linha.
- Taxas: lojista **INATIVO** (Globo Trotter) sai do cadastro. Se aparecer transação dele, vira pendência.
- `premissas.py` com o que já foi respondido:
  - 3 aliases com `confirmado_financeiro=True` e a fonte (R-05);
  - `spread_padrao_pct=1.5` (R-12);
  - a flag da remessa separada em duas: duplicata **conta uma vez** (R-13) e negativo **fica fora** (R-14);
  - condições comerciais com vigência e aprovador. Casa: 0% em MDR e antecipação de 01/09 a 31/12/2026. A data-base é a da venda para venda e estorno, e a da antecipação para antecipação e reversão (R-08, R-44);
  - Atlas: EC `1076801732` sem contrato desde 10/09, não fatura (R-06);
  - tolerância de spread de 0,01 p.p. (P-01).
- CLI `run --input/--output`. O `status` usa a descoberta.

### W1 — Trilha A, checkout (Dev 1, 14h30–16h15)
Entrada: linhas da Orbe (01 + 06 = **1.957**). Para cada linha:

| Tipo | Data-base da taxa (R-03, R-04, R-44) | Faixa |
| :--- | :--- | :--- |
| VENDA | `data_movimento` | modalidade e parcelas da linha |
| ESTORNO | `data_venda_original` | modalidade e parcelas **da linha do estorno** |
| ANTECIPACAO | `data_movimento` | coluna Antecipação |
| REVERSAO ANTECIPACAO | data da antecipação referenciada (busca em todos os arquivos da Orbe) | coluna Antecipação |

- Comissão da linha = `brl(valor_bruto × taxa_contratada / 100)`, arredondando meio centavo
  para longe do zero (R-02). `COM-CHK-<cnpj>` = soma das linhas, com uma linha como componente.
- Casa isenta (R-08/R-09): a comissão da linha é 0. O `valor_taxa` cobrado entra na **pendência
  de devolução**, não em divergência (P-06).
- **Divergência** (R-20/R-21): aplicada ≠ contratada, fora da isenção →
  `DIV-CHK-<id>` = `brl(bruto × (aplicada − contratada) / 100)`. Estorno de venda com taxa errada
  sai negativo.
- **Nota** (R-26): `NF-CHK-<cnpj>` quando a comissão é > 0, com os mesmos componentes. Zero ou
  negativa vira pendência.
- **Pendências:**
  - Atlas: não fatura (R-06/D-03);
  - devolução da Casa;
  - nota da Casa não emitida;
  - divergência por lojista, para contestar com a Orbe e ressarcir o lojista;
  - mais de 12x (R-10);
  - EC sem lojista;
  - estorno órfão (D-02);
  - alerta de antecipação (P-08).
- **Invariante:** toda linha de entrada cai em exatamente um destino (comissão, Atlas ou outra
  pendência). Σ `valor_taxa` = comissão + divergência + devolução da Casa + Atlas + resíduo de
  truncamento, com |resíduo| ≤ 0,01 × nº de linhas.
- **Pronto quando** bater com a §6, lojista a lojista.

### W2 — Trilha B, remessa (Pablo, 15h15–16h15)
- Operações vêm do anexo do `.eml`, só as linhas `PC-`. Dedupe por Nº, mantendo a primeira; a
  cópia vira pendência para a Ponte corrigir (R-13).
- Spread negativo fica fora (R-14). Vira pendência com dois valores: o do relatório e a diferença
  até o contrato (essa numa coluna extra).
- `COM-REM-<cnpj>` = Σ `brl(Spread R$ / 2)` por operação (R-11).
  `NF-REM-75374179000146` = Σ das mesmas metades (R-27).
- Divergência (R-23, P-01, P-05): |`Spread %` − contratado| ≥ 0,01 p.p. →
  `DIV-REM-<nº>` = `brl((Spread % − contratado) × Valor ME × PTAX)`.
- Pendências: negativos (Ponte), duplicata (Ponte), contestação da Mundo Aberto (Ponte/lojista),
  acompanhamento do repasse da Ponte em outubro (R-39), CNPJ fora da planilha (R-19, não ocorre).
- **Invariante:** Σ `Spread R$` do relatório (233 linhas) = incluídas + negativas + duplicata.
- **Pronto quando** bater com a §6.

### W3 — Trilha C, extratos (Dev 2, 14h30–16h00)
- Os 184 lançamentos (Aurora L9–L92 + 100 FITIDs do Meridiano) viram `LAN-…`, cada um com ele
  mesmo como componente.
- Tabela de regras pela contrapartida (R-29/R-30), só para contas com `ACEITA_LANCTO=S`:

| Padrão | Conta |
| :--- | :--- |
| `TED RECEBIDA … ORBE` | 1.1.03.001 |
| `PIX ENVIADO <lojista>` (inclui a Atlas, R-36) | 2.1.01.001 |
| Transferência entre contas (ida e volta) e L92 | 1.1.09.001 |
| `PIX RECEB <lojista>` no Meridiano (inclui o de R$ 18.240, R-34) | 2.1.02.001 |
| `TED ENVIADA PONTE … LIQ OPERACOES` | 2.1.02.001 |
| `TED RECEB PONTE … REPASSE COMISSAO 08/2026` | 1.1.03.002 |
| Folha / INSS / FGTS de agosto | 2.1.04.001 / .002 / .003 |
| ISS / PIS / COFINS / IRRF de agosto | 2.1.03.003 / .001 / .002 / .004 |
| Tarifas (Aurora e Meridiano) | 4.2.01 |
| Condomínio | 4.2.02 |
| AWS | 4.2.03 |
| Google Workspace | 4.2.04 |
| Seguro | 4.2.05 |
| IOF | 4.3.01 |
| Aplicação/resgate CDB | 1.1.02.001 |
| Rendimento | 3.2.01 |
| L50 Pix sem identificação | 1.1.09.002, com pendência |
| L65 devolução de Pix da Mundo Aberto | 2.1.01.001 (P-04), com pendência |

- A regra mais específica vem primeiro: "PONTE AEREA" (lojista) ≠ "PONTE CAMBIO".
  `metodo=REGRA`, `confianca=1`.
- **Resíduo** (zero em setembro): o que nenhuma regra cobre vai para `metodo=HUMANO`, com
  pendência. A IA **só sugere**, se houver chave e se der tempo (E5).
- **Invariantes:** 184 entradas = 184 saídas. Saldo anterior + Σ = saldo final nos dois bancos.
- **Testemunhas cruzadas** (contam como extra; não geram pendência quando batem):
  - as 21 TEDs para a Ponte = Σ(Valor R$ + IOF) das operações do dia;
  - os Pix dos lojistas = operações dos 7 dias seguintes.
- **Pronto quando** todas as 184 linhas tiverem conta lançável e as invariantes derem zero.

### W4 — Integração e verificação (Pablo + quem estiver livre, 16h15–17h00)
1. Merge das trilhas, `npm run run` → `saida/`, `npm run validate`, `npm test`.
2. Comparar com a §6 usando `scripts/controle_independente.py`. É o script da prévia,
   versionado como **segunda implementação**: não importa nada de `src/`.
3. Um teste nosso, `tests/test_controle.py`, trava os totais da §6. Não é o caixa-preta.
4. **Testes caixa-preta:** foram escritos antes das respostas do financeiro e podem codificar
   regra antiga (ex.: comissão pela taxa aplicada, duplicata só como pendência). Se falharem,
   **um humano** (Pablo) lê a asserção e compara com o `HIPOTESES.md`. Vale a regra da Helena. A IA
   não lê nem altera esses testes (diretiva 0 do `CLAUDE.md`).

### W5 — Extras (16h45–17h40, por ordem de valor; ver cortes na §8)
| # | Extra | Dono | Por quê |
| :--- | :--- | :--- | :--- |
| E1 | Descoberta de arquivos + conferência de layout com aviso | W0 | Sem isso o 06 some e outubro quebra. **Não é opcional** |
| E2 | Rascunho de e-mail de contestação por contraparte (Orbe, Ponte) e de devolução por lojista, gerado de `pendencias.csv` | Dev 1 | Pedido explícito da Helena (R-37). Mostra "como a analista usa em outubro" |
| E3 | Ensaio de outubro: copia a pasta renomeando para `*_out2026`, tira o 06, troca a ordem de uma coluna, e roda | Dev 2 | Prova o "roda em outubro" no pitch, com o print do aviso |
| E4 | Controle independente versionado + teste de totais | Pablo | Evidência de que verificamos a IA (20% da nota) |
| E5 | IA no resíduo dos extratos, com cache versionado e fallback HUMANO | Dev 2 | Mostra onde a IA atua. Não muda setembro (resíduo zero) |
| E6 | Pendências que passam para o mês seguinte (Atlas retroativa, R-07): `pendencias.csv` com colunas extras para recalcular depois | Dev 1 | Fecha o ciclo de outubro. Se não der tempo, vai para "mais um mês" |
| E7 | Painel atualizado com os números finais | Pablo | Já existe; só regerar |

### W6 — Entrega (17h45–18h25)
- **17h45: congelamento do código.** Depois disso só entram documentação e `saida/`.
- `saida/` gerado do zero pelo comando do README e commitado.
- README: instalar e rodar do zero (uv ou pip, sem depender de Node). Um comando com
  `--input`, onde mudar as premissas, chave de API opcional (`.env.example`), limitações
  conhecidas e o roteiro de outubro da analista.
- `HIPOTESES.md` final: perguntas feitas, com time e horário, respostas e premissas.
- `PROMPTS/`: cada pessoa exporta **todas** as sessões (Claude Code `/export` ou o `.jsonl` bruto)
  para `PROMPTS/<nome>/`. Pode tirar chave e dado pessoal; fora isso, não editar.
- `PROMPTS/MOMENTOS.md`: escolher de 2 a 4 momentos (A..E são candidatos), com pelo menos um
  erro da IA.
- **18h15: clone limpo numa pasta nova, seguir o README e conferir que o `saida/` sai igual.**
- **18h25: merge final na `main` (Pablo), conferir que o repositório está público e mandar o link
  por e-mail (L-06).**

### W7 — Pitch (Dev 2 a partir das 17h00; todos de 18h30 a 19h00)
Slides em PDF, para o financeiro e o CFO. Cobrem os 7 pontos pedidos:
1. O que está quebrado e por quê (§9).
2. O que a solução faz.
3. Quanto dinheiro está em jogo (§6).
4. Como a analista usa em outubro.
5. Onde a IA atua e onde não atua.
6. Onde a solução falha e o que acontece nesses casos.
7. O que faríamos com mais um mês.

Envio até 19h00.

---

## 5. Portões (não avançar sem passar)

| Portão | Hora-alvo | Critério | Se falhar |
| :--- | :--- | :--- | :--- |
| **G1 Mínimo** | 15h45 | `comissoes_por_lojista` CHECKOUT bate com a §6 **por lojista**, o rastro fecha e o `validate` passa | Às 16h15, todo mundo ajuda a trilha A |
| **G2 Alvo** | 16h45 | Remessa, divergências, notas e 184 lançamentos batem com a §6 | Cortar W5 de baixo para cima |
| **G3 Extra** | 17h40 | Pendências da §7 completas, invariantes em zero, ensaio de outubro sem quebrar | Entregar o G2 e registrar no README o que ficou de fora |

O checkpoint 2 (16h00) relata o estado do G1 e do G2 com honestidade.

---

## 6. Números de controle (01 + 06; prévia independente, `HIPOTESES.md` §5)

| Saída | Esperado |
| :--- | ---: |
| Comissão CHECKOUT, 21 lojistas (Casa −5,50; sem Atlas) | **R$ 203.735,34** |
| Notas CHECKOUT (20 lojistas com comissão > 0) | Σ = R$ 203.740,84 |
| Divergências CHECKOUT, 92 linhas (Rota: 299,62 + 539,26 + 707,40; Bridge: 29,95) | R$ 1.576,23 |
| Comissão REMESSA, 228 operações | **R$ 39.543,45** |
| Nota REMESSA (Ponte Câmbio, 75374179000146) | R$ 39.543,45 |
| Divergência REMESSA, Mundo Aberto, 23 operações | R$ 1.418,85 |
| Lançamentos classificados | 184 (84 Aurora + 100 Meridiano) |

Por lojista, a §5 do `HIPOTESES.md` traz a tabela antes e depois do 06. Diferença de 1 centavo
num lojista quase sempre é arredondamento: no float, na soma antes de arredondar, ou no
negativo arredondado para o lado errado.

---

## 7. Pendências esperadas em setembro (e o que **não** é pendência)

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
- as 7 + 39 bandeiras divergentes nos estornos (D-04);
- o Pix de R$ 18.240, que a R-34 explica;
- os aliases confirmados;
- os estornos de agosto, que a R-03 cobre;
- as ressalvas da Ponte (R-15).

---

## 8. Riscos e cortes

| Risco | Mitigação |
| :--- | :--- |
| W0 atrasa e as trilhas ficam sem o 06 | As trilhas leem `dados.orbe` como hoje. Quando a W0 cair, só ganham linhas. O G1 é conferido de novo depois da W0 |
| Centavos (float, ordem de arredondamento) | `Decimal` desde o texto cru, `brl()` por linha. Conferir lojista a lojista contra a §6 |
| Caixa-preta falhando por regra antiga | Um humano decide com base no `HIPOTESES.md` (W4). Não "consertar" o código para passar num teste errado |
| Conflitos de merge | Uma trilha = um arquivo (`trilhas/x.py`). `premissas.py` e `entrada.py` só pela W0 |
| Fim do atendimento às 17h45 | Pergunta nova só até 17h15 (§10). Depois disso, assumir e escrever no HIPOTESES |
| Tempo | **Ordem de corte:** E5 → E6 → E3 → E2 → E7. **Nunca cortar:** E1, trilhas, formato, README rodando do zero, PROMPTS, MOMENTOS |

---

## 9. Causa raiz (para o README e o pitch)

1. **Não existe chave comum entre as fontes.**
   - A Orbe identifica o lojista por EC, a Ponte por CNPJ e os bancos pelo nome truncado.
   - A ponte entre eles é uma planilha à mão, com 3 ECs faltando, CNPJ em 3 formatos e uma condição especial escondida num comentário de célula.
2. **A condição comercial não chega a quem cobra (R-49).** O comercial fecha e "quando lembra"
   avisa a Orbe e a Ponte. O resultado em setembro:
   - Rota: R$ 1.546,28;
   - Bridge: R$ 29,95;
   - Mundo Aberto: R$ 1.418,85;
   - Casa: R$ 15.396,77 a devolver.

   Hoje isso só aparece quando o lojista reclama.
3. **A regra só existe na cabeça da Helena.** Pelas palavras dela: "Quase tudo que vocês
   descobriram aqui estava só na minha cabeça". Estorno de agosto, isenção pela data, spread
   negativo, duplicata: tudo isso agora é dado versionado, com fonte.
4. **A conferência é por fonte, nunca cruzada.** A duplicata da Ponte e os spreads negativos
   passam porque ninguém compara o relatório com as TEDs do Meridiano. Nós comparamos: 21 de 21.
5. **Arquivo novo ou atrasado quebra o processo.** O 06 chegou depois do relatório e muda
   R$ 3.304,39 em 7 notas. Um processo que lê um nome fixo erra em silêncio.

---

## 10. Perguntas que ainda valem a pena

O canal já respondeu quase tudo de setembro. Pergunta vaga recebe resposta vaga, e perguntar o
que já foi respondido conta contra. Por isso a lista é curta, e cada pergunta diz o que destrava.

### 10.1 Para a organização do hackathon — `[Logística]`
| ID | Mensagem pronta | O que destrava |
| :--- | :--- | :--- |
| O-1 (Q-02) | "[Logística] Underdogs: no `rastro.csv`, para valores da Ponte, o `arquivo_origem` deve ser o `.eml` do pacote (`03_email_ponte_cambio_relatorio_set2026.eml`) ou o nome do anexo (`PonteCambio_Relatorio_TARVO_092026.xlsx`)? O `ref_origem` é o Nº Operação nos dois casos." | Correção automática do rastro da remessa |
| O-2 | "[Logística] Underdogs: a Helena disse que alguns itens podem ou não ser listados: a devolução da Casa em `divergencias_taxa.csv`, a Atlas com 0,00 em `comissoes_por_lojista.csv` e os spreads negativos em `divergencias_taxa.csv`. Na correção automática, incluir esses itens conta como alarme falso ou é neutro? Nossa escolha hoje é deixar os três **só** em `pendencias.csv`." | P-06, P-07 e D-03: evita perder pontos por alarme falso |
| O-3 | "[Logística] Underdogs: a correção casa as linhas pelo `cnpj`/`ref_origem` (e `linha_negocio`), e o `id_saida` é livre? Usamos `COM-CHK-<cnpj>`, `DIV-CHK-<id_transacao>` etc." | Confirma que o nosso padrão de `id_saida` não atrapalha a correção |

Acompanhar sem perguntar de novo: **Q-07** (estrutura do rastro), que a Turma do Barulho fez às 13h48.

### 10.2 Para o financeiro da Tarvo — `[Financeiro]`, Helena até 17h45
| ID | Mensagem pronta | O que destrava |
| :--- | :--- | :--- |
| T-1 | "[Financeiro] Underdogs: para o fechamento de outubro, como vocês dão baixa numa pendência de um mês para o outro? Exemplo: a Atlas fica pendente em setembro e, quando o comercial confirmar a taxa, setembro entra junto com o mês seguinte (como a senhora disse). Propomos que a analista marque `status=resolvida` e a decisão numa coluna do `pendencias.csv` do mês anterior, e que o agente de outubro leia esse arquivo e só reabra o que continua aberto. Funciona para vocês, ou a baixa acontece em outro lugar, como a aba de controle da planilha?" | E6 (pendências que passam de mês) e o roteiro de outubro do pitch |
| T-2 | "[Financeiro] Underdogs: hoje a isenção da Casa está só num comentário da Bia na célula A13 da planilha, e nem a Orbe ficou sabendo. Para outubro em diante, propomos uma aba 'Condições especiais' na mesma planilha (lojista, linha, condição, de, até, quem aprovou), preenchida pela Bia depois do ok do comercial, e o agente lê essa aba. Vocês adotariam? Se não, onde a condição especial deveria ficar registrada?" | P-03 com dono no cliente; é a resposta à causa raiz 2 |

Acompanhar sem perguntar de novo (são de outros times e ainda estão sem resposta):
- **Q-04:** valor do ajuste da Ponte (Desbravadores, 12h04).
- **Q-05:** bandeira divergente (Turma do Barulho, 13h35).
- **Q-06:** id repetido e estorno órfão no ajuste da Orbe (Desbravadores, 13h36).

Se a resposta chegar, ela muda flag em `premissas.py`, não código.

**Não perguntar:**
- se os números estão certos, ou conta por conta: a Helena não valida nenhum dos dois (R-48);
- nada que o `HIPOTESES.md` já cita com link;
- a unidade da taxa, que o time decidiu em 2.69 (P-09).

---

## 11. Linha do tempo

| Hora | Pablo | Dev 1 | Dev 2 |
| :--- | :--- | :--- | :--- |
| 14h20–14h30 | Lê o plano, faz o merge do #10, distribui as frentes | Lê a §4 W1 e a §6 | Lê a §4 W3 |
| 14h30–15h15 | W0: entrada, Decimal, premissas, CLI | W1 (lê `dados.orbe` atual) | W3: regras |
| 15h15–16h00 | W2 remessa | W1 até o G1 | W3 até as invariantes |
| **16h00** | **Checkpoint 2** (DM ao organizador) | | |
| 16h00–16h45 | W2 + W4 integração | W1 rebase sobre a W0, G1 de novo | E3 ensaio de outubro |
| 16h45–17h40 | E4 controle, E7 painel | E2 rascunhos, E6 se der | Pitch (rascunho) + E5 se der |
| até 17h15 | Mandar O-1..O-3 e T-1, T-2, se o time aprovar | | |
| **17h45** | **Congelamento do código** | README (roteiro de outubro) | Pitch |
| 17h45–18h15 | `saida/` final, HIPOTESES final | PROMPTS (export) + MOMENTOS | PROMPTS (export) |
| 18h15–18h25 | Clone limpo + merge final + e-mail | | |
| 18h30–19h00 | Pitch (todos) → PDF por e-mail até 19h00 | | |
