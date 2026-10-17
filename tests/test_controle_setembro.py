"""Controle independente de setembro (HIPOTESES.md §5, plano-construcao §7 e §8), 01 + 06.

Não é a suíte caixa-preta: confere a saída do pipeline contra a prévia calculada fora
do `src/`, guardada em `controle/esperado_setembro.json` (a mesma que a página de
conferência mostra). Diferença aqui é para investigar, não para ajustar o número no código.
"""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.conferencia import (
    carregar_esperado,
    comparar_pendencias,
    comparar_totais,
    ler_saida,
)
from src.config import DATA_PACK_DIR
from src.core.pipeline import run_pipeline

ESPERADO = carregar_esperado()


@pytest.fixture(scope="module")
def saida(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pd.DataFrame]:
    out = tmp_path_factory.mktemp("saida")
    res = run_pipeline(DATA_PACK_DIR, out)
    for trilha, inv in res["conservacao"].items():
        assert all(v == 0 for v in inv.values()), (trilha, inv)
    return ler_saida(Path(out))


@pytest.mark.parametrize("item", [t["item"] for t in ESPERADO["totais"]])
def test_totais(saida: dict[str, pd.DataFrame], item: str) -> None:
    linha = next(t for t in comparar_totais(saida, ESPERADO) if t["item"] == item)
    assert linha["ok"], f"{item}: esperado {linha['esperado']}, gerado {linha['gerado']}"


def test_pendencias_esperadas_e_sem_sobra(saida: dict[str, pd.DataFrame]) -> None:
    pends, sobrando = comparar_pendencias(saida, ESPERADO)
    erradas = [(p["id_saida"], p["esperado"], p["gerado"]) for p in pends if not p["ok"]]
    assert not erradas, erradas
    assert not sobrando, sobrando


def test_rastro_fecha(saida: dict[str, pd.DataFrame]) -> None:
    rastro = saida["rastro.csv"]
    somas = rastro.groupby("id_saida")["valor"].apply(lambda s: sum(map(Decimal, s), Decimal(0)))
    for nome, col in [
        ("comissoes_por_lojista.csv", "comissao_brl"),
        ("divergencias_taxa.csv", "diferenca_brl"),
        ("notas_a_emitir.csv", "valor_brl"),
        ("lancamentos_classificados.csv", "valor"),
    ]:
        df = saida[nome]
        for ids, v in zip(df.id_saida, df[col]):
            assert somas[ids] == Decimal(v), (nome, ids)
