import os
import csv
import json
import shutil
import subprocess
import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import click
from shared.models import App, GithubRepoURL


BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
SAMPLE_SYNC = os.path.join(BASE, "sample-sync.yaml")
FIELD_MAP = {
    "repo_url": "Repo_URL",
    "deploy_dir": "Deploy_Dir",
    "route": "Route",
    "branch": "Branch",
    "entry_file": "Entry_File",
}


def _map_kwargs(kwargs):
    return {FIELD_MAP[k]: v for k, v in kwargs.items() if v is not None}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected. Run 'butler init' first.")
    with open(CONFIG_PATH) as f:
        return json.load(f)


@dataclass
class ManifestContext:
    repo_url: GithubRepoURL
    dest: Path
    manifest_path: Path
    apps: list[App]


# --- Manifest validation pipeline ---
# Each step has a different failure policy:
#   Step 1 (_load_config):    hard fail — tell user to init
#   Step 2 (_ensure_repo):    hard fail — tell user to re-init
#   Step 3 (_load_manifest):  create if missing, halt if corrupt
#   Step 4 (_ensure_workflow): auto-fix if missing, prompt if mismatch

def _load_config() -> str:
    """Step 1: config.json must exist with a valid repo_url.
    Hard fail — user must run 'butler init'."""
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected. Run 'butler init' first.")
    with open(CONFIG_PATH) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError("config.json is corrupt. Run 'butler init' again.")
    repo_url = data.get("repo_url")
    if not repo_url:
        raise RuntimeError("config.json missing repo_url. Run 'butler init' again.")
    return repo_url


def _ensure_repo(repo_url_str: str) -> Path:
    """Step 2: local clone of the manifest repo must exist.
    Hard fail — user must run 'butler init'."""
    repo_url = GithubRepoURL(repo_url_str)
    dest = Path(BASE) / repo_url.repo
    if not (dest / ".git").exists():
        raise RuntimeError(f"Manifest repo not cloned at {dest}. Run 'butler init' again.")
    subprocess.run(["git", "pull"], cwd=dest, check=False)
    return dest


def _load_manifest(dest: Path) -> list[App]:
    """Step 3: manifest.csv must exist with valid App rows.
    If missing -> create empty header and return [].
    If corrupt -> warn and halt."""
    manifest_path = dest / "manifest.csv"
    if not manifest_path.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=App.model_fields.keys()).writeheader()
        _git_commit(dest, "manifest.csv", msg="[init] create manifest")
        return []
    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        apps = []
        for i, row in enumerate(reader, start=2):
            try:
                apps.append(App(**row))
            except Exception as e:
                print(f"ERROR: manifest.csv line {i}: {e}")
                raise RuntimeError("manifest.csv contains invalid rows. Fix or recreate it.")
        return apps


def _ensure_workflow(dest: Path) -> None:
    """Step 4: .github/workflows/sync.yaml must exist and match the template.
    If missing -> auto-copy from sample-sync.yaml.
    If mismatched -> prompt user before overwriting."""
    if not os.path.exists(SAMPLE_SYNC):
        return
    workflow_path = dest / ".github" / "workflows" / "sync.yaml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)

    head_has_it = subprocess.run(
        ["git", "show", "HEAD:.github/workflows/sync.yaml"],
        cwd=dest, capture_output=True, check=False
    ).returncode == 0

    if not workflow_path.exists() and head_has_it:
        subprocess.run(["git", "checkout", "HEAD", "--", ".github/workflows/sync.yaml"], cwd=dest, check=False)
        return

    with open(SAMPLE_SYNC) as sf:
        template = sf.read()
    if workflow_path.exists() and workflow_path.read_text() == template:
        return

    if workflow_path.exists():
        if not click.confirm(
            f"{workflow_path} differs from template. Overwrite?",
            default=True
        ):
            print("WARNING: workflow file is out of date. Deploy pipeline may behave unexpectedly.")
            return

    workflow_path.write_text(template)
    _git_commit(dest, ".github/workflows/sync.yaml", msg="[cli:init] created workflow", push=False)
    subprocess.run(["git", "push"], cwd=dest, check=False)


def ensure_manifest() -> ManifestContext:
    """Orchestrate the validation pipeline. Guarantees a valid manifest repo on return."""
    repo_url_str = _load_config()             # Step 1: read repo URL
    dest = _ensure_repo(repo_url_str)         # Step 2: clone/pull
    apps = _load_manifest(dest)               # Step 3: load/create manifest.csv
    _ensure_workflow(dest)                    # Step 4: ensure workflow yaml
    return ManifestContext(
        repo_url=GithubRepoURL(repo_url_str),
        dest=dest,
        manifest_path=dest / "manifest.csv",
        apps=apps,
    )


def _git_commit(dest, *files, msg, push=True):
    for f in files:
        subprocess.run(["git", "add", f], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=dest, check=True)
    subprocess.run(["git", "push"], cwd=dest, check=push)


def with_manifest(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        ctx = ensure_manifest()
        result = f(ctx, *args, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            new_apps, commit_msg = result
            with open(ctx.manifest_path, "w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=App.model_fields.keys())
                writer.writeheader()
                writer.writerows(a.model_dump() for a in new_apps)
            _git_commit(ctx.dest, "manifest.csv", msg=commit_msg, push=False)
            return commit_msg
        return result
    return wrapper


def app_options(f):
    f = click.option("--repo-url", default=None)(f)
    f = click.option("--branch", default=None)(f)
    f = click.option("--route", default=None)(f)
    f = click.option("--deploy-dir", default=None)(f)
    f = click.option("--entry-file", default=None)(f)
    return f


def prompt_app_fields(default: Optional[App] = None) -> dict:
    repo_url = click.prompt("Repo URL", default=str(default.Repo_URL) if default else None)
    if default:
        deploy_dir_default = str(default.Deploy_Dir)
    else:
        deploy_dir_default = f"~/.local/{GithubRepoURL(repo_url).repo}"
    deploy_dir = click.prompt("Deploy dir", default=deploy_dir_default)
    route = click.prompt("Route", default=default.Route if default else None)
    branch = click.prompt("Branch", default=default.Branch if default else "dist")
    entry_file = click.prompt("Entry file", default=str(default.Entry_File) if default else "index.html")
    return dict(Repo_URL=repo_url, Deploy_Dir=deploy_dir, Route=route, Branch=branch, Entry_File=entry_file)
