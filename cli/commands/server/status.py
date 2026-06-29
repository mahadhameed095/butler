import click
import paramiko
from cli.utils import handle_errors, with_ssh, run


@click.command("status")
@with_ssh
@handle_errors
def status(client: paramiko.SSHClient):
    status = run(client, "systemctl is-active butler.service", check=False)
    click.echo(status)
