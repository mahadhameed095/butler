import click
from cli.commands.init import init
from cli.commands.commit import commit
from cli.commands.manifest import manifest

@click.group()
def cli():
    pass

cli.add_command(init)
cli.add_command(commit)
cli.add_command(manifest)

if __name__ == "__main__":
    cli()
