"""Controle independente de setembro (HIPOTESES.md §5, plano-construcao §7), 01 + 06.

Não é a suíte caixa-preta: confere a saída do pipeline contra a prévia calculada fora
do `src/`. Diferença aqui é para investigar, não para ajustar o número no código.
"""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.config import DATA_PACK_DIR
from src.core.pipeline import run_pipeline


@pytest.fixture(scope="module")
def saida(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pd.DataFrame]:
    out = tmp_path_factory.mktemp("saida")
    res = run_pipeline(DATA_PACK_DIR, out)
    for trilha, inv in res["conservacao"].items():
        assert all(v == 0 for v in inv.values()), (trilha, inv)
    return {p.name: pd.read_csv(p, sep=";", dtype=str) for p in Path(out).glob("*.csv")}


def _soma(df: pd.DataFrame, col: str) -> Decimal:
    return sum((Decimal(v) for v in df[col]), Decimal(0))


def test_comissao_checkout(saida: dict[str, pd.DataFrame]) -> None:
    c = saida["comissoes_por_lojista.csv"]
    chk = c[c.linha_negocio == "CHECKOUT"]
    assert len(chk) == 21
    assert _soma(chk, "comissao_brl") == Decimal("203735.34")
    casa = chk[chk.cnpj == "00520815000100"]
    assert casa.comissao_brl.tolist() == ["-5.50"]


def test_notas(saida: dict[str, pd.DataFrame]) -> None:
    n = saida["notas_a_emitir.csv"]
    chk, rem = n[n.linha_negocio == "CHECKOUT"], n[n.linha_negocio == "REMESSA"]
    assert len(chk) == 20 and _soma(chk, "valor_brl") == Decimal("203740.84")
    assert rem.tomador_cnpj.tolist() == ["75374179000146"]
    assert rem.valor_brl.tolist() == ["39543.45"]


def test_divergencias(saida: dict[str, pd.DataFrame]) -> None:
    d = saida["divergencias_taxa.csv"]
    chk, rem = d[d.linha_negocio == "CHECKOUT"], d[d.linha_negocio == "REMESSA"]
    assert len(chk) == 92 and _soma(chk, "diferenca_brl") == Decimal("1576.23")
    assert len(rem) == 23 and _soma(rem, "diferenca_brl") == Decimal("1418.85")


def test_comissao_remessa(saida: dict[str, pd.DataFrame]) -> None:
    c = saida["comissoes_por_lojista.csv"]
    assert _soma(c[c.linha_negocio == "REMESSA"], "comissao_brl") == Decimal("39543.45")


def test_lancamentos(saida: dict[str, pd.DataFrame]) -> None:
    lan = saida["lancamentos_classificados.csv"]
    assert (lan.banco == "AURORA").sum() == 84 and (lan.banco == "MERIDIANO").sum() == 100


@pytest.mark.parametrize(
    "id_saida,valor",
    [
        ("PEN-CHK-SEMCONTRATO-1076801732", "7876.05"),
        ("PEN-CHK-DEVOLUCAO-00520815000100", "15396.77"),
        ("PEN-CHK-SEMNOTA-00520815000100", "-5.50"),
        ("PEN-CHK-CONTESTACAO-95927868000148", "1546.28"),
        ("PEN-CHK-CONTESTACAO-22224579000109", "29.95"),
        ("PEN-CHK-ALERTA-ANTECIPACAO-1076801732", "124235.32"),
        ("PEN-REM-CONTESTACAO-17217888000111", "1418.85"),
        ("PEN-EXT-NAOIDENT-L50", "7350.00"),
        ("PEN-EXT-DEVOLUCAO-L65", "12400.00"),
        ("PEN-EXT-TRANSF-L92", "-300000.00"),
    ],
)
def test_pendencias_esperadas(saida: dict[str, pd.DataFrame], id_saida: str, valor: str) -> None:
    p = saida["pendencias.csv"].set_index("id_saida")
    assert p.loc[id_saida, "valor_brl"] == valor


def test_spread_negativo(saida: dict[str, pd.DataFrame]) -> None:
    p = saida["pendencias.csv"]
    neg = p[p.tipo == "SPREAD_NEGATIVO"]
    assert len(neg) == 4 and _soma(neg, "valor_brl") == Decimal("-1834.05")


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
