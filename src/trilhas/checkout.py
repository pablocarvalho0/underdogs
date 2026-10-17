"""Trilha A — Checkout (Dev 1): comissão CHECKOUT por lojista (nível mínimo).

Divergências de taxa, notas e pendências ficam para as próximas fatias.
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from src.core.cadastro import Cadastro
from src.core.entrada import DadosEntrada
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.premissas import Premissas


def _data(s: str) -> date:
    return datetime.strptime(s.strip(), "%d/%m/%Y").date()


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    comp: dict[str, list[Componente]] = defaultdict(list)
    sem_contrato: dict[str, int] = defaultdict(int)
    n_comissao = 0
    n_sem = 0

    for r in dados.orbe.to_dict("records"):
        ec = str(r["cod_estabelecimento"]).strip()
        tipo = str(r["tipo_lancamento"]).strip()
        loj = cadastro.lojista_por_ec(ec)  # R-05: aliases só via cadastro
        if tipo == "VENDA":
            modalidade, data_ref = r["modalidade"], _data(r["data_movimento"])
        elif tipo == "ESTORNO":
            # R-03: taxa da data da venda original; faixa vem da linha do estorno.
            modalidade, data_ref = r["modalidade"], _data(r["data_venda_original"])
        elif tipo == "ANTECIPACAO":
            # R-44: vale a data da antecipação.
            modalidade, data_ref = "ANTECIPACAO", _data(r["data_movimento"])
        elif tipo == "REVERSAO ANTECIPACAO":
            modalidade, data_ref = "ANTECIPACAO", _data(r["data_venda_original"])
        else:
            raise ValueError(f"Orbe: tipo_lancamento desconhecido {tipo!r} em {r['id_transacao']}")

        parcelas = int(r["qtd_parcelas"]) if str(r["qtd_parcelas"]).strip() not in ("", "nan") else 1
        taxa = (
            cadastro.taxa_contratada_pct(loj.cnpj, str(modalidade), parcelas, data_ref) if loj else None
        )
        if loj is None or taxa is None:
            sem_contrato[ec] += 1
            n_sem += 1
            continue

        isento = any(i.cnpj == loj.cnpj and i.inicio <= data_ref <= i.fim for i in premissas.isencoes_checkout)  # R-08
        # R-01: taxa contratada sobre valor_bruto (já negativo em estorno/reversão); R-02: half-up por linha.
        valor = brl(0) if isento else brl(r["valor_bruto"] * taxa / 100)
        comp[loj.cnpj].append(Componente(r["arquivo_origem"], r["id_transacao"], valor))
        n_comissao += 1

    res = ResultadoTrilha(trilha="checkout")
    nomes = {l.cnpj: l.nome for l in cadastro.lojistas()}
    for cnpj in sorted(comp):
        campos = {"cnpj": cnpj, "lojista": nomes[cnpj], "linha_negocio": "CHECKOUT"}
        res.linhas.append(LinhaSaida.somando("comissoes_por_lojista.csv", f"COM-CHK-{cnpj}", campos, comp[cnpj]))

    res.conservacao["linhas_orbe"] = Decimal(len(dados.orbe) - (n_comissao + n_sem))
    for ec, n in sorted(sem_contrato.items()):
        res.conservacao[f"sem_contrato_{ec}"] = Decimal(n)
    return res
