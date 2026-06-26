import click
from cli.ManifestManager import ManifestManager, handle_errors


@click.command()
@handle_errors
def push():
    ManifestManager().push()
    click.echo("Pushed manifest repo.")
