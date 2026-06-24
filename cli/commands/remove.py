import os
import csv
import json
import subprocess
from shared.models import App
from shared.utils import parse_github_url

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def remove(repo_url):
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError("No manifest repo connected")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    dest = os.path.join(BASE, parse_github_url(config["repo_url"]).repo)

    manifest_path = os.path.join(dest, "manifest.csv")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("manifest.csv not found")

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        apps = [App(**row) for row in reader]

    filtered = [a for a in apps if a.Repo_Url != repo_url]

    if len(filtered) == len(apps):
        return f"App {repo_url} not found in manifest"

    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=App.model_fields.keys())
        writer.writeheader()
        writer.writerows(a.model_dump() for a in filtered)

    subprocess.run(["git", "add", "manifest.csv"], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", f"[cli:remove] {repo_url}"], cwd=dest, check=True)
    subprocess.run(["git", "push"], cwd=dest, check=True)

    return f"Removed {repo_url} from manifest"
