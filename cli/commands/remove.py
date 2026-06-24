from shared.models import App
from cli.shared import with_manifest


@with_manifest
def remove(apps, dest, repo_url):
    filtered = [a for a in apps if a.Repo_URL != repo_url]
    if len(filtered) == len(apps):
        return f"App {repo_url} not found in manifest"
    return filtered, f"[cli:remove] {repo_url}"
