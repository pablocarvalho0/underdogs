# Momentos Chave do Uso de IA (PROMPTS/MOMENTOS.md)

Este documento registra os momentos críticos na interação com a IA durante o desenvolvimento da solução de conciliação financeira da Tarvo, destacando a direção humana, correções de rumo e pensamento crítico.

---

### Momento 1: Inicialização do Repositório e Definição da Arquitetura de Rastreabilidade
- **O que foi pedido:** Criação do repositório base com governança estrita (branch protection com aprovação obrigatória do mantenedor), configuração de ambiente sem decisões de negócio precipitadas e alinhamento às exigências do regulamento da Barte AI.
- **O que a IA devolveu:** A IA gerou a infraestrutura de código, `README.md`, `CLAUDE.md`, `.gitignore`, `pyproject.toml` e `HIPOTESES.md`, modelando o pipeline para exigir rastreabilidade (`rastro.csv`) linha a linha.
- **O que foi feito com isso:** Aprovada a estrutura base com foco em rastreabilidade auditável desde a primeira linha de código, garantindo que nenhuma regra financeira seja codificada sem validação prévia.

---

### Momento 2: Tentativa de Automatização Precipitada de Regras Fiscais (Erro da IA)
- **O que foi pedido:** Análise preliminar do relatório de comissões e faturamento de notas fiscais.
- **O que a IA devolveu:** A IA assumiu inicialmente que a Tarvo deveria emitir notas fiscais pelo valor bruto transacionado nas agências de intercâmbio, confundindo o volume transacionado no checkout com a receita de intermediação da Tarvo.
- **O que foi feito com isso:** A proposta foi imediatamente refutada e corrigida. No modelo de subadquirência, a subadquirente fatura exclusivamente a sua receita de serviço (taxa MDR líquida e antecipação), não o montante transacionado pelos alunos. A dúvida foi registrada como premissa a validar formalmente em `HIPOTESES.md`.

---

### Momento 3: Auditoria Crítica de Governança, Regras do Hackathon e Blindagem de Testes
- **O que foi pedido:** Validação da confiabilidade dos testes como gabarito, verificação de aderência às condições de contorno da Barte AI e blindagem para impedir que IAs adulterassem os testes para obter falsos positivos.
- **O que a IA devolveu:** A análise revelou que o `README.md` e `CLAUDE.md` estavam incorretamente configurados como "repositório privado" (o que violava o regulamento eliminatório da Barte que exige repositório público para correção automática), que o teste sintético inicial ignorava validação contábil do ERP Fênix e que apenas avisos em texto não impediam fisicamente que IAs alterassem os testes.
- **O que foi feito com isso:** A documentação foi corrigida imediatamente para repositório público; as asserções de teste foram estendidas para validar classificações contábeis, notas fiscais individuais e rastreabilidade estendida; foi criada uma suíte de integridade para o dataset real (`npm run test:real`); e os arquivos foram blindados via permissões de sistema (`chmod 444`) e hook de pré-commit do Git.


---

### Momento 4: Agentes confundindo o runner de testes (jest × pytest)
- **O que foi pedido:** Investigar por que os agentes de IA tropeçavam ao rodar `npm test`, alternando entre jest, `pytest` e `python -m pytest`.
- **O que a IA devolveu:** O diagnóstico mostrou duas causas. A primeira era um hook local de proteção de memória que tratava todo `npm test` como jest sem ler o `package.json`, então bloqueava o comando oficial e empurrava o agente a improvisar. A segunda era a documentação, que oferecia "`npm test` ou `pytest`" como equivalentes, embora o pytest e as dependências existam só na `.venv`: chamado com o python do sistema, ele falha com `ModuleNotFoundError`.
- **O que foi feito com isso:** O hook passou a ler o script real do `package.json` e só barra quando ele chama jest ou vitest; isso ficou coberto por bateria de regressão. `CLAUDE.md`, `GEMINI.md` e `README.md` agora definem `npm test` como comando único e explicam que é um atalho para o pytest da `.venv`. Também documentam o que não fazer: flags de jest, `npm install` e `pytest` com o python do sistema. Os caminhos paralelos foram removidos: o `test.sh` e o script `test:watch`, que nunca funcionou porque dependia do `pytest-xdist`, ausente do projeto. A explicação ficou num lugar só, a seção 5 do `CLAUDE.md`.

---

### Momento 5: [A preencher durante a validação contra o gabarito]
- **O que foi pedido:** *(Registrar validação final de números)*
- **O que a IA devolveu:** *(Registrar retorno da IA)*
- **O que foi feito com isso:** *(Registrar decisão e ajuste adotado)*

