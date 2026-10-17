"""Cadastro de lojistas: EC Orbe -> lojista -> taxa contratada vigente na data.

Interface congelada na Fase 0a; implementação na Fase 0b (Pablo). Até lá as trilhas
podem usar `CadastroFalso` com 2-3 lojistas escritos à mão.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

import pandas as pd

from src.premissas import Premissas


@dataclass(frozen=True)
class Lojista:
    cnpj: str  # 14 dígitos
    nome: str  # nome da planilha de taxas
    ec_orbe: str | None


class Cadastro(Protocol):
    def lojista_por_ec(self, ec: str) -> Lojista | None:
        """None = EC sem lojista na planilha vigente (vira pendência na trilha)."""
        ...

    def lojista_por_cnpj(self, cnpj: str) -> Lojista | None: ...

    def taxa_contratada_pct(
        self, cnpj: str, modalidade: str, qtd_parcelas: int, data_ref: date
    ) -> Decimal | None:
        """Taxa em pontos percentuais (2.49 = 2,49%). `modalidade`: DEBITO,
        CREDITO A VISTA, CREDITO PARCELADO, PIX ou ANTECIPACAO. None = sem taxa."""
        ...

    def spread_contratado_pct(self, cnpj: str) -> Decimal | None:
        """Spread de remessa em pontos percentuais. None = não definido."""
        ...


def montar_cadastro(taxas: pd.DataFrame, premissas: Premissas) -> Cadastro:
    raise NotImplementedError("Fase 0b: cadastro a partir da aba 'Taxas vigentes'.")
