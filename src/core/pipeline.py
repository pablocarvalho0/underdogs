"""Motor de execução da conciliação financeira Tarvo."""

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

    resultados = [t.rodar(dados, cadastro, premissas) for t in (checkout, remessa, extratos)]
    linhas = [ln for r in resultados for ln in r.linhas]
    contagem = escrever(linhas, Path(output_dir))

    return {
        "arquivos": contagem,
        "conservacao": {r.trilha: r.conservacao for r in resultados},
    }
