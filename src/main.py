"""Ponto de entrada CLI para execução e validação da conciliação Tarvo."""

import typer
from rich.console import Console
from rich.table import Table

from src.config import DATA_PACK_DIR, OUTPUT_DIR, ROOT_DIR
from src.core.pipeline import run_pipeline
from src.loaders import (
    load_extrato_aurora,
    load_extrato_meridiano,
    load_orbe_report,
    load_plano_de_contas,
    load_ponte_cambio_report,
    load_taxas_contratadas,
)
from src.painel import gerar_painel
from src.validators import validate_all_outputs

app = typer.Typer(help="Pipeline de Conciliação e Fechamento Tarvo - Underdogs")
console = Console()


@app.command()
def status():
    """Exibe o status dos arquivos brutos de entrada do Data Pack."""
    console.print("\n[bold cyan]🔍 Verificando Data Pack Tarvo (Setembro/2026):[/bold cyan]\n")
    table = Table(title="Arquivos Brutos de Entrada")
    table.add_column("Arquivo", style="bold white")
    table.add_column("Status", style="green")
    table.add_column("Registros Carregados", justify="right")

    # Orbe
    try:
        orbe_df = load_orbe_report()
        table.add_row("01_orbe_relatorio_comissoes_set2026.csv", "✓ OK", f"{len(orbe_df):,}")
    except Exception as e:
        table.add_row("01_orbe_relatorio_comissoes_set2026.csv", f"✗ Erro: {e}", "0")

    # Taxas
    try:
        taxas_df = load_taxas_contratadas()
        table.add_row("02_tabela_taxas_contratadas.xlsx", "✓ OK", f"{len(taxas_df):,}")
    except Exception as e:
        table.add_row("02_tabela_taxas_contratadas.xlsx", f"✗ Erro: {e}", "0")

    # Ponte Câmbio
    try:
        ponte_df = load_ponte_cambio_report()
        table.add_row("03_email_ponte_cambio_relatorio_set2026.eml", "✓ OK (Anexo extraído)", f"{len(ponte_df):,}")
    except Exception as e:
        table.add_row("03_email_ponte_cambio_relatorio_set2026.eml", f"✗ Erro: {e}", "0")

    # Fênix ERP
    try:
        fenix_df = load_plano_de_contas()
        table.add_row("04_plano_de_contas_fenix_erp.csv", "✓ OK", f"{len(fenix_df):,}")
    except Exception as e:
        table.add_row("04_plano_de_contas_fenix_erp.csv", f"✗ Erro: {e}", "0")

    # Extrato Aurora
    try:
        aurora_df = load_extrato_aurora()
        table.add_row("05a_extrato_banco_aurora_cc4471_set2026.csv", "✓ OK", f"{len(aurora_df):,}")
    except Exception as e:
        table.add_row("05a_extrato_banco_aurora_cc4471_set2026.csv", f"✗ Erro: {e}", "0")

    # Extrato Meridiano
    try:
        meridiano_df = load_extrato_meridiano()
        table.add_row("05b_extrato_banco_meridiano_cc90233_set2026.ofx", "✓ OK", f"{len(meridiano_df):,}")
    except Exception as e:
        table.add_row("05b_extrato_banco_meridiano_cc90233_set2026.ofx", f"✗ Erro: {e}", "0")

    console.print(table)


@app.command()
def validate():
    """Valida se os arquivos em saida/ cumprem os requisitos obrigatórios."""
    console.print(f"\n[bold cyan]Validando arquivos de saída em {OUTPUT_DIR}...[/bold cyan]\n")
    is_valid, errors = validate_all_outputs(OUTPUT_DIR)
    if is_valid:
        console.print("[bold green]✓ Todos os arquivos de saída estão válidos e conformes![/bold green]\n")
    else:
        console.print(f"[bold red]✗ Foram encontrados {len(errors)} erros de validação:[/bold red]")
        for err in errors:
            console.print(f"  - [red]{err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def run():
    """Executa o pipeline completo de conciliação financeira e gera os CSVs em saida/."""
    console.print("\n[bold yellow]Executando pipeline de conciliação Tarvo...[/bold yellow]")
    resultado = run_pipeline(DATA_PACK_DIR, OUTPUT_DIR)
    for nome, n in resultado["arquivos"].items():
        console.print(f"  {nome}: {n} linhas")
    console.print("\n[bold cyan]Invariantes de conservação (diferença deve ser 0):[/bold cyan]")
    for trilha, inv in resultado["conservacao"].items():
        if not inv:
            console.print(f"  [yellow]{trilha}: nenhum invariante reportado[/yellow]")
        for nome, dif in inv.items():
            cor = "green" if dif == 0 else "red"
            console.print(f"  [{cor}]{trilha}.{nome}: {dif}[/{cor}]")


@app.command()
def report():
    """Gera o painel HTML (input, processamento, output) em painel/index.html."""
    console.print("\n[bold cyan]Gerando painel visual...[/bold cyan]")
    caminho = gerar_painel(ROOT_DIR / "painel" / "index.html")
    console.print(f"[bold green]Painel gerado:[/bold green] {caminho}")


if __name__ == "__main__":
    app()
