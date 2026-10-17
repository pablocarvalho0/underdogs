"""Escreve os 6 CSVs de saída no formato fixo do desafio.

Formato: separador `;`, ponto decimal, datas AAAA-MM-DD, CNPJ 14 dígitos (garantido
pelas trilhas). Antes de escrever, confere que todo `valor` é a soma exata dos seus
componentes — se não for, falha alto em vez de publicar número sem rastro.
"""

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.config import OUTPUT_FILES
from src.core.model import COLUNA_VALOR, LinhaSaida


class RastroNaoFecha(Exception):
    pass


class ColunasForaDoTemplate(Exception):
    pass


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, Decimal):
        return format(v, "f")
    return str(v)


def conferir_rastro(linhas: list[LinhaSaida]) -> None:
    erros = []
    ids_vistos: set[str] = set()
    for ln in linhas:
        if ln.id_saida in ids_vistos:
            erros.append(f"id_saida duplicado: {ln.id_saida}")
        ids_vistos.add(ln.id_saida)
        if ln.valor is None:
            continue
        soma = sum((c.valor for c in ln.componentes), Decimal(0))
        if not ln.componentes or soma != ln.valor:
            erros.append(f"{ln.id_saida}: valor={ln.valor} soma_componentes={soma}")
    if erros:
        raise RastroNaoFecha("\n".join(erros[:20]))


def conferir_colunas(linhas: list[LinhaSaida]) -> None:
    """Cada linha traz exatamente as colunas do template: nem a mais, nem a menos.

    Coluna sem valor vem explícita como None (sai vazia); a coluna do número rastreado
    e `id_saida` não vão em `campos`.
    """
    erros = []
    for ln in linhas:
        coluna_valor = COLUNA_VALOR[ln.arquivo]
        esperadas = set(OUTPUT_FILES[ln.arquivo]) - {"id_saida", coluna_valor}
        recebidas = set(ln.campos)
        extras = recebidas - esperadas
        faltando = esperadas - recebidas
        if extras:
            erros.append(f"{ln.id_saida} ({ln.arquivo}): colunas fora do template {sorted(extras)}")
        if faltando:
            erros.append(f"{ln.id_saida} ({ln.arquivo}): colunas ausentes {sorted(faltando)}")
    if erros:
        raise ColunasForaDoTemplate("\n".join(erros[:20]))


def escrever(linhas: list[LinhaSaida], output_dir: Path) -> dict[str, int]:
    conferir_colunas(linhas)
    conferir_rastro(linhas)
    output_dir.mkdir(parents=True, exist_ok=True)

    por_arquivo: dict[str, list[dict[str, str]]] = {nome: [] for nome in OUTPUT_FILES}
    for ln in linhas:
        row = {k: _fmt(v) for k, v in ln.campos.items()}
        row["id_saida"] = ln.id_saida
        if ln.valor is not None:
            row[COLUNA_VALOR[ln.arquivo]] = _fmt(ln.valor)
        por_arquivo[ln.arquivo].append(row)
        for c in ln.componentes:
            por_arquivo["rastro.csv"].append(
                {
                    "id_saida": ln.id_saida,
                    "arquivo_origem": c.arquivo_origem,
                    "ref_origem": c.ref_origem,
                    "valor": _fmt(c.valor),
                }
            )

    contagem = {}
    for nome, rows in por_arquivo.items():
        with open(output_dir / nome, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=OUTPUT_FILES[nome], delimiter=";", restval="", lineterminator="\n"
            )
            w.writeheader()
            w.writerows(rows)
        contagem[nome] = len(rows)
    return contagem
