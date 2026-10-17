# Hipóteses, Premissas e Perguntas ao Time Financeiro

Este documento registra a separação explícita entre o que se sabe com base nos dados brutos, o que foi assumido (hipóteses) e as dúvidas a serem validadas com o time financeiro da Tarvo.

---

## 📋 1. O Que Sabemos com Certeza (Fatos Documentados)

1. **Volume e Operação:**
   - Cerca de 25 lojistas ativos no nicho de educação internacional.
   - Competência avaliada: **Setembro de 2026**.
   - Duas linhas de negócio: **Checkout** (adquirente Orbe) e **Remessas** (parceiro Ponte Câmbio).
2. **Modelo de Receita:**
   - **Checkout:** Tarvo ganha a taxa de desconto de lojista (MDR) e a taxa de antecipação negociadas na planilha de taxas.
   - **Remessas:** Repasse de 50% do spread apurado pela Ponte Câmbio conforme contrato informado no e-mail (`docs/Tarvo_Data_Pack_set2026/03_email_ponte_cambio_relatorio_set2026.eml`).
3. **Ponte Câmbio:**
   - Transações com status `"APROVADO C/ RESSALVA"` seguem para liquidação normalmente.
   - Repasse programado para 06/10/2026 mediante recebimento de nota fiscal de intermediação.
4. **Estrutura de Saída:**
   - 6 arquivos em `saida/` com esquemas fixos, separador `;`, ponto decimal, datas `AAAA-MM-DD` e CNPJ numérico de 14 dígitos.
   - Rastreabilidade obrigatória em `rastro.csv` ligando 100% dos valores reportados às suas origens.

---

## 🔍 2. Hipóteses e Premissas Assumidas

| ID | Premissa Assumida | Racional / Justificativa | Status |
| :--- | :--- | :--- | :--- |
| **H-01** | Transações de checkout estornadas (`tipo_lancamento == 'ESTORNO'`) revertem a comissão proporcionalmente ao valor estornado. | Na adquirente, estornos diminuem o faturamento líquido do lojista e a taxa de adquirente. | A confirmar com financeiro |
| **H-02** | Divergência de taxa ocorre sempre que `taxa_aplicada_pct != taxa_contratada_pct` para a mesma modalidade/bandeira e lojista. | A planilha `02_tabela_taxas_contratadas.xlsx` define a regra contratada oficial. Diferença em reais = `valor_bruto * (taxa_aplicada_pct - taxa_contratada_pct) / 100`. | A confirmar com financeiro |
| **H-03** | Notas fiscais a emitir de Checkout são faturadas contra o lojista pelo valor total da receita da Tarvo no mês. | Subadquirentes emitem NF de prestação de serviços de intermediação contra o lojista pelo valor da sua receita líquida. | A confirmar com financeiro |
| **H-04** | Notas fiscais a emitir de Remessa são emitidas contra a Ponte Câmbio (CNPJ 75.374.179/0001-46). | O e-mail da Ponte Câmbio afirma expressamente: "repasse de 50% [...] será creditado em 06/10/2026, mediante recebimento da nota fiscal de intermediação". | Consistente com e-mail |
| **H-05** | Operações repetidas no relatório da Ponte Câmbio com mesmo ID / hash são isoladas para conferência humana em `pendencias.csv`. | O time financeiro relatou: "Às vezes vem operação repetida [...] e eu não sei se aceito". Não aceitar duplicação automática sem decisão. | Pendência humana |
| **H-06** | Operações com spread negativo no relatório da Ponte Câmbio são lançadas em `pendencias.csv`. | O time financeiro relatou insegurança quanto a aceitar spreads negativos. | Pendência humana |
| **H-07** | O extrato Aurora (banco principal) contém repasses aos lojistas que devem conciliar com o valor líquido calculado das vendas após comissões. | As transferências para lojistas no Aurora liquidam as obrigações registradas na conta `2.1.01.001` (Repasses a lojistas a pagar). | Em validação |

---

## ❓ 3. Perguntas Formuladas para o Time Financeiro (`#tarvo-financeiro`)

### Pergunta 1: Faturamento das Notas Fiscais de Checkout
- **Pergunta:** *"[Time Underdogs] No Checkout, a emissão de nota fiscal da Tarvo para o lojista deve ser feita pelo valor total da taxa cobrada (MDR + antecipação) ou apenas pelo markup da Tarvo descontada a taxa cobrada pela Orbe?"*
- **Resposta:** *(Aguardando resposta)*

### Pergunta 2: Tratamento de Estornos e Cancelamentos na Orbe
- **Pergunta:** *"[Time Underdogs] Quando há estorno no relatório da Orbe, a comissão da Tarvo deve ser estornada integralmente ou a Tarvo retém alguma tarifa mínima de processamento?"*
- **Resposta:** *(Aguardando resposta)*

### Pergunta 3: Spread Negativo nas Remessas da Ponte Câmbio
- **Pergunta:** *"[Time Underdogs] Se houver operação com spread negativo no relatório da Ponte Câmbio, a Tarvo absorve 50% do prejuízo reduzindo o repasse final ou essas linhas devem ser contestadas com a Ponte?"*
- **Resposta:** *(Aguardando resposta)*

---

## 📝 4. Log de Decisões do Projeto

- **2026-10-17 08:30:** Inicialização do repositório com branch protection e exigência de aprovação manual por Pull Request.
- **2026-10-17 08:35:** Definição da arquitetura modular em `src/` com parsers desacoplados e mecanismo de auditoria `rastro.csv` nativo em todos os cálculos.
