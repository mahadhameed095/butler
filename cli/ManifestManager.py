import csv
import json
import subprocess
import functools
from pathlib import Path
import click
from shared.models import App, GithubRepoURL
from cli.constants import CONFIG_PATH, BASE, SAMPLE_SYNC


class ManifestManager:

    def __init__(self):
        repo_url_str = self._load_config()
        self.repo_url = GithubRepoURL(repo_url_str)
        self.dest = self._ensure_repo()
        self.manifest_path = self.dest / "manifest.csv"
        self._apps = self._load_manifest()
        self._ensure_workflow()
        self._dirty = False

    def _load_config(self) -> str:
        if not Path(CONFIG_PATH).exists():
            raise RuntimeError("No manifest repo connected. Run 'butler init' first.")
        with open(CONFIG_PATH) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                raise RuntimeError("config.json is corrupt. Run 'butler init' again.")
        repo_url = data.get("repo_url")
        if not repo_url:
            raise RuntimeError("config.json missing repo_url. Run 'butler init' again.")
        return repo_url

    def _ensure_repo(self) -> Path:
        dest = Path(BASE) / self.repo_url.repo
        if not (dest / ".git").exists():
            raise RuntimeError(f"Manifest repo not cloned at {dest}. Run 'butler init' again.")
        result = subprocess.run(["git", "pull"], cwd=dest, capture_output=True)
        if result.returncode != 0:
            click.echo("WARNING: git pull failed, working with local copy", err=True)
        return dest

    def _load_manifest(self) -> list[App]:
        if not self.manifest_path.exists():
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=App.model_fields.keys()).writeheader()
            self._git_commit("manifest.csv", msg="[init] create manifest")
            return []
        with open(self.manifest_path, newline="") as f:
            apps = []
            for i, row in enumerate(csv.DictReader(f), start=2):
                try:
                    apps.append(App(**row))
                except Exception as e:
                    click.echo(f"ERROR: manifest.csv line {i}: {e}", err=True)
                    raise RuntimeError("manifest.csv contains invalid rows. Fix or recreate it.")
            return apps

    def _ensure_workflow(self) -> None:
        if not Path(SAMPLE_SYNC).exists():
            return
        workflow_path = self.dest / ".github" / "workflows" / "sync.yaml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)

        head_has_it = subprocess.run(
            ["git", "show", "HEAD:.github/workflows/sync.yaml"],
            cwd=self.dest, capture_output=True, check=False
        ).returncode == 0

        if not workflow_path.exists() and head_has_it:
            subprocess.run(["git", "checkout", "HEAD", "--", ".github/workflows/sync.yaml"], cwd=self.dest, check=False)
            return

        template = Path(SAMPLE_SYNC).read_text()
        if workflow_path.exists() and workflow_path.read_text() == template:
            return

        if workflow_path.exists():
            if not click.confirm(f"{workflow_path} differs from template. Overwrite?", default=True):
                click.echo("WARNING: workflow file is out of date. Deploy pipeline may behave unexpectedly.")
                return

        workflow_path.write_text(template)
        self._git_commit(".github/workflows/sync.yaml", msg="[cli:init] updated workflow", push=False)
        subprocess.run(["git", "push"], cwd=self.dest, check=False)

    # --- Git ---

    def _git_commit(self, *files, msg: str, push: bool = False) -> None:
        for f in files:
            subprocess.run(["git", "add", f], cwd=self.dest, check=True)
        subprocess.run(["git", "commit", "-m", msg], cwd=self.dest, check=True)
        if push:
            subprocess.run(["git", "push"], cwd=self.dest, check=True)

    def push(self) -> None:
        subprocess.run(["git", "push"], cwd=self.dest, check=True)

    # --- CRUD ---

    def get_apps(self) -> list[App]:
        return self._apps

    def get_app(self, repo_url: str) -> App | None:
        return next((a for a in self._apps if str(a.Repo_URL) == repo_url), None)

    def upsert_app(self, app: App) -> None:
        idx = next((i for i, a in enumerate(self._apps) if a.Repo_URL == app.Repo_URL), None)
        if idx is None:
            self._apps.append(app)
        else:
            self._apps[idx] = app
        self._dirty = True

    def remove_app(self, repo_url: str) -> None:
        before = len(self._apps)
        self._apps = [a for a in self._apps if str(a.Repo_URL) != repo_url]
        if len(self._apps) == before:
            raise RuntimeError(f"{repo_url} not found in manifest")
        self._dirty = True

    def commit(self, msg: str) -> None:
        if not self._dirty:
            return
        with open(self.manifest_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=App.model_fields.keys())
            writer.writeheader()
            writer.writerows(a.model_dump() for a in self._apps)
        self._git_commit("manifest.csv", msg=msg)
        self._dirty = False

    # --- Decorator ---

    @staticmethod
    def with_manifest(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(ManifestManager(), *args, **kwargs)
        return wrapper
