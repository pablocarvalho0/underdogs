"""Parser do relatório de comissões da adquirente Orbe."""

from pathlib import Path
from typing import Any
import pandas as pd
from src.config import ORBE_CSV


def parse_brazilian_float(val: Any) -> float:
    """Converte strings com vírgula decimal para float."""
    if pd.isna(val) or val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def load_orbe_report(file_path: Path = ORBE_CSV) -> pd.DataFrame:
    """
    Carrega o relatório da adquirente Orbe sem alterações manuais.
    Converte valores monetários e percentuais para float nativo.
    """
    df = pd.read_csv(
        file_path,
        sep=";",
        dtype={
            "id_transacao": str,
            "cod_estabelecimento": str,
            "nome_estabelecimento": str,
            "tipo_lancamento": str,
            "modalidade": str,
            "qtd_parcelas": str,
            "bandeira": str,
            "id_referencia": str,
        },
    )

    float_cols = ["valor_bruto", "taxa_aplicada_pct", "valor_taxa", "valor_liquido"]
    for col in float_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_brazilian_float)

    return df
