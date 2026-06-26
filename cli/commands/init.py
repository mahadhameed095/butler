import os
import json
import shutil
from pathlib import Path
import subprocess
import click
from shared.models import GithubRepoURL
from cli.constants import CONFIG_PATH, BASE
from cli.ManifestManager import ManifestManager, handle_errors


@click.command()
@click.option("--repo-url", default=None)
@handle_errors
def init(repo_url):
    repo_url = repo_url or click.prompt("Repo for butler manifest")
    repo_url = GithubRepoURL(repo_url)

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            click.echo(f"Already connected to {json.load(f)['repo_url']}")
            return

    dest = Path(BASE) / repo_url.repo
    if dest.exists():
        shutil.rmtree(dest)

    subprocess.run(["git", "clone", repo_url, dest], check=True)

    with open(CONFIG_PATH, "w") as f:
        json.dump({"repo_url": str(repo_url)}, f, indent=2)

    manifest = ManifestManager()
    apps = manifest.get_apps()

    if apps:
        click.echo(f"Connected to {repo_url}. Loaded {len(apps)} app(s) from manifest.")
    else:
        click.echo(f"Connected to {repo_url}.")
