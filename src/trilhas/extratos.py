"""Trilha C — Extratos (Dev 2): classificação dos lançamentos Aurora e Meridiano no plano de contas e pendências.

Contrato: docs/plano-engenharia.md §2 e §4. Cada lançamento sai com um componente (a própria
linha do extrato). `conta_codigo` é a contrapartida do movimento (R-29). Só classifica o que uma
regra do HIPOTESES.md ou a descrição do plano de contas determina; o resto vira pendência (R-47, P-16).
Não casa nome do extrato com lojista (lacunas §7.3).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.core.cadastro import Cadastro
from src.core.entrada import ARQ_AURORA, ARQ_MERIDIANO, DadosEntrada
from src.core.model import Componente, LinhaSaida, ResultadoTrilha, brl
from src.premissas import Premissas

HELENA = "Helena (Financeiro Tarvo)"
AURORA = "AURORA"
MERIDIANO = "MERIDIANO"

CONF_REGRA = Decimal("1.0")
# lacunas N-10/H-03: DARF sem competência no histórico é tratado como de agosto (baixa de passivo, R-30).
# Hipótese não confirmada (lacunas §7.1: "confianca pode ser < 1").
CONF_DARF_SEM_COMPETENCIA = Decimal("0.9")

# Tipos de pendência desta trilha.
T_NAO_IDENTIFICADO = "CREDITO_NAO_IDENTIFICADO"  # R-32, N-02, E-09
T_DEVOLUCAO = "DEVOLUCAO_PIX_LOJISTA"  # R-32, P-04, N-03
T_TRANSFERENCIA = "ACOMPANHAMENTO_TRANSFERENCIA"  # R-33, R-39, P-11, N-14
T_INDETERMINADO = "CLASSIFICACAO_INDETERMINADA"  # R-47, P-16


@dataclass(frozen=True)
class _Regra:
    padrao: str  # regex sobre a descrição em maiúsculas
    conta: str
    regra: str  # ID da regra + critério (L-10)
    sinal: int = 0  # +1 só crédito, -1 só débito, 0 qualquer
    banco: str | None = None  # None = vale para os dois extratos
    competencia: bool = False  # R-30: baixa de passivo só para competência anterior ao pagamento
    pendencia: str | None = None  # tipo de pendência que a linha também gera


# A mais específica vem primeiro. Contas conferidas contra o plano carregado (ACEITA_LANCTO = S).
REGRAS: tuple[_Regra, ...] = (
    # --- Créditos ---
    _Regra(r"^TED RECEBIDA\b.*\bORBE ADQUIRENCIA\b", "1.1.03.001", "R-29/R-35: TED da Orbe baixa o recebível; plano 1.1.03.001 Recebíveis de adquirente - Orbe", +1),
    _Regra(r"^PIX RECEBIDO\b.*\bSEM IDENTIFICACAO\b", "1.1.09.002", "R-32: não é receita até identificar; plano 1.1.09.002 Créditos não identificados", +1, pendencia=T_NAO_IDENTIFICADO),
    _Regra(r"^DEVOLUCAO PIX\b", "2.1.01.001", "R-32/P-04: repasse que voltou, volta a ser devido; plano 2.1.01.001 Repasses a lojistas a pagar", +1, AURORA, pendencia=T_DEVOLUCAO),
    _Regra(r"^TED RECEB(IDA)? PONTE CAMBIO\b.*\bREPASSE COMISSAO\b", "1.1.03.002", "R-30: repasse da Ponte de comissão de mês anterior já registrado; plano 1.1.03.002 Comissões de intermediação a receber - câmbio", +1, competencia=True),
    _Regra(r"^PIX RECEB\b", "2.1.02.001", "R-34/P-12 e §1 (Pix de lojista = Σ operações de remessa): plano 2.1.02.001 Recursos de lojistas para remessas a liquidar", +1, MERIDIANO),
    _Regra(r"\bMESMA TITULARIDADE\b", "1.1.09.001", "P-11: transferência entre contas próprias; plano 1.1.09.001 Transferências entre contas próprias", +1),
    _Regra(r"^RESGATE AUTOMATICO\b", "1.1.02.001", "R-29: resgate baixa a aplicação; plano 1.1.02.001 Aplicação automática Meridiano", +1, MERIDIANO),
    _Regra(r"^RENDIMENTO APLIC", "3.2.01", "R-29 natureza receita; plano 3.2.01 Rendimentos de aplicações", +1),
    # --- Débitos ---
    _Regra(r"^TRANSF ENTRE CONTAS\b", "1.1.09.001", "P-11: transferência entre contas próprias; plano 1.1.09.001 Transferências entre contas próprias", -1),
    _Regra(r"^TED ENVIADA PONTE CAMBIO\b.*\bLIQ OPERACOES\b", "2.1.02.001", "§1 (TED = Σ Valor R$ + IOF R$ das operações do dia): liquida recursos de remessa; plano 2.1.02.001 Recursos de lojistas para remessas a liquidar", -1),
    _Regra(r"^APLICACAO AUTOMATICA\b", "1.1.02.001", "R-29: aplicação; plano 1.1.02.001 Aplicação automática Meridiano", -1, MERIDIANO),
    _Regra(r"\bFOLHA\b", "2.1.04.001", "R-30: folha de competência anterior provisionada, baixa; plano 2.1.04.001 Salários a pagar", -1, competencia=True),
    _Regra(r"\bISS\b", "2.1.03.003", "R-30: ISS de competência anterior provisionado, baixa; plano 2.1.03.003 ISS a recolher", -1, competencia=True),
    _Regra(r"\bINSS\b", "2.1.04.002", "R-30: INSS de competência anterior provisionado, baixa; plano 2.1.04.002 INSS a recolher", -1, competencia=True),
    _Regra(r"\bFGTS\b", "2.1.04.003", "R-30: FGTS de competência anterior provisionado, baixa; plano 2.1.04.003 FGTS a recolher", -1, competencia=True),
    _Regra(r"^DEBITO DARF\b.*\bIRRF\b", "2.1.03.004", "R-30 + lacunas N-10/H-03: DARF de competência anterior provisionado, baixa; plano 2.1.03.004 IRRF a recolher", -1, competencia=True),
    _Regra(r"^DEBITO DARF\b.*\bPIS\b", "2.1.03.001", "R-30 + lacunas N-10/H-03: DARF de competência anterior provisionado, baixa; plano 2.1.03.001 PIS a recolher", -1, competencia=True),
    _Regra(r"^DEBITO DARF\b.*\bCOFINS\b", "2.1.03.002", "R-30 + lacunas N-10/H-03: DARF de competência anterior provisionado, baixa; plano 2.1.03.002 COFINS a recolher", -1, competencia=True),
    _Regra(r"^IOF\b", "4.3.01", "N-12/E-10: IOF, sem dúvida de conta; plano 4.3.01 IOF", -1),
    _Regra(r"^TAR(IFA)?\b", "4.2.01", "R-30: tarifa é despesa do mês; plano 4.2.01 Tarifas bancárias", -1),
    _Regra(r"\b(CONDOMINIO|ALUGUEL)\b", "4.2.02", "R-30: aluguel é despesa do mês; plano 4.2.02 Aluguel e condomínio", -1),
    _Regra(r"\bAMAZON WEB SERVICES\b", "4.2.03", "R-30: cloud é despesa do mês; plano 4.2.03 Cloud e infraestrutura", -1),
    _Regra(r"\bGOOGLE WORKSPACE\b", "4.2.04", "R-30: assinatura é despesa do mês; plano 4.2.04 Softwares e assinaturas", -1),
    _Regra(r"^SEGURO\b", "4.2.05", "R-30: só folha, impostos e repasse Ponte estavam registrados, o resto é despesa; plano 4.2.05 Seguros", -1),
    _Regra(r"^PIX ENVIADO CONTABILIDADE\b", "4.2.06", "R-30: serviço é despesa do mês; plano 4.2.06 Serviços contábeis e jurídicos", -1, AURORA),
    _Regra(r"^PIX ENVIADO\b", "2.1.01.001", "R-36: Pix enviado é o repasse ao lojista (mesmo critério da P-04); plano 2.1.01.001 Repasses a lojistas a pagar", -1, AURORA),
)

_RE_COMPETENCIA = re.compile(r"\b(\d{2})/(\d{4})\b")
_RE_CNPJ = re.compile(r"\b(\d{14})\b")
_RE_TRANSF_SAIDA = re.compile(r"^TRANSF ENTRE CONTAS\b")
_RE_TRANSF_ENTRADA = re.compile(r"\bMESMA TITULARIDADE\b")


@dataclass
class _Lanc:
    banco: str
    arquivo: str
    ref: str
    data: date
    descricao: str
    valor: Decimal

    @property
    def comp(self) -> Componente:
        return Componente(self.arquivo, self.ref, self.valor)


@dataclass
class _Pend:
    chave: str
    tipo: str
    comps: list[Componente]
    motivo: str
    regra: str


def _brl_txt(v: Decimal) -> str:
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _data_txt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _ler(dados: DadosEntrada) -> list[_Lanc]:
    out: list[_Lanc] = []
    for r in dados.aurora.to_dict("records"):
        out.append(_Lanc(AURORA, ARQ_AURORA, str(r["linha_fisica"]), _iso(r["data"]), str(r["descricao"]).strip(), brl(r["valor"])))
    for r in dados.meridiano.to_dict("records"):
        out.append(_Lanc(MERIDIANO, ARQ_MERIDIANO, str(r["fitid"]), _iso(r["data"]), str(r["descricao"]).strip(), brl(r["valor"])))
    return out


def _iso(v: Any) -> date:
    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def _casa(regra: _Regra, ln: _Lanc) -> bool:
    if regra.banco and regra.banco != ln.banco:
        return False
    if regra.sinal and (ln.valor > 0) != (regra.sinal > 0):
        return False
    return re.search(regra.padrao, ln.descricao.upper()) is not None


def _contas_analiticas(dados: DadosEntrada) -> dict[str, str]:
    pc = dados.plano_contas
    ok = pc[pc["ACEITA_LANCTO"].astype(str).str.strip().str.upper() == "S"]
    return {str(c).strip(): str(d).strip() for c, d in zip(ok["COD_CONTA"], ok["DESCRICAO"])}


def _parear_transferencias(lancs: list[_Lanc]) -> list[_Lanc]:
    """R-33/R-39/P-11: transferência Aurora→Meridiano sem crédito de mesmo valor no Meridiano (mesma data ou depois)."""
    saidas = sorted((l for l in lancs if l.banco == AURORA and l.valor < 0 and _RE_TRANSF_SAIDA.search(l.descricao.upper())), key=lambda l: l.data)
    entradas = sorted((l for l in lancs if l.banco == MERIDIANO and l.valor > 0 and _RE_TRANSF_ENTRADA.search(l.descricao.upper())), key=lambda l: l.data)
    livres = list(entradas)
    sem_par: list[_Lanc] = []
    for s in saidas:
        par = next((e for e in livres if e.valor == -s.valor and e.data >= s.data), None)
        if par is None:
            sem_par.append(s)
        else:
            livres.remove(par)
    return sem_par + livres  # créditos no Meridiano sem saída no Aurora também ficam para conferência


def rodar(dados: DadosEntrada, cadastro: Cadastro, premissas: Premissas) -> ResultadoTrilha:
    res = ResultadoTrilha(trilha="extratos")
    contas = _contas_analiticas(dados)
    lancs = _ler(dados)

    classificados: list[_Lanc] = []
    so_pendencia: list[_Lanc] = []
    pends: list[_Pend] = []
    por_tipo: dict[tuple[str, str], list[_Lanc]] = {}

    for ln in lancs:
        regra = next((r for r in REGRAS if _casa(r, ln)), None)
        conta, txt, conf = (regra.conta, regra.regra, CONF_REGRA) if regra else ("", "", CONF_REGRA)
        motivo_indet = ""
        if regra is None:
            motivo_indet = "nenhuma regra do HIPOTESES.md nem descrição do plano de contas determina a contrapartida"
        elif conta not in contas:
            motivo_indet = f"a regra aponta para a conta {conta}, que não existe ou não aceita lançamento no plano carregado"
        elif regra.competencia:
            m = _RE_COMPETENCIA.search(ln.descricao)
            if m is None:
                conf = CONF_DARF_SEM_COMPETENCIA  # lacunas N-10/H-03: sem mês no histórico, tratado como mês anterior
                txt += " (sem competência no histórico: lacunas N-10/H-03)"
            elif (int(m.group(2)), int(m.group(1))) >= (ln.data.year, ln.data.month):
                # R-30 só cobre o que já estava provisionado (mês anterior); R-31: provisão do mês não é nossa.
                motivo_indet = f"competência {m.group(0)} não é anterior ao pagamento; a R-30 só cobre o que já estava provisionado"
            else:
                txt += f" (competência {m.group(0)})"

        if motivo_indet:
            so_pendencia.append(ln)
            pends.append(
                _Pend(
                    f"{'AUR' if ln.banco == AURORA else 'MER'}-{ln.ref}",
                    T_INDETERMINADO,
                    [ln.comp],
                    f"Lançamento de {_brl_txt(ln.valor)} em {_data_txt(ln.data)} no {ln.banco.title()} ({ln.ref}, '{ln.descricao}') "
                    f"sem conta definida: {motivo_indet}. Indicar a conta de contrapartida (R-47).",
                    "R-47/P-16: sem regra, não classifica",
                )
            )
            continue

        assert regra is not None
        classificados.append(ln)
        campos = {
            "banco": ln.banco,
            "ref_origem": ln.ref,
            "data": ln.data,
            "descricao": ln.descricao,
            "conta_codigo": conta,
            "metodo": "REGRA",
            "confianca": conf,
            "regra": txt,
        }
        prefixo = "LAN-AUR-" if ln.banco == AURORA else "LAN-MER-"
        res.linhas.append(LinhaSaida.somando("lancamentos_classificados.csv", prefixo + ln.ref, campos, [ln.comp]))
        if regra.pendencia:
            if regra.pendencia == T_NAO_IDENTIFICADO:
                m = _RE_CNPJ.search(ln.descricao)
                contraparte = m.group(1) if m else ln.ref  # P-13: uma por contraparte (CNPJ do histórico)
            else:
                contraparte = re.sub(r"^DEVOLUCAO PIX\s*-?\s*", "", ln.descricao.upper()).strip() or ln.ref
            por_tipo.setdefault((regra.pendencia, contraparte), []).append(ln)

    # R-32, N-02/E-09 e P-04, N-03: pendência por contraparte (P-13).
    cnpjs = {l.cnpj for l in cadastro.lojistas()}
    for (tipo, contraparte), ls in por_tipo.items():
        refs = ", ".join(f"{l.ref} {_brl_txt(l.valor)} em {_data_txt(l.data)}" for l in ls)
        if tipo == T_NAO_IDENTIFICADO:
            if _RE_CNPJ.fullmatch(contraparte):
                onde = "está no cadastro de lojistas" if contraparte in cnpjs else "não está no cadastro de lojistas (planilha de taxas)"
                pista = f"O histórico do banco traz o CNPJ {contraparte}, que {onde}."
            else:
                pista = "O histórico do banco não traz CNPJ do pagador."
            motivo = (
                f"Pix recebido sem identificação do pagador ({refs}). {pista} Não é receita até alguém identificar (R-32): "
                f"ficou em 1.1.09.002 Créditos não identificados. Identificar quem pagou e a que se refere."
            )
            regra_p = "R-32, N-02/E-09: CNPJ extraído do histórico"
        else:
            motivo = (
                f"Devolução de Pix de repasse ao lojista ({contraparte}; {refs}), motivo desconhecido (R-32). "
                f"Classificada em 2.1.01.001 Repasses a lojistas a pagar (P-04): o valor volta a ser devido ao lojista. "
                f"Confirmar o motivo da devolução e se o valor deve ser repassado de novo."
            )
            regra_p = "R-32, P-04, N-03"
        pends.append(_Pend("-".join(l.ref for l in ls), tipo, [l.comp for l in ls], motivo, regra_p))

    # R-33/R-39/P-11/N-14: transferência entre contas sem o crédito do outro lado no mês é acompanhamento.
    for ln in _parear_transferencias(lancs):
        # §7.2: o valor é o que falta conferir (crédito esperado), positivo.
        comp = Componente(ln.arquivo, ln.ref, ln.valor)  # rastro com o sinal do extrato
        if ln.banco == AURORA:
            motivo = (
                f"Transferência de {_brl_txt(abs(ln.valor))} do Aurora para o Meridiano em {_data_txt(ln.data)} ({ln.ref}) "
                f"sem crédito de mesmo valor no extrato do Meridiano do período. Ficou em 1.1.09.001 Transferências entre "
                f"contas próprias (P-11). Acompanhamento: conferir o crédito no Meridiano quando cair (R-33, R-39)."
            )
        else:
            motivo = (
                f"Crédito de {_brl_txt(ln.valor)} de mesma titularidade no Meridiano em {_data_txt(ln.data)} ({ln.ref}) "
                f"sem transferência de mesmo valor no extrato do Aurora do período. Ficou em 1.1.09.001 (P-11). "
                f"Acompanhamento: conferir a origem da transferência (R-39)."
            )
        pends.append(_Pend(ln.ref, T_TRANSFERENCIA, [comp], motivo, "R-33, R-39, P-11, N-14: pareamento por valor e data"))

    for p in pends:
        campos = {
            "tipo": p.tipo,
            "ref_origem": "|".join(c.ref_origem for c in p.comps),  # L-04
            "motivo": p.motivo,
            "quem_decide": HELENA,  # R-40: regra de fechamento é da Helena
            "regra": p.regra,
        }
        res.linhas.append(LinhaSaida.somando("pendencias.csv", f"PEN-EXT-{p.chave}", campos, p.comps))

    # Conservação: todo lançamento lido está classificado ou só em pendência, em contagem e em valor.
    for banco, df in ((AURORA, dados.aurora), (MERIDIANO, dados.meridiano)):
        lidos = [l for l in lancs if l.banco == banco]
        cls = [l for l in classificados if l.banco == banco]
        pen = [l for l in so_pendencia if l.banco == banco]
        nome = banco.lower()
        res.conservacao[f"{nome}_linhas"] = Decimal(len(df) - (len(cls) + len(pen)))
        res.conservacao[f"{nome}_valor"] = sum((l.valor for l in lidos), Decimal(0)) - sum(
            (l.valor for l in cls + pen), Decimal(0)
        )

    # Aurora: saldo anterior + Σ valor = saldo final (o Meridiano só traz LEDGERBAL, N-09).
    ini, fim = dados.aurora.attrs.get("saldo_anterior"), dados.aurora.attrs.get("saldo_final")
    if ini is not None and fim is not None:
        soma = sum((l.valor for l in lancs if l.banco == AURORA), Decimal(0))
        res.conservacao["aurora_saldo"] = brl(ini) + soma - brl(fim)
    return res
