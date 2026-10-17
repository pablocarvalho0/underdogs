"""Ponto de entrada CLI para execução e validação da conciliação Tarvo."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.config import DATA_PACK_DIR, OUTPUT_DIR, ROOT_DIR
from src.core.entrada import carregar
from src.core.pipeline import run_pipeline
from src.painel import gerar_painel
from src.validators import validate_all_outputs

app = typer.Typer(help="Pipeline de Conciliação e Fechamento Tarvo - Underdogs")
console = Console()


@app.command()
def status():
    """Exibe o que a entrada achou no Data Pack: mesma descoberta do pipeline (todos os arquivos da Orbe)."""
    console.print("\n[bold cyan]🔍 Verificando Data Pack Tarvo:[/bold cyan]\n")
    table = Table(title="Arquivos Brutos de Entrada")
    table.add_column("Arquivo", style="bold white")
    table.add_column("Papel", style="green")
    table.add_column("Registros Carregados", justify="right")

    dados = carregar(DATA_PACK_DIR)
    for nome, n in dados.orbe["arquivo_origem"].value_counts().sort_index().items():
        table.add_row(str(nome), "orbe", f"{n:,}")
    for papel in ("taxas", "ponte", "plano_contas", "aurora", "meridiano"):
        df = getattr(dados, papel)
        table.add_row(dados.arquivos.get(papel, "—"), papel, f"{len(df):,}")
    console.print(table)
    for aviso in dados.avisos:
        console.print(f"[yellow]Aviso: {aviso}[/yellow]")
    console.print()


@app.command()
def validate(
    output: Path = typer.Option(OUTPUT_DIR, "--output", "-o", help="Pasta com os 6 CSVs."),  # noqa: B008
):
    """Valida se os arquivos em saida/ cumprem os requisitos obrigatórios."""
    console.print(f"\n[bold cyan]Validando arquivos de saída em {output}...[/bold cyan]\n")
    is_valid, errors = validate_all_outputs(output)
    if is_valid:
        console.print("[bold green]✓ Todos os arquivos de saída estão válidos e conformes![/bold green]\n")
    else:
        console.print(f"[bold red]✗ Foram encontrados {len(errors)} erros de validação:[/bold red]")
        for err in errors:
            console.print(f"  - [red]{err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def run(
    input: Path = typer.Option(DATA_PACK_DIR, "--input", "-i", help="Pasta do data pack do mês."),  # noqa: B008
    output: Path = typer.Option(OUTPUT_DIR, "--output", "-o", help="Pasta onde gravar os 6 CSVs."),  # noqa: B008
):
    """Executa o pipeline completo de conciliação financeira e gera os CSVs em saida/."""
    console.print(f"\n[bold yellow]Executando pipeline de conciliação Tarvo em {input}...[/bold yellow]")
    resultado = run_pipeline(input, output)
    console.print("\n[bold cyan]Arquivos reconhecidos:[/bold cyan]")
    for papel, nome in resultado["arquivos_lidos"].items():
        console.print(f"  {papel}: {nome}")
    for aviso in resultado["avisos"]:
        console.print(f"  [yellow]AVISO {aviso.tipo} ({aviso.ref}): {aviso.motivo}[/yellow]")
    console.print(f"\n[bold cyan]Saída em {output}:[/bold cyan]")
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
def conferencia(
    input: Path = typer.Option(DATA_PACK_DIR, "--input", "-i", help="Pasta do data pack do mês."),  # noqa: B008
):
    """Gera conferencia/index.html: entradas, resultado esperado e saídas geradas."""
    from src.conferencia import gerar

    caminho = gerar(input)
    console.print(f"[bold green]Página de conferência gerada:[/bold green] {caminho}")


@app.command()
def report():
    """Gera o painel HTML (input, processamento, output) em painel/index.html."""
    console.print("\n[bold cyan]Gerando painel visual...[/bold cyan]")
    caminho = gerar_painel(ROOT_DIR / "painel" / "index.html")
    console.print(f"[bold green]Painel gerado:[/bold green] {caminho}")


if __name__ == "__main__":
    app()
