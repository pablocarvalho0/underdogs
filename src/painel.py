"""Gera o painel HTML estático (input, processamento, output) do pipeline Tarvo.

Nada é gravado em `saida/`: o pipeline roda num diretório temporário.
"""

import html
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DATA_PACK_DIR, OUTPUT_FILES, ROOT_DIR
from src.core.pipeline import run_pipeline
from src.loaders import (
    load_extrato_aurora,
    load_extrato_meridiano,
    load_orbe_report,
    load_plano_de_contas,
    load_ponte_cambio_report,
    load_taxas_contratadas,
)
from src.validators import validate_all_outputs

ENTRADAS: list[tuple[str, Callable[[], pd.DataFrame]]] = [
    ("01_orbe_relatorio_comissoes_set2026.csv", load_orbe_report),
    ("02_tabela_taxas_contratadas.xlsx", load_taxas_contratadas),
    ("03_email_ponte_cambio_relatorio_set2026.eml", load_ponte_cambio_report),
    ("04_plano_de_contas_fenix_erp.csv", load_plano_de_contas),
    ("05a_extrato_banco_aurora_cc4471_set2026.csv", load_extrato_aurora),
    ("05b_extrato_banco_meridiano_cc90233_set2026.ofx", load_extrato_meridiano),
]

CSS = """
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;color:#1f2933;background:#f5f7fa}
header{background:#1f2933;color:#fff;padding:16px 24px}
header h1{margin:0 0 6px;font-size:20px}
header .meta{font-size:13px;color:#cbd2d9}
main{padding:16px 24px}
nav{display:flex;gap:4px;margin-bottom:12px}
nav button{border:0;padding:10px 18px;background:#e4e7eb;cursor:pointer;font-size:14px;border-radius:6px 6px 0 0}
nav button.on{background:#fff;font-weight:600}
section{display:none;background:#fff;padding:16px;border-radius:0 6px 6px 6px}
section.on{display:block}
.resumo{font-weight:600;margin:0 0 14px}
.card{border:1px solid #e4e7eb;border-radius:6px;padding:10px 14px;margin-bottom:14px}
.card h3{margin:0 0 6px;font-size:15px}
.scroll{overflow-x:auto;max-height:420px;overflow-y:auto}
table{border-collapse:collapse;font-size:12px}
th,td{border:1px solid #d9dee3;padding:3px 8px;text-align:left;white-space:nowrap}
th{background:#f0f2f5}
.ok{color:#0a7d32;font-weight:600}.err{color:#c0262d;font-weight:600}.warn{color:#a66b00;font-weight:600}
.bg-ok{background:#d9f5e1}.bg-err{background:#fbdcdc}.bg-warn{background:#fff3cd}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:16px}
.box{border:2px solid #52606d;border-radius:6px;padding:8px 12px;background:#f0f2f5;font-size:13px;text-align:center}
.arrow{font-size:20px;color:#52606d}
.col{display:flex;flex-direction:column;gap:6px}
pre{background:#fbdcdc;padding:10px;overflow-x:auto;font-size:12px}
.vazio{color:#7b8794;font-style:italic}
"""

JS = """
function aba(i){document.querySelectorAll('section').forEach(function(s,j){s.classList.toggle('on',i===j)});
document.querySelectorAll('nav button').forEach(function(b,j){b.classList.toggle('on',i===j)});}
"""


def _e(x: Any) -> str:
    return html.escape(str(x))


def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", *args], cwd=ROOT_DIR, check=False, capture_output=True, text=True, timeout=15
        )
        return r.stdout.strip() or "?"
    except Exception:  # noqa: BLE001
        return "?"


def _tabela(df: pd.DataFrame, n: int) -> str:
    return (
        '<div class="scroll">'
        + df.head(n).to_html(index=False, border=0, na_rep="", escape=True)
        + "</div>"
    )


