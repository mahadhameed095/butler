import subprocess
from pathlib import Path
import click
import yaml
from pydantic import ValidationError
from shared.models import App, GithubRepoURL
from shared.utils import git
from cli.config import ManifestRepo
from cli.utils import with_active_manifest, handle_errors
from cli.constants import SAMPLE_SYNC


WARNINGS = {
    "Deploy_Dir": "App will be moved from {old} to {new}.",
    "Route":      "WARNING: Route changed. This is destructive. Consider setting up a redirect.",
    "Branch":     "Branch changed. This will replace the current deployment with the new branch.",
    "Entry_File": "Entry file changed from {old} to {new}.",
}


# --- Validation ---

def _validate_apps(raw: list[dict], *, label: str) -> tuple[list[App], list[str]]:
    apps, errors = [], []
    for i, entry in enumerate(raw):
        try:
            app = App(**entry)
            app = App.model_validate({**entry, "Repo_URL": GithubRepoURL(app.Repo_URL).url2https})
            apps.append(app)
        except (ValidationError, ValueError) as e:
            errors.append(f"  [{label} entry {i+1}] {e}")
    return apps, errors


def _cross_validate(apps: list[App]) -> list[str]:
    errors = []
    seen_repo, seen_route, seen_dir = {}, {}, {}
    for app in apps:
        repo, route, deploy_dir = str(app.Repo_URL), str(app.Route), str(app.Deploy_Dir)
        if repo in seen_repo:
            errors.append(f"  Duplicate Repo_URL: {repo}")
        seen_repo[repo] = True
        if route in seen_route:
            errors.append(f"  Duplicate Route: {route} (conflicts with {seen_route[route]})")
        seen_route[route] = repo
        if deploy_dir in seen_dir:
            errors.append(f"  Duplicate Deploy_Dir: {deploy_dir} (conflicts with {seen_dir[deploy_dir]})")
        seen_dir[deploy_dir] = repo
    return errors


# --- Git helpers ---

def _head_exists(repo_path: Path) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path, capture_output=True
    ).returncode == 0


