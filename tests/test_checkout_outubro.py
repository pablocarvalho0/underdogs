"""Robustez para outubro: arquivo extra da Orbe, estorno órfão (R-51), encoding (R-42).

Dados sintéticos em diretório temporário: o data pack é copiado e alterado só na cópia.
"""

import shutil
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.config import DATA_PACK_DIR
from src.core.pipeline import run_pipeline
from src.premissas import PREMISSAS

CABECALHO_ORBE = (
    "id_transacao;data_movimento;cod_estabelecimento;nome_estabelecimento;tipo_lancamento;"
    "modalidade;qtd_parcelas;bandeira;valor_bruto;taxa_aplicada_pct;valor_taxa;valor_liquido;"
    "id_referencia;data_venda_original"
)
CSVS = (
    "comissoes_por_lojista.csv",
    "divergencias_taxa.csv",
    "notas_a_emitir.csv",
    "lancamentos_classificados.csv",
    "pendencias.csv",
    "rastro.csv",
)


def _rodar(pack: Path, out: Path) -> dict[str, pd.DataFrame]:
    res = run_pipeline(pack, out)
    for trilha, inv in res["conservacao"].items():
        assert all(v == 0 for v in inv.values()), (trilha, inv)
    return {n: pd.read_csv(out / n, sep=";", dtype=str, keep_default_na=False) for n in CSVS}


def _copiar_pack(tmp: Path) -> Path:
    pack = tmp / "pack"
    shutil.copytree(DATA_PACK_DIR, pack)
    return pack


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pd.DataFrame]:
    return _rodar(DATA_PACK_DIR, tmp_path_factory.mktemp("base"))


def _comissao(saida: dict[str, pd.DataFrame], id_saida: str) -> Decimal:
    df = saida["comissoes_por_lojista.csv"]
    return Decimal(df.loc[df.id_saida == id_saida, "comissao_brl"].iloc[0])


def test_setembro_sem_original_ausente(base: dict[str, pd.DataFrame]) -> None:
    # Os 9 estornos de agosto apontam para ids ausentes, mas a venda é de agosto: sem alarme.
    assert "ORIGINAL_AUSENTE" not in set(base["pendencias.csv"].tipo)
    assert "LINHA_IGNORADA_AURORA" not in set(base["pendencias.csv"].tipo)


def test_estorno_orfao_do_mes_abate_e_gera_pendencia(
    tmp_path: Path, base: dict[str, pd.DataFrame]
) -> None:
    pack = _copiar_pack(tmp_path)
    (pack / "07_orbe_ajuste_extra_set2026.csv").write_text(
        CABECALHO_ORBE
        + "\nTX99999901;30/09/2026;1041180753;MAPLE STUDY ASSESSORIA;ESTORNO;DEBITO;1;VISA;"
        "-1000,00;1,49;-14,90;-985,10;TX99999999;10/09/2026\n",
        encoding="utf-8",
    )
    saida = _rodar(pack, tmp_path / "out")

    pend = saida["pendencias.csv"]
    orf = pend[pend.tipo == "ORIGINAL_AUSENTE"]
    assert list(orf.id_saida) == ["PEN-CHK-ORIGINAL-AUSENTE-1041180753"]
    assert orf.ref_origem.iloc[0] == "TX99999901"
    assert Decimal(orf.valor_brl.iloc[0]) == Decimal("-1000.00")
    assert "pedir à Orbe" in orf.motivo.iloc[0]

    # Abatimento pelo valor que veio, com rastro para o arquivo extra.
    ids = [i for i in saida["comissoes_por_lojista.csv"].id_saida if i.startswith("COM-CHK-")]
    deltas = {i: _comissao(saida, i) - _comissao(base, i) for i in ids}
    mudou = {i: d for i, d in deltas.items() if d != 0}
    assert len(mudou) == 1
    ((id_com, delta),) = mudou.items()
    assert delta == Decimal("-14.90")
    rastro = saida["rastro.csv"]
    linha = rastro[(rastro.id_saida == id_com) & (rastro.ref_origem == "TX99999901")]
    assert list(linha.arquivo_origem) == ["07_orbe_ajuste_extra_set2026.csv"]

    # Só uma pendência nova; o resto de setembro igual.
    assert set(pend.id_saida) - set(base["pendencias.csv"].id_saida) == set(orf.id_saida)


