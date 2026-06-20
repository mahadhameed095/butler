import click
from cli.commands.init import init as _init
from cli.commands.add import add as _add
from cli.commands.list import list_apps as _list
from cli.commands.update import update as _update
from cli.commands.remove import remove as _remove


@click.group()
def cli():
    pass


@cli.command()
@click.argument("repo_url")
@click.argument("vm_host")
@click.option("--path", default=None, help="clone destination")
def init(repo_url, vm_host, path):
    click.echo(_init(repo_url, vm_host, path))


@cli.command()
@click.option("--repo-url", required=True)
@click.option("--server-path", required=True)
@click.option("--route", required=True)
@click.option("--branch", default="main")
@click.option("--entry", default="index.html")
@click.option("--sha", default=None)
def add(repo_url, server_path, route, branch, entry, sha):
    click.echo(_add(repo_url, server_path, route, branch, entry, sha))


@cli.command()
def list_apps():
    apps = _list()
    if not apps:
        click.echo("No apps deployed.")
        return
    for url, info in apps.items():
        click.echo(f"{url}  [{info['SHA'][:7]}]  route={info['Route']}")


@cli.command()
@click.option("--repo-url", required=True)
@click.option("--server-path", required=True)
@click.option("--route", required=True)
@click.option("--branch", default="main")
@click.option("--entry", default="index.html")
@click.option("--sha", default=None)
def update(repo_url, server_path, route, branch, entry, sha):
    click.echo(_update(repo_url, server_path, route, branch, entry, sha))


@cli.command()
@click.argument("repo_url")
def remove(repo_url):
    click.echo(_remove(repo_url))


if __name__ == "__main__":
    cli()
