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
- **O que foi feito com isso:** O hook passou a ler o script real do `package.json` e só barra quando ele chama jest ou vitest; isso ficou coberto por bateria de regressão. `CLAUDE.md`, `GEMINI.md` e `README.md` agora definem `npm test` como comando único e explicam que é um atalho para o pytest da `.venv`. Também documentam o que não fazer: flags de jest, `npm install` e `pytest` com o python do sistema.

---

### Momento 5: [A preencher durante a validação contra o gabarito]
- **O que foi pedido:** *(Registrar validação final de números)*
- **O que a IA devolveu:** *(Registrar retorno da IA)*
- **O que foi feito com isso:** *(Registrar decisão e ajuste adotado)*
