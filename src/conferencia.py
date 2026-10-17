"""Página de conferência: entradas do data pack, resultados esperados e saídas geradas.

Roda o pipeline do zero num diretório temporário (prova que a saída é reproduzível),
compara com `controle/esperado_setembro.json` (prévia independente do HIPOTESES §5) e
grava um HTML estático, sem dependência externa, em `conferencia/index.html`.
"""

import filecmp
import html
import json
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import OUTPUT_DIR, OUTPUT_FILES, ROOT_DIR
from src.core.entrada import ORBE, PAPEIS, carregar
from src.core.pipeline import run_pipeline

ESPERADO_JSON = ROOT_DIR / "controle" / "esperado_setembro.json"
DESTINO = ROOT_DIR / "conferencia" / "index.html"

NOME_PAPEL = {
    "orbe": "Orbe (adquirente)",
    "taxas": "Planilha de taxas contratadas",
    "ponte": "Ponte Câmbio (e-mail + anexo)",
    "plano_contas": "Plano de contas Fênix",
    "aurora": "Extrato Banco Aurora",
    "meridiano": "Extrato Banco Meridiano (OFX)",
}


# --- comparação (também usada por tests/test_controle_setembro.py) ---------------------


def carregar_esperado(caminho: Path = ESPERADO_JSON) -> dict[str, Any]:
    return json.loads(caminho.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def ler_saida(saida_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        nome: pd.read_csv(saida_dir / nome, sep=";", dtype=str, keep_default_na=False)
        for nome in OUTPUT_FILES
    }


def medir(saida: dict[str, pd.DataFrame], spec: dict[str, Any]) -> Decimal:
    df = saida[spec["arquivo"]]
    for col, val in spec.get("filtro", {}).items():
        df = df[df[col] == val]
    if spec["metrica"] == "linhas":
        return Decimal(len(df))
    return sum((Decimal(v) for v in df[spec["coluna"]]), Decimal(0))


def comparar_totais(saida: dict[str, pd.DataFrame], esperado: dict[str, Any]) -> list[dict[str, Any]]:
    linhas = []
    for spec in esperado["totais"]:
        gerado = medir(saida, spec)
        esp = Decimal(spec["esperado"])
        linhas.append({**spec, "gerado": str(gerado), "ok": gerado == esp})
    return linhas


def comparar_pendencias(
    saida: dict[str, pd.DataFrame], esperado: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Esperadas (presentes e com o valor certo) e sobrando (geradas, não previstas)."""
    pend = saida["pendencias.csv"].set_index("id_saida")
    linhas = []
    for e in esperado["pendencias"]:
        presente = e["id_saida"] in pend.index
        gerado = str(pend.loc[e["id_saida"], "valor_brl"]) if presente else ""
        ok = presente and (e["esperado"] is None or Decimal(gerado) == Decimal(e["esperado"]))
        linhas.append({**e, "gerado": gerado, "presente": presente, "ok": ok})
    previstas = {e["id_saida"] for e in esperado["pendencias"]}
    cobertos = set(esperado.get("tipos_cobertos_pelos_totais", []))
    sobrando = [
        {"id_saida": i, "tipo": r["tipo"], "valor_brl": r["valor_brl"]}
        for i, r in pend.iterrows()
        if i not in previstas and r["tipo"] not in cobertos
    ]
    return linhas, sobrando


# --- HTML -----------------------------------------------------------------------------

CSS = """
:root{--bg:#f6f7f9;--surface:#fff;--surface-2:#eef1f4;--text:#17202a;--muted:#5b6673;
--border:#d8dde3;--accent:#2457c5;--ok:#13734a;--ok-bg:#e1f4ea;--err:#b42318;--err-bg:#fde7e5;
--warn:#8a5a00;--warn-bg:#fff2d6;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11151a;--surface:#181e25;
--surface-2:#212933;--text:#e6eaef;--muted:#9aa5b1;--border:#2e3843;--accent:#7aa2ff;--ok:#5fd39a;
--ok-bg:#16352a;--err:#ff8a80;--err-bg:#3d1f1d;--warn:#f2c46b;--warn-bg:#3a2f15}}
:root[data-theme="dark"]{--bg:#11151a;--surface:#181e25;--surface-2:#212933;--text:#e6eaef;
--muted:#9aa5b1;--border:#2e3843;--accent:#7aa2ff;--ok:#5fd39a;--ok-bg:#16352a;--err:#ff8a80;
--err-bg:#3d1f1d;--warn:#f2c46b;--warn-bg:#3a2f15}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:28px 16px 8px;max-width:1180px;margin:0 auto}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:18px;margin:28px 0 8px}
.sub{color:var(--muted);margin:0}
main{max-width:1180px;margin:0 auto;padding:0 16px 48px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:13px}
nav{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-top:8px;overflow-x:auto}
nav button{background:none;border:0;border-bottom:2px solid transparent;color:var(--muted);
padding:10px 14px;font:inherit;cursor:pointer;white-space:nowrap}
nav button[aria-selected="true"]{color:var(--text);border-color:var(--accent);font-weight:600}
section[hidden]{display:none}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin:12px 0}
.card h3{margin:0 0 4px;font-size:15px}
.meta{color:var(--muted);font-size:13px;margin:0 0 8px}
.scroll{overflow:auto;max-height:460px;border:1px solid var(--border);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px;background:var(--surface)}
th,td{padding:6px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--surface-2);font-weight:600;z-index:1}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td code,.mono{font-family:var(--mono);font-size:12px}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600}
.tag.ok{background:var(--ok-bg);color:var(--ok)}.tag.err{background:var(--err-bg);color:var(--err)}
.tag.warn{background:var(--warn-bg);color:var(--warn)}
.ferr{background:var(--err-bg)}
input[type=search]{width:100%;max-width:420px;padding:8px 10px;border:1px solid var(--border);
border-radius:8px;background:var(--surface);color:var(--text);font:inherit;margin:4px 0 10px}
a.id{color:var(--accent);cursor:pointer;text-decoration:underline;font-family:var(--mono);font-size:12px}
#rastro{position:fixed;inset:auto 16px 16px auto;width:min(560px,calc(100vw - 32px));max-height:70vh;
overflow:auto;background:var(--surface);border:1px solid var(--border);border-radius:12px;
box-shadow:0 10px 30px rgba(0,0,0,.25);padding:14px 16px;z-index:5}
#rastro button{float:right;background:var(--surface-2);border:1px solid var(--border);color:var(--text);
border-radius:6px;padding:2px 10px;cursor:pointer}
ul{margin:6px 0;padding-left:20px}
.fluxo{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px}
.fluxo span{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:6px 10px}
.fluxo i{color:var(--muted);font-style:normal}
"""

JS = r"""
const D = JSON.parse(document.getElementById('dados').textContent);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const NUM = new Set(['comissao_brl','diferenca_brl','valor_brl','valor','confianca','taxa_contratada_pct','taxa_aplicada_pct']);
const LIMITE = 400;
const rastro = {};
for (const r of D.saidas['rastro.csv'].linhas) (rastro[r[0]] ||= []).push(r);
const valorDe = {};
for (const [nome, t] of Object.entries(D.saidas)) {
  if (nome === 'rastro.csv') continue;
  const iv = t.colunas.findIndex(c => ['comissao_brl','diferenca_brl','valor_brl','valor'].includes(c));
  for (const r of t.linhas) valorDe[r[0]] = [nome, iv >= 0 ? r[iv] : ''];
}

