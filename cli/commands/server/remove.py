import click
import paramiko
from cli.utils import handle_errors, with_ssh, run
from cli.config import ButlerConfig


@click.command("remove")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@with_ssh
@handle_errors
def remove(client: paramiko.SSHClient, yes: bool):
    if not yes:
        click.confirm("This will stop the service, delete the remote repo, and remove the server config. Continue?", abort=True)
    click.echo("Stopping and disabling service...")
    run(client, "sudo systemctl stop butler.service || true", check=False)
    run(client, "sudo systemctl disable butler.service || true", check=False)
    run(client, "sudo rm /etc/systemd/system/butler.service || true", check=False)
    run(client, "sudo systemctl daemon-reload")

    config = ButlerConfig.load()
    if config.server_config:
        clone_dir = config.server_config.clone_dir
        click.echo(f"Removing remote directory {clone_dir}...")
        run(client, f"rm -rf {clone_dir}")

    config.server_config = None
    config.save()
    click.echo("Server removed from config.")
