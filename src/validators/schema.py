"""Validador rigoroso dos arquivos de saída gerados em saida/."""

import re
from pathlib import Path

import pandas as pd

from src.config import OUTPUT_DIR, OUTPUT_FILES


def validate_file_columns(file_path: Path, expected_cols: list[str]) -> list[str]:
    """Verifica se o cabeçalho é exatamente o do template: mesmas colunas, mesma ordem."""
    if not file_path.exists():
        return [f"Arquivo ausente: {file_path.name}"]

    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().rstrip("\r\n")

    actual_cols = first_line.split(";")
    if actual_cols != expected_cols:
        return [f"{file_path.name}: cabeçalho {actual_cols} difere do template {expected_cols}"]
    return []


def validate_cnpj_format(df: pd.DataFrame, file_name: str, col_name: str) -> list[str]:
    """Valida se os CNPJs contêm apenas dígitos (14 números)."""
    errors: list[str] = []
    if col_name not in df.columns:
        return errors
    invalid_rows = []
    for idx, val in df[col_name].dropna().items():
        s = str(val).strip()
        if not re.match(r"^\d{14}$", s):
            invalid_rows.append((int(str(idx)) + 2, s))
    if invalid_rows:
        errors.append(
            f"{file_name}: {len(invalid_rows)} CNPJs inválidos (ex: linha {invalid_rows[0][0]}='{invalid_rows[0][1]}')"
        )
    return errors


def validate_date_format(df: pd.DataFrame, file_name: str, col_name: str) -> list[str]:
    """Valida formato de data AAAA-MM-DD."""
    errors: list[str] = []
    if col_name not in df.columns:
        return errors
    invalid_dates = []
    for idx, val in df[col_name].dropna().items():
        s = str(val).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            invalid_dates.append((int(str(idx)) + 2, s))
    if invalid_dates:
        errors.append(
            f"{file_name}: {len(invalid_dates)} datas fora do padrão AAAA-MM-DD (ex: linha {invalid_dates[0][0]}='{invalid_dates[0][1]}')"
        )
    return errors


def validate_rastro_integrity(output_dir: Path = OUTPUT_DIR) -> list[str]:
    """
    Verifica se a soma dos valores em rastro.csv bate com os números reportados
    nos arquivos de saída.
    """
    errors: list[str] = []
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


def validate_all_outputs(output_dir: Path = OUTPUT_DIR) -> tuple[bool, list[str]]:
    """Executa a bateria de validações nos arquivos gerados em saida/."""
    all_errors: list[str] = []

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
