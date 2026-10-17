"""Carrega o data pack a partir de um diretório qualquer (a suíte passa `input_dir`)."""

from dataclasses import dataclass, field
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
    cols = [c for c in orbe.columns if c != "arquivo_origem"]
    # P-14: linha idêntica entre arquivos conta uma vez.
    orbe = orbe.drop_duplicates(cols, keep="first").reset_index(drop=True)
    substituidas: list[tuple[dict, dict]] = []
    antigas = orbe.duplicated("id_transacao", keep="last")
    if antigas.any():
        # P-14: versão diferente vale a do arquivo mais recente (o ajuste, que vem depois na ordem
        # dos nomes); a substituída sai do cálculo e do rastro e vai para a pendência.
        novas = {r["id_transacao"]: r for r in orbe[~antigas].to_dict("records")}
        substituidas = [(r, novas[r["id_transacao"]]) for r in orbe[antigas].to_dict("records")]
        orbe = orbe[~antigas].reset_index(drop=True)
    orbe.attrs["substituidas"] = substituidas
    return orbe


@dataclass
class DadosEntrada:
    orbe: pd.DataFrame
    taxas: pd.DataFrame
    ponte: pd.DataFrame
    plano_contas: pd.DataFrame
    aurora: pd.DataFrame
    meridiano: pd.DataFrame
    # papel -> nome real do arquivo na pasta (vai para `Componente.arquivo_origem`)
    arquivos: dict[str, str] = field(default_factory=dict)


def _primeiras_linhas(p: Path, n: int = 6) -> str:
    try:
        with p.open(encoding="utf-8-sig", errors="replace") as f:
            return "".join(f.readline() for _ in range(n))
    except OSError:
        return ""


def descobrir(input_dir: Path) -> dict[str, Path]:
    """D-01, P-15: o nome de setembro é só o primeiro palpite; se não existir, o papel sai do conteúdo."""
    fixos = {"taxas": ARQ_TAXAS, "ponte": ARQ_PONTE, "plano_contas": ARQ_FENIX, "aurora": ARQ_AURORA, "meridiano": ARQ_MERIDIANO}
    achados = {papel: input_dir / nome for papel, nome in fixos.items() if (input_dir / nome).is_file()}
    arquivos = sorted(p for p in input_dir.iterdir() if p.is_file())
    criterios = {
        "taxas": lambda p: p.suffix.lower() == ".xlsx",
        "ponte": lambda p: p.suffix.lower() == ".eml",
        "meridiano": lambda p: p.suffix.lower() == ".ofx",
        "plano_contas": lambda p: p.suffix.lower() == ".csv" and "COD_CONTA" in _primeiras_linhas(p, 1),
        "aurora": lambda p: p.suffix.lower() == ".csv" and "aurora" in _primeiras_linhas(p).lower(),
    }
    for papel, ok in criterios.items():
        if papel not in achados:
            cand = [p for p in arquivos if p not in achados.values() and ok(p)]
            if cand:
                achados[papel] = cand[0]
    faltando = sorted(set(fixos) - set(achados))
    if faltando:
        # R-42: avisa com clareza qual fonte falta.
        raise FileNotFoundError(f"Fonte(s) não encontrada(s) em {input_dir}: {', '.join(faltando)}")
    return achados


def carregar(input_dir: Path) -> DadosEntrada:
    achados = descobrir(input_dir)
    orbe = carregar_orbe(input_dir)
    nomes = {papel: p.name for papel, p in achados.items()}
    nomes["orbe"] = ";".join(sorted(set(orbe["arquivo_origem"]))) if "arquivo_origem" in orbe.columns else ""
    return DadosEntrada(
        orbe=orbe,
        taxas=load_taxas_contratadas(achados["taxas"]),
        ponte=load_ponte_cambio_report(achados["ponte"]),
        plano_contas=load_plano_de_contas(achados["plano_contas"]),
        aurora=load_extrato_aurora(achados["aurora"]),
        meridiano=load_extrato_meridiano(achados["meridiano"]),
        arquivos=nomes,
    )
