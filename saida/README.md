# Arquivos de Saída da Conciliação de Setembro/2026

Os arquivos nesta pasta são gerados pela execução do pipeline (`python -m src.main run`) e devem respeitar os requisitos estritos do regulamento:

1. **Separador de colunas:** `;`
2. **Separador decimal:** `.` (ponto)
3. **Datas:** `AAAA-MM-DD`
4. **CNPJ:** 14 dígitos numéricos (apenas números)

### Arquivos Obrigatórios:
- `comissoes_por_lojista.csv`: `id_saida; cnpj; lojista; linha_negocio; comissao_brl`
- `divergencias_taxa.csv`: `id_saida; cnpj; linha_negocio; ref_origem; taxa_contratada_pct; taxa_aplicada_pct; diferenca_brl`
- `notas_a_emitir.csv`: `id_saida; tomador_cnpj; tomador; linha_negocio; valor_brl; discriminacao`
- `lancamentos_classificados.csv`: `id_saida; banco; ref_origem; data; descricao; valor; conta_codigo; metodo; confianca`
- `pendencias.csv`: `id_saida; tipo; ref_origem; valor_brl; motivo; quem_decide`
- `rastro.csv`: `id_saida; arquivo_origem; ref_origem; valor`

> **Importante:** A soma dos valores em `rastro.csv` agrupados por `id_saida` deve fechar com exatidão matemática com o valor reportado no respectivo arquivo.
