"""Trilha B — Remessa: dedup, spread negativo, comissão 50% do spread, divergência de spread, NF Ponte e pendências.

Contrato: docs/plano-engenharia.md §2 e §4. Devolve linhas via `LinhaSaida.somando`
(componentes = linhas de origem) e preenche `conservacao` com o invariante da trilha.
Regras: HIPOTESES.md §2.2 (R-11..R-19), §2.3 (R-23, R-24), §2.4 (R-27, R-28), §2.6, §3 (P-01, P-05, P-07, P-10, P-13).
"""

from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

import pandas as pd

from src.core.cadastro import Cadastro
from src.core.entrada import ARQ_PONTE, DadosEntrada
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.premissas import Premissas

LINHA = "REMESSA"
# R-12: spread em branco ou "padrão" = 1,5% (usado se premissas/cadastro não trouxer o default).
SPREAD_PADRAO_PCT = Decimal("1.5")
# P-01: |Spread % − contratado| < 0,01 p.p. é ruído.
TOLERANCIA_PP = Decimal("0.01")
NOME_PONTE = "Ponte Câmbio"  # R-27
HELENA = "Helena (Financeiro Tarvo)"
PONTE = "Ponte Câmbio"
COMERCIAL = "Comercial"

_CAMPOS_DUP = (
    "Data Contratação",
    "CNPJ Cliente",
    "Moeda",
    "Valor ME",
    "Taxa Cliente",
    "PTAX Ref.",
    "Valor R$",
    "Spread R$",
    "Spread %",
)


def _dec(v: Any) -> Decimal | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return Decimal(str(v).strip())
    except (InvalidOperation, ValueError):
        return None


def _fmt_brl(v: Decimal, casas: int = 2) -> str:
    """R$ no padrão brasileiro, só para texto de motivo/discriminação (sem arredondar além de `casas`)."""
    q = abs(v).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    s = f"{q:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'−' if v < 0 else ''}R$ {s}"


def _fmt_pp(v: Decimal) -> str:
    """p.p. com 2 a 4 casas, vírgula decimal (texto de motivo)."""
    t = f"{abs(v.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)):.4f}"
    t = t[:-2] + t[-2:].rstrip("0") if t.endswith("0") else t
    return ("−" if v < 0 else "") + t.replace(".", ",")


