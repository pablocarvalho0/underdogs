# Histórico das sessões de IA (Claude Code)

Transcripts **brutos** das sessões de Claude Code usadas no case, desde a liberação, exportados
de `~/.claude/projects/` às 18h06 de 17/10. Formato JSONL: uma linha por evento (mensagem do
usuário, resposta, chamada de ferramenta, resultado). Abre em qualquer editor ou com
`jq -c . arquivo.jsonl | less`.

| Sessão | O que foi |
| :--- | :--- |
| `7bdb4540-….jsonl` | Sessão principal de construção (líder): leitura dos dados e do canal, `HIPOTESES.md`, nível Mínimo (PR #16), `feat/alvo`, conferência cruzada, documentação e releitura final do Slack. `7bdb4540-…/subagents/` tem os subagents dela |
| `d33dbedd-….jsonl` | Sessão de revisão e integração, em paralelo à anterior: review do PR #16, QA do painel, revisões independentes (checkout, remessa, extratos, entregas, testes), nível Extra (PR #19) e segunda rodada (PR #21). `d33dbedd-…/subagents/` tem os subagents de revisão e de construção |
| `f9999436-….jsonl` | Sessão curta de configuração (`/plugin`), sem trabalho do case |

As duas sessões principais conversaram entre si (mensagens `cross-session-message`) para dividir
o trabalho. As pastas `tool-results/` guardam saídas longas de ferramentas citadas nos transcripts.

**O que foi removido**, e nada além disso (o enunciado permite tirar chaves e dados pessoais):

- e-mails (1.016 ocorrências, inclusive de participantes do Slack) → `<email-removido>`; ficaram só
  `noreply@anthropic.com`, `git@github.com` e os de `@example.com`;
- caminho e nome de usuário da máquina local → `/home/<usuario>`, `<usuario>`;
- nomes de participantes de outros times e da organização, que aparecem nas mensagens do Slack →
  `<participante-NN>` (o mesmo número para a mesma pessoa em todos os arquivos). Ficam os nomes do
  nosso time, os nomes de times (Fox AI, MN AI…) e as pessoas fictícias do case (Helena, Bia, Diego, Caio);
- varredura de chaves e tokens (GitHub, Anthropic, OpenAI, Slack, AWS, chave privada, Bearer), CPF e
  telefone: **nenhuma ocorrência** encontrada.

Cada linha foi decodificada, redigida nas strings e regravada como JSON válido (conferido linha a
linha); fora isso, o conteúdo está como saiu do Claude Code. Sessões de IA feitas por outros
integrantes em outras máquinas não estão aqui.