def _head_file(repo_path: Path, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=repo_path, capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else None


def _load_head_apps(repo_path: Path) -> tuple[list[App], list[str]]:
    raw = _head_file(repo_path, "manifest.yaml")
    if raw is None:
        return [], []
    return _validate_apps(yaml.safe_load(raw), label="HEAD")


def _sync_yaml_status(repo_path: Path, template: str) -> str | None:
    head_sync = _head_file(repo_path, ".github/workflows/sync.yaml")
    if head_sync is None:
        return "initialized sync.yaml"
    if head_sync != template:
        return "updated sync.yaml"
    return None


# --- Diff ---

def _diff(old: list[App], new: list[App]) -> tuple[list[App], list[App], list[tuple[App, App]]]:
    old_map = {str(a.Repo_URL): a for a in old}
    new_map = {str(a.Repo_URL): a for a in new}
    added   = [a for k, a in new_map.items() if k not in old_map]
    removed = [a for k, a in old_map.items() if k not in new_map]
    updated = [
        (old_map[k], new_map[k])
        for k in new_map
        if k in old_map and old_map[k].model_dump() != new_map[k].model_dump()
    ]
    return added, removed, updated


# --- Commit message ---

def _build_commit_message(
    added: list[App],
    removed: list[App],
    updated: list[tuple[App, App]],
    head_warnings: list[str],
    is_first_commit: bool,
    sync_status: str | None,
) -> str:
    parts = []
    if is_first_commit:
        parts.append("init")
    if added:
        parts.append(f"added: {', '.join(str(a.Repo_URL) for a in added)}")
    if removed:
        parts.append(f"removed: {', '.join(str(a.Repo_URL) for a in removed)}")
    if updated:
        parts.append(f"updated: {', '.join(str(o.Repo_URL) for o, _ in updated)}")

    lines = [f"[butler] {' | '.join(parts)}", ""]

    if is_first_commit:
        lines += ["initialized manifest.yaml (first commit)", ""]
    if sync_status:
        lines += [f"workflow: {sync_status}", ""]
    if head_warnings:
        lines += ["WARNINGS (existing apps in invalid state):", *head_warnings, ""]
    if added:
        lines += ["added:", *[f"  - {a.Repo_URL}" for a in added], ""]
    if removed:
        lines += ["removed:", *[f"  - {a.Repo_URL}" for a in removed], ""]
    if updated:
        lines.append("updated:")
        for old, new in updated:
            lines.append(f"  - {old.Repo_URL}")
            for field, template in WARNINGS.items():
                old_val, new_val = str(getattr(old, field)), str(getattr(new, field))
                if old_val != new_val:
                    lines.append(f"    {template.format(old=old_val, new=new_val)}")
        lines.append("")

    return "\n".join(lines).strip()


# --- Sync helpers ---

def _pull_with_stash(repo_path: Path) -> None:
    stashes = git(["stash", "list"], cwd=repo_path)
    if stashes:
        raise click.ClickException(
            "Existing git stashes detected. Resolve them manually before running 'butler commit'."
        )

    dirty = git(["status", "--porcelain"], cwd=repo_path)
    non_manifest = [l for l in dirty.splitlines() if "manifest.yaml" not in l]
    if non_manifest:
        raise click.ClickException(
            "Unexpected local changes detected outside manifest.yaml. "
            "Resolve them manually before running 'butler commit'."
        )

    has_manifest_changes = any("manifest.yaml" in l for l in dirty.splitlines())

    if has_manifest_changes:
        git(["stash", "--", "manifest.yaml"], cwd=repo_path)

    git(["pull"], cwd=repo_path)

    if has_manifest_changes:
        try:
            git(["stash", "pop"], cwd=repo_path)
        except Exception:
            click.echo("Conflict detected. Opening merge editor...")
            subprocess.run(["git", "mergetool"], cwd=repo_path)
            remaining = git(["diff", "--name-only", "--diff-filter=U"], cwd=repo_path)
            if remaining:
                raise click.ClickException(
                    "Conflicts remain unresolved. Fix them and run 'butler commit' again."
                )
            git(["stash", "drop"], cwd=repo_path)


# --- Command ---

@click.command()
@handle_errors
@with_active_manifest
def commit(entry: ManifestRepo):
    repo_path = entry.clone_dir_path
    manifest_path = entry.manifest_file_path
    workflow_path = repo_path / ".github" / "workflows" / "sync.yaml"
    template = Path(SAMPLE_SYNC).read_text()

    # step 1: sync with remote
    _pull_with_stash(repo_path)

    # step 2: push any unpushed local commits
    unpushed = git(["rev-list", "HEAD@{u}..HEAD", "--count"], cwd=repo_path)
    if int(unpushed) > 0:
        click.confirm(
            f"There are {unpushed} unpushed local commits. Push them now?",
            abort=True
        )
        git(["push"], cwd=repo_path)

    # step 3: validate sync.yaml exists
    if not workflow_path.exists():
        raise click.ClickException(
            "sync.yaml not found. Run 'butler init' to set up the workflow."
        )

    # step 4: validate manifest.yaml exists
    if not manifest_path.exists():
        raise click.ClickException(
            "manifest.yaml not found. Run 'butler init' to set up the manifest."
        )

    # step 5: validate app entries
    raw_new = yaml.safe_load(manifest_path.read_text())
    new_apps, new_errors = _validate_apps(raw_new, label="new")
    if new_errors:
        raise click.ClickException(
            "manifest.yaml contains invalid entries. Run 'butler manifest' to fix them:\n"
            + "\n".join(new_errors)
        )

    # step 6: cross-validate uniqueness
    cross_errors = _cross_validate(new_apps)
    if cross_errors:
        raise click.ClickException(
            "manifest.yaml has conflicting entries. Run 'butler manifest' to fix them:\n"
            + "\n".join(cross_errors)
        )

    # step 7: diff and build commit message
    old_apps, head_warnings = _load_head_apps(repo_path)
    is_first_commit = not _head_exists(repo_path)
    added, removed, updated = _diff(old_apps, new_apps)
    sync_status = _sync_yaml_status(repo_path, template)

    # step 8: nothing changed
    if not added and not removed and not updated and not sync_status:
        click.echo("Nothing to commit.")
        return

    message = _build_commit_message(
        added, removed, updated,
        head_warnings,
        is_first_commit,
        sync_status,
    )

    # step 9: commit and push
    git(["add", "."], cwd=repo_path)
    git(["commit", "-m", message], cwd=repo_path)
    git(["push"], cwd=repo_path)

    click.echo(message)