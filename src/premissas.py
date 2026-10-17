"""Premissas de negócio como configuração.

Cada campo corresponde a uma hipótese do HIPOTESES.md ou a uma pergunta F-xx do
docs/plano-engenharia.md. Quando o financeiro responder, troca-se o valor aqui e
registra-se a resposta no HIPOTESES.md — sem reescrever regra nas trilhas.

Valores marcados PROVISÓRIO são o default até o dono da trilha confirmar.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class AliasEC:
    """Liga um EC da Orbe a um CNPJ quando a planilha não traz o EC. Nunca por fuzzy."""

    cnpj: str
    justificativa: str
    confirmado_financeiro: bool = False  # False => a trilha também gera pendência


@dataclass(frozen=True)
class Isencao:
    """Tarifa zero no checkout (MDR e antecipação) para um CNPJ, em [inicio, fim]."""

    cnpj: str
    inicio: date
    fim: date
    aprovador: str
    fonte: str


_ALIASES_EC: dict[str, AliasEC] = {
    "1043300981": AliasEC("66564512000199", "R-05: Novo Horizonte Intercâmbio", True),
    "1043396662": AliasEC("78576234000179", "R-05: Horizonte Viagens (empresa diferente da anterior)", True),
    "1038867654": AliasEC("07752116000126", "R-05: Kiwi Experience", True),
}

_ISENCOES_CHECKOUT: tuple[Isencao, ...] = (
    Isencao(
        cnpj="00520815000100",
        inicio=date(2026, 9, 1),
        fim=date(2026, 12, 31),
        aprovador="Comercial (concessão), registrada pela Helena",
        fonte="R-08, R-44 [T7][T35][T41]",
    ),
)


@dataclass(frozen=True)
class Premissas:
    # --- Trilha A (checkout) ---
    # R-01 (era F-01), respondido. CONTRATADA: comissão pela taxa do contrato, excedente é divergência.
    comissao_checkout_base: Literal["CONTRATADA", "APLICADA"] = "CONTRATADA"
    # R-03 (era F-04), respondido. Estorno de venda de mês anterior abate a comissão de setembro.
    estorno_mes_anterior_abate: bool = True
    # R-05 (era F-03), confirmados pelo financeiro.
    aliases_ec: dict[str, AliasEC] = field(default_factory=lambda: dict(_ALIASES_EC))
    # R-08, R-44: concessões de tarifa zero no checkout.
    isencoes_checkout: tuple["Isencao", ...] = field(default_factory=lambda: _ISENCOES_CHECKOUT)

    # --- Trilha B (remessa) ---
    participacao_spread_tarvo: Decimal = Decimal("0.5")  # fato: e-mail da Ponte
    # F-06. None = spread "padrão" desconhecido; a trilha gera pendência.
    spread_padrao_pct: Decimal | None = None
    # D-05. PROVISÓRIO. Spread negativo e duplicata ficam fora da comissão até decisão.
    excecao_remessa_fora_da_comissao: bool = True
    cnpj_ponte_cambio: str = "75374179000146"  # fato: assinatura do e-mail

    # --- Trilha C (extratos) ---
    # D-02. PROVISÓRIO. Classificação do resíduo por IA (com cache) ou direto p/ HUMANO.
    usar_ia_extratos: bool = False
    confianca_minima_ia: Decimal = Decimal("0.8")


PREMISSAS = Premissas()
