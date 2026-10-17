# Task Dev 2 — Trilha B (Remessa) + Trilha C (Extratos)

**Branches:** `feat/trilha-remessa` e `feat/trilha-extratos`, um PR cada, a partir da `main` depois do merge do serial (Pablo avisa). **Faça a B primeiro**: é menor e fecha um número do pitch.
**Arquivos seus:** `src/trilhas/remessa.py` e `src/trilhas/extratos.py` (e módulos novos `src/trilhas/remessa_*.py` / `extratos_*.py`, se quiser).
**Freeze:** os dois PRs abertos até **17h00**.
**Revisor:** Pablo. Cada regra abaixo tem ID; cite o ID no comentário do código onde ela é aplicada.

Leia antes, nesta ordem: `CLAUDE.md` (diretiva 0 e §5), `HIPOTESES.md` §1, §2.2, §2.3, §2.4, §2.5, §3 e §5, `src/core/model.py`, `src/core/cadastro.py`, `src/premissas.py`.

## Proibições

- **Não leia nem altere** `tests/test_blackbox_immutable.py` e `tests/fixtures/blackbox/`. Só rode `npm test`.
- O gabarito da suíte roda com um **data pack sintético**. Nada fixo para setembro: nenhum CNPJ, Nº de operação, FITID, linha `Lxx` ou total escrito no código. Exceções de setembro (L50, L65…) têm que sair de **regra**, não de `if ref == "L50"`.
- Nada de casar lojista por nome aproximado. Na remessa, lojista é por `cnpj_limpo` → `cadastro.lojista_por_cnpj`.
- Coluna ausente ou linha estranha não derruba a trilha: vira pendência (R-42).

## Contrato comum

```python
def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha
```

- Toda linha de saída é criada com `LinhaSaida.somando(...)`, e os componentes são linhas de origem. O writer recusa escrever se a soma não fechar.
- Dinheiro em `Decimal`, `brl()` por linha (half-up, inclusive no negativo), e só depois somado (R-02).

### O que o serial entrega (já vai estar na `main`)

- `premissas.spread_padrao_pct = 1.5` (R-12), `premissas.duplicata_conta_uma_vez` (R-13), `premissas.spread_negativo_fora` (R-14), `premissas.tolerancia_spread_pp = 0.01` (P-01), `premissas.taxa_saida_em_pp` (P-09), `premissas.usar_ia_extratos`, `premissas.confianca_minima_ia`.
- `src/core/pendencias.py`:
  ```python
  def pendencia(trilha, chave, tipo, componentes, motivo, quem_decide) -> LinhaSaida
  ```
  Gera `id_saida = PEN-<trilha>-<chave>` e `ref_origem` com os refs juntados por `|`. Use `trilha="REM"` e `"EXT"`. **Uma pendência por contraparte e por lojista** (R-37, P-13).

---

## Trilha B — Remessa

**Entrada:** `dados.ponte`, com as colunas `Nº Operação, Data Contratação, Data Liquidação, CNPJ Cliente, Cliente, Moeda, Valor ME, Taxa Cliente, PTAX Ref., Valor R$, Spread R$, Spread %, Spread Estimado R$ (D-1), IOF R$, Status Compliance, Observação, linha_planilha, cnpj_limpo`.
- O loader já tira o rodapé: são 233 linhas, 232 operações + 1 repetição.
- Componente: `Componente(ARQ_PONTE, nº_operação, valor)`. `ARQ_PONTE` é o `.eml` (P-10).
- **Confira a unidade de `Spread %`** (p.p. ou fração) antes de comparar com `cadastro.spread_contratado_pct`, que devolve p.p.

**Regras**

