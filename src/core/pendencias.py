"""Fábrica de linhas de `pendencias.csv`.

Uma pendência por contraparte e por lojista (R-37, P-13), com os `ref_origem` das
transações separados por `|` (L-04). O valor é a soma dos componentes, então o rastro
de pendência fecha pelo mesmo assert do writer.
"""

from src.core.entrada import Aviso
from src.core.model import Componente, LinhaSaida


def pendencia(
    trilha: str,
    chave: str,
    tipo: str,
    componentes: list[Componente],
    motivo: str,
    quem_decide: str,
) -> LinhaSaida:
    refs = list(dict.fromkeys(c.ref_origem for c in componentes))
    campos = {
        "tipo": tipo,
        "ref_origem": "|".join(refs),
        # Sem ";" no texto: quem abre o CSV num editor simples não vê coluna quebrada.
        "motivo": motivo.replace(";", ","),
        "quem_decide": quem_decide,
    }
    id_saida = f"PEN-{trilha}-{chave}"
    if not componentes:
        return LinhaSaida("pendencias.csv", id_saida, campos, None)
    return LinhaSaida.somando("pendencias.csv", id_saida, campos, componentes)


def pendencia_de_aviso(aviso: Aviso, n: int) -> LinhaSaida:
    """Aviso da entrada (fonte ausente, layout novo) vira pendência sem valor."""
    campos = {
        "tipo": aviso.tipo,
        "ref_origem": aviso.ref,
        "motivo": aviso.motivo,
        "quem_decide": aviso.quem_decide,
    }
    return LinhaSaida("pendencias.csv", f"PEN-ENT-{n:03d}", campos, None)
