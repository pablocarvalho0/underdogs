# GEMINI.md — Instruções e Regras do Projeto para Gemini / Antigravity

Este documento orienta os assistentes baseados em Gemini (Antigravity IDE, Gemini CLI, Gemini Code Assist) e desenvolvedores que trabalham no projeto **Tarvo Fechamento Financeiro** da equipe **Underdogs**.

As diretivas completas e detalhadas estão documentadas em [`CLAUDE.md`](./CLAUDE.md).

---

## 🚫 DIRETIVA MANDATÓRIA: SUÍTE DE TESTES IMUTÁVEL

> ⚠️ **ATENÇÃO MÁXIMA PARA AGENTES GEMINI:**
>
> 1. **NÃO LEIA NEM INSPECIONE O ARQUIVO DE TESTE:** É terminantemente proibido inspecionar `tests/test_blackbox_immutable.py` ou os gabaritos em `tests/fixtures/blackbox/` para sobreajustar regras ou vazar respostas.
> 2. **NÃO ALTERE NEM AFROUXE TESTES:** A suíte `tests/test_blackbox_immutable.py` e os arquivos de fixture em `tests/fixtures/blackbox/` são **IMUTÁVEIS**.
> 3. **PAPEL DO AGENTE:** Construir a lógica de conciliação e fechamento financeiro dentro de `src/` respeitando os contratos oficiais descritos em `docs/`.
> 4. **COMANDO PERMITIDO:** A IA deve apenas executar `npm test` para avaliar o progresso.
> 5. **ANTES DE RODAR:** `npm test` é pytest da `.venv`, não jest. Leia a seção 5 do [`CLAUDE.md`](./CLAUDE.md) — ela lista o que não fazer.

---

## 📌 Guia Rápido de Contexto

- **Domínio:** Fechamento financeiro automatizado para Tarvo Pagamentos (Setembro/2026).
- **Rastreabilidade Total:** Todo valor apurado deve ter linha correspondente em `saida/rastro.csv`.
- **Formato de Saídas (`saida/`):**
  - Separador: `;`
  - Decimal: `.`
  - Data: `AAAA-MM-DD`
  - CNPJ: 14 dígitos apenas.
- **Dúvidas & Premissas:** Documente sempre em [`HIPOTESES.md`](./HIPOTESES.md).
- **Consulte o guia completo:** [`CLAUDE.md`](./CLAUDE.md)
