"""Motor de execução da conciliação financeira Tarvo."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

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
    contagem = escrever(linhas, Path(output_dir))

    resultado = {
        "arquivos": contagem,
        "conservacao": {r.trilha: r.conservacao for r in resultados},
    }
    _registrar_execucao(Path(input_dir), Path(output_dir), dados, inicio, resultado)
    return resultado


def _registrar_execucao(input_dir: Path, output_dir: Path, dados: Any, inicio: datetime, resultado: dict) -> None:
    """L-10: registro de cada execução — arquivos que entraram, linhas de cada um, data e hora."""
    orbe = dados.orbe
    linhas_entrada: dict[str, int] = {}
    if "arquivo_origem" in orbe.columns:
        linhas_entrada.update({str(k): int(v) for k, v in orbe["arquivo_origem"].value_counts().sort_index().items()})
    for nome in ("taxas", "ponte", "plano_contas", "aurora", "meridiano"):
        df = getattr(dados, nome, None)
        if df is not None:
            linhas_entrada[nome] = int(len(df))
    registro = {
        "executado_em": inicio.isoformat(timespec="seconds"),
        "pasta_entrada": str(input_dir),
        "arquivos_na_pasta": sorted(p.name for p in input_dir.iterdir() if p.is_file()),
        "linhas_lidas": linhas_entrada,
        "linhas_por_saida": resultado["arquivos"],
        "conservacao": {t: {k: str(v) for k, v in inv.items()} for t, inv in resultado["conservacao"].items()},
    }
    with open(output_dir / "registro_execucao.json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