document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('nav button').forEach(x => x.setAttribute('aria-selected', x === b));
  document.querySelectorAll('main > section').forEach(s => s.hidden = s.id !== b.dataset.aba);
}));

function tabela(el, t, filtro) {
  const f = (filtro || '').toLowerCase();
  const linhas = f ? t.linhas.filter(r => r.join(' ').toLowerCase().includes(f)) : t.linhas;
  const cab = t.colunas.map(c => `<th class="${NUM.has(c) ? 'n' : ''}">${esc(c)}</th>`).join('');
  const corpo = linhas.slice(0, LIMITE).map(r => '<tr>' + r.map((v, i) => {
    const c = t.colunas[i];
    if (c === 'id_saida' && t.rastreavel) return `<td><a class="id" data-id="${esc(v)}">${esc(v)}</a></td>`;
    return `<td class="${NUM.has(c) ? 'n' : ''}">${esc(v)}</td>`;
  }).join('') + '</tr>').join('');
  el.querySelector('.scroll').innerHTML = `<table><thead><tr>${cab}</tr></thead><tbody>${corpo}</tbody></table>`;
  el.querySelector('.cont').textContent = `${linhas.length.toLocaleString('pt-BR')} de ${t.linhas.length.toLocaleString('pt-BR')} linhas` + (linhas.length > LIMITE ? ` (mostrando ${LIMITE})` : '');
}

