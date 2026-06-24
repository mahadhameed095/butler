import click
from cli.ManifestManager import ManifestManager


@click.command()
@click.option("--repo-url", default=None)
def remove(repo_url):
    manifest = ManifestManager()
    repo_url = repo_url or click.prompt("Repo URL")
    try:
        manifest.remove_app(repo_url)
    except RuntimeError as e:
        raise click.ClickException(str(e))
    manifest.commit(f"[cli:remove] {repo_url}")
    click.echo(f"Removed {repo_url}")
