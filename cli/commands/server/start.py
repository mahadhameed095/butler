import click
import paramiko
from cli.utils import handle_errors, with_ssh, run


@click.command("start")
@click.option("-r", "--restart", is_flag=True, help="Restart the service")
@with_ssh
@handle_errors
def start(client: paramiko.SSHClient, restart: bool):
    status = run(client, "systemctl is-active butler.service", check=False)
    if status == "active":
        if restart:
            run(client, "sudo systemctl restart butler.service")
            click.echo("Butler server restarted.")
        else:
            click.echo("Butler server is already running.")
    else:
        run(client, "sudo systemctl start butler.service")
        click.echo("Butler server started.")