def _aba_input() -> tuple[str, str]:
    cartoes = []
    ok = 0
    for nome, loader in ENTRADAS:
        try:
            df = loader()
            ok += 1
            cols = ", ".join(_e(c) for c in df.columns)
            cartoes.append(
                f'<div class="card"><h3>{_e(nome)} <span class="ok">OK</span></h3>'
                f"<p>{len(df):,} registros<br>Colunas: {cols}</p>{_tabela(df, 10)}</div>"
            )
        except Exception as exc:  # noqa: BLE001
            cartoes.append(
                f'<div class="card"><h3>{_e(nome)} <span class="err">ERRO</span></h3>'
                f"<pre>{_e(type(exc).__name__)}: {_e(exc)}</pre></div>"
            )
    resumo = f"{ok}/{len(ENTRADAS)} arquivos carregados"
    return resumo, "".join(cartoes)


FLUXO = [
    "Data pack<br>(6 arquivos)",
    "Carregar<br>(core/entrada)",
    "Cadastro<br>(core/cadastro)",
]
TRILHAS = ["Trilha checkout", "Trilha remessa", "Trilha extratos"]
FIM = ["Writer<br>(core/writer)", "6 CSVs"]


def _diagrama() -> str:
    seta = '<span class="arrow">&rarr;</span>'
    pre = seta.join(f'<div class="box">{t}</div>' for t in FLUXO)
    tri = '<div class="col">' + "".join(f'<div class="box">{t}</div>' for t in TRILHAS) + "</div>"
    pos = seta.join(f'<div class="box">{t}</div>' for t in FIM)
    return f'<div class="flow">{pre}{seta}{tri}{seta}{pos}</div>'


def _aba_processamento(tmp: Path) -> tuple[str, str]:
    corpo = _diagrama()
    try:
        res = run_pipeline(DATA_PACK_DIR, tmp)
    except Exception:  # noqa: BLE001
        corpo += f'<p class="err">Pipeline falhou:</p><pre>{_e(traceback.format_exc())}</pre>'
        return "pipeline falhou", corpo

    linhas = "".join(f"<tr><td>{_e(n)}</td><td>{q}</td></tr>" for n, q in res["arquivos"].items())
    corpo += (
        f"<h3>Linhas geradas</h3><table><tr><th>Arquivo</th><th>Linhas</th></tr>{linhas}</table>"
    )
    corpo += "<h3>Invariantes de conservação (diferença deve ser 0)</h3>"
    linhas_inv = ""
    ruins = 0
    for trilha, inv in res["conservacao"].items():
        if not inv:
            linhas_inv += (
                f'<tr class="bg-warn"><td>{_e(trilha)}</td><td colspan="2">'
                "nenhum invariante reportado</td></tr>"
            )
        for nome, dif in inv.items():
            zero = dif == 0
            ruins += 0 if zero else 1
            cls = "bg-ok" if zero else "bg-err"
            linhas_inv += (
                f'<tr class="{cls}"><td>{_e(trilha)}</td><td>{_e(nome)}</td><td>{_e(dif)}</td></tr>'
            )
    corpo += (
        f"<table><tr><th>Trilha</th><th>Invariante</th><th>Diferença</th></tr>{linhas_inv}</table>"
    )
    total = sum(res["arquivos"].values())
    return f"{total} linhas de saída · {ruins} invariantes quebrados", corpo


