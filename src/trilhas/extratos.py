"""Trilha C — Extratos: classifica cada lançamento do Aurora e do Meridiano no plano de contas.

`conta_codigo` é a contrapartida do movimento (R-29): o que já estava registrado baixa a
conta onde estava (R-30); o resto vai para receita ou despesa. As regras são genéricas
(texto da descrição + sinal + cruzamento com outras fontes), nunca por linha ou FITID
de setembro. O que nenhuma regra pega vai para HUMANO com pendência (D-02).
"""

import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

import pandas as pd

from src.core.cadastro import Cadastro
from src.core.entrada import AURORA, MERIDIANO, DadosEntrada, competencia
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.core.pendencias import pendencia
from src.premissas import Premissas
from src.trilhas.checkout import _brl_txt


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", s.upper())


@dataclass
class Lanc:
    banco: str
    arquivo: str
    ref: str
    data: str
    descricao: str
    valor: Decimal

    @property
    def desc(self) -> str:
        return unicodedata.normalize("NFKD", self.descricao).encode("ascii", "ignore").decode().upper()


@dataclass(frozen=True)
class Regra:
    nome: str
    conta: str
    aplica: Callable[[Lanc, "Contexto"], bool]
    pendencia: str | None = None  # tipo de pendência que a regra abre, se abre


@dataclass
class Contexto:
    lojistas: list[str]  # nomes normalizados (planilha, Orbe, Ponte)
    competencia: str  # AAAA-MM do fechamento
    transf_recebidas: list[Decimal]  # créditos "mesma titularidade" no outro banco

    def eh_lojista(self, trecho: str) -> bool:
        t = _norm(trecho)
        if len(t) < 4:
            return False
        return any(n.startswith(t) or t.startswith(n) for n in self.lojistas if len(n) >= 4)

    def competencia_anterior(self, desc: str) -> bool:
        """Folha/imposto 'MM/AAAA' de mês anterior ao fechado: já estava provisionado (R-30)."""
        m = re.search(r"(\d{2})/(\d{4})", desc)
        return m is not None and f"{m.group(2)}-{m.group(1)}" < self.competencia


def _apos(prefixo: str, desc: str) -> str:
    return desc.split(prefixo, 1)[1] if prefixo in desc else ""


