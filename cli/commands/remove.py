import click
from cli.ManifestManager import ManifestManager, handle_errors


@click.command()
@click.option("--repo-url", default=None)
@handle_errors
def remove(repo_url):
    manifest = ManifestManager()
    repo_url = repo_url or click.prompt("Repo URL")
    manifest.remove_app(repo_url)
    manifest.commit(f"[cli:remove] {repo_url}")
    click.echo(f"Removed {repo_url}")