@dataclass
class _Op:
    num: str
    cnpj: str
    cliente: str
    spread_brl: Decimal
    spread_pp: Decimal  # Spread % do relatório convertido para p.p.
    valor_me: Decimal
    ptax: Decimal
    competencia: str  # MM/AAAA, R-16: data de contratação
    obs: str = ""


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="remessa")
    ponte = dados.ponte
    part = premissas.participacao_spread_tarvo

    vistos: dict[str, dict[str, Any]] = {}
    incluidas: list[_Op] = []
    negativas: list[_Op] = []
    duplicadas: list[tuple[dict[str, Any], dict[str, Any]]] = []  # (cópia, original)
    incompletas: list[dict[str, Any]] = []
    soma_total = Decimal(0)

    registros: list[dict[str, Any]] = [
        {str(k): v for k, v in r.items()} for r in ponte.to_dict("records")
    ]
    registros.sort(key=lambda r: r.get("linha_planilha", 0))
    for r in registros:
        num = str(r.get("Nº Operação") or "").strip()
        spread_brl = _dec(r.get("Spread R$"))
        spread_frac = _dec(r.get("Spread %"))
        valor_me, ptax = _dec(r.get("Valor ME")), _dec(r.get("PTAX Ref."))
        cnpj = r.get("cnpj_limpo")
        data = r.get("Data Contratação")
        if spread_brl is not None:
            soma_total += spread_brl
        # R-42: linha estranha não derruba a trilha, vira pendência.
        if (
            not num
            or spread_brl is None
            or spread_frac is None
            or valor_me is None
            or ptax is None
            or not cnpj
            or pd.isna(data)
        ):
            incompletas.append(r)
            continue
        # R-13: Nº de operação único; a primeira ocorrência conta, a repetição vai para a Ponte.
        if num in vistos:
            duplicadas.append((r, vistos[num]))
            continue
        vistos[num] = r
        op = _Op(
            num=num,
            cnpj=str(cnpj),
            cliente=str(r.get("Cliente") or "").strip(),
            spread_brl=spread_brl,
            spread_pp=spread_frac * 100,  # Spread % vem como fração (0.015004)
            valor_me=valor_me,
            ptax=ptax,
            competencia=pd.Timestamp(data).strftime("%m/%Y"),
            obs="" if pd.isna(r.get("Observação")) else str(r.get("Observação")).strip(),
        )
        # R-14: spread negativo fica fora da comissão e da nota.
        (negativas if spread_brl < 0 else incluidas).append(op)

    # --- Comissão por lojista (R-11, R-15, R-16, R-17) ---
    com_por_cnpj: dict[str, list[Componente]] = defaultdict(list)
    todas_com: list[Componente] = []
    sem_cadastro: dict[str, list[_Op]] = defaultdict(list)
    for op in incluidas:
        c = Componente(ARQ_PONTE, op.num, brl(op.spread_brl * part))  # R-11: half-up por operação
        com_por_cnpj[op.cnpj].append(c)
        todas_com.append(c)
        if cadastro.lojista_por_cnpj(op.cnpj) is None:
            sem_cadastro[op.cnpj].append(op)  # R-19: calcula mesmo assim + pendência

    nomes_relatorio = {op.cnpj: op.cliente for op in incluidas}
    for cnpj in sorted(com_por_cnpj):
        loj = cadastro.lojista_por_cnpj(cnpj)
        regra = "R-11 R-13 R-14 R-15 R-16 R-17 P-10" + (" R-19" if loj is None else "")
        campos: dict[str, Any] = {
            "cnpj": cnpj,
            "lojista": loj.nome if loj else nomes_relatorio[cnpj],
            "linha_negocio": LINHA,
            "regra": regra,
        }
        res.linhas.append(
            LinhaSaida.somando(
                "comissoes_por_lojista.csv", f"COM-REM-{cnpj}", campos, com_por_cnpj[cnpj]
            )
        )

    # --- Divergências de spread (R-23, R-24, P-01, P-05, P-07) ---
    def contratado(cnpj: str) -> tuple[Decimal | None, bool]:
        if cadastro.lojista_por_cnpj(cnpj) is None:
            return None, False  # R-19: sem contrato não há divergência; vai para o Comercial
        c = cadastro.spread_contratado_pct(cnpj)
        if c is None:
            pad = premissas.spread_padrao_pct
            return (pad if pad is not None else SPREAD_PADRAO_PCT), True  # R-12
        return c, False

    div_por_cnpj: dict[str, list[tuple[_Op, Decimal, Componente]]] = defaultdict(list)
    for op in incluidas:  # negativas ficam fora (P-07)
        contr, padrao = contratado(op.cnpj)
        if contr is None:
            continue
        dif_pp = op.spread_pp - contr
        if abs(dif_pp) < TOLERANCIA_PP:
            continue
        # P-05: valor cheio = (Spread % − contratado) × Valor ME × PTAX Ref.
        comp = Componente(ARQ_PONTE, op.num, brl(dif_pp / 100 * op.valor_me * op.ptax))
        campos = {
            "cnpj": op.cnpj,
            "linha_negocio": LINHA,
            "ref_origem": op.num,
            "taxa_contratada_pct": contr.quantize(Decimal("0.01")),
            "taxa_aplicada_pct": op.spread_pp.quantize(Decimal("0.0001")),
            "regra": "R-23 R-24 P-01 P-05 P-09" + (" R-12" if padrao else ""),
        }
        res.linhas.append(
            LinhaSaida.somando("divergencias_taxa.csv", f"DIV-REM-{op.num}", campos, [comp])
        )
        div_por_cnpj[op.cnpj].append((op, contr, comp))

    # --- Nota única para a Ponte (R-27, R-28) ---
    total_nota = sum((c.valor for c in todas_com), Decimal(0))
    competencias = sorted({op.competencia for op in incluidas})
    comp_txt = ", ".join(competencias)
    cnpj_ponte = premissas.cnpj_ponte_cambio
    pct_txt = f"{(part * 100).normalize():f}%"
    if todas_com and total_nota > 0:
        campos = {
            "tomador_cnpj": cnpj_ponte,
            "tomador": NOME_PONTE,
            "linha_negocio": LINHA,
            "discriminacao": (
                f"Participação de {pct_txt} no spread realizado das operações de remessa internacional "
                f"(câmbio) de clientes Tarvo. Competência {comp_txt}. {len(todas_com)} operações."
            ),
            "regra": "R-11 R-13 R-14 R-16 R-17 R-27 R-28",
        }
        res.linhas.append(
            LinhaSaida.somando("notas_a_emitir.csv", f"NF-REM-{cnpj_ponte}", campos, todas_com)
        )
    elif todas_com:
        res.linhas.append(
            LinhaSaida.somando(
                "pendencias.csv",
                "PEN-REM-NOTA-NAO-EMITIDA",
                {
                    "tipo": "NOTA_NAO_EMITIDA",
                    "ref_origem": "|".join(c.ref_origem for c in todas_com),
                    "motivo": (
                        f"A participação de remessa da competência {comp_txt} somou {_fmt_brl(total_nota)}, "
                        "zero ou negativa. A nota para a Ponte Câmbio não foi emitida."
                    ),
                    "quem_decide": HELENA,
                    "regra": "R-27",
                },
                todas_com,
            )
        )

    # --- Pendências (P-13: uma por contraparte e por lojista; L-04: refs com |) ---
    def pend(
        chave: str, tipo: str, comps: list[Componente], motivo: str, quem: str, regra: str
    ) -> None:
        campos = {
            "tipo": tipo,
            "ref_origem": "|".join(c.ref_origem for c in comps),
            "motivo": motivo,
            "quem_decide": quem,
            "regra": regra,
        }
        res.linhas.append(LinhaSaida.somando("pendencias.csv", f"PEN-REM-{chave}", campos, comps))

    def nome(cnpj: str, fallback: str) -> str:
        loj = cadastro.lojista_por_cnpj(cnpj)
        return loj.nome if loj else fallback

    # Contestação de spread acima/abaixo do contrato (R-23, R-25, R-38), por lojista.
    for cnpj in sorted(div_por_cnpj):
        itens = div_por_cnpj[cnpj]
        comps = [c for _, _, c in itens]
        tot = sum((c.valor for c in comps), Decimal(0))
        contrs = sorted({ct for _, ct, _ in itens})
        aplic = sorted(op.spread_pp for op, _, _ in itens)
        motivo = (
            f"{nome(cnpj, itens[0][0].cliente)} (CNPJ {cnpj}): a Ponte Câmbio aplicou spread diferente do contrato "
            f"({' / '.join(_fmt_pp(c) for c in contrs)}% contratado, aplicado entre {_fmt_pp(aplic[0])}% e "
            f"{_fmt_pp(aplic[-1])}%) em {len(itens)} operações. Diferença total cobrada do lojista: {_fmt_brl(tot)} "
            "(valor cheio, (Spread % − contratado) × Valor ME × PTAX). Contestar com a Ponte Câmbio e ressarcir o "
            "lojista. A comissão e a nota já saem pelo realizado (R-17). Detalhe por operação em divergencias_taxa.csv."
        )
        pend(
            f"CONTESTACAO-SPREAD-{cnpj}",
            "CONTESTACAO_SPREAD",
            comps,
            motivo,
            HELENA,
            "R-17 R-23 R-25 R-37 R-38 P-05 P-13",
        )

    # Spread negativo (R-14, P-07), por lojista: valor do relatório no valor_brl; diferença até o contrato no motivo.
    neg_por_cnpj: dict[str, list[_Op]] = defaultdict(list)
    for op in negativas:
        neg_por_cnpj[op.cnpj].append(op)
    for cnpj in sorted(neg_por_cnpj):
        ops = neg_por_cnpj[cnpj]
        comps = [Componente(ARQ_PONTE, op.num, brl(op.spread_brl)) for op in ops]
        detalhes = []
        tot_contr = Decimal(0)
        tem_contr = True
        usou_padrao = False
        for op in ops:
            contr, padrao = contratado(op.cnpj)
            usou_padrao = usou_padrao or padrao
            if contr is None:
                tem_contr = False
                detalhes.append(
                    f"{op.num}: spread do relatório {_fmt_brl(brl(op.spread_brl))} ({_fmt_pp(op.spread_pp)}%), sem spread contratado no cadastro"
                )
                continue
            ate = brl((op.spread_pp - contr) / 100 * op.valor_me * op.ptax)
            tot_contr += ate
            detalhes.append(
                f"{op.num}: spread do relatório {_fmt_brl(brl(op.spread_brl))} ({_fmt_pp(op.spread_pp)}%)"
                + (f', observação da Ponte "{op.obs}"' if op.obs else "")
                + f", diferença até o contrato de {_fmt_pp(contr)}%{' (padrão, R-12)' if padrao else ''}: {_fmt_brl(ate)}"
            )
        tot = sum((c.valor for c in comps), Decimal(0))
        motivo = (
            f"{nome(cnpj, ops[0].cliente)} (CNPJ {cnpj}): spread negativo no relatório da Ponte. Spread negativo não é "
            "aceito"
            + (
                " (taxa travada D-1: a trava vale 2 horas e já tinha vencido)"
                if any("D-1" in op.obs for op in ops)
                else ""
            )
            + ". Ficou fora da comissão e da nota. Contestar com a Ponte Câmbio. "
            f"Spread do relatório: {_fmt_brl(tot)}"
            + (f". Diferença até o spread do contrato: {_fmt_brl(tot_contr)}" if tem_contr else "")
            + ". "
            + ". ".join(detalhes)
            + ". Diferença até o contrato = (Spread % − contratado) × Valor ME × PTAX."
        )
        pend(
            f"SPREAD-NEGATIVO-{cnpj}",
            "SPREAD_NEGATIVO",
            comps,
            motivo,
            HELENA,
            "R-14 R-37 R-38 P-07 P-13" + (" R-12" if usou_padrao else ""),
        )

    # Operação repetida no relatório (R-13): valor = spread da cópia, para a Ponte corrigir.
    if duplicadas:
        comps = [
            Componente(ARQ_PONTE, str(cp["Nº Operação"]).strip(), brl(_dec(cp["Spread R$"]) or 0))
            for cp, _ in duplicadas
        ]
        partes = []
        for cp, o in duplicadas:
            igual = all(str(cp.get(k)) == str(o.get(k)) for k in _CAMPOS_DUP)
            obs = str(cp.get("Observação") or "").strip()
            partes.append(
                f"{str(cp['Nº Operação']).strip()} repetida (linhas {o.get('linha_planilha')} e {cp.get('linha_planilha')} da planilha"
                + (f', observação "{obs}"' if obs and obs.lower() != "nan" else "")
                + (", conteúdo idêntico" if igual else ", conteúdo DIFERENTE entre as cópias")
                + f", spread da cópia {_fmt_brl(brl(_dec(cp['Spread R$']) or 0))})"
            )
        motivo = (
            "Operação repetida no relatório da Ponte Câmbio. O Nº de operação é único: contou uma vez na comissão e na nota. "
            + ". ".join(partes)
            + ". Pedir à Ponte que corrija o relatório: o total do relatório soma a cópia."
        )
        pend("OPERACAO-REPETIDA", "OPERACAO_REPETIDA", comps, motivo, PONTE, "R-13")

    # R-19: CNPJ fora do cadastro.
    for cnpj in sorted(sem_cadastro):
        ops = sem_cadastro[cnpj]
        comps = [c for c in com_por_cnpj[cnpj]]
        motivo = (
            f"CNPJ {cnpj} ({ops[0].cliente}, nome do relatório da Ponte) não está na planilha de taxas vigente. "
            f"A participação de {pct_txt} foi calculada mesmo assim e entrou na nota. Sem spread contratado, não há como "
            "conferir divergência. Cadastrar o lojista e o spread."
        )
        pend(f"CADASTRO-{cnpj}", "CADASTRO", comps, motivo, COMERCIAL, "R-19")

    # R-42: linha incompleta.
    for ri in incompletas:
        ref = str(ri.get("Nº Operação") or f"linha {ri.get('linha_planilha')}").strip()
        res.linhas.append(
            LinhaSaida(
                "pendencias.csv",
                f"PEN-REM-LINHA-INCOMPLETA-{ri.get('linha_planilha')}",
                {
                    "tipo": "LINHA_INCOMPLETA",
                    "ref_origem": ref,
                    "motivo": "Linha do relatório da Ponte sem Nº, CNPJ, data ou valores de spread. Ficou fora da comissão. Conferir com a Ponte.",
                    "quem_decide": HELENA,
                    "regra": "R-42",
                },
                None,
            )
        )

    # Acompanhamento do repasse da Ponte (R-39; N-04/C-03/H-10): nossa nota × 50% do total do relatório.
    if todas_com and total_nota > 0:
        rodape = ponte.attrs.get("rodape", {}) if hasattr(ponte, "attrs") else {}
        total_rel = brl(soma_total)
        metade_rel = brl(total_rel * part)
        soma_neg = sum((op.spread_brl for op in negativas), Decimal(0))
        soma_dup = sum(((_dec(c["Spread R$"]) or Decimal(0)) for c, _ in duplicadas), Decimal(0))
        soma_inc = sum((op.spread_brl for op in incluidas), Decimal(0))
        arred = total_nota - soma_inc * part  # half-up por operação (R-11)
        arred_ponte = metade_rel - soma_total * part  # meio centavo do total da Ponte
        dif = total_nota - metade_rel
        rod_txt = ""
        if rodape:
            rod_txt = (
                " (rodapé do relatório: "
                + ", ".join(
                    f"{k} {_fmt_brl(Decimal(str(v))).replace('R$ ', '') if isinstance(v, float) else v}"
                    for k, v in rodape.items()
                )
                + ")"
            )
        motivo = (
            f"Acompanhamento, não é erro: conferir a TED do repasse da Ponte Câmbio quando cair. A nossa nota é de "
            f"{_fmt_brl(total_nota)} ({len(todas_com)} operações, {pct_txt} do spread realizado). O relatório da Ponte soma "
            f"{_fmt_brl(total_rel)} em {len(ponte)} linhas{rod_txt}, incluindo a repetição e os spreads negativos. "
            f"{pct_txt} dele são {_fmt_brl(metade_rel)}. Diferença de {_fmt_brl(dif)} = metade dos negativos "
            f"({_fmt_brl(-soma_neg * part, 3)}) − metade da repetição ({_fmt_brl(soma_dup * part, 3)}) + arredondamento "
            f"por operação ({_fmt_brl(arred, 3)}) − arredondamento do total da Ponte ({_fmt_brl(arred_ponte, 3)}). "
            "Se a TED vier pelo total do relatório, a diferença entra na contestação."
        )
        pend(
            "ACOMPANHAMENTO-REPASSE",
            "ACOMPANHAMENTO_REPASSE",
            list(todas_com),
            motivo,
            HELENA,
            "R-13 R-14 R-27 R-39",
        )

    # --- Conservação ---
    n_dup, n_neg, n_inc, n_inco = len(duplicadas), len(negativas), len(incluidas), len(incompletas)
    res.conservacao["linhas_ponte"] = Decimal(len(ponte) - (n_inc + n_neg + n_dup + n_inco))
    soma_dup_all = sum(((_dec(c["Spread R$"]) or Decimal(0)) for c, _ in duplicadas), Decimal(0))
    res.conservacao["spread_brl"] = soma_total - (
        sum((op.spread_brl for op in incluidas), Decimal(0))
        + sum((op.spread_brl for op in negativas), Decimal(0))
        + soma_dup_all
    )
    # Nota = Σ comissões (mesmos componentes); só vale quando a nota sai.
    soma_com = sum(
        (
            (ln.valor or Decimal(0))
            for ln in res.linhas
            if ln.arquivo == "comissoes_por_lojista.csv"
        ),
        Decimal(0),
    )
    res.conservacao["nota_menos_comissoes"] = (
        (total_nota - soma_com) if total_nota > 0 else Decimal(0)
    )
    return res
