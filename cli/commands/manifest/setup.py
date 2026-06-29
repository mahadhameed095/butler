import shutil
from pathlib import Path
import click
import yaml
import os
from shared.models import GithubRepoURL, SafePath, App
from shared.utils import git, staged_directory
from cli.config import ButlerConfig, ManifestRepo
from cli.utils import handle_errors
from cli.constants import DEFAULT_CLONE_DIR, SAMPLE_SYNC


def _ensure_workflow(repo_path: Path) -> str | None:
    workflow_path = repo_path / ".github" / "workflows" / "sync.yaml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    template = Path(SAMPLE_SYNC).read_text()
    if not workflow_path.exists():
        workflow_path.write_text(template)
        return "created .github/workflows/sync.yaml"
    if workflow_path.read_text() != template:
        workflow_path.write_text(template)
        return "updated .github/workflows/sync.yaml"
    return None


def _ensure_manifest(repo_path: Path) -> str | None:
    manifest_path = repo_path / "manifest.yaml"
    if not manifest_path.exists():
        fields = list(App.model_fields.keys())
        manifest_path.write_text(yaml.dump([{f: "" for f in fields}], default_flow_style=False))
        return "created manifest.yaml"
    return None


@click.command("setup")
@click.argument("repo")
@click.option("--clone-dir", default=DEFAULT_CLONE_DIR)
@click.option("--force", is_flag=True, default=False)
@handle_errors
def setup(repo, clone_dir, force):
    repo_url = GithubRepoURL(repo)
    clone_dir = SafePath(clone_dir)
    dest = clone_dir / repo_url.repo

    config = ButlerConfig.load()
    existing = next((m for m in config.manifests if str(m.repo_url) == str(repo_url)), None)

    if existing:
        if not force:
            raise click.ClickException(
                f"Already initialized at {existing.clone_dir_path}. Use --force to reinitialize from remote."
            )
        click.confirm("This will nuke the local clone and lose all uncommitted work. Continue?", abort=True)

    os.makedirs(clone_dir, exist_ok=True)

    actions = []

    with staged_directory(dest) as stg_path:
        for item in stg_path.iterdir():
            shutil.rmtree(item) if item.is_dir() else item.unlink()

        git(["clone", str(repo_url), "."], cwd=stg_path)

        actions = list(filter(None, [
            _ensure_workflow(stg_path),
            _ensure_manifest(stg_path),
        ]))

    (config
        .register(ManifestRepo(repo_url=repo_url, clone_dir_path=dest))
        .save())

    click.echo(f"Connected to {repo_url} at {dest}.")
    for action in actions:
        click.echo(f"  {action}")
    click.echo("Run 'butler manifest edit' to edit your apps, then 'butler manifest commit' to deploy.")
