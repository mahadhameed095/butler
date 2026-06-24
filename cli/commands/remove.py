from shared.models import App
from cli.lib import with_manifest


@with_manifest
def remove(ctx, repo_url):
    filtered = [a for a in ctx.apps if a.Repo_URL != repo_url]
    if len(filtered) == len(ctx.apps):
        return f"App {repo_url} not found in manifest"
    return filtered, f"[cli:remove] {repo_url}"
