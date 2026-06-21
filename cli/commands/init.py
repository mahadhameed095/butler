import os
import csv
import json
import subprocess
from shared.models import App

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
SAMPLE_SYNC = os.path.join(BASE, "sample-sync.yaml")


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

    workflow_dir = os.path.join(dest, ".github", "workflows")
    workflow_path = os.path.join(workflow_dir, "sync.yaml")
    os.makedirs(workflow_dir, exist_ok=True)

    with open(SAMPLE_SYNC) as sf:
        workflow_content = sf.read()

    existed = os.path.exists(workflow_path)
    content_matches = existed and open(workflow_path).read() == workflow_content

    if content_matches:
        wf_msg = "Workflow already up to date"
    else:
        with open(workflow_path, "w") as f:
            f.write(workflow_content)
        subprocess.run(["git", "add", ".github/workflows/sync.yaml"], cwd=dest, check=True)
        commit_msg = "[cli:init] modified workflow" if existed else "[cli:init] created workflow"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=dest, check=True)
        subprocess.run(["git", "push"], cwd=dest, check=True)
        wf_msg = commit_msg

    config = {"repo_url": repo_url}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    return f"{msg}, {wf_msg}, written {CONFIG_PATH}"
