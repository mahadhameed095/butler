import os
import json
import shutil
from pathlib import Path
from shared.models import GithubRepoURL
from cli.lib import ensure_manifest, CONFIG_PATH, BASE
import subprocess

def init(repo_url: GithubRepoURL):
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return f"Already connected to {json.load(f)['repo_url']}"

    dest = Path(BASE) / repo_url.repo
    if dest.exists():
        shutil.rmtree(dest)

    subprocess.run(["git", "clone", repo_url, dest], check=True)

    with open(CONFIG_PATH, "w") as f:
        json.dump({"repo_url": str(repo_url)}, f, indent=2)

    ctx = ensure_manifest()

    if ctx.apps:
        return f"Connected to {repo_url}. Loaded {len(ctx.apps)} app(s) from manifest."
    return f"Connected to {repo_url}."
