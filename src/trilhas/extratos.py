"""Trilha C — Extratos (Dev 2): classificação dos lançamentos Aurora e Meridiano no plano de contas e pendências.

Contrato: docs/plano-engenharia.md §2 e §4. Devolve linhas via `LinhaSaida.somando`
(componentes = linhas de origem) e preenche `conservacao` com o invariante da trilha.
"""

from src.core.cadastro import Cadastro
from src.core.entrada import DadosEntrada
from src.core.model import ResultadoTrilha
from src.premissas import Premissas


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    return ResultadoTrilha(trilha="extratos")
