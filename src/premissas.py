"""Premissas de negócio como configuração.

Cada campo corresponde a uma hipótese do HIPOTESES.md ou a uma pergunta F-xx do
docs/plano-engenharia.md. Quando o financeiro responder, troca-se o valor aqui e
registra-se a resposta no HIPOTESES.md — sem reescrever regra nas trilhas.

Valores marcados PROVISÓRIO são o default até o dono da trilha confirmar.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class AliasEC:
    """Liga um EC da Orbe a um CNPJ quando a planilha não traz o EC. Nunca por fuzzy."""

    cnpj: str
    justificativa: str
    confirmado_financeiro: bool = False  # False => a trilha também gera pendência


@dataclass(frozen=True)
class Premissas:
    # --- Trilha A (checkout) ---
    # F-01. PROVISÓRIO. CONTRATADA: comissão pela taxa do contrato, excedente é divergência.
    comissao_checkout_base: Literal["CONTRATADA", "APLICADA"] = "CONTRATADA"
    # F-04. PROVISÓRIO. Estorno de venda de mês anterior abate a comissão de setembro.
    estorno_mes_anterior_abate: bool = True
    # F-03. Preenchido pelo dono da trilha A, com justificativa.
    aliases_ec: dict[str, AliasEC] = field(default_factory=dict)

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
