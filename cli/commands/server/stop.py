import click
import paramiko
from cli.utils import handle_errors, with_ssh, run


@click.command("stop")
@with_ssh
@handle_errors
def stop(client: paramiko.SSHClient):
    status = run(client, "systemctl is-active butler.service", check=False)
    if status == "active":
        run(client, "sudo systemctl stop butler.service")
        click.echo("Butler server stopped.")
    else:
        click.echo("Butler server is not running.")
