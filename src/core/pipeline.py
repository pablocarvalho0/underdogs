"""Motor de execução da conciliação financeira Tarvo."""

import json
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core import entrada
from src.core.cadastro import montar_cadastro
from src.core.entrada import carregar
from src.core.writer import escrever
from src.premissas import PREMISSAS, Premissas
from src.trilhas import checkout, extratos, remessa


def run_pipeline(
    input_dir: Path, output_dir: Path, premissas: Premissas = PREMISSAS
) -> dict[str, Any]:
    """Carrega o data pack de `input_dir`, roda as 3 trilhas e grava os 6 CSVs em `output_dir`."""
    dados = carregar(Path(input_dir))
    cadastro = montar_cadastro(dados.taxas, premissas)

    inicio = datetime.now()
    resultados = [t.rodar(dados, cadastro, premissas) for t in (checkout, remessa, extratos)]
    linhas = [ln for r in resultados for ln in r.linhas]
    _nomes_reais(linhas, dados.arquivos)
    contagem = escrever(linhas, Path(output_dir))

    resultado = {
        "arquivos": contagem,
        "conservacao": {r.trilha: r.conservacao for r in resultados},
    }
    _registrar_execucao(Path(input_dir), Path(output_dir), dados, inicio, resultado)
    return resultado


def _nomes_reais(linhas: list[Any], arquivos: dict[str, str]) -> None:
    """P-19: se a fonte veio com outro nome, o rastro aponta para o arquivo que de fato foi lido."""
    padrao = {
        entrada.ARQ_TAXAS: "taxas",
        entrada.ARQ_PONTE: "ponte",
        entrada.ARQ_FENIX: "plano_contas",
        entrada.ARQ_AURORA: "aurora",
        entrada.ARQ_MERIDIANO: "meridiano",
    }
    troca = {nome: arquivos[papel] for nome, papel in padrao.items() if arquivos.get(papel, nome) != nome}
    if not troca:
        return
    for ln in linhas:
        ln.componentes = [
            replace(c, arquivo_origem=troca.get(c.arquivo_origem, c.arquivo_origem)) for c in ln.componentes
        ]


def _registrar_execucao(input_dir: Path, output_dir: Path, dados: Any, inicio: datetime, resultado: dict) -> None:
    """L-10: registro de cada execução — arquivos que entraram, linhas de cada um, data e hora."""
    orbe = dados.orbe
    linhas_entrada: dict[str, int] = {}
    if "arquivo_origem" in orbe.columns:
        linhas_entrada.update({str(k): int(v) for k, v in orbe["arquivo_origem"].value_counts().sort_index().items()})
    for nome in ("taxas", "ponte", "plano_contas", "aurora", "meridiano"):
        df = getattr(dados, nome, None)
        if df is not None:
            linhas_entrada[nome] = len(df)
    registro = {
        "executado_em": inicio.isoformat(timespec="seconds"),
        "pasta_entrada": os.path.relpath(input_dir) if input_dir.resolve().is_relative_to(Path.cwd()) else input_dir.name,
        "arquivos_na_pasta": sorted(p.name for p in input_dir.iterdir() if p.is_file()),
        "linhas_lidas": linhas_entrada,
        "linhas_por_saida": resultado["arquivos"],
        "conservacao": {t: {k: str(v) for k, v in inv.items()} for t, inv in resultado["conservacao"].items()},
    }
    with open(output_dir / "registro_execucao.json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
