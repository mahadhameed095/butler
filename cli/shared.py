import os
import csv
import json
import subprocess
import functools
from typing import Optional
import click
from shared.models import App, GithubRepoURL


BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
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


def with_manifest(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        config = load_config()
        repo_url = config["repo_url"]
        dest = os.path.join(BASE, GithubRepoURL(repo_url).repo)
        manifest_path = os.path.join(dest, "manifest.csv")

        subprocess.run(["git", "pull"], cwd=dest, check=False)

        apps = []
        if os.path.exists(manifest_path):
            with open(manifest_path, newline="") as fh:
                reader = csv.DictReader(fh)
                apps = [App(**row) for row in reader]

        result = f(apps, *args, **kwargs)

        if isinstance(result, tuple) and len(result) == 2:
            new_apps, commit_msg = result
            with open(manifest_path, "w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=App.model_fields.keys())
                writer.writeheader()
                writer.writerows(a.model_dump() for a in new_apps)

            subprocess.run(["git", "add", "manifest.csv"], cwd=dest, check=True)
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=dest, check=True)
            subprocess.run(["git", "push"], cwd=dest, check=False)
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