# Ordem importa: a mais específica primeiro. Contas lidas do plano carregado (conferidas
# abaixo); regra que aponte para conta que não aceita lançamento vira HUMANO, não silêncio.
REGRAS: list[Regra] = [
    # --- entradas ---
    Regra("TED da adquirente Orbe: baixa recebíveis", "1.1.03.001",
          lambda l, c: l.valor > 0 and "ORBE" in l.desc),
    Regra("Repasse de comissão da Ponte de mês anterior: baixa o a receber (R-30)", "1.1.03.002",
          lambda l, c: l.valor > 0 and "PONTE CAMBIO" in l.desc and "REPASSE" in l.desc),
    Regra("Transferência recebida de conta própria", "1.1.09.001",
          lambda l, c: l.valor > 0 and "MESMA TITULARIDADE" in l.desc),
    Regra("Rendimento de aplicação", "3.2.01",
          lambda l, c: l.valor > 0 and "RENDIMENTO" in l.desc),
    Regra("Resgate de aplicação", "1.1.02.001",
          lambda l, c: l.valor > 0 and "RESGATE" in l.desc),
    Regra("Devolução de Pix a lojista: o repasse volta a ser devido (P-04)", "2.1.01.001",
          lambda l, c: l.valor > 0 and "DEVOLUCAO PIX" in l.desc, "DEVOLUCAO_PIX"),
    Regra("Pix de lojista para remessa: recursos de clientes (R-34)", "2.1.02.001",
          lambda l, c: l.valor > 0 and l.banco == "MERIDIANO" and "PIX RECEB" in l.desc
          and c.eh_lojista(_apos("PIX RECEB", l.desc))),
    Regra("Crédito sem identificação: não é receita até identificar (R-32)", "1.1.09.002",
          lambda l, c: l.valor > 0 and ("SEM IDENTIFICACAO" in l.desc or "PIX RECEB" in l.desc),
          "CREDITO_NAO_IDENTIFICADO"),
    # --- saídas ---
    Regra("Liquidação de operações de câmbio com a Ponte", "2.1.02.001",
          lambda l, c: l.valor < 0 and "PONTE CAMBIO" in l.desc),
    Regra("Transferência para conta própria", "1.1.09.001",
          lambda l, c: l.valor < 0 and "TRANSF ENTRE CONTAS" in l.desc),
    Regra("Aplicação financeira", "1.1.02.001",
          lambda l, c: l.valor < 0 and "APLICACAO" in l.desc),
    Regra("Repasse a lojista", "2.1.01.001",
          lambda l, c: l.valor < 0 and "PIX ENVIADO" in l.desc
          and c.eh_lojista(_apos("PIX ENVIADO", l.desc))),
    Regra("Folha de mês anterior: baixa salários a pagar (R-30)", "2.1.04.001",
          lambda l, c: l.valor < 0 and ("SALARIO" in l.desc or "FOLHA" in l.desc)
          and c.competencia_anterior(l.desc)),
    Regra("Folha do mês", "4.1.01",
          lambda l, c: l.valor < 0 and ("SALARIO" in l.desc or "FOLHA" in l.desc)),
    Regra("ISS: baixa ISS a recolher (R-30)", "2.1.03.003",
          lambda l, c: l.valor < 0 and "ISS" in l.desc.split()),
    Regra("INSS: baixa INSS a recolher (R-30)", "2.1.04.002",
          lambda l, c: l.valor < 0 and "INSS" in l.desc),
    Regra("FGTS: baixa FGTS a recolher (R-30)", "2.1.04.003",
          lambda l, c: l.valor < 0 and "FGTS" in l.desc),
    Regra("DARF IRRF: baixa IRRF a recolher (R-30)", "2.1.03.004",
          lambda l, c: l.valor < 0 and "DARF" in l.desc and "IRRF" in l.desc),
    Regra("DARF PIS: baixa PIS a recolher (R-30)", "2.1.03.001",
          lambda l, c: l.valor < 0 and "DARF" in l.desc and "PIS" in l.desc.split()),
    Regra("DARF COFINS: baixa COFINS a recolher (R-30)", "2.1.03.002",
          lambda l, c: l.valor < 0 and "DARF" in l.desc and "COFINS" in l.desc),
    Regra("IOF", "4.3.01", lambda l, c: l.valor < 0 and "IOF" in l.desc.split()),
    Regra("Tarifa bancária", "4.2.01",
          lambda l, c: l.valor < 0 and re.search(r"\bTAR(IFA)?\b", l.desc) is not None),
    Regra("Condomínio/aluguel", "4.2.02",
          lambda l, c: l.valor < 0 and ("CONDOMINIO" in l.desc or "ALUGUEL" in l.desc)),
    Regra("Cloud e infraestrutura", "4.2.03",
          lambda l, c: l.valor < 0 and any(k in l.desc for k in ("AMAZON WEB", "AWS", "AZURE", "GOOGLE CLOUD"))),
    Regra("Software e assinaturas", "4.2.04",
          lambda l, c: l.valor < 0 and any(k in l.desc for k in ("WORKSPACE", "SOFTWARE", "ASSINATURA", "LICENCA"))),
    Regra("Seguro", "4.2.05", lambda l, c: l.valor < 0 and "SEGURO" in l.desc),
    Regra("Serviços contábeis e jurídicos", "4.2.06",
          lambda l, c: l.valor < 0 and any(k in l.desc for k in ("CONTABIL", "ADVOCACIA", "JURIDIC"))),
]  # fmt: skip


