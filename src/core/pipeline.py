"""Motor de execução da conciliação financeira Tarvo."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.cadastro import montar_cadastro
from src.core.entrada import carregar
from src.core.pendencias import pendencia_de_aviso
from src.core.writer import escrever
from src.premissas import PREMISSAS, Premissas
from src.trilhas import checkout, extratos, remessa


def run_pipeline(
    input_dir: Path, output_dir: Path, premissas: Premissas = PREMISSAS
) -> dict[str, Any]:
    """Carrega o data pack de `input_dir`, roda as 3 trilhas e grava os 6 CSVs em `output_dir`."""
    dados = carregar(Path(input_dir))
    cadastro = montar_cadastro(dados.taxas, premissas)

    resultados = [t.rodar(dados, cadastro, premissas) for t in (checkout, remessa, extratos)]
    linhas = [ln for r in resultados for ln in r.linhas]
    # R-42: o que faltou ou mudou na entrada vira pendência, e o resto fecha.
    linhas += [pendencia_de_aviso(a, i) for i, a in enumerate(dados.avisos, start=1)]
    contagem = escrever(linhas, Path(output_dir))

    resultado = {
        "arquivos": contagem,
        "arquivos_lidos": dados.arquivos,
        "avisos": dados.avisos,
        "conservacao": {r.trilha: r.conservacao for r in resultados},
    }
    _registrar_execucao(Path(input_dir), Path(output_dir), resultado)
    return resultado


def _registrar_execucao(input_dir: Path, output_dir: Path, resultado: dict[str, Any]) -> None:
    """L-10: registro de cada execução — arquivos que entraram, linhas de cada saída, data e hora."""
    pasta = os.path.relpath(input_dir) if input_dir.resolve().is_relative_to(Path.cwd()) else input_dir.name
    registro = {
        "executado_em": datetime.now().isoformat(timespec="seconds"),
        "pasta_entrada": pasta,
        "arquivos_na_pasta": sorted(p.name for p in input_dir.iterdir() if p.is_file()),
        **resultado,
    }
    with open(output_dir / "registro_execucao.json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2, default=str)
