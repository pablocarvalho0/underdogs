"""Motor de execução da conciliação financeira Tarvo."""

from pathlib import Path
from typing import Dict, Any


def run_pipeline(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Executa o pipeline completo de conciliação lendo os arquivos de input_dir
    e gravando os 6 arquivos CSV auditáveis em output_dir.
    
    Esta função deve ser implementada no código de negócio sem alterar
    os testes imutáveis de caixa-preta.
    """
    raise NotImplementedError(
        "O pipeline de conciliação ainda não foi implementado em src/core/pipeline.py. "
        "Construa a lógica em src/ para fazer a suíte de testes passar!"
    )
