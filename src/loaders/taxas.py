"""Parser da tabela de taxas contratadas mantida pelo time financeiro."""

import re
from pathlib import Path
from typing import Optional
import pandas as pd
import openpyxl
from src.config import TAXAS_XLSX


def clean_cnpj(val: any) -> Optional[str]:
    """Extrai apenas os 14 dígitos numéricos do CNPJ."""
    if pd.isna(val) or val is None:
        return None
    digits = re.sub(r"\D", "", str(val))
    if len(digits) == 14:
        return digits
    if len(digits) > 0:
        return digits.zfill(14)
    return None


def load_taxas_contratadas(file_path: Path = TAXAS_XLSX) -> pd.DataFrame:
    """
    Carrega a aba 'Taxas vigentes' da planilha de taxas contratadas.
    Ignora a aba antiga obsoleta e normaliza CNPJs e percentuais.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb["Taxas vigentes"]

    # Identificar linha de cabeçalho (que contém 'Lojista' e 'CNPJ')
    header_row_idx = None
    for idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        row_vals = [str(v).strip().lower() if v is not None else "" for v in row]
        if "lojista" in row_vals and "cnpj" in row_vals:
            header_row_idx = idx
            headers = [str(v).strip() if v is not None else f"col_{i}" for i, v in enumerate(row)]
            break

    if header_row_idx is None:
        raise ValueError("Cabeçalho da tabela de taxas contratadas não encontrado.")

    data = []
    for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
        if not any(row):
            continue
        row_dict = dict(zip(headers, row))
        # Pular linhas sem lojista ou sem CNPJ
        if not row_dict.get("Lojista") or not row_dict.get("CNPJ"):
            continue
        data.append(row_dict)

    df = pd.DataFrame(data)
    df["cnpj_limpo"] = df["CNPJ"].apply(clean_cnpj)

    return df
