import click
from shared.models import App
from cli.shared import app_options, prompt_app_fields, _map_kwargs
from cli.commands.init import init as _init
from cli.commands.add import add as _add
from cli.commands.list import list_apps as _list
from cli.commands.update import update as _update, get_app as _get_app
from cli.commands.remove import remove as _remove
from shared.models import GithubRepoURL


@click.group()
def cli():
    pass


@cli.command()
@click.option("--repo-url", default=None)
def init(repo_url):
    repo_url = repo_url or click.prompt("Repo for butler manifest")
    click.echo(_init(GithubRepoURL(repo_url)))


@cli.command()
@app_options
def add(**kwargs):
    mapped = _map_kwargs(kwargs)
    default = App(**mapped) if mapped else None
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
    merged = current.model_copy(update=_map_kwargs(kwargs))
    fields = prompt_app_fields(default=merged)
    click.echo(_update(App(**fields)))


@cli.command()
@click.option("--repo-url", default=None)
def remove(repo_url):
    repo_url = repo_url or click.prompt("Repo URL")
    click.echo(_remove(repo_url))


if __name__ == "__main__":
    cli()
