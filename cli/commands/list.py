import click
from rich.console import Console
from rich.table import Table
from shared.models import App
from cli.ManifestManager import ManifestManager


@click.command()
def list_cmd():
    manifest = ManifestManager()
    if not manifest.get_apps():
        click.echo("No apps deployed.")
        return
    table = Table()
    for header in App.model_fields.keys():
        table.add_column(header)
    for a in manifest.get_apps():
        table.add_row(*[str(getattr(a, f)) for f in App.model_fields.keys()])
    console = Console()
    with console.capture() as capture:
        console.print(table)
    click.echo(capture.get())
