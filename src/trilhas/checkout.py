"""Trilha A — Checkout: comissão CHECKOUT por lojista, divergências de taxa, notas e pendências.

Regras: HIPOTESES.md §2.1 (comissão), §2.3 (divergências), §2.4 (notas), P-08 e P-13 (pendências).
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.core.cadastro import Cadastro
from src.core.entrada import DadosEntrada
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.premissas import Premissas

TIPOS = ("VENDA", "ESTORNO", "ANTECIPACAO", "REVERSAO ANTECIPACAO")
HELENA = "Helena (Financeiro Tarvo)"


def _data(s: Any) -> date | None:
    s = str(s).strip() if s is not None else ""
    if not s or s == "nan":
        return None
    return datetime.strptime(s, "%d/%m/%Y").date()


def _brl_txt(v: Decimal) -> str:
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct_txt(v: Decimal) -> str:
    return f"{v.normalize():f}".replace(".", ",") + "%"


def _pendencia(chave: str, tipo: str, comps: list[Componente], motivo: str, quem: str, regra: str) -> LinhaSaida:
    campos = {
        "tipo": tipo,
        "ref_origem": "|".join(c.ref_origem for c in comps),
        "motivo": motivo,
        "quem_decide": quem,
        "regra": regra,
    }
    return LinhaSaida.somando("pendencias.csv", f"PEN-CHK-{chave}", campos, comps)


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="checkout")
    nomes = {l.cnpj: l.nome for l in cadastro.lojistas()}
    registros = dados.orbe.to_dict("records")
    datas_mov = [d for d in (_data(r["data_movimento"]) for r in registros) if d]
    inicio_mes = min(datas_mov).replace(day=1) if datas_mov else None
    competencia = inicio_mes.strftime("%m/%Y") if inicio_mes else ""

    comp: dict[str, list[Componente]] = defaultdict(list)
    divs: dict[str, list[tuple[Componente, Decimal, Decimal]]] = defaultdict(list)
    isentos: dict[str, list[Componente]] = defaultdict(list)
    sem_contrato: dict[str, list[Componente]] = defaultdict(list)
    sem_contrato_info: dict[str, tuple[str, str]] = {}
    fora_regra: list[tuple[Componente, str]] = []

    for r in registros:
        ec = str(r["cod_estabelecimento"]).strip()
        tipo = str(r["tipo_lancamento"]).strip()
        ref = str(r["id_transacao"])
        arq = r["arquivo_origem"]
        valor_taxa = r["valor_taxa"] if r["valor_taxa"] is not None else Decimal(0)
        if tipo not in TIPOS:
            # R-42: avisa sem quebrar. Fica fora da comissão até alguém dizer o que é.
            fora_regra.append((Componente(arq, ref, valor_taxa), f"tipo_lancamento desconhecido {tipo!r}"))
            continue
        loj = cadastro.lojista_por_ec(ec)  # R-05: aliases só via cadastro
        if tipo == "VENDA":
            modalidade, data_ref = r["modalidade"], _data(r["data_movimento"])
        elif tipo == "ESTORNO":
            # R-03: taxa da data da venda original; faixa vem da linha do estorno.
            modalidade, data_ref = r["modalidade"], _data(r["data_venda_original"])
        elif tipo == "ANTECIPACAO":
            # R-44: vale a data da antecipação.
            modalidade, data_ref = "ANTECIPACAO", _data(r["data_movimento"])
        else:
            modalidade, data_ref = "ANTECIPACAO", _data(r["data_venda_original"])

        parcelas = int(r["qtd_parcelas"]) if str(r["qtd_parcelas"]).strip() not in ("", "nan") else 1
        if tipo in ("VENDA", "ESTORNO") and str(modalidade).strip() == "CREDITO PARCELADO" and parcelas > 12:
            fora_regra.append((Componente(arq, ref, valor_taxa), f"crédito parcelado em {parcelas}x (R-10)"))
            continue
        taxa = (
            cadastro.taxa_contratada_pct(loj.cnpj, str(modalidade), parcelas, data_ref)
            if loj and data_ref
            else None
        )
        if loj is None or taxa is None:
            # R-06: sem taxa vigente não fatura; o que a Orbe cobrou fica na pendência.
            sem_contrato[ec].append(Componente(arq, ref, valor_taxa))
            sem_contrato_info.setdefault(ec, (str(r["nome_estabelecimento"]).strip(), "" if loj is None else loj.cnpj))
            continue

        isento = any(i.cnpj == loj.cnpj and i.inicio <= data_ref <= i.fim for i in premissas.isencoes_checkout)  # R-08
        # R-01: taxa contratada sobre valor_bruto (já negativo em estorno/reversão); R-02: half-up por linha.
        valor = brl(0) if isento else brl(r["valor_bruto"] * taxa / 100)
        comp[loj.cnpj].append(Componente(arq, ref, valor))
        if isento:
            # R-09: o que a Orbe cobrou na isenção é devolução ao lojista, não divergência.
            isentos[loj.cnpj].append(Componente(arq, ref, valor_taxa))
            continue
        aplicada = r["taxa_aplicada_pct"]
        if aplicada is not None and aplicada != taxa:
            # R-20, R-21: transação a transação, estorno com sinal negativo.
            dif = brl(r["valor_bruto"] * (aplicada - taxa) / 100)
            divs[loj.cnpj].append((Componente(arq, ref, dif), taxa, aplicada))

    # comissoes_por_lojista.csv e notas_a_emitir.csv (R-26, R-28)
    for cnpj in sorted(comp):
        campos = {"cnpj": cnpj, "lojista": nomes[cnpj], "linha_negocio": "CHECKOUT", "regra": "R-01 R-02 R-03 R-04 R-08 R-44"}
        linha = LinhaSaida.somando("comissoes_por_lojista.csv", f"COM-CHK-{cnpj}", campos, comp[cnpj])
        res.linhas.append(linha)
        assert linha.valor is not None
        if linha.valor > 0:
            nota = {
                "tomador_cnpj": cnpj,
                "tomador": nomes[cnpj],
                "linha_negocio": "CHECKOUT",
                "discriminacao": f"Comissão de intermediação de pagamentos (checkout), competência {competencia}",
                "regra": "R-26 R-28 R-45",
            }
            res.linhas.append(LinhaSaida.somando("notas_a_emitir.csv", f"NF-CHK-{cnpj}", nota, comp[cnpj]))
        else:
            res.linhas.append(
                _pendencia(
                    f"NOTA-{cnpj}",
                    "NOTA_NAO_EMITIDA",
                    [c for c in comp[cnpj] if c.valor != 0],
                    f"{nomes[cnpj]}: comissão de checkout de {competencia} é {_brl_txt(linha.valor)}. "
                    "Comissão zero ou negativa não emite nota e não passa automaticamente para o mês seguinte.",
                    HELENA,
                    "R-26",
                )
            )

    # divergencias_taxa.csv, transação a transação, e uma pendência por lojista (P-13, R-37)
    for cnpj in sorted(divs):
        for c, contratada, aplicada in divs[cnpj]:
            campos = {
                "cnpj": cnpj,
                "linha_negocio": "CHECKOUT",
                "ref_origem": c.ref_origem,
                "taxa_contratada_pct": contratada.normalize(),
                "taxa_aplicada_pct": aplicada.normalize(),
                "regra": "R-20 R-21 R-22",
            }
            res.linhas.append(LinhaSaida.somando("divergencias_taxa.csv", f"DIV-CHK-{c.ref_origem}", campos, [c]))
        pares = sorted({(ct, ap) for _, ct, ap in divs[cnpj]})
        taxas_txt = "; ".join(f"contratada {_pct_txt(ct)}, Orbe aplicou {_pct_txt(ap)}" for ct, ap in pares)
        comps = [c for c, _, _ in divs[cnpj]]
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            _pendencia(
                f"DIV-{cnpj}",
                "DIVERGENCIA_TAXA_ORBE",
                comps,
                f"{nomes[cnpj]}: a Orbe cobrou taxa diferente do contrato em {len(comps)} transações ({taxas_txt}). "
                f"Diferença líquida {_brl_txt(total)}: o lojista recebeu a menos e deve ser ressarcido; "
                "contestar com a Orbe. Vale o contrato, não o aviso.",
                f"{HELENA}: contestar com a Orbe",
                "R-20 R-21 R-22 R-25 R-37",
            )
        )

    # R-09: devolução da isenção (Casa do Estudante)
    for cnpj in sorted(isentos):
        comps = isentos[cnpj]
        total = sum((c.valor for c in comps), Decimal(0))
        res.linhas.append(
            _pendencia(
                f"ISENCAO-{cnpj}",
                "DEVOLUCAO_ISENCAO",
                comps,
                f"{nomes[cnpj]}: tarifa zero no checkout por concessão do comercial, mas a Orbe cobrou "
                f"{_brl_txt(total)} em {len(comps)} transações isentas. É devolução ao lojista, paga pela Tarvo, "
                "e não divergência de contrato. A Orbe não foi avisada da isenção: o desconto se repete no mês seguinte.",
                f"{HELENA} e Comercial",
                "R-08 R-09 R-44 R-49",
            )
        )

    # R-06, R-07: EC sem taxa vigente
    for ec in sorted(sem_contrato):
        comps = sem_contrato[ec]
        nome_orbe, cnpj = sem_contrato_info[ec]
        total = sum((c.valor for c in comps), Decimal(0))
        quem_e = f"EC {ec} ({nome_orbe})" + (f", CNPJ {cnpj}" if cnpj else ", sem lojista na aba de taxas vigente")
        res.linhas.append(
            _pendencia(
                f"SEMCONTRATO-{ec}",
                "SEM_CONTRATO",
                comps,
                f"{quem_e}: {len(comps)} transações sem taxa contratada vigente, fora da comissão e da nota. "
                f"A Orbe cobrou {_brl_txt(total)}. Não faturar até o comercial confirmar a taxa; quando confirmar, "
                "a taxa vale desde o início e estas linhas entram no fechamento seguinte.",
                "Comercial",
                "R-06 R-07",
            )
        )

    for i, (c, motivo) in enumerate(fora_regra, 1):
        res.linhas.append(
            _pendencia(
                f"FORAREGRA-{c.ref_origem}",
                "LANCAMENTO_FORA_DA_REGRA",
                [c],
                f"Transação {c.ref_origem}: {motivo}. Ficou fora da comissão; valor = taxa cobrada pela Orbe.",
                HELENA,
                "R-10 R-42",
            )
        )

    # P-14: id_transacao repetido com conteúdo diferente entre arquivos da Orbe
    for antiga, nova in dados.orbe.attrs.get("substituidas", []):
        ref = str(nova["id_transacao"])
        res.linhas.append(
            _pendencia(
                f"SUBSTITUIDA-{ref}",
                "AJUSTE_SUBSTITUIU_LINHA",
                [Componente(nova["arquivo_origem"], ref, nova["valor_bruto"])],
                f"Transação {ref} veio em {antiga['arquivo_origem']} e de novo, diferente, em {nova['arquivo_origem']}. "
                f"Valeu a versão do ajuste ({nova['tipo_lancamento']}, bruto {_brl_txt(nova['valor_bruto'])}, taxa "
                f"{nova['taxa_aplicada_pct']}%) no lugar de ({antiga['tipo_lancamento']}, bruto "
                f"{_brl_txt(antiga['valor_bruto'])}, taxa {antiga['taxa_aplicada_pct']}%). Valor = bruto da versão adotada.",
                HELENA,
                "P-14",
            )
        )

    # P-08: alerta de antecipação para lojista sem venda antes do mês
    if inicio_mes:
        for linha in _alertas_antecipacao(registros, cadastro, inicio_mes):
            res.linhas.append(linha)

    n_saida = sum(len(v) for v in comp.values()) + sum(len(v) for v in sem_contrato.values()) + len(fora_regra)
    res.conservacao["linhas_orbe"] = Decimal(len(registros) - n_saida)
    for ec, cs in sorted(sem_contrato.items()):
        res.conservacao[f"sem_contrato_{ec}"] = Decimal(len(cs))
    return res


def _alertas_antecipacao(registros: list[dict[str, Any]], cadastro: Cadastro, inicio_mes: date) -> list[LinhaSaida]:
    """P-08: lojista sem venda antes do mês cuja antecipação acumulada supera as vendas acumuladas (o pico).

    "Sem venda antes do mês", pelo que os arquivos mostram: nenhuma linha da Orbe aponta para venda
    anterior ao mês e o EC não tem taxa vigente na planilha no primeiro dia do mês.
    """
    por_ec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    antigo: set[str] = set()
    for r in registros:
        ec = str(r["cod_estabelecimento"]).strip()
        por_ec[ec].append(r)
        dvo = _data(r["data_venda_original"])
        if dvo and dvo < inicio_mes:
            antigo.add(ec)

    saida = []
    for ec in sorted(por_ec):
        if ec in antigo:
            continue
        loj = cadastro.lojista_por_ec(ec)
        if loj and cadastro.taxa_contratada_pct(loj.cnpj, "DEBITO", 1, inicio_mes) is not None:
            continue
        linhas = sorted(
            (r for r in por_ec[ec] if r["tipo_lancamento"] in TIPOS and r["tipo_lancamento"] != "ESTORNO"),
            key=lambda r: _data(r["data_movimento"]) or inicio_mes,
        )
        ant = ven = Decimal(0)
        pico: tuple[Decimal, date | None, Decimal, Decimal] = (Decimal(0), None, Decimal(0), Decimal(0))
        dias = sorted({_data(r["data_movimento"]) for r in linhas} - {None})
        for dia in dias:
            for r in linhas:
                if _data(r["data_movimento"]) != dia:
                    continue
                if r["tipo_lancamento"] == "VENDA":
                    ven += r["valor_bruto"]
                else:
                    ant += r["valor_bruto"]
            if ant - ven > pico[0]:
                pico = (ant - ven, dia, ant, ven)
        excesso, dia_pico, ant_pico, ven_pico = pico
        if dia_pico is None:
            continue
        comps = [
            Componente(
                r["arquivo_origem"],
                str(r["id_transacao"]),
                r["valor_bruto"] if r["tipo_lancamento"] != "VENDA" else -r["valor_bruto"],
            )
            for r in linhas
            if (_data(r["data_movimento"]) or inicio_mes) <= dia_pico
        ]
        reversoes = [r for r in linhas if r["tipo_lancamento"] == "REVERSAO ANTECIPACAO"]
        rev_txt = (
            f" Houve {len(reversoes)} reversões de antecipação no mês, somando "
            f"{_brl_txt(-sum((r['valor_bruto'] for r in reversoes), Decimal(0)))}."
            if reversoes
            else ""
        )
        nome = loj.nome if loj else str(linhas[0]["nome_estabelecimento"]).strip() if linhas else ec
        saida.append(
            _pendencia(
                f"ANTECIPACAO-{ec}",
                "ALERTA_ANTECIPACAO",
                comps,
                f"{nome} (EC {ec}), lojista sem venda antes do mês: em {dia_pico:%d/%m} a antecipação acumulada "
                f"({_brl_txt(ant_pico)}) superou as vendas acumuladas ({_brl_txt(ven_pico)}) em {_brl_txt(excesso)}."
                f"{rev_txt} Valor = antecipações menos vendas até o pico.",
                f"{HELENA} e Comercial",
                "P-08 R-36",
            )
        )
    return saida
