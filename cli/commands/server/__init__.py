import click
from cli.commands.server.setup import setup
from cli.commands.server.start import start
from cli.commands.server.stop import stop
from cli.commands.server.status import status
from cli.commands.server.remove import remove


@click.group()
def server():
    pass


server.add_command(setup)
server.add_command(start)
server.add_command(stop)
server.add_command(status)
server.add_command(remove)
