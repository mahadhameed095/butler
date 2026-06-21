import os
import csv
import json
import subprocess
from shared.models import App

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def _get_manifest_path():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    dest = os.path.join(BASE, config["repo_url"].rstrip("/").removesuffix(".git").rsplit("/", 1)[-1])
    return os.path.join(dest, "manifest.csv"), dest


def get_app(repo_url):
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected")
    manifest_path, _ = _get_manifest_path()
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("manifest.csv not found")
    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Repo_Url"] == repo_url:
                return App(**row)
    return None


def update(repo_url, server_path, route, branch, entry):
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected")
    manifest_path, dest = _get_manifest_path()
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("manifest.csv not found")

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        apps = [App(**row) for row in reader]

    idx = None
    for i, a in enumerate(apps):
        if a.Repo_Url == repo_url:
            idx = i
            break
    if idx is None:
        raise RuntimeError(f"{repo_url} not found in manifest. Use add instead.")

    current = apps[idx]
    new_app = App(Repo_Url=repo_url, Server_Path=server_path, Route=route, Branch=branch, Entry=entry)

    changes = []
    if current.Server_Path != new_app.Server_Path:
        changes.append(("server_path", current.Server_Path, new_app.Server_Path))
        print(f"App will be moved from {current.Server_Path} to {new_app.Server_Path}")
    if current.Route != new_app.Route:
        changes.append(("route", current.Route, new_app.Route))
        print(f"WARNING: Route changed from {current.Route} to {new_app.Route}. This is destructive. Consider setting up a redirect.")
    if current.Branch != new_app.Branch:
        changes.append(("branch", current.Branch, new_app.Branch))
        print(f"Branch changed from {current.Branch} to {new_app.Branch}. This will destructive, and will replace current deployment with the new branch.")
    if current.Entry != new_app.Entry:
        changes.append(("entry", current.Entry, new_app.Entry))
        print(f"Entry changed from {current.Entry} to {new_app.Entry}")

    if not changes:
        return "No changes detected"

    apps[idx] = new_app

    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=App.model_fields.keys())
        writer.writeheader()
        writer.writerows(a.model_dump() for a in apps)

    param_names = [p for p, _, _ in changes]
    commit_msg = f"[cli:update] {repo_url} | [{', '.join(param_names)}]"

    subprocess.run(["git", "add", "manifest.csv"], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=dest, check=True)
    subprocess.run(["git", "push"], cwd=dest, check=True)

    return f"Updated {len(changes)} field(s) for {repo_url}"
