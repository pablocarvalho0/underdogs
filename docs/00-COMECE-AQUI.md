# Comece aqui

Mapa do projeto para quem chega agora, humano ou agente. Diz onde estamos, qual documento
manda em quê e como trabalhamos até a entrega. Atualizado em 17/10, 17h55.

---

## 1. Onde estamos (medido, não estimado)

| Peça | Estado | Como foi medido |
| :--- | :--- | :--- |
| Regras de negócio | ✅ R-01..R-51 respondidas pela Helena; premissas P-01..P-18 | `HIPOTESES.md` |
| Cálculo de negócio | ✅ As 3 trilhas no MVP da `main` (b64734f): Mínimo e Alvo completos | `npm run run` gera os 6 CSVs |
| Números | ✅ Batem com a prévia independente (§5 do `HIPOTESES.md`) e com uma segunda implementação feita à parte (`feat/alvo`): comissões R$ 243.278,79, 115 divergências, 21 notas, 184 lançamentos, 16 pendências | `conferencia/index.html`: 25/25 totais, 12/12 pendências esperadas, 0 invariantes quebrados |
| Rastro | ✅ Todo `id_saida` com valor fecha com a soma das linhas de origem; reexecução gera `saida/` idêntica | writer recusa rastro que não fecha; conferência |
| Entrada | ✅ Papel de cada arquivo pelo conteúdo; o 06 entra; outubro com nomes trocados gera a mesma saída (D-01 implementada) | `npm run run -- --input <pasta>` |
| Suíte caixa-preta | ⚠️ `1 failed`: um valor (gerado 43,80, esperado 53,80). A suíte é anterior às respostas da Helena; triagem humana | `npm test` |
| `PROMPTS/` | ❌ Só o `MOMENTOS.md`. O export das sessões, **entrega obrigatória**, depende de aprovação do conteúdo (repositório público) | `ls PROMPTS` |
| Pitch | ❌ Entrega até 19h00 | — |

**Em uma frase:** os números de setembro estão calculados, rastreados e conferidos por dois caminhos
independentes; faltam o histórico das sessões de IA e o pitch.

---

## 2. Qual documento manda em quê

Se dois documentos discordarem, vale o da coluna "fonte de verdade".

| Assunto | Fonte de verdade | Status |
| :--- | :--- | :--- |
| O que o desafio pede, prazos, critérios de nota | `docs/01_instrucoes_participantes.docx.md` | Oficial, não editar |
| Regras de negócio, premissas, perguntas, números esperados | `HIPOTESES.md` | Vigente |
| Plano de construção: frentes, portões G1–G3, cortes | `docs/plano-construcao.md` | Vigente (PR #15) |
| O que ainda não sabemos, hipóteses abertas, anomalias nos dados e conflitos entre documentos | `docs/lacunas-e-conflitos.md` | Vigente (17/10 14h40) |
| Tarefa de cada dev | `docs/tasks/dev1-checkout.md`, `dev2-remessa-extratos.md` | Na `main` (PR #13), mas em conflito com o plano (§3) |
| Regras para agentes de IA | `CLAUDE.md` (o `GEMINI.md` só aponta para ele) | Vigente |
| Princípios e onde a IA atua (base do pitch) | `docs/visao-geral.md` §3, §4 e §6 | Vigente só nessas seções. As §8 e §10 foram superadas pelo `HIPOTESES.md` |
| Arquitetura e contrato do código | `docs/plano-engenharia.md` §2 | Só a §2 vale. Cronograma, perguntas F-xx e decisões D-xx foram superados |
| Como instalar e rodar | `README.md` | Vigente (a árvore de pastas foi corrigida neste PR) |
| Momentos de uso da IA | `PROMPTS/MOMENTOS.md` | Vigente: 4 momentos, como pede o enunciado |

Não são documentação de trabalho: `docs/Tarvo_Data_Pack_set2026/` é a entrada, `saida/` é
gerado e `docs/audios/` é a transcrição do briefing.

---

## 3. Conflitos e decisões abertas

Cada item é uma decisão do Pablo. Até ela ser tomada, ninguém deve construir em cima do item.

1. ~~**Quem faz a remessa.**~~ Resolvido: o MVP da `main` traz as 3 trilhas.
2. ~~**Merge do plano e das tasks.**~~ Resolvido: entraram na `main` pelos PRs #13 e #15.
3. **D-01..D-06** (`HIPOTESES.md` §4.1): a D-01 e a D-03 estão implementadas; ver a situação de cada uma lá.
4. **Áudio no repositório público.** O `docs/audios/briefing.ogg`, com a voz de quem gravou,
   entrou na `main` pelo PR #13. Decidir se fica ou sai.

---

## 4. Como trabalhamos daqui até 18h30

1. **O próximo número vale mais que o próximo documento.** Daqui em diante, documento novo só
   se destravar uma decisão. A ordem é a do desafio: Mínimo → Alvo → Extra.
2. **A régua é a §5 do `HIPOTESES.md`.** Uma trilha só está pronta quando bate com ela,
   lojista a lojista. "Rodou sem erro" não basta.
3. **Uma trilha = um arquivo = uma branch = um PR.** `premissas.py` e `entrada.py` têm um dono
   só, para não gerar conflito.
4. **Resposta nova do financeiro muda `premissas.py` e o `HIPOTESES.md`**, nunca regra escrita
   dentro da trilha.
5. **Ninguém lê nem altera os testes caixa-preta** (`CLAUDE.md` §0). Se o teste falhar por
   regra antiga, um humano compara com o `HIPOTESES.md`, e vale a regra da Helena.
6. **Horários fixos:** checkpoint 2 às 16h00, fim do atendimento do financeiro às 17h45,
   congelamento do código às 17h45, repositório às 18h30, pitch às 19h00.
