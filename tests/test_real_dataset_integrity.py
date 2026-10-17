"""Testes de integridade e completude das regras contra o Data Pack real de Setembro/2026.

Este arquivo complementa a suíte caixa-preta sintética, garantindo que
os contratos de negócio do mês real (1943 transações Orbe, 230 remessas,
planilha de taxas com renegociação em 15/09, extratos bancários e ERP Fênix)
não quebrem ao rodar a solução final.
"""

from datetime import datetime
import pandas as pd
import pytest

from src.loaders import (
    load_orbe_report,
    load_taxas_contratadas,
    load_ponte_cambio_report,
    load_plano_de_contas,
    load_extrato_aurora,
    load_extrato_meridiano,
)


def test_orbe_real_modalidades_e_lancamentos():
    """Valida que o relatório real da Orbe tem todos os 4 tipos de lançamentos esperados."""
    df_orbe = load_orbe_report()
    tipos = set(df_orbe["tipo_lancamento"].dropna().unique())
    assert "VENDA" in tipos
    assert "ESTORNO" in tipos
    assert "ANTECIPACAO" in tipos
    assert "REVERSAO ANTECIPACAO" in tipos
    assert len(df_orbe) == 1943


def test_taxas_renegociacao_temporal_bridge():
    """Valida que a planilha de taxas possui a renegociação da Bridge Idiomas em 15/09."""
    df_taxas = load_taxas_contratadas()
    bridge_rows = df_taxas[df_taxas["Lojista"].str.contains("Bridge", case=False, na=False)]
    assert len(bridge_rows) >= 2, "Bridge Idiomas deve conter ao menos duas vigências na planilha de taxas"


def test_ponte_cambio_spread_negativo_existente():
    """Valida que o relatório de câmbio contém casos de spread negativo a serem isolados em pendências."""
    df_ponte = load_ponte_cambio_report()
    spread_col = [c for c in df_ponte.columns if "spread" in c.lower()]
    assert len(spread_col) > 0, "Coluna de spread não encontrada no relatório da Ponte Câmbio"
    col_name = spread_col[0]
    # Converter para float
    spreads = pd.to_numeric(df_ponte[col_name].astype(str).str.replace(".", "").str.replace(",", "."), errors="coerce")
    negativos = spreads[spreads < 0]
    assert len(negativos) > 0, "Deve haver operações com spread negativo no dataset real da Ponte Câmbio"


def test_plano_de_contas_fenix_contas_chave():
    """Valida presença das contas contábeis obrigatórias para classificação de extrato."""
    df_fenix = load_plano_de_contas()
    contas = set(df_fenix["COD_CONTA"].astype(str).str.strip())
    # Contas de Banco/Disponibilidades
    assert any(c.startswith("1.1.01") for c in contas), "Conta de caixa/bancos ausente no plano Fênix"
    # Contas de Repasses a Lojistas (Passivo Circulante)
    assert any(c.startswith("2.1.01") for c in contas), "Conta de repasses a lojistas ausente"
    # Contas de Tarifas e Despesas Bancárias (Resultado - Grupo 4)
    assert any(c.startswith("4.2") or c.startswith("4.1") for c in contas), "Conta de despesas/tarifas ausente"


def test_extratos_ref_origem_formatos():
    """Valida formatação estrita de ref_origem para Aurora (L8, L9...) e Meridiano (FITID)."""
    df_aurora = load_extrato_aurora()
    assert all(r.startswith("L") and r[1:].isdigit() for r in df_aurora["linha_fisica"]), (
        "Todas as ref_origem do Aurora devem seguir o formato L{numero_linha}"
    )

    df_meridiano = load_extrato_meridiano()
    assert all(len(str(f).strip()) > 0 for f in df_meridiano["fitid"]), (
        "Todas as transações do Meridiano devem ter FITID não nulo"
    )