def test_orbe_e_aurora_em_cp1252_dao_o_mesmo_resultado(
    tmp_path: Path, base: dict[str, pd.DataFrame]
) -> None:
    pack = _copiar_pack(tmp_path)
    ajuste = next(pack.glob("06_*.csv"))
    texto = ajuste.read_text(encoding="utf-8")
    # Acento no nome (o 01 já fixou o nome de cada EC) obriga o fallback para cp1252.
    assert "INTERCAMBIO" in texto
    ajuste.write_bytes(texto.replace("INTERCAMBIO", "INTERCÂMBIO").encode("cp1252"))
    with pytest.raises(UnicodeDecodeError):
        ajuste.read_text(encoding="utf-8")
    aurora = next(pack.glob("05a_*.csv"))
    aurora.write_bytes(aurora.read_text(encoding="utf-8").encode("cp1252"))
    with pytest.raises(UnicodeDecodeError):
        aurora.read_text(encoding="utf-8")

    saida = _rodar(pack, tmp_path / "out")
    for nome in CSVS:
        pd.testing.assert_frame_equal(saida[nome], base[nome], obj=nome)


def test_linha_curta_do_aurora_vira_pendencia(tmp_path: Path) -> None:
    pack = _copiar_pack(tmp_path)
    aurora = next(pack.glob("05a_*.csv"))
    texto = aurora.read_text(encoding="utf-8")
    n = len(texto.splitlines()) + 1
    aurora.write_text(texto.rstrip("\n") + "\nlinha;truncada\n", encoding="utf-8")
    saida = _rodar(pack, tmp_path / "out")
    pend = saida["pendencias.csv"]
    curta = pend[pend.tipo == "LINHA_IGNORADA_AURORA"]
    assert len(curta) == 1
    assert f"L{n}" in curta.motivo.iloc[0]


def test_orbe_cobrando_abaixo_nao_manda_ressarcir(tmp_path: Path) -> None:
    # R-24: Maple não tem divergência em setembro; uma venda a 0,99% (contrato 1,49%).
    pack = _copiar_pack(tmp_path)
    (pack / "07_orbe_ajuste_extra_set2026.csv").write_text(
        CABECALHO_ORBE
        + "\nTX99999902;30/09/2026;1041180753;MAPLE STUDY ASSESSORIA;VENDA;DEBITO;1;VISA;"
        "1000,00;0,99;9,90;990,10;;\n",
        encoding="utf-8",
    )
    pend = _rodar(pack, tmp_path / "out")["pendencias.csv"]
    cont = pend[pend.id_saida == "PEN-CHK-CONTESTACAO-34671260000100"]
    assert Decimal(cont.valor_brl.iloc[0]) == Decimal("-5.00")
    assert "caso a caso" in cont.motivo.iloc[0]
    assert "ressarcir o lojista (R-22" not in cont.motivo.iloc[0]
    # Cobrança acima continua com o texto de contestar e ressarcir.
    acima = pend[(pend.tipo == "DIVERGENCIA_TAXA_ORBE") & (pend.id_saida != cont.id_saida.iloc[0])]
    assert all("ressarcir o lojista" in m for m in acima.motivo)


def test_alias_nao_confirmado_gera_pendencia(tmp_path: Path, base: dict[str, pd.DataFrame]) -> None:
    aliases = dict(PREMISSAS.aliases_ec)
    aliases["1038867654"] = replace(aliases["1038867654"], confirmado_financeiro=False)
    saida_ = run_pipeline(DATA_PACK_DIR, tmp_path, replace(PREMISSAS, aliases_ec=aliases))
    assert saida_ is not None
    pend = pd.read_csv(tmp_path / "pendencias.csv", sep=";", dtype=str, keep_default_na=False)
    novas = set(pend.id_saida) - set(base["pendencias.csv"].id_saida)
    assert novas == {"PEN-CHK-ALIAS-1038867654"}
    com = pd.read_csv(
        tmp_path / "comissoes_por_lojista.csv", sep=";", dtype=str, keep_default_na=False
    )
    pd.testing.assert_frame_equal(com, base["comissoes_por_lojista.csv"])
