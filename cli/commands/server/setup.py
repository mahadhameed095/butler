import click
import paramiko
from cli.constants import CONFIG_PATH, DEFAULT_BUTLER_SERVER_CLONE_DIR
from cli.utils import handle_errors, run
from cli.config import ButlerConfig, ServerConfig

BUTLER_REPO = "https://github.com/mahadhameed095/butler"

SYSTEMD_SERVICE = """
[Unit]
Description=Butler Server
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={clone_dir}
ExecStart={clone_dir}/.venv/bin/butler-server
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

@click.command("setup")
@click.option("--name", required=True, help="Server name")
@click.option("--host", required=True, help="Server hostname or IP")
@click.option("--user", required=True, help="SSH user")
@click.option("--ssh-key-path", type=click.Path(exists=True), required=True, help="Path to SSH private key")
@click.option("--port", default=22, type=int, help="SSH port")
@click.option("--clone-dir", default=DEFAULT_BUTLER_SERVER_CLONE_DIR, help="Remote clone directory")
@handle_errors
def setup(name, host, user, ssh_key_path, port, clone_dir):
    config = ButlerConfig.load()
    config.server_config = ServerConfig(
        name=name,
        host=host,
        user=user,
        ssh_key_path=ssh_key_path,
        port=port,
        clone_dir=clone_dir,
    )
    config.save()
    click.echo(f"Server '{name}' configured and saved.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, key_filename=str(ssh_key_path))

    click.echo("Connected to server via SSH.")

    # 1. Handle existing clone dir
    dir_exists = run(client, f"[ -d {clone_dir} ] && echo yes || echo no", check=False)
    if dir_exists == "yes":
        if not click.confirm(f"Directory {clone_dir} already exists. Overwrite?"):
            raise click.ClickException("Aborted.")
        run(client, f"rm -rf {clone_dir}")
        click.echo(f"Removed existing directory {clone_dir}.")

    # 2. Clone and install
    click.echo(f"Cloning Butler from {BUTLER_REPO}...")
    run(client, f"git clone {BUTLER_REPO} {clone_dir}")
    click.echo("Creating venv and installing Butler server...")
    run(client, f"python3 -m venv {clone_dir}/.venv")
    run(client, f"{clone_dir}/.venv/bin/pip install -e '{clone_dir}[server]' --quiet")
    click.echo("Butler server installed.")

    # 3. Handle existing systemd service
    service_exists = run(client, "systemctl list-unit-files butler.service | grep -c butler.service || true", check=False)
    if service_exists.strip() != "0":
        if not click.confirm("A 'butler' systemd service already exists. Overwrite?"):
            raise click.ClickException("Aborted.")
        run(client, "sudo systemctl stop butler.service || true", check=False)
        run(client, "sudo rm /etc/systemd/system/butler.service")

    # 4. Write service file, enable and start
    service_content = SYSTEMD_SERVICE.format(user=user, clone_dir=clone_dir).strip()
    run(client, f"echo '{service_content}' | sudo tee /etc/systemd/system/butler.service > /dev/null")
    run(client, "sudo systemctl daemon-reload")
    run(client, "sudo systemctl enable butler.service")
    run(client, "sudo systemctl start butler.service")
    click.echo("Butler service created and started.")

    client.close()

    click.echo(f"\nSetup complete. Butler server running at http://{host}:8000")