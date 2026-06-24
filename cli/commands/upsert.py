import click
from shared.models import App, GithubRepoURL
from cli.ManifestManager import ManifestManager
from cli.pydantic_click import pydantic_options, make_optional

PartialApp = make_optional(App)

WARNINGS = {
    "Deploy_Dir": "App will be moved from {old} to {new}.",
    "Route":      "WARNING: Route changed. This is destructive. Consider setting up a redirect.",
    "Branch":     "Branch changed. This will replace the current deployment with the new branch.",
    "Entry_File": "Entry file changed from {old} to {new}.",
}


def _prompt_fields(repo_url: str, d: App | None) -> dict:
    fields = {}
    for field_name, field_info in App.model_fields.items():
        if field_name == "Repo_URL":
            fields["Repo_URL"] = repo_url
            continue
        meta = field_info.json_schema_extra
        raw_default = meta["default"]
        resolved = raw_default(repo_url) if callable(raw_default) else (str(getattr(d, field_name)) if d else raw_default)
        fields[field_name] = click.prompt(meta["prompt"], default=resolved)
    return fields


@click.command()
@pydantic_options(PartialApp)
def upsert(app: PartialApp):
    manifest = ManifestManager()
    repo_url = str(app.Repo_URL) if app.Repo_URL else click.prompt("Repo URL")
    current = manifest.get_app(repo_url)

    mapped = {k: v for k, v in app.model_dump().items() if v is not None}
    default = current.model_copy(update=mapped) if current else None

    fields = _prompt_fields(repo_url, default)

    if current:
        for field, msg in WARNINGS.items():
            old, new = str(getattr(current, field)), fields[field]
            if old != new:
                click.echo(msg.format(old=old, new=new))

    manifest.upsert_app(App(**fields))
    manifest.commit(f"[cli:upsert] {repo_url}")
    click.echo(f"{'Updated' if current else 'Added'} {repo_url}")