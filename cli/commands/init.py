import os
import csv
import json
import subprocess
from shared.models import App

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def init(repo_url):
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return f"Already connected to {config['repo_url']}"

    dest = os.path.join(BASE, repo_url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1])
    subprocess.run(["git", "clone", repo_url, dest], check=True)

    manifest_path = os.path.join(dest, "manifest.csv")
    if os.path.exists(manifest_path):
        with open(manifest_path, newline="") as f:
            reader = csv.DictReader(f)
            apps = [App(**row) for row in reader]
        msg = f"Loaded {len(apps)} apps from manifest"
    else:
        msg = "No manifest found"

    config = {"repo_url": repo_url}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    return f"{msg}, written {CONFIG_PATH}"
