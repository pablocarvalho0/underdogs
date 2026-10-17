"""Premissas de negócio como configuração.

Cada campo aponta para uma regra (R-xx) ou premissa (P-xx) do HIPOTESES.md. Quando o
financeiro ou o comercial mudar algo, troca-se o valor aqui e registra-se no
HIPOTESES.md, sem reescrever regra nas trilhas.

Condição comercial (alias de EC, isenção) é dado com vigência, fonte e aprovador
(P-03): rodar outubro não exige mexer em código, só neste arquivo.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class AliasEC:
    """Liga um EC da Orbe a um CNPJ quando a planilha não traz o EC. Nunca por fuzzy."""

    cnpj: str
    justificativa: str
    confirmado_financeiro: bool = False  # False => a trilha também gera pendência


@dataclass(frozen=True)
class Isencao:
    """Condição comercial fora da planilha: tarifa zerada no checkout (R-08, P-03)."""

    cnpj: str
    inicio: date
    fim: date
    aprovador: str
    fonte: str

    def vale_em(self, d: date) -> bool:
        return self.inicio <= d <= self.fim


# R-05 [T4]: confirmados pela Helena no canal.
_ALIASES = {
    "1043300981": AliasEC("66564512000199", "R-05: Novo Horizonte Intercâmbio", True),
    "1043396662": AliasEC("78576234000179", "R-05: Horizonte Viagens (empresa diferente)", True),
    "1038867654": AliasEC("07752116000126", "R-05: Kiwi Experience", True),
}

# R-08, R-44 [T7][T35][T41]: Casa do Estudante, MDR e antecipação zerados set–dez/2026.
_ISENCOES = [
    Isencao(
        cnpj="00520815000100",
        inicio=date(2026, 9, 1),
        fim=date(2026, 12, 31),
        aprovador="Comercial (Diego), registrado pela Helena",
        fonte="R-08 [T7] [T35]",
    ),
]


@dataclass(frozen=True)
class Premissas:
    # --- Trilha A (checkout) ---
    aliases_ec: dict[str, AliasEC] = field(default_factory=lambda: dict(_ALIASES))
    isencoes_checkout: list[Isencao] = field(default_factory=lambda: list(_ISENCOES))
    # D-03 (a): lojista sem contrato fica só na pendência, sem linha 0,00 na comissão.
    sem_contrato_lista_zero: bool = False
    max_parcelas: int = 12  # R-10

    # --- Trilha B (remessa) ---
    participacao_spread_tarvo: Decimal = Decimal("0.5")  # R-11, e-mail da Ponte
    spread_padrao_pct: Decimal | None = Decimal("1.5")  # R-12, pontos percentuais
    tolerancia_spread_pp: Decimal = Decimal("0.01")  # P-01
    # Fallback se o e-mail da Ponte não trouxer a assinatura com o CNPJ.
    cnpj_ponte_cambio: str = "75374179000146"
    nome_ponte_cambio: str = "Ponte Câmbio S.A."

    # --- Saída ---
    taxa_saida_em_pp: bool = True  # P-09

    # --- Trilha C (extratos) ---
    # D-02: resíduo sem regra vai para IA (com cache) ou direto para HUMANO.
    usar_ia_extratos: bool = False
    confianca_minima_ia: Decimal = Decimal("0.8")


PREMISSAS = Premissas()
