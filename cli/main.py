import click
from cli.commands.manifest import manifest
from cli.commands.server import server

@click.group()
def cli():
    pass

cli.add_command(manifest)
cli.add_command(server)

if __name__ == "__main__":
    cli()
