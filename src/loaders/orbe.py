"""Parser do relatório de comissões da adquirente Orbe."""

from decimal import Decimal, InvalidOperation
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


def parse_decimal_br(val: Any, linha: str = "?", coluna: str = "?") -> Decimal | None:
    """'1.791,28' -> Decimal('1791.28'). Vazio -> None; ilegível levanta erro (nunca vira 0)."""
    if val is None or (not isinstance(val, str) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        return Decimal(s.replace(".", "").replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"Orbe: valor ilegível {val!r} na coluna {coluna} (linha {linha})") from None


def load_orbe_report(file_path: Path = ORBE_CSV) -> pd.DataFrame:
    """
    Carrega o relatório da adquirente Orbe sem alterações manuais.
    Converte valores monetários e percentuais para Decimal (None se vazio).
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
            "valor_bruto": str,
            "taxa_aplicada_pct": str,
            "valor_taxa": str,
            "valor_liquido": str,
            "data_movimento": str,
            "data_venda_original": str,
        },
    )

    dec_cols = ["valor_bruto", "taxa_aplicada_pct", "valor_taxa", "valor_liquido"]
    for col in dec_cols:
        if col in df.columns:
            # dtype=str antes: o pandas não pode passar por float.
            valores = [
                parse_decimal_br(v, f"{file_path.name}:{i + 2}", col)
                for i, v in enumerate(df[col].astype(object).where(df[col].notna(), None))
            ]
            df[col] = pd.Series(valores, index=df.index, dtype=object)

    return df
