"""Carrega o data pack de uma pasta qualquer, descobrindo o papel de cada arquivo.

D-01 (a): o papel sai do conteúdo (cabeçalho, anexo, extensão), nunca do nome fixo de
setembro. Todos os arquivos da Orbe da pasta são concatenados (R-43), com
`arquivo_origem` por linha. Fonte ausente, arquivo desconhecido ou valor ilegível não
derrubam a execução: viram `Aviso`, que o pipeline transforma em pendência (R-42).
"""

import email
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from email import policy
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd

from src.loaders import (
    load_extrato_aurora,
    load_extrato_meridiano,
    load_plano_de_contas,
    load_ponte_cambio_report,
    load_taxas_contratadas,
)

# Papéis do data pack.
ORBE = "orbe"
TAXAS = "taxas"
PONTE = "ponte"
PLANO = "plano_contas"
AURORA = "aurora"
MERIDIANO = "meridiano"
PAPEIS = (ORBE, TAXAS, PONTE, PLANO, AURORA, MERIDIANO)

COLUNAS_ORBE = [
    "id_transacao", "data_movimento", "cod_estabelecimento", "nome_estabelecimento",
    "tipo_lancamento", "modalidade", "qtd_parcelas", "bandeira", "valor_bruto",
    "taxa_aplicada_pct", "valor_taxa", "valor_liquido", "id_referencia", "data_venda_original",
]  # fmt: skip
_DECIMAIS_ORBE = ("valor_bruto", "taxa_aplicada_pct", "valor_taxa", "valor_liquido")
_IGNORAR = {".md", ".txt", ".pdf", ".docx"}


@dataclass(frozen=True)
class Aviso:
    """Algo na entrada que a analista precisa ver, mas que não impede o fechamento."""

    tipo: str  # FONTE_AUSENTE | ARQUIVO_DESCONHECIDO | VALOR_ILEGIVEL | ID_REPETIDO_ORBE
    ref: str
    motivo: str
    quem_decide: str = "Helena"


@dataclass
class DadosEntrada:
    orbe: pd.DataFrame
    taxas: pd.DataFrame
    ponte: pd.DataFrame
    plano_contas: pd.DataFrame
    aurora: pd.DataFrame
    meridiano: pd.DataFrame
    # papel -> nome do arquivo de origem (o da Orbe pode ser vários; vai por linha).
    arquivos: dict[str, str] = field(default_factory=dict)
    avisos: list[Aviso] = field(default_factory=list)


# --- descoberta -------------------------------------------------------------------


def _primeiras_linhas(p: Path, n: int = 30) -> list[str]:
    for enc in ("utf-8", "latin-1"):
        try:
            with open(p, encoding=enc) as f:
                return [f.readline() for _ in range(n)]
        except UnicodeDecodeError:
            continue
    return []


def _papel_csv(p: Path) -> str | None:
    linhas = _primeiras_linhas(p)
    if not linhas:
        return None
    cab = linhas[0].lower()
    if "id_transacao" in cab and "valor_taxa" in cab:
        return ORBE
    if "cod_conta" in cab and "aceita_lancto" in cab:
        return PLANO
    for ln in linhas:
        partes = [x.strip().lower() for x in ln.split(";")]
        if "data" in partes and any(x.startswith("lan") for x in partes) and any(
            x.startswith("saldo") for x in partes
        ):
            return AURORA
    return None


def _papel_xlsx(p: Path) -> str | None:
    try:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    except Exception:  # noqa: BLE001
        return None
    for ws in wb.worksheets:
        for row in ws.iter_rows(max_row=15, values_only=True):
            vals = {str(v).strip().lower() for v in row if v is not None}
            if "lojista" in vals and "cnpj" in vals:
                return TAXAS
    return None