1. **Repetição (R-13).** O Nº de operação é único: a primeira ocorrência conta, as demais saem da comissão e viram pendência para a Ponte corrigir o relatório.
2. **Spread negativo (R-14).** Fica fora da comissão e da nota. Pendência de contestação com **dois valores**: o `Spread R$` do relatório e a diferença até o spread do contrato. Exemplo: `PC-0926-0210` dá −R$ 687,52 e −R$ 1.351,87. Um vai no `valor_brl` e no rastro, o outro no `motivo`. Não entra em divergências (P-07).
3. **Comissão por operação (R-11):** `brl(0,5 × Spread R$)` realizado (`premissas.participacao_spread_tarvo`). Ex.: 50% de 262,01 = 131,01. Competência pela **data de contratação** (R-16): contratada em 30/09 e liquidada em 01/10 entra. `APROVADO C/ RESSALVA` não muda nada (R-15).
4. **`comissoes_por_lojista.csv`:** `COM-REM-<cnpj>`, `linha_negocio = REMESSA`, componentes = comissões por operação do lojista.
5. **`notas_a_emitir.csv` (R-27):** **uma única nota**, `NF-REM-<cnpj ponte>`, tomador = Ponte Câmbio (`premissas.cnpj_ponte_cambio`), valor = total da participação, componentes = todas as comissões por operação. Discriminação simples, com o serviço e a competência tirada dos dados.
6. **Divergência (R-23, P-01, P-05).** Quando `|Spread % − contratado| ≥ tolerância`: uma linha por operação, `DIV-REM-<nº>`, `ref_origem = nº`, `diferenca_brl = brl((Spread % − contratado) × Valor ME × PTAX Ref.)` (valor **cheio**, não a metade), taxas em p.p.
   - Contratado vazio ou `padrão` = 1,5% (R-12, já resolvido no cadastro).
   - A comissão da Mundo Aberto sai pelo **realizado** mesmo assim (R-17).
7. **Pendências (`REM`):**

   | Caso | Quem decide |
   | :--- | :--- |
   | Contestação de spread por lojista (soma das divergências) | Helena (Ponte Câmbio) |
   | Spreads negativos, uma pendência por lojista | Helena (Ponte Câmbio) |
   | Repetição no relatório | Ponte Câmbio |
   | CNPJ fora do cadastro: calcula a metade mesmo assim e abre pendência (R-19) | Comercial |
   | Acompanhamento: conferir a TED do repasse quando cair (data do e-mail, R-39) | Helena |

8. **Invariante:** `Σ Spread R$ (todas as linhas) = Σ incluído na comissão + Σ negativos + Σ repetições`, e em contagem `linhas = incluídas + negativas + repetidas`. As duas diferenças vão em `conservacao` e têm que dar 0.

**Pronto (B):**

| Item | Valor |
| :--- | ---: |
| Comissão de remessa, 228 operações → uma nota para a Ponte | **R$ 39.543,45** |
| Divergência Mundo Aberto, 23 operações (valor cheio) | R$ 1.418,85 |
| Spreads negativos: pelo relatório / até o contrato | −R$ 1.834,05 / −R$ 3.565,98 |

---

## Trilha C — Extratos

**Entrada:**
- `dados.aurora`: colunas `linha_fisica` (`L9`…`L92`), `data`, `descricao`, `documento`, `valor`, `saldo`, com 84 lançamentos (o loader já tira o saldo anterior e o rodapé).
- `dados.meridiano`: colunas `fitid`, `data`, `descricao`, `valor`, `tipo`, com 100 lançamentos.
- `dados.plano_contas`: colunas `COD_CONTA, DESCRICAO, TIPO, NATUREZA, ACEITA_LANCTO, COD_SUPERIOR`.

**Saída:** `lancamentos_classificados.csv`, uma linha por lançamento.
- `id_saida`: `LAN-AUR-<linha_fisica>` ou `LAN-MER-<fitid>`.
- `banco`: `AURORA` ou `MERIDIANO`.
- `ref_origem`: `L10` ou o FITID.
- `valor`: com sinal; o componente é o próprio lançamento.
- `conta_codigo`, `metodo` (`REGRA`, `IA` ou `HUMANO`) e `confianca` (de 0 a 1).

**Regras**