---

## Candidatos a momento (para o time escolher)

As instruções pedem de 2 a 4 momentos. Os registros abaixo são da exploração do data pack e das respostas do financeiro. O time decide quais entram e quais saem.

### Candidato A: a IA leu os valores da planilha e ignorou o comentário e o tachado (erro da IA)
- **O que foi pedido:** Perfilar a planilha de taxas (`02_...xlsx`) para montar o cadastro de lojistas.
- **O que a IA devolveu:** Um perfil só com os valores das células. Ficaram de fora o comentário da Bia na célula A13 ("conversar com Diego (comercial) sobre condição especial", da Casa do Estudante) e a linha tachada da Globo Trotter. Com isso, a Casa foi tratada como lojista comum.
- **O que foi feito com isso:** Lendo o canal, vimos perguntas de outros times sobre uma condição especial da Casa. Voltamos ao arquivo com um script que lê comentários, formatação e linhas ocultas, e achamos os dois sinais. A Helena confirmou a isenção de set a dez (R-08 no `HIPOTESES.md`). Lição para o agente: a leitura de planilha tem que reportar comentário, tachado e linha oculta como aviso, nunca descartar em silêncio.

### Candidato B: mapeamento de EC pela "impressão digital" das taxas, tratado como hipótese
- **O que foi pedido:** Descobrir de quem são os 3 ECs da Orbe que não estão na planilha.
- **O que a IA devolveu:** O mapeamento pelo conjunto de taxas cobradas em cada EC, comparado com as linhas sem EC da planilha: `1038867654` = Kiwi; `1043300981` = Novo Horizonte; `1043396662` = Horizonte Viagens.
- **O que foi feito com isso:** Não usamos como fato. Perguntamos no canal e a Helena confirmou os três (R-05). O alias ficou como dado, com fonte e aprovador, e não como código. Assim, um EC novo em outubro vira pendência de cadastro em vez de ser adivinhado.

### Candidato C: arredondar a soma ou cada linha (R$ 0,57 de diferença)
- **O que foi pedido:** O total da comissão de remessa de setembro.
- **O que a IA devolveu:** R$ 39.542,88 na primeira conta, arredondando só a soma das metades de spread.
- **O que foi feito com isso:** A Helena definiu arredondamento comum por linha, depois soma (R-02). O total correto é R$ 39.543,45. Essa regra é também a única compatível com a invariante do `rastro.csv` (a soma das linhas do rastro tem que ser igual ao número reportado), então ela virou regra de contrato do código, não detalhe de implementação.

### Candidato D: não confiar a priori no que já está escrito (direção humana)
- **O que foi pedido:** "Reveja os dados e o contexto que temos [...] não tome como verdade o que está escrito hoje no repositório; leia sem confiar a priori."
- **O que a IA devolveu:** Uma releitura contra os arquivos, que achou erros no plano (o Aurora tem 84 lançamentos, não 80; a divergência da Rota começa em 12/09, não em 01/09; o canal `#tarvo-financeiro` não existe). Achou também uma afirmação de outro participante no canal que os dados contradizem: o débito da Rota continua em 1,49%; só o crédito mudou.
- **O que foi feito com isso:** O `HIPOTESES.md` foi reescrito com três níveis separados: fato medido, regra do financeiro (com link do thread) e premissa nossa. Os totais de controle foram calculados de forma independente, fora do `src/` (§5 do `HIPOTESES.md`).

### Candidato E: releitura do canal inteiro antes de fechar (direção humana)
- **O que foi pedido:** Ler o `#duvidas-hackathon-ai` inteiro, thread por thread, e comparar com o que o `HIPOTESES.md` já registrava: o que bate, o que diverge e o que falta. Separar o que o financeiro **disse** do que um time **propôs**.
- **O que a IA devolveu:** 42 threads lidas. A comparação achou o que faltava, entre outras coisas a recusa explícita da Helena em validar números e contas ("Número eu não valido", "Conta por conta eu não valido"), e itens registrados como regra que, pelo texto, eram decisões delegadas ao time (R-19). Duas leituras paralelas do mesmo canal, com 20 minutos de diferença, divergiram: uma tratava como abertas duas perguntas que a Helena já tinha respondido.
- **O que foi feito com isso:** As duas leituras foram consolidadas conferindo cada thread divergente direto no Slack, e não escolhendo uma versão. O que faltava entrou como R-45..R-49, L-06..L-09 e Q-04..Q-07. Lição: proposta de time que ninguém respondeu não vira regra, e registro do canal tem prazo de validade curto; antes de decidir em cima de "sem resposta", reler a thread.
