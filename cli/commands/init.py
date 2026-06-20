import os
import json
import subprocess

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def init(repo_url, vm_host, path):
    if path:
        subprocess.run(["git", "clone", repo_url, path], check=True)
    else:
        path = repo_url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
        subprocess.run(["git", "clone", repo_url, path], check=True)

    config = {"repo_url": repo_url, "vm_host": vm_host, "path": path}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return f"Written {CONFIG_PATH}"
