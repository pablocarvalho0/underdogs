"""Parser do plano de contas exportado do ERP Fênix."""

from pathlib import Path

import pandas as pd

from src.config import FENIX_ERP_CSV


def load_plano_de_contas(file_path: Path = FENIX_ERP_CSV) -> pd.DataFrame:
    """
    Carrega o plano de contas do ERP Fênix usando encoding ISO-8859-1/Latin1.
    """
    df = pd.read_csv(
        file_path,
        sep=";",
        encoding="latin1",
        dtype={
            "COD_CONTA": str,
            "DESCRICAO": str,
            "TIPO": str,
            "NATUREZA": str,
            "ACEITA_LANCTO": str,
            "COD_SUPERIOR": str,
        },
    )
    # Limpeza básica de strings
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
    return df
