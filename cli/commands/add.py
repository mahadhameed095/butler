import os
import csv
import json
import subprocess
from shared.models import App
from shared.utils import parse_github_url

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def add(app: App):
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    repo_url = config["repo_url"]
    dest = os.path.join(BASE, parse_github_url(repo_url).repo)

    manifest_path = os.path.join(dest, "manifest.csv")
    apps = []
    if os.path.exists(manifest_path):
        with open(manifest_path, newline="") as f:
            reader = csv.DictReader(f)
            apps = [App(**row) for row in reader]

    apps.append(app)

    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=App.model_fields.keys())
        writer.writeheader()
        writer.writerows(a.model_dump() for a in apps)

    subprocess.run(["git", "add", "manifest.csv"], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", f"[cli:add] {app.Repo_Url} | {app.Branch}"], cwd=dest, check=True)
    subprocess.run(["git", "push"], cwd=dest, check=True)

    return f"Added {app.Repo_Url} to manifest"