def _lancamentos(dados: DadosEntrada) -> list[Lanc]:
    out: list[Lanc] = []
    if not dados.aurora.empty:
        for r in dados.aurora.to_dict("records"):
            out.append(Lanc("AURORA", dados.arquivos[AURORA], r["linha_fisica"], r["data"],
                            r["descricao"], brl(r["valor"])))  # fmt: skip
    if not dados.meridiano.empty:
        for r in dados.meridiano.to_dict("records"):
            out.append(Lanc("MERIDIANO", dados.arquivos[MERIDIANO], r["fitid"], r["data"],
                            str(r["descricao"] or ""), brl(r["valor"])))  # fmt: skip
    return out


def _nomes_lojistas(dados: DadosEntrada, cadastro: Cadastro) -> list[str]:
    nomes = {_norm(l.nome) for l in cadastro.lojistas()}
    nomes |= {_norm(l.nome) for l in getattr(cadastro, "inativos_por_ec", {}).values()}
    if not dados.orbe.empty:
        nomes |= {_norm(n) for n in dados.orbe["nome_estabelecimento"].unique()}
    if not dados.ponte.empty and "Cliente" in dados.ponte:
        nomes |= {_norm(str(n)) for n in dados.ponte["Cliente"].dropna().unique()}
    return sorted(n for n in nomes if n)


