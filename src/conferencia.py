"""Confere a saída contra a prévia independente do `HIPOTESES.md` §5.

O painel usa isso para responder "o nível Mínimo/Alvo está certo?" sem depender do
teste caixa-preta, que para na primeira asserção e não separa uma trilha da outra.
Os esperados são copiados da §5: se ela mudar, mude aqui também.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pandas as pd

ATLAS_EC = "1076801732"
ATLAS_CNPJ = "39566044000119"
CASA_CNPJ = "00520815000100"
MUNDO_ABERTO_CNPJ = "17217888000111"

# §5, tabela "O que o 06 muda": comissão com o 06, por CNPJ.
LOJISTAS_06 = {
    "23109187000161": ("Oxford Prep", "13845.71"),
    "34671260000100": ("Maple Study", "14165.77"),
    "16181276000153": ("EduAbroad", "11858.16"),
    "22224579000109": ("Bridge", "11769.74"),
    "68567965000102": ("Dublin Hub", "11876.37"),
    "17217888000111": ("Mundo Aberto", "18508.09"),
    "07752116000126": ("Kiwi", "10886.22"),
}
LINHAS_06 = 14  # soma da coluna "Linhas do 06" da mesma tabela


@dataclass
class Checagem:
    nivel: str
    item: str
    esperado: str
    obtido: str
    status: str  # "ok", "falhou" ou "pendente" (a saída ainda não tem essas linhas)


def _ler(saida: Path, nome: str) -> pd.DataFrame:
    try:
        return pd.read_csv(saida / nome, sep=";", dtype=str).fillna("")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def _soma(df: pd.DataFrame, col: str) -> Decimal:
    return sum((Decimal(v) for v in df[col]), Decimal(0))


def _valor(nivel: str, item: str, df: pd.DataFrame, col: str, esperado: str) -> Checagem:
    if df.empty:
        return Checagem(nivel, item, esperado, "sem linhas", "pendente")
    obtido = _soma(df, col)
    status = "ok" if obtido == Decimal(esperado) else "falhou"
    return Checagem(nivel, item, esperado, str(obtido), status)


def _contagem(nivel: str, item: str, df: pd.DataFrame, esperado: int) -> Checagem:
    if df.empty:
        return Checagem(nivel, item, str(esperado), "sem linhas", "pendente")
    status = "ok" if len(df) == esperado else "falhou"
    return Checagem(nivel, item, str(esperado), str(len(df)), status)


def _filtra(df: pd.DataFrame, col: str, valor: str) -> pd.DataFrame:
    return df[df[col] == valor] if not df.empty else df


def conferir(saida: Path) -> list[Checagem]:
    """Lê os 6 CSVs de `saida` e devolve uma checagem por número de controle da §5."""
    com = _ler(saida, "comissoes_por_lojista.csv")
    div = _ler(saida, "divergencias_taxa.csv")
    pen = _ler(saida, "pendencias.csv")
    ras = _ler(saida, "rastro.csv")

    chk = _filtra(com, "linha_negocio", "CHECKOUT")
    m = "Mínimo"
    out = [
        _valor(m, "Comissão CHECKOUT total, com o 06", chk, "comissao_brl", "203735.34"),
        _contagem(m, "Lojistas com comissão CHECKOUT (21, sem a Atlas)", chk, 21),
        _valor(
            m,
            "Casa do Estudante (só o estorno TX88445133)",
            _filtra(chk, "cnpj", CASA_CNPJ),
            "comissao_brl",
            "-5.50",
        ),
    ]
    for cnpj, (nome, esperado) in LOJISTAS_06.items():
        out.append(
            _valor(
                m, f"{nome} (muda com o 06)", _filtra(chk, "cnpj", cnpj), "comissao_brl", esperado
            )
        )

    atlas = (
        chk[(chk["cnpj"] == ATLAS_CNPJ) | chk["lojista"].str.contains("Atlas")]
        if not chk.empty
        else chk
    )
    out.append(
        Checagem(
            m,
            "Atlas fora da comissão (R-06, P-02)",
            "0 linhas",
            f"{len(atlas)} linhas",
            "ok" if atlas.empty else "falhou",
        )
    )

    ras_chk = (
        ras[ras["id_saida"].isin(chk["id_saida"])]
        if not chk.empty and not ras.empty
        else pd.DataFrame()
    )
    if ras_chk.empty:
        out.append(
            Checagem(
                m, "Rastro fecha com cada comissão CHECKOUT", "21/21", "sem rastro", "pendente"
            )
        )
    else:
        somas = {k: _soma(g, "valor") for k, g in ras_chk.groupby("id_saida")}
        batem = sum(
            somas.get(i, None) == Decimal(v) for i, v in zip(chk["id_saida"], chk["comissao_brl"])
        )
        out.append(
            Checagem(
                m,
                "Rastro fecha com cada comissão CHECKOUT",
                f"{len(chk)}/{len(chk)}",
                f"{batem}/{len(chk)}",
                "ok" if batem == len(chk) else "falhou",
            )
        )
        do_06 = ras_chk[ras_chk["arquivo_origem"].str.startswith("06_")]
        out.append(
            _contagem(m, "Linhas do 06 no rastro (prova de que o 06 entrou)", do_06, LINHAS_06)
        )

    a = "Alvo"
    div_chk = _filtra(div, "linha_negocio", "CHECKOUT")
    div_rem = _filtra(_filtra(div, "linha_negocio", "REMESSA"), "cnpj", MUNDO_ABERTO_CNPJ)
    pen_atlas = (
        pen[pen["ref_origem"].str.contains(ATLAS_EC) | pen["motivo"].str.contains("Atlas")]
        if not pen.empty
        else pen
    )
    ras_atlas = (
        ras[ras["id_saida"].isin(pen_atlas["id_saida"])] if not pen_atlas.empty else pen_atlas
    )
    out += [
        _valor(
            a,
            "Comissão REMESSA (228 operações, nota para a Ponte)",
            _filtra(com, "linha_negocio", "REMESSA"),
            "comissao_brl",
            "39543.45",
        ),
        _contagem(a, "Divergências CHECKOUT: linhas", div_chk, 92),
        _valor(a, "Divergências CHECKOUT: total", div_chk, "diferenca_brl", "1576.23"),
        _contagem(a, "Divergência REMESSA Mundo Aberto: operações", div_rem, 23),
        _valor(a, "Divergência REMESSA Mundo Aberto: total", div_rem, "diferenca_brl", "1418.85"),
        _contagem(a, "Pendência da Atlas: transações no rastro (P-02)", ras_atlas, 57),
    ]
    return out
