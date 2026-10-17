"""Testes automatizados para os parsers de dados brutos."""

from decimal import Decimal

from src.loaders import (
    load_orbe_report,
    load_taxas_contratadas,
    load_ponte_cambio_report,
    load_plano_de_contas,
    load_extrato_aurora,
    load_extrato_meridiano,
)


def test_load_orbe_report():
    df = load_orbe_report()
    assert len(df) == 1943
    assert "id_transacao" in df.columns
    assert "valor_bruto" in df.columns
    # Valores em Decimal a partir do texto cru (sem passar por float).
    assert all(isinstance(v, Decimal) for v in df["valor_bruto"])


def test_load_taxas_contratadas():
    df = load_taxas_contratadas()
    assert len(df) >= 20
    assert "cnpj_limpo" in df.columns
    # Todos os CNPJs limpos devem ter 14 dígitos
    valid_cnpjs = df["cnpj_limpo"].dropna()
    assert all(len(c) == 14 for c in valid_cnpjs)


def test_load_ponte_cambio_report():
    df = load_ponte_cambio_report()
    assert len(df) > 200
    assert "Nº Operação" in df.columns
    assert "cnpj_limpo" in df.columns


def test_load_plano_de_contas():
    df = load_plano_de_contas()
    assert len(df) >= 50
    assert "COD_CONTA" in df.columns
    assert "DESCRICAO" in df.columns


def test_load_extratos():
    df_aurora = load_extrato_aurora()
    assert len(df_aurora) > 50
    assert df_aurora["linha_fisica"].iloc[0].startswith("L")

    df_meridiano = load_extrato_meridiano()
    assert len(df_meridiano) == 100
    assert "fitid" in df_meridiano.columns
