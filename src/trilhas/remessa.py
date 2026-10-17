"""Trilha B — Remessa: dedup, spread negativo, comissão 50% do spread, divergência de spread,
NF única para a Ponte e pendências.

Regras: HIPOTESES.md §2.2, §2.3 (R-23) e §2.4 (R-27). Componente = Nº Operação no
arquivo do pacote (o .eml, P-10).
"""

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any

import pandas as pd

from src.core.cadastro import Cadastro
from src.core.entrada import PONTE, DadosEntrada, so_digitos
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.core.pendencias import pendencia
from src.premissas import Premissas
from src.trilhas.checkout import _brl_txt


def _dec(v: Any) -> Decimal:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return Decimal(0)
    return Decimal(str(v))


def _ops(n: int, adj: str = "") -> str:
    """Concordância: "1 operação", "2 operações" (com adjetivo opcional)."""
    if n == 1:
        return f"1 operação{' ' + adj if adj else ''}"
    return f"{n} operações{' ' + adj + 's' if adj else ''}"


# R-18: ajuste de contestação chega como linha nova com "AJUSTE REF PC-…" na Observação.
_AJUSTE = re.compile(r"^\s*AJUSTE\s+REF\s+(PC-[\w-]+)", re.IGNORECASE)
# Colunas que não contam para dizer se duas cópias do mesmo Nº são iguais.
_IGNORAR_NA_COPIA = {"Observação", "linha_planilha"}


def _igual(a: Any, b: Any) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return bool(a == b)


