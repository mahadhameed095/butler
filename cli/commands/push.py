import click
from cli.ManifestManager import ManifestManager


@click.command()
def push():
    ManifestManager().push()
    click.echo("Pushed manifest repo.")
