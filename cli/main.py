import click
from cli.commands.init import init
from cli.commands.upsert import upsert
from cli.commands.list import list_cmd
from cli.commands.remove import remove
from cli.commands.push import push

@click.group()
def cli():
    pass

cli.add_command(init)
cli.add_command(upsert)
cli.add_command(list_cmd, name="list")
cli.add_command(remove)
cli.add_command(push)

if __name__ == "__main__":
    cli()
