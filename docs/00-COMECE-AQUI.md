# Comece aqui

Mapa do projeto para quem chega agora, humano ou agente. Diz onde estamos, qual documento
manda em quê e como trabalhamos até a entrega. Atualizado em 17/10, 14h16.

---

## 1. Onde estamos (medido, não estimado)

| Peça | Estado | Como foi medido |
| :--- | :--- | :--- |
| Regras de negócio | ✅ Quase todas respondidas pela Helena: R-01..R-49, premissas P-01..P-16 | `HIPOTESES.md` na `main` (PR #10) |
| Números esperados | ✅ Prévia independente: checkout R$ 203.735,34, remessa R$ 39.543,45 etc. | `HIPOTESES.md` §5 |
| Contrato e fundação | ✅ `model.py`, `writer.py` (recusa rastro que não fecha), `cadastro.py`, loaders, painel | Código na `main` |
| **Cálculo de negócio** | ❌ **Zero.** As 3 trilhas (`src/trilhas/*.py`) têm 14 linhas cada e devolvem vazio | `run_pipeline` gera os 6 CSVs **só com cabeçalho** |
| Suíte caixa-preta | ❌ `1 failed` | `npm test` |
| Entrada | ⚠️ Nome de arquivo fixo de setembro: o `06_` é ignorado (D-01) | `src/core/entrada.py` |
| `premissas.py` | ⚠️ Defaults de antes das respostas: sem aliases (R-05), `spread_padrao_pct=None` (R-12 diz 1,5%) | `src/premissas.py` |
| `PROMPTS/` | ❌ Só o `MOMENTOS.md`. O export das sessões, que é **entrega obrigatória**, não existe | `ls PROMPTS` |
| Pitch | ❌ | — |

**Em uma frase:** entendemos o problema e temos a régua para conferir os números, mas nenhum
número de saída foi calculado ainda. O que parece "muito código" é infraestrutura, documento e
painel. O nível **Mínimo** do desafio (comissão de checkout com rastro) ainda não existe.

---

## 2. Qual documento manda em quê

Se dois documentos discordarem, vale o da coluna "fonte de verdade".

| Assunto | Fonte de verdade | Status |
| :--- | :--- | :--- |
| O que o desafio pede, prazos, critérios de nota | `docs/01_instrucoes_participantes.docx.md` | Oficial, não editar |
| Regras de negócio, premissas, perguntas, números esperados | `HIPOTESES.md` | Vigente |
| Plano de construção: frentes, portões G1–G3, cortes | `docs/plano-construcao.md` | Vigente (PR #15) |
| Tarefa de cada dev | `docs/tasks/dev1-checkout.md`, `dev2-remessa-extratos.md` | Na `main` (PR #13), mas em conflito com o plano (§3) |
| Regras para agentes de IA | `CLAUDE.md` (o `GEMINI.md` só aponta para ele) | Vigente |
| Princípios e onde a IA atua (base do pitch) | `docs/visao-geral.md` §3, §4 e §6 | Vigente só nessas seções. As §8 e §10 foram superadas pelo `HIPOTESES.md` |
| Arquitetura e contrato do código | `docs/plano-engenharia.md` §2 | Só a §2 vale. Cronograma, perguntas F-xx e decisões D-xx foram superados |
| Como instalar e rodar | `README.md` | Vigente (a árvore de pastas foi corrigida neste PR) |
| Momentos de uso da IA | `PROMPTS/MOMENTOS.md` | Momento 5 em aberto |

Não são documentação de trabalho: `docs/Tarvo_Data_Pack_set2026/` é a entrada, `saida/` é
gerado e `docs/audios/` é a transcrição do briefing.

---

## 3. Conflitos e decisões abertas

Cada item é uma decisão do Pablo. Até ela ser tomada, ninguém deve construir em cima do item.

1. **Quem faz a remessa.** O plano de construção dá a trilha B ao Pablo. A task do dev 2 dá a
   B e a C ao dev 2. É preciso escolher uma das duas versões antes de distribuir.
2. ~~**Merge do plano e das tasks.**~~ Resolvido: entraram na `main` pelos PRs #13 e #15.
3. **D-01..D-06** (`HIPOTESES.md` §4.1): continuam como recomendação. A D-01 (entrada pelo
   cabeçalho) bloqueia o `06_`, e o `06_` muda R$ 3.304,39 no checkout.
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