def _diferencas(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    return [k for k in a if k not in _IGNORAR_NA_COPIA and not _igual(a.get(k), b.get(k))]


def _txt(v: Any) -> str:
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return "vazio" if pd.isna(v) else str(v)


def _ponte_do_email(corpo: str, premissas: Premissas) -> tuple[str, str]:
    """Nome e CNPJ da Ponte pela assinatura do e-mail; fallback em premissas."""
    m = re.search(r"-\s*([^-\n]+?)\s*-\s*CNPJ\s*([\d./-]{14,18})", corpo or "")
    if m and len(so_digitos(m.group(2))) == 14:
        return m.group(1).strip(), so_digitos(m.group(2))
    return premissas.nome_ponte_cambio, premissas.cnpj_ponte_cambio


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="remessa")
    df = dados.ponte
    if df.empty:
        return res
    arq = dados.arquivos[PONTE]
    corpo = str(df.attrs.get("corpo_email", ""))
    nome_ponte, cnpj_ponte = _ponte_do_email(corpo, premissas)
    m = re.search(r"creditado em (\d{2}/\d{2}/\d{4})", corpo)
    data_repasse = m.group(1) if m else "data a confirmar"

    datas = pd.to_datetime(df["Data Contratação"], errors="coerce")
    comp = str(datas.dt.strftime("%Y-%m").mode().iloc[0]) if datas.notna().any() else ""

    registros = [{str(k): v for k, v in r.items()} for r in df.to_dict("records")]
    por_nop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in registros:
        por_nop[str(r["Nº Operação"]).strip()].append(r)
    # R-13: cópia idêntica (Observação à parte) conta uma vez. Cópia com valor diferente:
    # nenhuma entra na comissão até a Ponte dizer qual vale (premissa nova, ver HIPOTESES).
    divergentes = {
        nop: rs
        for nop, rs in por_nop.items()
        if len(rs) > 1 and any(_diferencas(rs[0], o) for o in rs[1:])
    }

    vistos: set[str] = set()
    comissao: dict[str, list[Componente]] = defaultdict(list)
    nome_de: dict[str, str] = {}
    contestar: dict[str, list[Componente]] = defaultdict(list)
    negativos: dict[str, list[tuple[Componente, Decimal]]] = defaultdict(list)
    repetidas: list[Componente] = []
    sem_cadastro: dict[str, list[Componente]] = defaultdict(list)
    ajustes: list[tuple[str, str, str, Componente, Decimal]] = []
    outro_mes: dict[str, list[Componente]] = defaultdict(list)
    copias_div: list[Componente] = []
    soma_total = soma_incl = soma_neg = soma_rep = soma_aj = soma_fora = soma_div = Decimal(0)
    n_incl = n_neg = n_rep = n_aj = n_fora = n_div = 0

    for r in registros:
        nop = str(r["Nº Operação"]).strip()
        spread = _dec(r["Spread R$"])
        soma_total += spread
        comp_spread = Componente(arq, nop, spread)

        if nop in divergentes:
            copias_div.append(comp_spread)
            soma_div += spread
            n_div += 1
            continue
        # R-13: Nº de operação é único; a cópia sai e vai para a Ponte corrigir.
        if nop in vistos:
            repetidas.append(comp_spread)
            soma_rep += spread
            n_rep += 1
            continue
        vistos.add(nop)

        cnpj = r.get("cnpj_limpo") or so_digitos(str(r.get("CNPJ Cliente")))
        loj = cadastro.lojista_por_cnpj(cnpj)
        nome_de.setdefault(cnpj, loj.nome if loj else str(r.get("Cliente") or "").strip())
        bruta = r.get("Data Contratação")
        data = pd.to_datetime(str(bruta) if bruta is not None else "", errors="coerce")

        # R-18, R-46: ajuste da Ponte entra no mês em que aparece e abate a participação
        # na nota única; o rastro aponta para a operação original. Q-04 aberta: tratamos o
        # Spread R$ como spread inteiro (cai 50%, como a R-11) e a Helena confirma.
        m_aj = _AJUSTE.match(str(r.get("Observação") or ""))
        if m_aj:
            original = m_aj.group(1).upper()
            parte = brl(spread * premissas.participacao_spread_tarvo)
            comp_aj = Componente(arq, original, parte)
            comissao[cnpj].append(comp_aj)
            ajustes.append((cnpj, nop, original, comp_aj, brl(spread)))
            soma_aj += spread
            n_aj += 1
            if loj is None:
                sem_cadastro[cnpj].append(comp_aj)
            continue

        # R-16: competência é a data de contratação; operação de outro mês não entra.
        if not isinstance(data, pd.Timestamp) or data.strftime("%Y-%m") != comp:
            outro_mes[cnpj].append(comp_spread)
            soma_fora += spread
            n_fora += 1
            continue

        contratado = cadastro.spread_contratado_pct(cnpj, data.date())  # pontos percentuais
        vme, ptax = _dec(r["Valor ME"]), _dec(r["PTAX Ref."])

        # R-14: spread negativo fora da comissão e da nota; dois valores na pendência.
        if spread < 0:
            ate_contrato = (
                brl(spread - contratado / 100 * vme * ptax) if contratado is not None else spread
            )
            negativos[cnpj].append((comp_spread, ate_contrato))
            soma_neg += spread
            n_neg += 1
            continue

        # R-11, R-02: metade do spread realizado, half-up por operação.
        parte = brl(spread * premissas.participacao_spread_tarvo)
        comissao[cnpj].append(Componente(arq, nop, parte))
        soma_incl += spread
        n_incl += 1
        if loj is None:  # R-19: calcula mesmo assim e abre pendência de cadastro
            sem_cadastro[cnpj].append(Componente(arq, nop, parte))

        # R-23, P-01, P-05: divergência pelo valor cheio, base × diferença de taxa.
        if contratado is not None:
            aplicado_pp = _dec(r["Spread %"]) * 100
            if abs(aplicado_pp - contratado) >= premissas.tolerancia_spread_pp:
                dif = brl((aplicado_pp - contratado) / 100 * vme * ptax)
                res.linhas.append(
                    LinhaSaida.somando(
                        "divergencias_taxa.csv",
                        f"DIV-REM-{nop}",
                        {
                            "cnpj": cnpj,
                            "linha_negocio": "REMESSA",
                            "ref_origem": nop,
                            "taxa_contratada_pct": contratado
                            if premissas.taxa_saida_em_pp
                            else contratado / 100,
                            "taxa_aplicada_pct": aplicado_pp.normalize()
                            if premissas.taxa_saida_em_pp
                            else _dec(r["Spread %"]),
                        },
                        [Componente(arq, nop, dif)],
                    )
                )
                contestar[cnpj].append(Componente(arq, nop, dif))

    todas: list[Componente] = []
    for cnpj, comps in sorted(comissao.items()):
        res.linhas.append(
            LinhaSaida.somando(
                "comissoes_por_lojista.csv",
                f"COM-REM-{cnpj}",
                {"cnpj": cnpj, "lojista": nome_de[cnpj], "linha_negocio": "REMESSA"},
                comps,
            )
        )
        todas.extend(comps)

    if todas:
        # R-27: uma nota só, tomadora a Ponte.
        nota = LinhaSaida.somando(
            "notas_a_emitir.csv",
            f"NF-REM-{cnpj_ponte}",
            {
                "tomador_cnpj": cnpj_ponte,
                "tomador": nome_ponte,
                "linha_negocio": "REMESSA",
                "discriminacao": "Intermediação de câmbio - participação de "
                f"{premissas.participacao_spread_tarvo * 100:.0f}% no spread - competência {comp}",
            },
            todas,
        )
        res.linhas.append(nota)
        # R-39: acompanhamento do repasse (não é alarme falso).
        res.linhas.append(
            pendencia(
                "REM", f"REPASSE-{cnpj_ponte}", "ACOMPANHAMENTO_REPASSE", todas,
                f"Conferir o crédito do repasse da {nome_ponte} de {_brl_txt(nota.valor or Decimal(0))} "
                f"(competência {comp}), previsto para {data_repasse}, quando cair no banco.",
                "Helena",
            )
        )  # fmt: skip

    for cnpj, comps in sorted(contestar.items()):
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            pendencia(
                "REM", f"CONTESTACAO-{cnpj}", "DIVERGENCIA_SPREAD", comps,
                f"{nome_de[cnpj]}: spread cobrado acima do contratado em {_ops(len(comps))}, "
                f"{_brl_txt(total)} pagos a mais pelo lojista (valor cheio). Comissão e nota "
                "saíram pelo realizado; contestar com a Ponte (R-17, R-23).",
                f"Helena ({nome_ponte})",
            )
        )  # fmt: skip
    for cnpj, pares in sorted(negativos.items()):
        comps = [c for c, _ in pares]
        rel = sum((c.valor for c in comps), Decimal(0))
        ate = sum((a for _, a in pares), Decimal(0))
        res.linhas.append(
            pendencia(
                "REM", f"SPREADNEG-{cnpj}", "SPREAD_NEGATIVO", comps,
                f"{nome_de[cnpj]}: {_ops(len(comps))} com spread negativo (taxa travada D-1 "
                f"já vencida), {_brl_txt(rel)} pelo relatório e {_brl_txt(ate)} até o spread do "
                "contrato. Fora da comissão e da nota; contestar com a Ponte (R-14).",
                f"Helena ({nome_ponte})",
            )
        )  # fmt: skip
    if repetidas:
        res.linhas.append(
            pendencia(
                "REM", "DUPLICATA", "OPERACAO_DUPLICADA", repetidas,
                f"{_ops(len(repetidas), 'repetida')} no relatório da Ponte, cópia idêntica. "
                "Contou uma vez; pedir à Ponte que corrija o relatório e o total do rodapé (R-13).",
                nome_ponte,
            )
        )  # fmt: skip
    if copias_div:
        versoes = []
        for nop, rs in divergentes.items():
            cols = list(dict.fromkeys(c for o in rs[1:] for c in _diferencas(rs[0], o)))
            v = " x ".join(
                f"linha {r.get('linha_planilha', '?')} ("
                + ", ".join(f"{c}={_txt(r.get(c))}" for c in cols)
                + ")"
                for r in rs
            )
            versoes.append(f"{nop}: {v}")
        res.linhas.append(
            pendencia(
                "REM", "DUPLICATA-DIVERGENTE", "OPERACAO_DUPLICADA_DIVERGENTE", copias_div,
                f"{_ops(len(divergentes), 'repetida')} com valores diferentes entre as cópias: "
                + " | ".join(versoes) + ". Nenhuma cópia entrou na comissão nem na nota; "
                "pedir à Ponte qual versão vale (R-13).",
                nome_ponte,
            )
        )  # fmt: skip
    for cnpj, nop, original, comp_aj, cheio in ajustes:
        res.linhas.append(
            pendencia(
                "REM", f"AJUSTE-{nop}", "AJUSTE_PONTE", [comp_aj],
                f"{nome_de[cnpj]}: ajuste {nop} da Ponte referente à {original}, Spread R$ "
                f"{_brl_txt(cheio)}. Abatido {_brl_txt(comp_aj.valor)} (50%, lendo como spread "
                f"inteiro, R-11) na comissão e na nota do mês (R-18). Se for já a nossa parte, "
                f"o abatimento é {_brl_txt(cheio)} (100%). Confirmar a Q-04.",
                "Helena",
            )
        )  # fmt: skip
    for cnpj, comps in sorted(outro_mes.items()):
        res.linhas.append(
            pendencia(
                "REM", f"OUTRO-MES-{cnpj}", "OPERACAO_DE_OUTRO_MES", comps,
                f"{nome_de[cnpj]}: {_ops(len(comps))} de outro mês (data de contratação fora "
                f"de {comp} ou ausente). Fora da comissão e da nota desta competência (R-16).",
                "Helena",
            )
        )  # fmt: skip
    for cnpj, comps in sorted(sem_cadastro.items()):
        res.linhas.append(
            pendencia(
                "REM", f"CADASTRO-{cnpj}", "CNPJ_FORA_DO_CADASTRO", comps,
                f"CNPJ {cnpj} ({nome_de[cnpj]}) operou remessa mas não está na planilha de "
                "taxas. A participação foi calculada mesmo assim; cadastrar o lojista (R-19).",
                "Comercial",
            )
        )  # fmt: skip

    # Invariante: tudo que entrou está na comissão (com os ajustes), nos negativos, nas
    # repetições, nas cópias divergentes ou nas operações de outro mês.
    fora = soma_neg + soma_rep + soma_div + soma_fora
    res.conservacao["spread_total"] = soma_total - (soma_incl + soma_aj + fora)
    res.conservacao["linhas_ponte"] = Decimal(
        len(df) - (n_incl + n_aj + n_neg + n_rep + n_div + n_fora)
    )
    return res