def _conferir_teds_ponte(dados: DadosEntrada, lancs: list[Lanc]) -> list[Lanc]:
    """Cada TED à Ponte = Σ(Valor R$ + IOF R$) das operações contratadas no dia.
    Devolve as TEDs que não batem (deduplicando o Nº Operação, R-13)."""
    if dados.ponte.empty:
        return []
    p = dados.ponte.drop_duplicates("Nº Operação")
    dia = pd.to_datetime(p["Data Contratação"], errors="coerce").dt.strftime("%Y-%m-%d")
    devido: dict[str, Decimal] = defaultdict(Decimal)
    for d, v, iof in zip(dia, p["Valor R$"], p["IOF R$"]):
        devido[d] += Decimal(str(v)) + Decimal(str(iof or 0))
    return [
        l
        for l in lancs
        if l.valor < 0 and "PONTE CAMBIO" in l.desc and brl(devido.get(l.data, 0)) != -l.valor
    ]


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="extratos")
    lancs = _lancamentos(dados)
    if not lancs:
        return res

    plano = dados.plano_contas
    analiticas: set[str] = (
        set(plano.loc[plano["ACEITA_LANCTO"].str.upper() == "S", "COD_CONTA"])
        if not plano.empty
        else set()
    )
    transf_receb = [l.valor for l in lancs if l.valor > 0 and "MESMA TITULARIDADE" in l.desc]
    ctx = Contexto(_nomes_lojistas(dados, cadastro), competencia(dados), transf_receb)

    pend: dict[str, list[tuple[Lanc, Regra]]] = defaultdict(list)
    humanos: list[Lanc] = []
    contagem = {"REGRA": 0, "IA": 0, "HUMANO": 0}

    for l in lancs:
        regra = next((r for r in REGRAS if r.aplica(l, ctx)), None)
        if regra is not None and regra.conta in analiticas:
            conta, metodo, confianca = regra.conta, "REGRA", Decimal(1)
            if regra.pendencia:
                pend[regra.pendencia].append((l, regra))
        else:
            # D-02: sem regra (ou regra apontando para conta que o plano não aceita).
            conta, metodo, confianca = "", "HUMANO", Decimal(0)
            humanos.append(l)
        contagem[metodo] += 1
        prefixo = "AUR" if l.banco == "AURORA" else "MER"
        res.linhas.append(
            LinhaSaida.somando(
                "lancamentos_classificados.csv",
                f"LAN-{prefixo}-{l.ref}",
                {
                    "banco": l.banco,
                    "ref_origem": l.ref,
                    "data": l.data,
                    "descricao": l.descricao,
                    "conta_codigo": conta,
                    "metodo": metodo,
                    "confianca": confianca,
                },
                [Componente(l.arquivo, l.ref, l.valor)],
            )
        )

    # --- pendências (uma por tipo de caso e contraparte) ---
    for l, _ in pend.get("CREDITO_NAO_IDENTIFICADO", []):
        res.linhas.append(
            pendencia(
                "EXT", f"NAOIDENT-{l.ref}", "CREDITO_NAO_IDENTIFICADO",
                [Componente(l.arquivo, l.ref, l.valor)],
                f"{l.banco} {l.ref} ({l.data}): crédito de {_brl_txt(l.valor)} sem identificação "
                f"('{l.descricao}'). Lançado em créditos não identificados; não é receita até "
                "alguém identificar a origem (R-32).",
                "Caio (identifica o pagador com o banco, até o fechamento de outubro)",  # R-55
            )
        )  # fmt: skip
    for l, _ in pend.get("DEVOLUCAO_PIX", []):
        res.linhas.append(
            pendencia(
                "EXT", f"DEVOLUCAO-{l.ref}", "DEVOLUCAO_PIX",
                [Componente(l.arquivo, l.ref, l.valor)],
                f"{l.banco} {l.ref} ({l.data}): '{l.descricao}' de {_brl_txt(l.valor)}. Repasse "
                "ao lojista que voltou, motivo desconhecido; o valor volta a ser devido ao "
                "lojista (P-04). Confirmar com o lojista e repetir o repasse.",
                "Helena",
            )
        )  # fmt: skip

    # P-11, R-33, R-39: transferência para conta própria sem crédito correspondente no mês.
    disponiveis = list(transf_receb)
    for l in lancs:
        if l.valor < 0 and "TRANSF ENTRE CONTAS" in l.desc:
            if -l.valor in disponiveis:
                disponiveis.remove(-l.valor)
            else:
                res.linhas.append(
                    pendencia(
                        "EXT", f"TRANSF-{l.ref}", "ACOMPANHAMENTO_TRANSFERENCIA",
                        [Componente(l.arquivo, l.ref, l.valor)],
                        f"{l.banco} {l.ref} ({l.data}): transferência de {_brl_txt(-l.valor)} "
                        "para conta própria sem crédito correspondente no outro extrato do mês. "
                        "Conferir a entrada no mês seguinte (R-33).",
                        "Helena",
                    )
                )  # fmt: skip

    for l in _conferir_teds_ponte(dados, lancs):
        res.linhas.append(
            pendencia(
                "EXT", f"TEDPONTE-{l.ref}", "TED_PONTE_NAO_CONFERE",
                [Componente(l.arquivo, l.ref, l.valor)],
                f"{l.banco} {l.ref} ({l.data}): TED de {_brl_txt(-l.valor)} à Ponte não bate com "
                "Σ(Valor R$ + IOF R$) das operações contratadas no dia. Conferir com a Ponte.",
                "Helena",
            )
        )  # fmt: skip

    if humanos:
        res.linhas.append(
            pendencia(
                "EXT", "CLASSIFICAR", "CLASSIFICACAO_MANUAL",
                [Componente(l.arquivo, l.ref, l.valor) for l in humanos],
                f"{len(humanos)} lançamentos sem regra de classificação. Classificar à mão e, se "
                "o caso se repetir, virar regra.",
                "Helena",
            )
        )  # fmt: skip

    # Invariantes: nenhum lançamento some; saldo do Aurora fecha.
    res.conservacao["lancamentos"] = Decimal(
        len(dados.aurora) + len(dados.meridiano) - sum(contagem.values())
    )
    a = dados.aurora
    if not a.empty and a.attrs.get("saldo_anterior") is not None and a.attrs.get("saldo_final") is not None:
        soma = sum((brl(v) for v in a["valor"]), Decimal(0))
        res.conservacao["saldo_aurora"] = (
            brl(a.attrs["saldo_anterior"]) + soma - brl(a.attrs["saldo_final"])
        )
    res.conservacao["teds_ponte_nao_conferem"] = Decimal(len(_conferir_teds_ponte(dados, lancs)))
    return res
