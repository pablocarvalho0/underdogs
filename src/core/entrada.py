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
ARQ_ORBE = config.ORBE_CSV.name
ARQ_TAXAS = config.TAXAS_XLSX.name
ARQ_PONTE = config.PONTE_EML.name
ARQ_FENIX = config.FENIX_ERP_CSV.name
ARQ_AURORA = config.AURORA_CSV.name
ARQ_MERIDIANO = config.MERIDIANO_OFX.name


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
        orbe=load_orbe_report(input_dir / ARQ_ORBE),
        taxas=load_taxas_contratadas(input_dir / ARQ_TAXAS),
        ponte=load_ponte_cambio_report(input_dir / ARQ_PONTE),
        plano_contas=load_plano_de_contas(input_dir / ARQ_FENIX),
        aurora=load_extrato_aurora(input_dir / ARQ_AURORA),
        meridiano=load_extrato_meridiano(input_dir / ARQ_MERIDIANO),
    )
