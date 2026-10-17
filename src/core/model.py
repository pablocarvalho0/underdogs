"""Contrato comum das trilhas: toda linha de saída carrega os componentes que a somam.

O writer recusa escrever uma linha cujo `valor` difere da soma dos componentes, então
o rastro.csv sai por construção e não tem como divergir dos números reportados.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

ArquivoSaida = Literal[
    "comissoes_por_lojista.csv",
    "divergencias_taxa.csv",
    "notas_a_emitir.csv",
    "lancamentos_classificados.csv",
    "pendencias.csv",
]

CENTAVO = Decimal("0.01")


def brl(valor: Any) -> Decimal:
    """Converte para Decimal com 2 casas (ROUND_HALF_UP). Usar em todo valor em reais."""
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Componente:
    """Uma linha de origem que compõe um número de saída."""

    arquivo_origem: str  # nome do arquivo do data pack, ex. "01_orbe_relatorio_comissoes_set2026.csv"
    ref_origem: str  # id_transacao | Nº Operação | L10 | FITID
    valor: Decimal


@dataclass
class LinhaSaida:
    """Uma linha de um dos CSVs de saída.

    `campos` traz as colunas do arquivo, exceto `id_saida` (vem do atributo) e a coluna
    do número rastreado, que o writer preenche a partir de `valor`.
    `valor=None` indica linha sem número rastreado (não gera rastro).
    """

    arquivo: ArquivoSaida
    id_saida: str
    campos: dict[str, Any]
    valor: Decimal | None
    componentes: list[Componente] = field(default_factory=list)

    @classmethod
    def somando(
        cls, arquivo: ArquivoSaida, id_saida: str, campos: dict[str, Any], componentes: list[Componente]
    ) -> "LinhaSaida":
        """Cria a linha com `valor` = soma dos componentes (o caminho normal)."""
        total = sum((c.valor for c in componentes), Decimal(0))
        return cls(arquivo, id_saida, campos, total, componentes)


@dataclass
class ResultadoTrilha:
    """O que cada trilha devolve ao pipeline."""

    trilha: str
    linhas: list[LinhaSaida] = field(default_factory=list)
    # Invariantes de conservação: nome -> diferença. Tudo que entrou está numa saída
    # ou numa pendência; diferença diferente de zero é bug da trilha.
    conservacao: dict[str, Decimal] = field(default_factory=dict)


# Coluna que recebe o `valor` rastreado em cada arquivo.
COLUNA_VALOR: dict[str, str] = {
    "comissoes_por_lojista.csv": "comissao_brl",
    "divergencias_taxa.csv": "diferenca_brl",
    "notas_a_emitir.csv": "valor_brl",
    "lancamentos_classificados.csv": "valor",
    "pendencias.csv": "valor_brl",
}
