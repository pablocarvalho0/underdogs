"""Parser do relatório da Ponte Câmbio a partir do e-mail .eml recebido."""

import email
from email import policy
import io
from pathlib import Path
import pandas as pd
import openpyxl
from src.config import PONTE_EML
from src.loaders.taxas import clean_cnpj


def load_ponte_cambio_report(file_path: Path = PONTE_EML) -> pd.DataFrame:
    """
    Lê o arquivo .eml da Ponte Câmbio, extrai programaticamente
    o anexo .xlsx e carrega a aba 'Operações'.
    """
    with open(file_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    xlsx_bytes = None
    for part in msg.walk():
        filename = part.get_filename()
        if filename and filename.lower().endswith(".xlsx"):
            xlsx_bytes = part.get_payload(decode=True)
            break

    if xlsx_bytes is None:
        raise FileNotFoundError("Anexo Excel (.xlsx) não encontrado no e-mail da Ponte Câmbio.")

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
    sheet = wb["Operações"] if "Operações" in wb.sheetnames else wb.active

    # Localizar linha do cabeçalho ('Nº Operação')
    header_row_idx = None
    headers = []
    for idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        row_str = [str(v).strip().lower() if v is not None else "" for v in row]
        if any("operação" in s or "operacao" in s for s in row_str):
            header_row_idx = idx
            headers = [str(v).strip() if v is not None else f"col_{i}" for i, v in enumerate(row)]
            break

    if header_row_idx is None:
        raise ValueError("Cabeçalho da planilha de operações da Ponte Câmbio não encontrado.")

    data = []
    for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
        if not any(row):
            continue
        row_dict = dict(zip(headers, row))
        data.append(row_dict)

    df = pd.DataFrame(data)
    if "CNPJ Cliente" in df.columns:
        df["cnpj_limpo"] = df["CNPJ Cliente"].apply(clean_cnpj)

    return df
