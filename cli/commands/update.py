from shared.models import App
from cli.lib import with_manifest, ensure_manifest


def get_app(repo_url):
    ctx = ensure_manifest()
    for app in ctx.apps:
        if app.Repo_URL == repo_url:
            return app
    return None


@with_manifest
def update(ctx, new_app: App):
    repo_url = new_app.Repo_URL
    idx = None
    for i, a in enumerate(ctx.apps):
        if a.Repo_URL == repo_url:
            idx = i
            break
    if idx is None:
        raise RuntimeError(f"{repo_url} not found in manifest. Use add instead.")

    current = ctx.apps[idx]
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

    ctx.apps[idx] = new_app
    param_names = [p for p, _, _ in changes]
    return ctx.apps, f"[cli:update] {repo_url} | [{', '.join(param_names)}]"
