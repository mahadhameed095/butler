from shared.models import App
from cli.lib import with_manifest


@with_manifest
def add(ctx, app: App):
    ctx.apps.append(app)
    return ctx.apps, f"[cli:add] {app.Repo_URL} | {app.Branch}"
