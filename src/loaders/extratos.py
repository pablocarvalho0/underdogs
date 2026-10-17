"""Parsers dos extratos bancários: Banco Aurora (CSV) e Banco Meridiano (OFX)."""

from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import ofxparse
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

    data: List[Dict[str, Any]] = []
    for line_num, line in enumerate(lines[header_idx:], start=header_idx + 1):
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = [p.strip() for p in line_clean.split(";")]
        if len(parts) < 4:
            continue
        # Descartar saldo anterior ou linhas puramente informativas
        dt_str = parts[0]
        desc = parts[1]
        doc = parts[2] if len(parts) > 2 else ""
        valor_str = parts[3] if len(parts) > 3 else "0"
        saldo_str = parts[4] if len(parts) > 4 else ""

        val = parse_brazilian_float(valor_str)

        data.append({
            "linha_fisica": f"L{line_num}",
            "data": dt_str,
            "descricao": desc,
            "documento": doc,
            "valor": val,
            "saldo": parse_brazilian_float(saldo_str),
        })

    return pd.DataFrame(data)


def load_extrato_meridiano(file_path: Path = MERIDIANO_OFX) -> pd.DataFrame:
    """
    Carrega o extrato do Banco Meridiano a partir do arquivo OFX.
    O identificador 'ref_origem' é o FITID (tx.id).
    """
    with open(file_path, "rb") as f:
        ofx = ofxparse.OfxParser.parse(f)

    data: List[Dict[str, Any]] = []
    for tx in ofx.account.statement.transactions:
        data.append({
            "fitid": tx.id,
            "data": tx.date.strftime("%Y-%m-%d") if tx.date else None,
            "descricao": tx.memo,
            "valor": float(tx.amount),
            "tipo": tx.type,
        })

    return pd.DataFrame(data)
