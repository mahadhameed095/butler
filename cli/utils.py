import functools
import click
import paramiko
from cli.config import ButlerConfig


def run(client: paramiko.SSHClient, command: str, check: bool = True) -> str:
    _, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if check and exit_code != 0:
        raise click.ClickException(f"Command failed: {command}\n{error}")
    return output


def with_ssh(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        config = ButlerConfig.load()
        server = config.server_config
        
        if not server:
            raise Exception("No server configured. Run 'butler server add' first.")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        key_path = str(server.ssh_key_path.expanduser())
        
        client.connect(
            hostname=server.host,
            port=server.port,
            username=server.user,
            key_filename=key_path
        )
        
        try:
            return f(client, *args, **kwargs)
        finally:
            client.close()
            
    return wrapper


def with_active_manifest(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        entry = ButlerConfig.load().get_active()
        return f(entry, *args, **kwargs)
    return wrapper


def handle_errors(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except click.ClickException:
            raise
        except Exception as e:
            raise click.ClickException(str(e))
    return wrapper
