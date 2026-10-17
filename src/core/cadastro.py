"""Cadastro de lojistas: EC Orbe -> lojista -> taxa contratada vigente na data.

Fonte única: aba "Taxas vigentes" da planilha do financeiro (a aba "ANTIGO 2025" é
ignorada de propósito). Tudo que a planilha não responde volta como `None` — a trilha
transforma em pendência; o cadastro nunca chuta.
"""

import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

import pandas as pd

from src.premissas import AliasEC, Premissas


@dataclass(frozen=True)
class Lojista:
    cnpj: str  # 14 dígitos
    nome: str  # nome da planilha de taxas (linha vigente mais recente)
    ec_orbe: str | None
    # Preenchido quando o EC só foi resolvido por alias de premissas.py.
    alias: AliasEC | None = None


class Cadastro(Protocol):
    def lojistas(self) -> list[Lojista]: ...

    def lojista_por_ec(self, ec: str) -> Lojista | None:
        """None = EC sem lojista na planilha vigente nem alias (vira pendência na trilha).
        Se veio de alias, `lojista.alias` diz se o financeiro já confirmou."""
        ...

    def lojista_por_cnpj(self, cnpj: str) -> Lojista | None: ...

    def taxa_contratada_pct(
        self, cnpj: str, modalidade: str, qtd_parcelas: int, data_ref: date
    ) -> Decimal | None:
        """Taxa em pontos percentuais (2.49 = 2,49%). `modalidade`: DEBITO,
        CREDITO A VISTA, CREDITO PARCELADO, PIX ou ANTECIPACAO. None = sem taxa."""
        ...

    def spread_contratado_pct(self, cnpj: str, data_ref: date | None = None) -> Decimal | None:
        """Spread de remessa em pontos percentuais, na linha vigente em `data_ref`.
        None = não definido."""
        ...


# Modalidade da Orbe -> coluna da planilha.
_COLUNA_MODALIDADE = {
    "DEBITO": "Débito",
    "CREDITO A VISTA": "Crédito à vista",
    "PIX": "Pix",
    "ANTECIPACAO": "Antecipação",
}
_PADRAO = "padrão"


def pct_planilha(v: Any) -> Decimal | None:
    """Normaliza percentual da planilha para pontos percentuais.

    A planilha mistura fração (0.0249) e texto ("2,49%"). Vazio -> None.
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str):
        s = v.strip()
        if not s or s.lower() == _PADRAO:
            return None
        return Decimal(s.replace("%", "").replace(",", ".").strip()).normalize()
    return (Decimal(str(v)) * 100).quantize(Decimal("0.0001")).normalize()


def _data_br(s: str) -> date:
    return datetime.strptime(s, "%d/%m/%Y").date()


def vigencia(v: Any) -> tuple[date | None, date | None]:
    """'até 14/09/2026' -> (None, 14/09); 'a partir de 15/09/2026' e '01/01/2026' ->
    (data, None); vazio -> (None, None)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return (None, None)
    if isinstance(v, (datetime, date)):
        return (v.date() if isinstance(v, datetime) else v, None)
    s = str(v).strip().lower()
    m = re.search(r"\d{2}/\d{2}/\d{4}", s)
    if not m:
        return (None, None)
    d = _data_br(m.group())
    return (None, d) if s.startswith("até") else (d, None)


@dataclass(frozen=True)
class _LinhaTaxa:
    lojista: Lojista
    inicio: date | None
    fim: date | None
    taxas: dict[str, Any]  # coluna da planilha -> valor cru

    def vale_em(self, d: date) -> bool:
        return (self.inicio is None or self.inicio <= d) and (self.fim is None or d <= self.fim)


class CadastroPlanilha:
    def __init__(self, taxas: pd.DataFrame, premissas: Premissas):
        self._premissas = premissas
        self._linhas: dict[str, list[_LinhaTaxa]] = {}
        # Linha marcada INATIVO na planilha (Globo Trotter, tachada): não vale taxa nenhuma.
        self.inativos_por_ec: dict[str, Lojista] = {}
        for _, r in taxas.iterrows():
            cnpj = r["cnpj_limpo"]
            ec = str(r["EC Orbe"]).strip() if pd.notna(r.get("EC Orbe")) else None
            loj = Lojista(cnpj=cnpj, nome=str(r["Lojista"]).strip(), ec_orbe=ec)
            if "INATIVO" in str(r.get("Obs") or "").upper():
                if ec:
                    self.inativos_por_ec[ec] = loj
                continue
            ini, fim = vigencia(r.get("Vigência"))
            self._linhas.setdefault(cnpj, []).append(_LinhaTaxa(loj, ini, fim, {str(k): v for k, v in r.items()}))

        # Nome da primeira linha (a razão social; a renegociação vem embaixo como "(NOVA)").
        self._por_cnpj = {c: ls[0].lojista for c, ls in self._linhas.items()}
        self._por_ec = {
            ln.lojista.ec_orbe: self._por_cnpj[c]
            for c, ls in self._linhas.items()
            for ln in ls
            if ln.lojista.ec_orbe
        }

    def lojistas(self) -> list[Lojista]:
        return list(self._por_cnpj.values())

    def lojista_por_cnpj(self, cnpj: str) -> Lojista | None:
        return self._por_cnpj.get(cnpj)

    def lojista_por_ec(self, ec: str) -> Lojista | None:
        if ec in self._por_ec:
            return self._por_ec[ec]
        alias = self._premissas.aliases_ec.get(ec)
        if alias is None:
            return None
        loj = self._por_cnpj.get(alias.cnpj)
        return replace(loj, alias=alias) if loj else None

    def _linha_vigente(self, cnpj: str, d: date) -> _LinhaTaxa | None:
        vigentes = [l for l in self._linhas.get(cnpj, []) if l.vale_em(d)]
        # Zero ou mais de uma linha vigente na data: a planilha não decide sozinha.
        return vigentes[0] if len(vigentes) == 1 else None

    def taxa_contratada_pct(
        self, cnpj: str, modalidade: str, qtd_parcelas: int, data_ref: date
    ) -> Decimal | None:
        linha = self._linha_vigente(cnpj, data_ref)
        if linha is None:
            return None
        if modalidade == "CREDITO PARCELADO":
            if 2 <= qtd_parcelas <= 6:
                coluna = "Créd. 2-6x"
            elif 7 <= qtd_parcelas <= 12:
                coluna = "Créd. 7-12x"
            else:
                return None
        elif modalidade in _COLUNA_MODALIDADE:
            coluna = _COLUNA_MODALIDADE[modalidade]
        else:
            return None
        return pct_planilha(linha.taxas.get(coluna))

    def spread_contratado_pct(self, cnpj: str, data_ref: date | None = None) -> Decimal | None:
        linhas = self._linhas.get(cnpj)
        if not linhas:
            return None
        # Linha vigente na data de contratação, como no checkout. Sem data, ou com a
        # planilha ambígua (zero ou duas vigentes), fica a última linha (o aditivo).
        linha = self._linha_vigente(cnpj, data_ref) if data_ref is not None else None
        if linha is None:
            linha = linhas[-1]
        # Rodapé da planilha: "spread em branco = padrão".
        valor = pct_planilha(linha.taxas.get("Spread remessa"))
        return valor if valor is not None else self._premissas.spread_padrao_pct


def montar_cadastro(taxas: pd.DataFrame, premissas: Premissas) -> Cadastro:
    return CadastroPlanilha(taxas, premissas)