for (const el of document.querySelectorAll('[data-tabela]')) {
  const [grupo, nome] = el.dataset.tabela.split('|');
  const t = D[grupo][nome];
  tabela(el, t, '');
  el.querySelector('input').addEventListener('input', e => tabela(el, t, e.target.value));
}

document.addEventListener('click', e => {
  const a = e.target.closest('a.id'); if (!a) return;
  const id = a.dataset.id, comps = rastro[id] || [];
  const soma = comps.reduce((s, r) => s + Math.round(parseFloat(r[3]) * 100), 0) / 100;
  const [arq, valor] = valorDe[id] || ['', ''];
  const fecha = valor === '' || Math.abs(soma - parseFloat(valor)) < 0.005;
  const box = document.getElementById('rastro');
  box.hidden = false;
  box.innerHTML = `<button type="button">fechar</button><h3 class="mono">${esc(id)}</h3>
    <p class="meta">${esc(arq)} · valor reportado <b>${esc(valor || '—')}</b> · soma do rastro <b>${soma.toFixed(2)}</b>
    <span class="tag ${fecha ? 'ok' : 'err'}">${fecha ? 'fecha' : 'não fecha'}</span></p>
    <div class="scroll"><table><thead><tr><th>arquivo_origem</th><th>ref_origem</th><th class="n">valor</th></tr></thead><tbody>
    ${comps.map(r => `<tr><td>${esc(r[1])}</td><td><code>${esc(r[2])}</code></td><td class="n">${esc(r[3])}</td></tr>`).join('')}
    </tbody></table></div>`;
  box.querySelector('button').onclick = () => box.hidden = true;
});
"""


def _e(x: Any) -> str:
    return html.escape(str(x))


def _brl(v: str | Decimal | None, metrica: str = "soma") -> str:
    if v is None or v == "":
        return "—"
    d = Decimal(str(v))
    if metrica == "linhas":
        return f"{int(d):,}".replace(",", ".")
    s = f"{abs(d):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'−' if d < 0 else ''}{s}"


def _tag(ok: bool, sim: str = "bate", nao: str = "não bate") -> str:
    return f'<span class="tag {"ok" if ok else "err"}">{sim if ok else nao}</span>'


def _tabela_js(grupo: str, nome: str, titulo: str, meta: str) -> str:
    return (
        f'<div class="card" data-tabela="{_e(grupo)}|{_e(nome)}"><h3>{titulo}</h3>'
        f'<p class="meta">{meta} · <span class="cont"></span></p>'
        '<input type="search" placeholder="Filtrar linhas…" aria-label="Filtrar">'
        '<div class="scroll"></div></div>'
    )


def _df_para_js(df: pd.DataFrame, rastreavel: bool = False) -> dict[str, Any]:
    df = df.astype(object).where(pd.notna(df), "")
    return {
        "colunas": [str(c) for c in df.columns],
        "linhas": [[("" if v is None else str(v)) for v in r] for r in df.itertuples(index=False)],
        "rastreavel": rastreavel,
    }


def gerar(input_dir: Path, destino: Path = DESTINO, esperado_json: Path = ESPERADO_JSON) -> Path:
    esperado = carregar_esperado(esperado_json)
    with tempfile.TemporaryDirectory() as tmp:
        res = run_pipeline(Path(input_dir), Path(tmp))
        saida = ler_saida(Path(tmp))
        identica = all(
            (OUTPUT_DIR / n).exists() and filecmp.cmp(Path(tmp) / n, OUTPUT_DIR / n, shallow=False)
            for n in OUTPUT_FILES
        )
    dados = carregar(Path(input_dir))
    totais = comparar_totais(saida, esperado)
    pends, sobrando = comparar_pendencias(saida, esperado)
    invariantes = [(f"{t}.{k}", v) for t, inv in res["conservacao"].items() for k, v in inv.items()]

    # --- entradas ---
    entradas_js: dict[str, Any] = {}
    cards_in = []
    for papel in PAPEIS:
        df: pd.DataFrame = getattr(dados, papel)
        nome = dados.arquivos.get(papel, "")
        if df.empty:
            cards_in.append(
                f'<div class="card"><h3>{_e(NOME_PAPEL[papel])} <span class="tag err">ausente</span></h3></div>'
            )
            continue
        if papel == ORBE:
            por_arq = df.groupby("arquivo_origem").size()
            meta = " + ".join(f"<code>{_e(a)}</code> ({n:,} linhas)" for a, n in por_arq.items())
            prev = pd.concat([g.head(8) for _, g in df.groupby("arquivo_origem")])
        else:
            meta = f"<code>{_e(nome)}</code> · {len(df):,} linhas"
            prev = df.head(15)
        entradas_js[papel] = _df_para_js(prev)
        cards_in.append(
            _tabela_js(
                "entradas", papel, _e(NOME_PAPEL[papel]),
                f"{meta} · {len(df.columns)} colunas · prévia das primeiras linhas",
            )
        )  # fmt: skip

    # --- saídas ---
    saidas_js = {n: _df_para_js(df, rastreavel=(n != "rastro.csv")) for n, df in saida.items()}
    cards_out = [
        _tabela_js(
            "saidas", n, f"<code>{_e(n)}</code>",
            f"{len(df):,} linhas · clique no <code>id_saida</code> para ver o rastro"
            if n != "rastro.csv"
            else f"{len(df):,} componentes",
        )
        for n, df in saida.items()
    ]  # fmt: skip

    # --- esperado × gerado ---
    ok_tot = sum(t["ok"] for t in totais)
    ok_pen = sum(p["ok"] for p in pends)
    inv_ok = all(v == 0 for _, v in invariantes)
    linhas_tot = "".join(
        f'<tr class="{"" if t["ok"] else "ferr"}"><td>{_e(t["grupo"])}</td><td>{_e(t["item"])}</td>'
        f'<td class="n">{_brl(t["esperado"], t["metrica"])}</td><td class="n">{_brl(t["gerado"], t["metrica"])}</td>'
        f'<td>{_tag(t["ok"])}</td><td class="meta">{_e(t["fonte"])}</td></tr>'
        for t in totais
    )
    linhas_pen = "".join(
        f'<tr class="{"" if p["ok"] else "ferr"}"><td>{_e(p["caso"])}</td>'
        f'<td>{"<a class=id data-id=" + _e(p["id_saida"]) + ">" + _e(p["id_saida"]) + "</a>" if p["presente"] else _e(p["id_saida"])}</td>'
        f'<td class="n">{_brl(p["esperado"])}</td><td class="n">{_brl(p["gerado"])}</td>'
        f'<td>{_e(p["quem_decide"])}</td><td>{_tag(p["ok"], "ok", "ausente" if not p["presente"] else "não bate")}</td></tr>'
        for p in pends
    )
    linhas_sob = "".join(
        f'<tr><td><a class="id" data-id="{_e(s["id_saida"])}">{_e(s["id_saida"])}</a></td>'
        f'<td>{_e(s["tipo"])}</td><td class="n">{_brl(s["valor_brl"])}</td></tr>'
        for s in sobrando
    )
    linhas_inv = "".join(
        f'<tr><td><code>{_e(k)}</code></td><td class="n">{_e(v)}</td><td>{_tag(v == 0, "zero", "diferença")}</td></tr>'
        for k, v in invariantes
    )
    nao_pend = "".join(f"<li>{_e(x)}</li>" for x in esperado["nao_e_pendencia"])
    avisos = "".join(f"<li><b>{_e(a.tipo)}</b> ({_e(a.ref)}): {_e(a.motivo)}</li>" for a in res["avisos"])

    payload = json.dumps({"entradas": entradas_js, "saidas": saidas_js}, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Conferência do fechamento</title>
<style>{CSS}</style></head>
<body>
<header>
<h1>Conferência do fechamento Tarvo, competência setembro/2026</h1>
<p class="sub">Entradas do data pack, resultado esperado (prévia independente, HIPOTESES.md §5) e o que o
pipeline gerou. Gerado em {agora} rodando <code>run_pipeline</code> do zero sobre
<code>{_e(Path(input_dir).relative_to(ROOT_DIR) if Path(input_dir).is_relative_to(ROOT_DIR) else input_dir)}</code>.</p>
</header>
<main>
<div class="kpis">
<div class="kpi"><b>{ok_tot}/{len(totais)}</b><span>totais iguais ao esperado</span></div>
<div class="kpi"><b>{ok_pen}/{len(pends)}</b><span>pendências esperadas presentes e com o valor certo</span></div>
<div class="kpi"><b>{len(sobrando)}</b><span>pendências não previstas (possível alarme falso)</span></div>
<div class="kpi"><b>{"zero" if inv_ok else "≠ 0"}</b><span>invariantes de conservação</span></div>
<div class="kpi"><b>{"sim" if identica else "não"}</b><span><code>saida/</code> versionado idêntico a esta execução</span></div>
</div>
<div class="fluxo"><span>pasta do mês</span><i>→</i><span>descoberta pelo conteúdo</span><i>→</i>
<span>cadastro + premissas</span><i>→</i><span>checkout · remessa · extratos</span><i>→</i>
<span>6 CSVs + rastro</span></div>
<nav role="tablist">
<button data-aba="esperado" aria-selected="true">Esperado × gerado</button>
<button data-aba="entradas" aria-selected="false">Entradas</button>
<button data-aba="saidas" aria-selected="false">Saídas geradas</button>
</nav>
<section id="esperado">
<h2>Totais</h2>
<div class="scroll"><table><thead><tr><th>Grupo</th><th>Item</th><th class="n">Esperado</th>
<th class="n">Gerado</th><th>Status</th><th>Fonte</th></tr></thead><tbody>{linhas_tot}</tbody></table></div>
<h2>Pendências esperadas</h2>
<p class="meta">Clique no id para ver as linhas de origem que compõem o valor.</p>
<div class="scroll"><table><thead><tr><th>Caso</th><th>id_saida</th><th class="n">Esperado</th>
<th class="n">Gerado</th><th>Quem decide</th><th>Status</th></tr></thead><tbody>{linhas_pen}</tbody></table></div>
<h2>Pendências geradas fora da lista</h2>
<p class="meta">Pendências dos tipos {_e(", ".join(esperado.get("tipos_cobertos_pelos_totais", [])))} são conferidas pelo total na tabela acima (uma por lojista).</p>
{'<p class="meta">Nenhuma.</p>' if not sobrando else '<p class="meta">Caso que a prévia não previu: revisar antes de liberar.</p><div class="scroll"><table><thead><tr><th>id_saida</th><th>tipo</th><th class="n">valor</th></tr></thead><tbody>' + linhas_sob + '</tbody></table></div>'}
<h2>O que não deve virar pendência</h2>
<ul>{nao_pend}</ul>
<h2>Invariantes de conservação</h2>
<div class="scroll"><table><thead><tr><th>Invariante</th><th class="n">Diferença</th><th>Status</th></tr></thead>
<tbody>{linhas_inv}</tbody></table></div>
<h2>Avisos da entrada</h2>
{f"<ul>{avisos}</ul>" if avisos else '<p class="meta">Nenhum: todas as fontes reconhecidas.</p>'}
</section>
<section id="entradas" hidden>
<p class="meta">O papel de cada arquivo é reconhecido pelo conteúdo, não pelo nome. Todos os arquivos da Orbe da pasta entram.</p>
{"".join(cards_in)}
</section>
<section id="saidas" hidden>
{"".join(cards_out)}
</section>
</main>
<div id="rastro" hidden></div>
<script type="application/json" id="dados">{payload}</script>
<script>{JS}</script>
</body></html>
"""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    return destino
