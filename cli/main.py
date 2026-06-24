import click
from typing import Optional
from shared.models import App
from cli.commands.init import init as _init
from cli.commands.add import add as _add
from cli.commands.list import list_apps as _list
from cli.commands.update import update as _update, get_app as _get_app
from cli.commands.remove import remove as _remove
from shared.utils import parse_github_url


def app_options(f):
    f = click.option("--entry", default=None)(f)
    f = click.option("--branch", default=None)(f)
    f = click.option("--route", default=None)(f)
    f = click.option("--server-path", default=None)(f)
    f = click.option("--repo-url", default=None)(f)
    return f


def prompt_app_fields(default: Optional[App] = None) -> dict:
    repo_url = click.prompt("Repo URL", default=default.repo_url if default else None)
    basename = parse_github_url(repo_url).repo
    server_path = click.prompt("Server path", default=default.server_path if default else f"~/.local/{basename}")
    route = click.prompt("Route", default=default.route if default else None)
    branch = click.prompt("Branch", default=default.branch if default else "dist")
    entry = click.prompt("Entry", default=default.entry if default else "index.html")
    return dict(repo_url=repo_url, server_path=server_path, route=route, branch=branch, entry=entry)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--repo-url", default=None)
def init(repo_url):
    repo_url = repo_url or click.prompt("Repo for butler manifest")
    click.echo(_init(parse_github_url(repo_url)))


@cli.command()
@app_options
def add(**kwargs):
    default = App(**{k: v for k, v in kwargs.items() if v is not None}) if any(kwargs.values()) else None
    fields = prompt_app_fields(default)
    click.echo(_add(App(**fields)))


@cli.command("list")
def list_cmd():
    click.echo(_list())


@cli.command()
@app_options
def update(**kwargs):
    repo_url = kwargs.pop("repo_url") or click.prompt("Repo URL")
    current = _get_app(repo_url)
    if current is None:
        raise click.ClickException(f"{repo_url} not found in manifest. Use add instead.")
    merged = current.model_copy(update={k: v for k, v in kwargs.items() if v is not None})
    fields = prompt_app_fields(default=merged)
    click.echo(_update(App(**fields)))


@cli.command()
@click.option("--repo-url", default=None)
def remove(repo_url):
    repo_url = repo_url or click.prompt("Repo URL")
    click.echo(_remove(repo_url))


if __name__ == "__main__":
    cli()