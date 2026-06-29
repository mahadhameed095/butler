import click
from cli.commands.manifest.setup import setup
from cli.commands.manifest.edit import edit
from cli.commands.manifest.commit import commit


@click.group()
def manifest():
    pass


manifest.add_command(setup)
manifest.add_command(edit)
manifest.add_command(commit)
