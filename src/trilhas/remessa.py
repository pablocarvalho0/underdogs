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

    vistos: set[str] = set()
    comissao: dict[str, list[Componente]] = defaultdict(list)
    nome_de: dict[str, str] = {}
    contestar: dict[str, list[Componente]] = defaultdict(list)
    negativos: dict[str, list[tuple[Componente, Decimal]]] = defaultdict(list)
    repetidas: list[Componente] = []
    sem_cadastro: dict[str, list[Componente]] = defaultdict(list)
    soma_total = soma_incl = soma_neg = soma_rep = Decimal(0)
    n_incl = n_neg = n_rep = 0

    for r in df.to_dict("records"):
        nop = str(r["Nº Operação"]).strip()
        spread = _dec(r["Spread R$"])
        soma_total += spread
        comp_spread = Componente(arq, nop, spread)

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
        contratado = cadastro.spread_contratado_pct(cnpj)  # pontos percentuais
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
                f"{nome_de[cnpj]}: spread cobrado acima do contratado em {len(comps)} operações, "
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
                f"{nome_de[cnpj]}: {len(comps)} operações com spread negativo (taxa travada D-1 "
                f"já vencida), {_brl_txt(rel)} pelo relatório e {_brl_txt(ate)} até o spread do "
                "contrato. Fora da comissão e da nota; contestar com a Ponte (R-14).",
                f"Helena ({nome_ponte})",
            )
        )  # fmt: skip
    if repetidas:
        res.linhas.append(
            pendencia(
                "REM", "DUPLICATA", "OPERACAO_DUPLICADA", repetidas,
                f"{len(repetidas)} operação(ões) repetida(s) no relatório da Ponte. Contou uma "
                "vez; pedir à Ponte que corrija o relatório e o total do rodapé (R-13).",
                nome_ponte,
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

    # Invariante: tudo que entrou está na comissão, nos negativos ou nas repetições.
    res.conservacao["spread_total"] = soma_total - (soma_incl + soma_neg + soma_rep)
    res.conservacao["linhas_ponte"] = Decimal(len(df) - (n_incl + n_neg + n_rep))
    return res
