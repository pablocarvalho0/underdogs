"""Trilha A — Checkout: comissão CHECKOUT, divergências de taxa, NF por lojista e pendências.

Regras: HIPOTESES.md §2.1, §2.3, §2.4. Toda linha sai por `LinhaSaida.somando`, com os
componentes apontando para a linha da Orbe (arquivo de origem por linha, R-43).
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from src.core.cadastro import Cadastro, Lojista
from src.core.entrada import DadosEntrada, competencia
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.core.pendencias import pendencia
from src.premissas import AliasEC, Premissas

ANTECIPACOES = ("ANTECIPACAO", "REVERSAO ANTECIPACAO")


def _fmt_pct(taxa: Decimal, premissas: Premissas) -> Decimal:
    # P-09: taxa em pontos percentuais na saída (2.69); fração só se a flag mudar.
    return taxa if premissas.taxa_saida_em_pp else taxa / 100


def _brl_txt(v: Decimal) -> str:
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if v < 0 else ''}R$ {s}"


def _data_ref(r: dict[str, Any], por_id: dict[str, dict[str, Any]]) -> date:
    """Data que define a taxa contratada da linha."""
    tipo = r["tipo_lancamento"]
    if tipo == "ESTORNO" and r["data_venda_original"]:
        return r["data_venda_original"]  # type: ignore[no-any-return]  # R-03
    if tipo == "REVERSAO ANTECIPACAO":
        orig = por_id.get(r["id_referencia"])
        if orig is not None:
            return orig["data_movimento"]  # type: ignore[no-any-return]  # R-04, R-44
    return r["data_movimento"]  # type: ignore[no-any-return]


def _original_ausente(
    r: dict[str, Any], por_id: dict[str, dict[str, Any]], inicio_mes: date
) -> bool:
    """R-51, D-02 (a): estorno ou reversão cuja original é do mês, mas não veio em nenhum
    arquivo da Orbe. Estorno de venda de mês anterior (os de agosto) não entra: a original
    é de outro mês e não deveria mesmo estar nos arquivos deste."""
    if r["tipo_lancamento"] not in ("ESTORNO", "REVERSAO ANTECIPACAO"):
        return False
    if r["id_referencia"] in por_id:
        return False
    dvo: date | None = r["data_venda_original"]
    return dvo is not None and (dvo.year, dvo.month) == (inicio_mes.year, inicio_mes.month)


def _alerta_antecipacao(
    rows: list[dict[str, Any]], inicio_mes: date
) -> tuple[date, Decimal, list[Componente]] | None:
    """P-08: lojista sem venda antes do mês cuja antecipação acumulada supera as vendas
    acumuladas em algum dia. Devolve o pico (dia, excesso, componentes que somam o excesso)."""
    vendas = [r for r in rows if r["tipo_lancamento"] == "VENDA"]
    if not vendas:
        return None
    venda_anterior = any(
        r["tipo_lancamento"] == "ESTORNO"
        and r["data_venda_original"]
        and r["data_venda_original"] < inicio_mes
        for r in rows
    )
    if venda_anterior or min(r["data_movimento"] for r in vendas) <= inicio_mes:
        return None
    pico: tuple[date, Decimal] | None = None
    ant = ven = Decimal(0)
    for dia in sorted({r["data_movimento"] for r in rows}):
        do_dia = [r for r in rows if r["data_movimento"] == dia]
        ant += sum((r["valor_bruto"] for r in do_dia if r["tipo_lancamento"] in ANTECIPACOES), Decimal(0))
        ven += sum((r["valor_bruto"] for r in do_dia if r["tipo_lancamento"] in ("VENDA", "ESTORNO")), Decimal(0))
        if ant > ven and (pico is None or ant - ven > pico[1]):
            pico = (dia, ant - ven)
    if pico is None:
        return None
    comps = [
        Componente(
            r["arquivo_origem"],
            r["id_transacao"],
            r["valor_bruto"] if r["tipo_lancamento"] in ANTECIPACOES else -r["valor_bruto"],
        )
        for r in rows
        if r["data_movimento"] <= pico[0]
        and r["tipo_lancamento"] in ANTECIPACOES + ("VENDA", "ESTORNO")
    ]
    return pico[0], pico[1], comps


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="checkout")
    if dados.orbe.empty:
        return res
    comp = competencia(dados)
    inicio_mes = date(int(comp[:4]), int(comp[5:7]), 1)
    rows: list[dict[str, Any]] = dados.orbe.to_dict("records")  # type: ignore[assignment]
    por_id = {r["id_transacao"]: r for r in rows}
    inativos: dict[str, Lojista] = getattr(cadastro, "inativos_por_ec", {})

    lojista_de: dict[str, Lojista] = {}
    comissao: dict[str, list[Componente]] = defaultdict(list)
    contestar: dict[str, list[Componente]] = defaultdict(list)
    devolucao: dict[str, list[Componente]] = defaultdict(list)
    sem_contrato: dict[str, list[Componente]] = defaultdict(list)
    inativo: dict[str, list[Componente]] = defaultdict(list)
    sem_taxa: dict[str, list[Componente]] = defaultdict(list)
    acima_12x: dict[str, list[Componente]] = defaultdict(list)
    ausente: dict[str, list[Componente]] = defaultdict(list)
    alias_pendente: dict[str, list[Componente]] = defaultdict(list)
    alias_de: dict[str, AliasEC] = {}
    nome_ec: dict[str, str] = {}
    destinos = 0

    for r in rows:
        ec, idt, arq = r["cod_estabelecimento"], r["id_transacao"], r["arquivo_origem"]
        cobrado = Componente(arq, idt, r["valor_taxa"] or Decimal(0))
        nome_ec.setdefault(ec, r["nome_estabelecimento"])
        if _original_ausente(r, por_id, inicio_mes):
            # Abate pelo valor que veio (segue o fluxo normal) e avisa a Helena.
            ausente[ec].append(Componente(arq, idt, r["valor_bruto"]))
        loj = cadastro.lojista_por_ec(ec)
        if loj is None:
            # R-06: sem contrato vigente não fatura; inativo idem, mas com outro motivo.
            (inativo if ec in inativos else sem_contrato)[ec].append(cobrado)
            destinos += 1
            continue
        lojista_de[loj.cnpj] = loj
        if loj.alias is not None and not loj.alias.confirmado_financeiro:
            alias_pendente[ec].append(cobrado)  # premissas.AliasEC: fatura, mas pede confirmação
            alias_de[ec] = loj.alias
        tipo = r["tipo_lancamento"]
        data_ref = _data_ref(r, por_id)

        # R-08, R-44: isenção vigente na data de referência -> devolução, não comissão (R-09).
        if any(i.cnpj == loj.cnpj and i.vale_em(data_ref) for i in premissas.isencoes_checkout):
            devolucao[loj.cnpj].append(cobrado)
            destinos += 1
            continue

        if tipo in ANTECIPACOES:
            modalidade, parcelas = "ANTECIPACAO", 1
        else:
            modalidade, parcelas = r["modalidade"], r["qtd_parcelas"]
            if parcelas > premissas.max_parcelas:  # R-10
                acima_12x[loj.cnpj].append(cobrado)
                destinos += 1
                continue

        taxa = cadastro.taxa_contratada_pct(loj.cnpj, modalidade, parcelas, data_ref)
        if taxa is None:
            sem_taxa[loj.cnpj].append(cobrado)
            destinos += 1
            continue

        # R-01, R-02: bruto × taxa contratada, half-up por linha; estorno e reversão
        # já vêm com bruto negativo (R-03, R-04).
        bruto: Decimal = r["valor_bruto"]
        comissao[loj.cnpj].append(Componente(arq, idt, brl(bruto * taxa / 100)))
        destinos += 1

        # R-20, R-21: taxa com taxa; centavo de truncamento da Orbe não conta.
        aplicada: Decimal | None = r["taxa_aplicada_pct"]
        if aplicada is not None and aplicada != taxa:
            dif = brl(bruto * (aplicada - taxa) / 100)
            res.linhas.append(
                LinhaSaida.somando(
                    "divergencias_taxa.csv",
                    f"DIV-CHK-{idt}",
                    {
                        "cnpj": loj.cnpj,
                        "linha_negocio": "CHECKOUT",
                        "ref_origem": idt,
                        "taxa_contratada_pct": _fmt_pct(taxa, premissas),
                        "taxa_aplicada_pct": _fmt_pct(aplicada, premissas),
                    },
                    [Componente(arq, idt, dif)],
                )
            )
            contestar[loj.cnpj].append(Componente(arq, idt, dif))

    # --- comissões e notas (R-26, R-28) ---
    for cnpj, comps in sorted(comissao.items()):
        loj = lojista_de[cnpj]
        linha = LinhaSaida.somando(
            "comissoes_por_lojista.csv",
            f"COM-CHK-{cnpj}",
            {"cnpj": cnpj, "lojista": loj.nome, "linha_negocio": "CHECKOUT"},
            comps,
        )
        res.linhas.append(linha)
        total = linha.valor or Decimal(0)
        if total > 0:
            res.linhas.append(
                LinhaSaida.somando(
                    "notas_a_emitir.csv",
                    f"NF-CHK-{cnpj}",
                    {
                        "tomador_cnpj": cnpj,
                        "tomador": loj.nome,
                        "linha_negocio": "CHECKOUT",
                        "discriminacao": "Intermediação de pagamentos (MDR e antecipação) - "
                        f"competência {comp}",
                    },
                    comps,
                )
            )
        else:
            res.linhas.append(
                pendencia(
                    "CHK", f"SEMNOTA-{cnpj}", "NOTA_NAO_EMITIDA", comps,
                    f"{loj.nome}: comissão de checkout de {comp} ficou em {_brl_txt(total)} "
                    "(zero ou negativa), então não há nota a emitir. Não passa sozinha para o "
                    "mês seguinte (R-26).",
                    "Helena",
                )
            )  # fmt: skip

    # --- pendências ---
    for cnpj, comps in sorted(contestar.items()):
        loj = lojista_de[cnpj]
        total = sum((c.valor for c in comps), Decimal(0))
        # R-24: cobrança abaixo do contrato também é divergência, mas não há o que devolver.
        acao = (
            "Contestar com a Orbe e ressarcir o lojista (R-22, R-25)."
            if total > 0
            else "No total a Orbe cobrou abaixo do contrato: decisão caso a caso com a Orbe, "
            "sem nada a ressarcir ao lojista (R-24)."
        )
        res.linhas.append(
            pendencia(
                "CHK", f"CONTESTACAO-{cnpj}", "DIVERGENCIA_TAXA_ORBE", comps,
                f"{loj.nome}: a Orbe aplicou taxa diferente do contrato em {len(comps)} "
                f"transações de {comp}, somando {_brl_txt(total)}. {acao}",
                "Helena (contestação com a Orbe)",
            )
        )  # fmt: skip
    for cnpj, comps in sorted(devolucao.items()):
        loj = lojista_de[cnpj]
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            pendencia(
                "CHK", f"DEVOLUCAO-{cnpj}", "DEVOLUCAO_ISENCAO", comps,
                f"{loj.nome} tem tarifa de checkout zerada por condição comercial, mas a Orbe "
                f"descontou {_brl_txt(total)} em {len(comps)} transações. A Tarvo devolve ao "
                "lojista; não é divergência de contrato com a Orbe (R-08, R-09).",
                "Helena + Comercial",
            )
        )  # fmt: skip
    for ec, comps in sorted(sem_contrato.items()):
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            pendencia(
                "CHK", f"SEMCONTRATO-{ec}", "LOJISTA_SEM_CONTRATO", comps,
                f"EC {ec} ({nome_ec[ec]}) não tem contrato na aba vigente da planilha: "
                f"{len(comps)} transações, {_brl_txt(total)} cobrados pela Orbe, não faturados. "
                "Quando o comercial confirmar a taxa, o mês entra junto com o seguinte (R-06, R-07).",
                "Comercial",
            )
        )  # fmt: skip
    for ec, comps in sorted(inativo.items()):
        res.linhas.append(
            pendencia(
                "CHK", f"INATIVO-{ec}", "LOJISTA_INATIVO", comps,
                f"EC {ec} ({inativos[ec].nome}) está marcado INATIVO na planilha, mas teve "
                f"{len(comps)} transações na Orbe. Não faturado até o comercial decidir.",
                "Comercial",
            )
        )  # fmt: skip
    for cnpj, comps in sorted(sem_taxa.items()):
        res.linhas.append(
            pendencia(
                "CHK", f"SEMTAXA-{cnpj}", "TAXA_NAO_ENCONTRADA", comps,
                f"{lojista_de[cnpj].nome}: {len(comps)} transações sem taxa contratada para a "
                "modalidade/data na planilha. Não faturadas até o comercial completar a taxa.",
                "Comercial",
            )
        )  # fmt: skip
    for cnpj, comps in sorted(acima_12x.items()):
        res.linhas.append(
            pendencia(
                "CHK", f"ACIMA12X-{cnpj}", "PARCELAMENTO_ACIMA_12X", comps,
                f"{lojista_de[cnpj].nome}: {len(comps)} vendas acima de 12x, que a Tarvo não "
                "vende (R-10). Fora da comissão até o comercial explicar.",
                "Comercial",
            )
        )  # fmt: skip

    for ec, comps in sorted(ausente.items()):
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            pendencia(
                "CHK", f"ORIGINAL-AUSENTE-{ec}", "ORIGINAL_AUSENTE", comps,
                f"EC {ec} ({nome_ec[ec]}): {len(comps)} estornos/reversões somando "
                f"{_brl_txt(total)} de bruto apontam para transação de {comp} que não veio em "
                "nenhum arquivo da Orbe. Venda original não veio: pedir à Orbe. O abatimento "
                "já entrou na comissão pelo valor que veio (R-51, D-02).",
                "Helena (pedir à Orbe)",
            )
        )  # fmt: skip
    for ec, comps in sorted(alias_pendente.items()):
        alias = alias_de[ec]
        res.linhas.append(
            pendencia(
                "CHK", f"ALIAS-{ec}", "ALIAS_NAO_CONFIRMADO", comps,
                f"EC {ec} ({nome_ec[ec]}) foi ligado ao CNPJ {alias.cnpj} por alias de "
                f"premissas ({alias.justificativa}) ainda não confirmado pelo financeiro: "
                f"{len(comps)} transações ligadas por esse vínculo. Confirmar antes de liberar.",
                "Helena",
            )
        )  # fmt: skip

    # R-41, P-08: alerta não muda número nenhum.
    por_ec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        por_ec[r["cod_estabelecimento"]].append(r)
    for ec, rs in sorted(por_ec.items()):
        alerta = _alerta_antecipacao(rs, inicio_mes)
        if alerta is None:
            continue
        dia, excesso, comps = alerta
        reversoes = sum(1 for r in rs if r["tipo_lancamento"] == "REVERSAO ANTECIPACAO")
        res.linhas.append(
            pendencia(
                "CHK", f"ALERTA-ANTECIPACAO-{ec}", "ALERTA_ANTECIPACAO", comps,
                f"EC {ec} ({nome_ec[ec]}), lojista novo no mês, antecipou mais do que vendeu: "
                f"pico em {dia.isoformat()}, {_brl_txt(excesso)} antecipados acima das vendas "
                f"acumuladas ({reversoes} reversões no mês). Alerta; não muda nenhum número (R-41).",
                "Helena + Comercial",
            )
        )  # fmt: skip

    # Invariante: cada linha da Orbe em exatamente um destino.
    res.conservacao["linhas_orbe"] = Decimal(len(rows) - destinos)
    return res
