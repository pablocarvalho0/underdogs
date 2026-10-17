"""Validador rigoroso dos arquivos de saída gerados em saida/."""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from src.config import OUTPUT_DIR, OUTPUT_FILES


def validate_file_columns(file_path: Path, expected_cols: List[str]) -> List[str]:
    """Verifica se o arquivo contém exatamente as colunas obrigatórias."""
    errors = []
    if not file_path.exists():
        return [f"Arquivo ausente: {file_path.name}"]

    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    actual_cols = [c.strip() for c in first_line.split(";")]
    missing = [c for c in expected_cols if c not in actual_cols]
    if missing:
        errors.append(f"{file_path.name}: colunas ausentes: {missing}")
    return errors


def validate_cnpj_format(df: pd.DataFrame, file_name: str, col_name: str) -> List[str]:
    """Valida se os CNPJs contêm apenas dígitos (14 números)."""
    errors = []
    if col_name not in df.columns:
        return errors
    invalid_rows = []
    for idx, val in df[col_name].dropna().items():
        s = str(val).strip()
        if not re.match(r"^\d{14}$", s):
            invalid_rows.append((idx + 2, s))
    if invalid_rows:
        errors.append(
            f"{file_name}: {len(invalid_rows)} CNPJs inválidos (ex: linha {invalid_rows[0][0]}='{invalid_rows[0][1]}')"
        )
    return errors


def validate_date_format(df: pd.DataFrame, file_name: str, col_name: str) -> List[str]:
    """Valida formato de data AAAA-MM-DD."""
    errors = []
    if col_name not in df.columns:
        return errors
    invalid_dates = []
    for idx, val in df[col_name].dropna().items():
        s = str(val).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            invalid_dates.append((idx + 2, s))
    if invalid_dates:
        errors.append(
            f"{file_name}: {len(invalid_dates)} datas fora do padrão AAAA-MM-DD (ex: linha {invalid_dates[0][0]}='{invalid_dates[0][1]}')"
        )
    return errors


def validate_rastro_integrity(output_dir: Path = OUTPUT_DIR) -> List[str]:
    """
    Verifica se a soma dos valores em rastro.csv bate com os números reportados
    nos arquivos de saída.
    """
    errors = []
    rastro_path = output_dir / "rastro.csv"
    if not rastro_path.exists():
        return ["rastro.csv não encontrado para conferência."]

    rastro_df = pd.read_csv(rastro_path, sep=";")
    if "id_saida" not in rastro_df.columns or "valor" not in rastro_df.columns:
        return ["rastro.csv não contém colunas 'id_saida' e 'valor'."]

    # Agrupar soma por id_saida
    rastro_sums = rastro_df.groupby("id_saida")["valor"].sum().to_dict()

    # Checar contra comissoes_por_lojista.csv
    comissoes_path = output_dir / "comissoes_por_lojista.csv"
    if comissoes_path.exists():
        com_df = pd.read_csv(comissoes_path, sep=";")
        for _, row in com_df.iterrows():
            id_s = str(row["id_saida"])
            val_rep = float(row["comissao_brl"])
            val_rastreado = float(rastro_sums.get(id_s, 0.0))
            if abs(val_rep - val_rastreado) > 0.02:
                errors.append(
                    f"Divergência de rastro no id_saida {id_s}: reportado={val_rep:.2f}, rastreado={val_rastreado:.2f}"
                )

    return errors


def validate_all_outputs(output_dir: Path = OUTPUT_DIR) -> Tuple[bool, List[str]]:
    """Executa a bateria de validações nos arquivos gerados em saida/."""
    all_errors: List[str] = []

    for file_name, expected_cols in OUTPUT_FILES.items():
        file_path = output_dir / file_name
        col_errs = validate_file_columns(file_path, expected_cols)
        all_errors.extend(col_errs)

        if not col_errs and file_path.exists():
            df = pd.read_csv(file_path, sep=";", dtype=str)
            if "cnpj" in df.columns:
                all_errors.extend(validate_cnpj_format(df, file_name, "cnpj"))
            if "tomador_cnpj" in df.columns:
                all_errors.extend(validate_cnpj_format(df, file_name, "tomador_cnpj"))
            if "data" in df.columns:
                all_errors.extend(validate_date_format(df, file_name, "data"))

    # Checar integridade matemática do rastro
    all_errors.extend(validate_rastro_integrity(output_dir))

    return len(all_errors) == 0, all_errors
