"""Remessa "roda em outubro sem retrabalho": ajuste da Ponte (R-18, Q-04), duplicata com
conteúdo diferente, operação de outro mês (R-16) e spread contratado com vigência.

Dados sintéticos montados aqui mesmo, sem tocar no data pack.
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.core.cadastro import CadastroPlanilha
from src.core.entrada import PONTE, DadosEntrada
from src.core.model import LinhaSaida, ResultadoTrilha
from src.premissas import PREMISSAS
from src.trilhas import remessa

ARQ = "03_email_ponte_cambio_relatorio_out2026.eml"
CNPJ = "11111111000111"


def _taxas() -> pd.DataFrame:
    # Renegociação no meio do mês: 1,50% até 14/10 e 2,00% a partir de 15/10.
    return pd.DataFrame(
        [
            {"cnpj_limpo": CNPJ, "EC Orbe": "900001", "Lojista": "Lojista Teste",
             "Obs": None, "Vigência": "até 14/10/2026", "Spread remessa": "1,50%"},
            {"cnpj_limpo": CNPJ, "EC Orbe": "900001", "Lojista": "Lojista Teste (NOVA)",
             "Obs": None, "Vigência": "a partir de 15/10/2026", "Spread remessa": "2,00%"},
        ]
    )  # fmt: skip


def _op(nop: str, dia: str, spread: float, obs: str | None = None, linha: int = 0) -> dict:
    return {
        "Nº Operação": nop,
        "Data Contratação": pd.Timestamp(dia),
        "CNPJ Cliente": CNPJ,
        "Cliente": "LOJISTA TESTE",
        "Valor ME": 10000.0,
        "PTAX Ref.": 5.0,
        "Spread R$": spread,
        "Spread %": 0.015,
        "Observação": obs,
        "linha_planilha": linha,
        "cnpj_limpo": CNPJ,
    }


def _ponte() -> pd.DataFrame:
    linhas = [
        _op("PC-1026-0001", "2026-10-05", 750.0),  # 1,50% contratado em 05/10: sem divergência
        _op("PC-1026-0002", "2026-10-20", 750.0),  # 2,00% contratado em 20/10: divergência
        _op("PC-1026-0003", "2026-10-07", -235.74, "AJUSTE REF PC-0926-0434"),
        _op("PC-1026-0004", "2026-10-08", -100.0, "Taxa travada no pedido (D-1)"),
        _op("PC-1026-0005", "2026-10-09", 50.0),
        _op("PC-1026-0005", "2026-10-09", 50.0, "reprocessada"),  # cópia idêntica
        _op("PC-1026-0006", "2026-10-10", 80.0),
        _op("PC-1026-0006", "2026-10-10", 90.0),  # cópia com valor diferente
        _op("PC-0926-0999", "2026-09-29", 60.0),  # outro mês
    ]
    for i, r in enumerate(linhas, start=5):
        r["linha_planilha"] = i
    df = pd.DataFrame(linhas)
    df.attrs["corpo_email"] = ""
    return df


@pytest.fixture(scope="module")
def cadastro() -> CadastroPlanilha:
    return CadastroPlanilha(_taxas(), PREMISSAS)


@pytest.fixture(scope="module")
def res(cadastro: CadastroPlanilha) -> ResultadoTrilha:
    vazio = pd.DataFrame()
    dados = DadosEntrada(
        orbe=vazio, taxas=_taxas(), ponte=_ponte(), plano_contas=vazio,
        aurora=vazio, meridiano=vazio, arquivos={PONTE: ARQ},
    )  # fmt: skip
    return remessa.rodar(dados, cadastro, PREMISSAS)


def _linha(res: ResultadoTrilha, id_saida: str) -> LinhaSaida:
    return next(ln for ln in res.linhas if ln.id_saida == id_saida)


def test_conservacao_fecha(res: ResultadoTrilha) -> None:
    assert all(v == 0 for v in res.conservacao.values()), res.conservacao


def test_ajuste_entra_na_comissao_e_abate_50pct(res: ResultadoTrilha) -> None:
    com = _linha(res, f"COM-REM-{CNPJ}")
    # 375 + 375 (normais) − 117,87 (ajuste: 50% de 235,74) + 25 (duplicata idêntica, 1 vez)
    assert com.valor == Decimal("657.13")
    aj = [c for c in com.componentes if c.valor == Decimal("-117.87")]
    assert len(aj) == 1 and aj[0].ref_origem == "PC-0926-0434" and aj[0].arquivo_origem == ARQ
    nota = _linha(res, f"NF-REM-{PREMISSAS.cnpj_ponte_cambio}")
    assert nota.valor == Decimal("657.13")


def test_ajuste_gera_pendencia_q04_para_helena(res: ResultadoTrilha) -> None:
    pen = _linha(res, "PEN-REM-AJUSTE-PC-1026-0003")
    assert pen.campos["quem_decide"] == "Helena"
    assert pen.campos["ref_origem"] == "PC-0926-0434"
    assert pen.valor == Decimal("-117.87")
    motivo = pen.campos["motivo"]
    assert "Q-04" in motivo and "117,87" in motivo and "235,74" in motivo


def test_so_negativo_que_nao_e_ajuste_vai_para_spread_negativo(res: ResultadoTrilha) -> None:
    neg = _linha(res, f"PEN-REM-SPREADNEG-{CNPJ}")
    assert neg.campos["ref_origem"] == "PC-1026-0004"
    assert neg.valor == Decimal(-100)
    assert "1 operação com spread negativo" in neg.campos["motivo"]


def test_duplicata_identica_conta_uma_vez(res: ResultadoTrilha) -> None:
    dup = _linha(res, "PEN-REM-DUPLICATA")
    assert dup.campos["ref_origem"] == "PC-1026-0005"
    assert dup.valor == Decimal(50)
    assert "1 operação repetida" in dup.campos["motivo"]


def test_duplicata_divergente_fica_fora_e_vai_para_a_ponte(res: ResultadoTrilha) -> None:
    pen = _linha(res, "PEN-REM-DUPLICATA-DIVERGENTE")
    assert pen.campos["quem_decide"] == PREMISSAS.nome_ponte_cambio
    assert pen.campos["ref_origem"] == "PC-1026-0006"
    assert pen.valor == Decimal(170)
    assert "80.0" in pen.campos["motivo"] and "90.0" in pen.campos["motivo"]
    com = _linha(res, f"COM-REM-{CNPJ}")
    assert all(c.ref_origem != "PC-1026-0006" for c in com.componentes)


def test_operacao_de_outro_mes_fica_fora(res: ResultadoTrilha) -> None:
    pen = _linha(res, f"PEN-REM-OUTRO-MES-{CNPJ}")
    assert pen.campos["quem_decide"] == "Helena"
    assert pen.campos["ref_origem"] == "PC-0926-0999"
    assert "outro mês" in pen.campos["motivo"]
    com = _linha(res, f"COM-REM-{CNPJ}")
    assert all(c.ref_origem != "PC-0926-0999" for c in com.componentes)


def test_spread_contratado_pela_vigencia(cadastro: CadastroPlanilha, res: ResultadoTrilha) -> None:
    assert cadastro.spread_contratado_pct(CNPJ, date(2026, 10, 5)) == Decimal("1.5")
    assert cadastro.spread_contratado_pct(CNPJ, date(2026, 10, 20)) == Decimal(2)
    assert cadastro.spread_contratado_pct(CNPJ) == Decimal(2)  # sem data: a última linha
    divs = [ln for ln in res.linhas if ln.arquivo == "divergencias_taxa.csv"]
    assert [d.campos["ref_origem"] for d in divs] == ["PC-1026-0002"]
    assert divs[0].valor == Decimal("-250.00")