1. **`conta_codigo` é a contrapartida (R-29).** O que já estava registrado baixa a conta onde estava; o resto vai para receita ou despesa. Já estavam registrados (R-30): folha, ISS, INSS, FGTS e DARFs **de agosto**, e o repasse da Ponte de 04/09 (comissão de agosto a receber → `1.1.03.002`). Tarifa, aluguel, cloud, assinaturas e serviços entram como despesa do mês. A provisão de setembro não é nossa (R-31).
2. **Conta válida:** só `COD_CONTA` com `ACEITA_LANCTO = S` **lida do plano carregado**, não de uma lista no código. Regra que aponte para conta inexistente ou sintética é erro alto, não silêncio.
3. **Tabela de regras** (regex sobre a descrição + sinal → conta), `metodo = REGRA`, `confianca = 1`. A regra mais específica vem primeiro. **Armadilha:** `PIX RECEB PONTE AEREA…` é o lojista Ponte Aérea Estudantil, não a Ponte Câmbio (R-34).

   Sugestões iniciais (confira cada uma contra R-29/R-30 e o plano de contas):

   | Lançamento | Conta sugerida |
   | :--- | :--- |
   | TED da Orbe | `1.1.03.001` |
   | PIX ENVIADO a lojista (repasse) | `2.1.01.001` |
   | Transferência Aurora↔Meridiano | `1.1.09.001` |
   | PIX RECEB de lojista no Meridiano | `2.1.02.001` |
   | TED ENVIADA PONTE | `2.1.02.001` |
   | Aplicação/resgate de CDB | `1.1.02.001` |
   | Rendimento | `3.2.01` |
   | Tarifas | `4.2.01` |
   | IOF | `4.3.01` |

4. **Resíduo com IA (D-02, decidido).** O que nenhuma regra pegou vai para o Claude se `usar_ia_extratos`, com o plano de contas analítico no prompt e saída estruturada `{conta_codigo, confianca, justificativa}`.
   - **Cache versionado** em `src/trilhas/extratos_cache_ia.json`, com chave pelo hash de (banco, descrição normalizada, sinal). Sem chave de API, roda pelo cache e reproduz a mesma saída. Sem chave e sem cache, vai para `HUMANO`.
   - Conta fora do plano analítico ou `confianca < confianca_minima_ia` → `metodo = HUMANO` + pendência.
   - A chave vem de `ANTHROPIC_API_KEY`. Escreva no PR uma seção curta para o README dizendo onde configurar.
   - Modelo: `claude-sonnet-5-5`.
5. **Casos já conhecidos:** têm que sair de regra genérica, mas o resultado esperado em setembro é este.

   | Lançamento | Conta | Pendência | Regra |
   | :--- | :--- | :--- | :--- |
   | Pix recebido sem identificação (L50, R$ 7.350) | `1.1.09.002` | sim, não é receita até identificar | R-32 |
   | Devolução de Pix de lojista (L65, R$ 12.400) | `2.1.01.001` | sim, motivo desconhecido | P-04 |
   | Transferência Aurora→Meridiano sem crédito no mês (L92, R$ 300 mil) | `1.1.09.001` | acompanhamento: crédito em 01/10 | P-11 |
   | Pix de lojista para remessa que sai no mês seguinte (`MRD2026090425`, R$ 18.240) | `2.1.02.001` | no máximo acompanhamento | P-12 |
   | `TED RECEB PONTE … REPASSE COMISSAO 08/2026` (R$ 61.884,12) | `1.1.03.002` | — | baixa de agosto, R-30 |

6. **Invariantes:**
   - `84 + 100 = lançamentos classificados` (nenhum some).
   - No Aurora, saldo inicial (`saldo − valor` da primeira linha) + `Σ valor` = `saldo` da última linha.
   - Bônus, se der tempo: cada TED Meridiano→Ponte = Σ(`Valor R$` + `IOF R$`) das operações contratadas no dia. São 21 de 21 em setembro, e o que não bater vira pendência.

**Pronto (C):** 184 linhas classificadas, todas com conta analítica válida, invariantes em 0, e as pendências da tabela acima saindo. Informe no PR quantas linhas foram `REGRA`, `IA` e `HUMANO`.

---

## Para os dois PRs

1. Se a prévia do `HIPOTESES.md` §5 não bater, investigue antes de abrir o PR. Diferença sem explicação **não** se ajusta no código. O serial deixa esse controle em `tests/test_controle_setembro.py` (rode com `npm run test:all`).
2. `npm test`, `.venv/bin/ruff check src` e `.venv/bin/mypy src` rodados, com a saída colada no PR. A suíte caixa-preta só passa por inteiro com as três trilhas; diga qual asserção falha e de quem ela é.
3. Premissa nova que você tiver que assumir: pare e mande para o Pablo, que decide e põe no `HIPOTESES.md`.
