from shared.models import App
from cli.shared import with_manifest, load_config, GithubRepoURL
import os


def get_app(repo_url):
    config = load_config()
    dest = os.path.join(os.path.dirname(os.path.dirname(__file__)), GithubRepoURL(config["repo_url"]).repo)
    manifest_path = os.path.join(dest, "manifest.csv")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("manifest.csv not found")
    with open(manifest_path, newline="") as f:
        from csv import DictReader
        for row in DictReader(f):
            app = App(**row)
            if app.Repo_URL == repo_url:
                return app
    return None


@with_manifest
def update(apps, new_app: App):
    repo_url = new_app.Repo_URL
    idx = None
    for i, a in enumerate(apps):
        if a.Repo_URL == repo_url:
            idx = i
            break
    if idx is None:
        raise RuntimeError(f"{repo_url} not found in manifest. Use add instead.")

    current = apps[idx]
    changes = []
    if current.Deploy_Dir != new_app.Deploy_Dir:
        changes.append(("deploy_dir", current.Deploy_Dir, new_app.Deploy_Dir))
        print(f"App will be moved from {current.Deploy_Dir} to {new_app.Deploy_Dir}")
    if current.Route != new_app.Route:
        changes.append(("route", current.Route, new_app.Route))
        print(f"WARNING: Route changed from {current.Route} to {new_app.Route}. This is destructive. Consider setting up a redirect.")
    if current.Branch != new_app.Branch:
        changes.append(("branch", current.Branch, new_app.Branch))
        print(f"Branch changed from {current.Branch} to {new_app.Branch}. This is destructive, and will replace current deployment with the new branch.")
    if current.Entry_File != new_app.Entry_File:
        changes.append(("entry_file", current.Entry_File, new_app.Entry_File))
        print(f"Entry file changed from {current.Entry_File} to {new_app.Entry_File}")

    if not changes:
        return "No changes detected"

    apps[idx] = new_app
    param_names = [p for p, _, _ in changes]
    return apps, f"[cli:update] {repo_url} | [{', '.join(param_names)}]"
