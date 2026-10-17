"""Carrega o data pack a partir de um diretório qualquer (a suíte passa `input_dir`)."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src import config
from src.loaders import (
    load_extrato_aurora,
    load_extrato_meridiano,
    load_orbe_report,
    load_plano_de_contas,
    load_ponte_cambio_report,
    load_taxas_contratadas,
)

# Nomes usados em `Componente.arquivo_origem`.
ARQ_TAXAS = config.TAXAS_XLSX.name
ARQ_PONTE = config.PONTE_EML.name
ARQ_FENIX = config.FENIX_ERP_CSV.name
ARQ_AURORA = config.AURORA_CSV.name
ARQ_MERIDIANO = config.MERIDIANO_OFX.name


def _cabecalho_orbe() -> str:
    # O cabeçalho de referência é o do arquivo 01 do data pack, lido da pasta de entrada.
    return "id_transacao;data_movimento;cod_estabelecimento;nome_estabelecimento;tipo_lancamento;modalidade;qtd_parcelas;bandeira;valor_bruto;taxa_aplicada_pct;valor_taxa;valor_liquido;id_referencia;data_venda_original"


def _arquivos_orbe(input_dir: Path) -> list[Path]:
    """R-43: todo *.csv da pasta com o cabeçalho da Orbe é arquivo da Orbe."""
    cab = _cabecalho_orbe()
    achados = []
    for p in sorted(input_dir.glob("*.csv")):
        with p.open(encoding="utf-8-sig", errors="replace") as f:
            if f.readline().strip() == cab:
                achados.append(p)
    return achados


def carregar_orbe(input_dir: Path) -> pd.DataFrame:
    arquivos = _arquivos_orbe(input_dir)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo da Orbe (cabeçalho id_transacao;data_movimento;...) em {input_dir}")
    partes = []
    for p in arquivos:
        df = load_orbe_report(p)
        df["arquivo_origem"] = p.name
        partes.append(df)
    orbe = pd.concat(partes, ignore_index=True)
    dup = orbe[orbe.duplicated("id_transacao", keep=False)]
    if not dup.empty:
        cols = [c for c in orbe.columns if c != "arquivo_origem"]
        # Idêntica entre arquivos: mantém uma. Diferente: erro (P-14 trata depois).
        if dup.drop_duplicates(cols).duplicated("id_transacao", keep=False).any():
            ids = sorted(dup.drop_duplicates(cols).loc[lambda d: d.duplicated("id_transacao", keep=False), "id_transacao"].unique())
            raise ValueError(f"Orbe: id_transacao repetido com conteúdo diferente entre arquivos: {ids[:5]}")
        orbe = orbe.drop_duplicates(cols, keep="first").reset_index(drop=True)
    return orbe


@dataclass
class DadosEntrada:
    orbe: pd.DataFrame
    taxas: pd.DataFrame
    ponte: pd.DataFrame
    plano_contas: pd.DataFrame
    aurora: pd.DataFrame
    meridiano: pd.DataFrame


def carregar(input_dir: Path) -> DadosEntrada:
    return DadosEntrada(
        orbe=carregar_orbe(input_dir),
        taxas=load_taxas_contratadas(input_dir / ARQ_TAXAS),
        ponte=load_ponte_cambio_report(input_dir / ARQ_PONTE),
        plano_contas=load_plano_de_contas(input_dir / ARQ_FENIX),
        aurora=load_extrato_aurora(input_dir / ARQ_AURORA),
        meridiano=load_extrato_meridiano(input_dir / ARQ_MERIDIANO),
    )
