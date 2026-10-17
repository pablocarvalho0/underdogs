"""Configurações, caminhos e esquemas oficiais dos relatórios."""

from pathlib import Path

# Diretórios base
ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
DATA_PACK_DIR = DOCS_DIR / "Tarvo_Data_Pack_set2026"
OUTPUT_DIR = ROOT_DIR / "saida"

# Arquivos brutos de entrada
ORBE_CSV = DATA_PACK_DIR / "01_orbe_relatorio_comissoes_set2026.csv"
TAXAS_XLSX = DATA_PACK_DIR / "02_tabela_taxas_contratadas.xlsx"
PONTE_EML = DATA_PACK_DIR / "03_email_ponte_cambio_relatorio_set2026.eml"
FENIX_ERP_CSV = DATA_PACK_DIR / "04_plano_de_contas_fenix_erp.csv"
AURORA_CSV = DATA_PACK_DIR / "05a_extrato_banco_aurora_cc4471_set2026.csv"
MERIDIANO_OFX = DATA_PACK_DIR / "05b_extrato_banco_meridiano_cc90233_set2026.ofx"

# Arquivos obrigatórios de saída em saida/
OUTPUT_FILES: dict[str, list[str]] = {
    "comissoes_por_lojista.csv": [
        "id_saida",
        "cnpj",
        "lojista",
        "linha_negocio",
        "comissao_brl",
    ],
    "divergencias_taxa.csv": [
        "id_saida",
        "cnpj",
        "linha_negocio",
        "ref_origem",
        "taxa_contratada_pct",
        "taxa_aplicada_pct",
        "diferenca_brl",
    ],
    "notas_a_emitir.csv": [
        "id_saida",
        "tomador_cnpj",
        "tomador",
        "linha_negocio",
        "valor_brl",
        "discriminacao",
    ],
    "lancamentos_classificados.csv": [
        "id_saida",
        "banco",
        "ref_origem",
        "data",
        "descricao",
        "valor",
        "conta_codigo",
        "metodo",
        "confianca",
    ],
    "pendencias.csv": [
        "id_saida",
        "tipo",
        "ref_origem",
        "valor_brl",
        "motivo",
        "quem_decide",
    ],
    "rastro.csv": [
        "id_saida",
        "arquivo_origem",
        "ref_origem",
        "valor",
    ],
}
