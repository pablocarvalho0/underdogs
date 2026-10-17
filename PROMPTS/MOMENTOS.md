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

### Momento 3: [A preencher durante a execução do pipeline de reconciliação]
- **O que foi pedido:** *(Registrar próximo momento crítico de refatoração ou conciliação)*
- **O que a IA devolveu:** *(Registrar retorno da IA)*
- **O que foi feito com isso:** *(Registrar decisão e ajuste adotado)*

---

### Momento 4: [A preencher durante a validação contra o gabarito]
- **O que foi pedido:** *(Registrar validação final de números)*
- **O que a IA devolveu:** *(Registrar retorno da IA)*
- **O que foi feito com isso:** *(Registrar decisão e ajuste adotado)*
