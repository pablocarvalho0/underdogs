"""Testes de integridade e completude das regras contra o Data Pack real de Setembro/2026.

Este arquivo complementa a suíte caixa-preta sintética, garantindo que
os contratos de negócio do mês real (1.943 transações no 01 e 14 no 06 da Orbe;
233 linhas da Ponte, 232 operações únicas,
planilha de taxas com renegociação em 15/09, extratos bancários e ERP Fênix)
não quebrem ao rodar a solução final.
"""

from decimal import Decimal

import pandas as pd

from src.loaders import (
    load_extrato_aurora,
    load_extrato_meridiano,
    load_orbe_report,
    load_plano_de_contas,
    load_ponte_cambio_report,
    load_taxas_contratadas,
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
    """O relatório da Ponte tem 4 operações com spread negativo, somando -R$ 1.834,05 (R-14)."""
    df_ponte = load_ponte_cambio_report()
    unicas = df_ponte.drop_duplicates("Nº Operação")
    spreads = pd.to_numeric(unicas["Spread R$"], errors="raise")
    negativos = spreads[spreads < 0]
    assert len(negativos) == 4
    assert round(Decimal(str(negativos.sum())), 2) == Decimal("-1834.05")


def test_ponte_linhas_e_operacoes_unicas():
    """233 linhas no relatório e 232 Nº Operação únicos: PC-0926-0162 vem repetida (R-13)."""
    df_ponte = load_ponte_cambio_report()
    assert len(df_ponte) == 233
    assert df_ponte["Nº Operação"].nunique() == 232
    repetidas = df_ponte[df_ponte.duplicated("Nº Operação", keep=False)]["Nº Operação"].unique()
    assert list(repetidas) == ["PC-0926-0162"]


def test_orbe_01_mais_06_pela_descoberta():
    """O caminho do pipeline acha os dois arquivos da Orbe pelo conteúdo: 1.943 + 14 = 1.957 (R-43)."""
    from src.config import DATA_PACK_DIR
    from src.core.entrada import carregar

    orbe = carregar(DATA_PACK_DIR).orbe
    assert len(orbe) == 1957
    por_arquivo = orbe["arquivo_origem"].value_counts().to_dict()
    assert por_arquivo == {
        "01_orbe_relatorio_comissoes_set2026.csv": 1943,
        "06_orbe_ajustes_tardios_set2026.csv": 14,
    }


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
