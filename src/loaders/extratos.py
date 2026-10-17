"""Parsers dos extratos bancários: Banco Aurora (CSV) e Banco Meridiano (OFX)."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import ofxparse  # type: ignore[import-untyped]
import pandas as pd

from src.config import AURORA_CSV, MERIDIANO_OFX
from src.loaders.orbe import parse_brazilian_float


def load_extrato_aurora(file_path: Path = AURORA_CSV) -> pd.DataFrame:
    """
    Carrega o extrato do Banco Aurora (CSV), capturando a linha física (L8, L9...)
    como 'ref_origem', conforme exigido pelo regulamento.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    header_idx = None
    for idx, line in enumerate(lines, start=1):
        parts = [p.strip().lower() for p in line.split(";")]
        if "data" in parts and any("lançamento" in p or "lancamento" in p for p in parts):
            header_idx = idx
            break

    if header_idx is None:
        raise ValueError("Cabeçalho do extrato Banco Aurora não encontrado.")

    # Só linhas com data e sem ser SALDO ANTERIOR/FINAL são lançamentos. Os saldos
    # ficam em df.attrs para o invariante saldo_anterior + Σ valor = saldo_final.
    data: list[dict[str, Any]] = []
    saldos: dict[str, float] = {}
    for line_num, line in enumerate(lines[header_idx:], start=header_idx + 1):
        parts = [p.strip() for p in line.strip().split(";")]
        if len(parts) < 5:
            continue
        dt_str, desc, doc, valor_str, saldo_str = parts[:5]
        if desc.upper().startswith("SALDO"):
            saldos[desc.upper()] = parse_brazilian_float(saldo_str)
            continue
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dt_str):
            continue

        data.append({
            "linha_fisica": f"L{line_num}",
            "data": datetime.strptime(dt_str, "%d/%m/%Y").strftime("%Y-%m-%d"),
            "descricao": desc,
            "documento": doc,
            "valor": parse_brazilian_float(valor_str),
            "saldo": parse_brazilian_float(saldo_str),
        })

    df = pd.DataFrame(data)
    df.attrs["saldo_anterior"] = saldos.get("SALDO ANTERIOR")
    df.attrs["saldo_final"] = saldos.get("SALDO FINAL")
    return df


def load_extrato_meridiano(file_path: Path = MERIDIANO_OFX) -> pd.DataFrame:
    """
    Carrega o extrato do Banco Meridiano a partir do arquivo OFX.
    O identificador 'ref_origem' é o FITID (tx.id).
    """
    with open(file_path, "rb") as f:
        ofx = ofxparse.OfxParser.parse(f)

    data: list[dict[str, Any]] = []
    for tx in ofx.account.statement.transactions:
        data.append({
            "fitid": tx.id,
            "data": tx.date.strftime("%Y-%m-%d") if tx.date else None,
            "descricao": tx.memo,
            "valor": float(tx.amount),
            "tipo": tx.type,
        })

    return pd.DataFrame(data)
