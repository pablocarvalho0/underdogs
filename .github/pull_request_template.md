## 📝 Descrição das Alterações
<!-- Descreva de forma clara e concisa o que este PR altera ou implementa -->

## 🎯 Tipo de Alteração
- [ ] Nova funcionalidade (parser, módulo de cálculo, etc.)
- [ ] Correção de bug / ajuste em regra de cálculo
- [ ] Atualização de premissas ou documentação (`HIPOTESES.md`, `CLAUDE.md`, etc.)
- [ ] Refatoração de código sem alteração no resultado numérico

## 🔍 Checklist de Rastreabilidade e Integridade
- [ ] **Zero Alucinação:** Todos os valores apurados possuem rastreabilidade linha a linha em `rastro.csv`.
- [ ] **Formato de Saída:** Arquivos em `saida/` validados com `;` de separador, `.` decimal, datas `AAAA-MM-DD` e CNPJs só dígitos.
- [ ] **Premissas Documentadas:** Novas hipóteses ou dúvidas para o time financeiro foram adicionadas em `HIPOTESES.md`.
- [ ] **Momentos de IA:** Se IA foi utilizada nesta alteração, momentos críticos foram registrados em `PROMPTS/MOMENTOS.md`.
- [ ] **Testes:** Testes automatizados executados e passando (`pytest`).

## ⚠️ Exceções e Pendências Geradas
<!-- Se este PR introduz ou modifica regras para pendencias.csv, liste aqui -->