def _rodar_testes(tmp: Path) -> tuple[str, str]:
    junit = tmp / "junit.xml"
    cmd = [
        sys.executable, "-m", "pytest", "tests/test_blackbox_immutable.py",
        "-q", f"--junitxml={junit}",
    ]  # fmt: skip
    try:
        subprocess.run(cmd, cwd=ROOT_DIR, check=False, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return "testes: timeout (300s)", '<p class="err">pytest excedeu 300s.</p>'
    if not junit.exists():
        return "testes: sem relatório", '<p class="err">pytest não gerou junit.xml.</p>'
    casos = []
    for tc in ET.parse(junit).getroot().iter("testcase"):
        status, msg = "passou", ""
        for tag, nome in (("failure", "falhou"), ("error", "erro"), ("skipped", "pulado")):
            el = tc.find(tag)
            if el is not None:
                status = nome
                msg = ((el.get("message") or el.text or "").strip().splitlines() or [""])[0]
                break
        casos.append((tc.get("name", "?"), status, msg))
    p = sum(c[1] == "passou" for c in casos)
    f = sum(c[1] == "falhou" for c in casos)
    er = sum(c[1] == "erro" for c in casos)
    cls = {"passou": "bg-ok", "falhou": "bg-err", "erro": "bg-err", "pulado": "bg-warn"}
    rows = "".join(
        f'<tr class="{cls[s]}"><td>{_e(n)}</td><td>{s}</td><td>{_e(m)}</td></tr>'
        for n, s, m in casos
    )
    corpo = (
        f"<h3>Testes caixa-preta: {p} passaram · {f} falharam · {er} com erro</h3>"
        '<div class="scroll"><table><tr><th>Teste</th><th>Status</th><th>Mensagem</th></tr>'
        f"{rows}</table></div>"
    )
    return f"{p}/{len(casos)} testes passando", corpo


def _aba_output(tmp: Path) -> tuple[str, str]:
    corpo = ""
    total = 0
    for nome in OUTPUT_FILES:
        caminho = tmp / nome
        if not caminho.exists():
            corpo += (
                f'<div class="card"><h3>{_e(nome)} <span class="warn">não gerado</span></h3></div>'
            )
            continue
        try:
            df = pd.read_csv(caminho, sep=";", dtype=str)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        total += len(df)
        vazio = '<p class="vazio">Arquivo sem linhas (trilha ainda stub?)</p>' if df.empty else ""
        corpo += (
            f'<div class="card"><h3>{_e(nome)}</h3><p>{len(df):,} linhas</p>'
            f"{vazio}{_tabela(df, 20)}</div>"
        )
    try:
        _, erros = validate_all_outputs(tmp)
    except Exception:  # noqa: BLE001
        erros = [f"validador falhou: {traceback.format_exc()}"]
    if erros:
        itens = "".join(f"<li>{_e(x)}</li>" for x in erros)
        val = f'<h3 class="err">Validação: {len(erros)} erros</h3><ul>{itens}</ul>'
    else:
        val = '<h3 class="ok">Validação: sem erros</h3>'
    resumo_t, corpo_t = _rodar_testes(tmp)
    return f"{total} linhas de saída · {resumo_t}", val + corpo_t + corpo


def gerar_painel(output_html: Path) -> Path:
    """Gera o painel em `output_html` e devolve o caminho."""
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="painel_tarvo_") as d:
        tmp = Path(d)
        r_in, c_in = _aba_input()
        r_proc, c_proc = _aba_processamento(tmp)
        r_out, c_out = _aba_output(tmp)

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    commit = _git("rev-parse", "--short", "HEAD")
    resumo = f"{r_in} · {r_out}"
    abas = [("Input", r_in, c_in), ("Processamento", r_proc, c_proc), ("Output", r_out, c_out)]
    nav = "".join(
        f'<button class="{"on" if i == 0 else ""}" onclick="aba({i})">{n}</button>'
        for i, (n, _, _) in enumerate(abas)
    )
    secoes = "".join(
        f'<section class="{"on" if i == 0 else ""}"><p class="resumo">{_e(r)}</p>{c}</section>'
        for i, (_, r, c) in enumerate(abas)
    )
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Painel Tarvo</title>
<style>{CSS}</style></head><body>
<header><h1>Painel do pipeline — Tarvo set/2026</h1>
<div class="meta">Gerado em {agora} · branch {_e(branch)} · commit {_e(commit)}</div>
<div class="meta" id="resumo">{_e(resumo)}</div></header>
<main><nav>{nav}</nav>{secoes}</main>
<script>{JS}</script></body></html>"""
    output_html.write_text(doc, encoding="utf-8")
    return output_html