def _papel_eml(p: Path) -> str | None:
    with open(p, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    for part in msg.walk():
        nome = part.get_filename() or ""
        if nome.lower().endswith(".xlsx"):
            return PONTE
    return None


def descobrir(input_dir: Path) -> tuple[dict[str, list[Path]], list[Aviso]]:
    papeis: dict[str, list[Path]] = {p: [] for p in PAPEIS}
    avisos: list[Aviso] = []
    for p in sorted(x for x in Path(input_dir).iterdir() if x.is_file()):
        ext = p.suffix.lower()
        if ext in _IGNORAR or p.name.startswith("."):
            continue
        papel = {
            ".csv": _papel_csv,
            ".xlsx": _papel_xlsx,
            ".eml": _papel_eml,
            ".ofx": lambda _: MERIDIANO,
        }.get(ext, lambda _: None)(p)
        if papel is None:
            avisos.append(
                Aviso(
                    "ARQUIVO_DESCONHECIDO",
                    p.name,
                    f"O arquivo {p.name} não foi reconhecido como nenhuma fonte do fechamento "
                    "(layout novo?). Ele foi ignorado; confira se deveria entrar.",
                )
            )
            continue
        papeis[papel].append(p)
    return papeis, avisos


# --- Orbe em Decimal ----------------------------------------------------------------


def _dec_br(s: str) -> Decimal | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return Decimal(s.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _data_br(s: str) -> date | None:
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def _carregar_orbe(arquivos: list[Path], avisos: list[Aviso]) -> pd.DataFrame:
    """Concatena todos os arquivos da Orbe em ordem de nome (o ajuste vem depois)."""
    por_id: dict[str, dict[str, Any]] = {}
    for arq in arquivos:
        bruto = pd.read_csv(arq, sep=";", dtype=str, keep_default_na=False, encoding="utf-8")
        faltando = [c for c in COLUNAS_ORBE if c not in bruto.columns]
        if faltando:
            avisos.append(
                Aviso(
                    "LAYOUT_ORBE",
                    arq.name,
                    f"O arquivo {arq.name} veio sem as colunas {faltando}. Ele não entrou no "
                    "fechamento; peça o arquivo no layout padrão à Orbe.",
                )
            )
            continue
        for _, r in bruto.iterrows():
            linha: dict[str, Any] = {c: str(r[c]).strip() for c in COLUNAS_ORBE}
            idt = linha["id_transacao"]
            for c in _DECIMAIS_ORBE:
                linha[c] = _dec_br(r[c])
            linha["data_movimento"] = _data_br(r["data_movimento"])
            linha["data_venda_original"] = _data_br(r["data_venda_original"])
            linha["qtd_parcelas"] = int(r["qtd_parcelas"]) if str(r["qtd_parcelas"]).strip().isdigit() else 0
            linha["arquivo_origem"] = arq.name
            if linha["valor_bruto"] is None or linha["data_movimento"] is None:
                avisos.append(
                    Aviso(
                        "VALOR_ILEGIVEL",
                        idt,
                        f"Transação {idt} de {arq.name} tem valor ou data ilegível e ficou fora "
                        "da comissão. Confira a linha no arquivo da Orbe.",
                    )
                )
                continue
            # P-14: id repetido entre arquivos. Igual conta uma vez; diferente vale o ajuste.
            anterior = por_id.get(idt)
            if anterior is not None:
                iguais = all(anterior[c] == linha[c] for c in COLUNAS_ORBE)
                if not iguais:
                    avisos.append(
                        Aviso(
                            "ID_REPETIDO_ORBE",
                            idt,
                            f"A transação {idt} aparece em {anterior['arquivo_origem']} e em "
                            f"{arq.name} com valores diferentes. Valeu a versão de {arq.name} "
                            "(mais recente); confira antes de liberar.",
                        )
                    )
            por_id[idt] = linha
    df = pd.DataFrame(list(por_id.values()), columns=COLUNAS_ORBE + ["arquivo_origem"])
    return df


# --- carga ---------------------------------------------------------------------------


def _ausente(papel: str, avisos: list[Aviso]) -> None:
    avisos.append(
        Aviso(
            "FONTE_AUSENTE",
            papel,
            f"Nenhum arquivo de '{papel}' na pasta do mês. O que depende dessa fonte não "
            "foi fechado; o restante saiu normalmente e é provisório até a fonte chegar.",
        )
    )


def carregar(input_dir: Path) -> DadosEntrada:
    papeis, avisos = descobrir(Path(input_dir))
    arquivos: dict[str, str] = {}
    for papel in PAPEIS:
        if not papeis[papel]:
            _ausente(papel, avisos)
        elif papel != ORBE:
            arquivos[papel] = papeis[papel][0].name
            for extra in papeis[papel][1:]:
                avisos.append(
                    Aviso(
                        "ARQUIVO_DUPLICADO",
                        extra.name,
                        f"Mais de um arquivo de '{papel}' na pasta; usado {papeis[papel][0].name}, "
                        f"ignorado {extra.name}.",
                    )
                )

    def um(papel: str, loader) -> pd.DataFrame:  # type: ignore[no-untyped-def]
        if not papeis[papel]:
            return pd.DataFrame()
        try:
            return loader(papeis[papel][0])
        except Exception as e:  # layout novo: avisa e segue (R-42)  # noqa: BLE001
            avisos.append(
                Aviso(
                    "LAYOUT_DESCONHECIDO",
                    papeis[papel][0].name,
                    f"Falha ao ler {papeis[papel][0].name} ({e}). O que depende dessa fonte "
                    "não foi fechado.",
                )
            )
            return pd.DataFrame()

    orbe = _carregar_orbe(papeis[ORBE], avisos)
    if papeis[ORBE]:
        arquivos[ORBE] = ", ".join(p.name for p in papeis[ORBE])
    return DadosEntrada(
        orbe=orbe,
        taxas=um(TAXAS, load_taxas_contratadas),
        ponte=um(PONTE, load_ponte_cambio_report),
        plano_contas=um(PLANO, load_plano_de_contas),
        aurora=um(AURORA, load_extrato_aurora),
        meridiano=um(MERIDIANO, load_extrato_meridiano),
        arquivos=arquivos,
        avisos=avisos,
    )


def competencia(dados: DadosEntrada) -> str:
    """AAAA-MM do mês fechado, tirado dos dados (o mês mais frequente da Orbe)."""
    if len(dados.orbe):
        meses = dados.orbe["data_movimento"].map(lambda d: d.strftime("%Y-%m"))
        return str(meses.mode().iloc[0])
    if len(dados.aurora):
        return str(dados.aurora["data"].str[:7].mode().iloc[0])
    return ""


def so_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")
