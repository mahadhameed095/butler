from shared.models import App
from cli.shared import with_manifest


@with_manifest
def add(apps, app: App):
    apps.append(app)
    return apps, f"[cli:add] {app.Repo_URL} | {app.Branch}"
