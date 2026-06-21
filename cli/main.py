import click
from shared.models import App
from cli.commands.init import init as _init
from cli.commands.add import add as _add
from cli.commands.list import list_apps as _list
from cli.commands.update import update as _update, get_app as _get_app
from cli.commands.remove import remove as _remove


@click.group()
def cli():
    pass


@cli.command()
def init():
    repo_url = click.prompt("Repo for butler manifest")
    click.echo(_init(repo_url))


@cli.command()
@click.option("--repo-url", default=None)
@click.option("--server-path", default=None)
@click.option("--route", default=None)
@click.option("--branch", default=None)
@click.option("--entry", default=None)
def add(repo_url, server_path, route, branch, entry):
    if repo_url is None:
        repo_url = click.prompt("Repo URL")
    if server_path is None:
        basename = repo_url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
        server_path = click.prompt("Server path", default=f"~/.local/{basename}")
    if route is None:
        route = click.prompt("Route")
    if branch is None:
        branch = click.prompt("Branch", default="dist")
    if entry is None:
        entry = click.prompt("Entry", default="index.html")
    app = App(Repo_Url=repo_url, Server_Path=server_path, Route=route, Branch=branch, Entry=entry)
    click.echo(_add(app))


@cli.command("list")
def list_cmd():
    click.echo(_list())


@cli.command()
@click.option("--repo-url", default=None)
@click.option("--server-path", default=None)
@click.option("--route", default=None)
@click.option("--branch", default=None)
@click.option("--entry", default=None)
def update(repo_url, server_path, route, branch, entry):
    if repo_url is None:
        repo_url = click.prompt("Repo URL")

    current = _get_app(repo_url)
    if current is None:
        raise RuntimeError(f"{repo_url} not found in manifest. Use add instead.")

    if server_path is None:
        server_path = click.prompt("Server path", default=current.Server_Path)
    if route is None:
        route = click.prompt("Route", default=current.Route)
    if branch is None:
        branch = click.prompt("Branch", default=current.Branch)
    if entry is None:
        entry = click.prompt("Entry", default=current.Entry)

    click.echo(_update(repo_url, server_path, route, branch, entry))


@cli.command()
@click.option("--repo-url", default=None)
def remove(repo_url):
    if repo_url is None:
        repo_url = click.prompt("Repo URL")
    click.echo(_remove(repo_url))


if __name__ == "__main__":
    cli()
