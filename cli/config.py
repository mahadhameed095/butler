import json
from pathlib import Path
from typing import Optional
import click
from pydantic import BaseModel
from cli.constants import CONFIG_PATH, DEFAULT_BUTLER_SERVER_CLONE_DIR
from shared.models import GithubRepoURL, SafePath


class ManifestRepo(BaseModel):
    repo_url: GithubRepoURL
    clone_dir_path: SafePath

    @property
    def manifest_file_path(self) -> Path:
        return self.clone_dir_path / "manifest.yaml"

class ServerConfig(BaseModel):
    name: str
    host: str
    user: str              
    ssh_key_path: Path
    port: int = 22
    clone_dir: str = DEFAULT_BUTLER_SERVER_CLONE_DIR

class ButlerConfig(BaseModel):
    active_repo: Optional[str] = None
    manifests: list[ManifestRepo] = []
    server_config : Optional[ServerConfig] = None

    @staticmethod
    def load() -> "ButlerConfig":
        if not Path(CONFIG_PATH).exists():
            return ButlerConfig()
        with open(CONFIG_PATH) as f:
            return ButlerConfig.model_validate(json.load(f))

    def save(self) -> None:
        Path(CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    def get_active(self) -> ManifestRepo:
        if not self.active_repo:
            raise click.ClickException("No active repo. Run 'butler init' first.")
        entry = next((m for m in self.manifests if m.repo_url == self.active_repo), None)
        if not entry:
            raise click.ClickException(f"Active repo {self.active_repo} not found in config.")
        return entry

    def register(self, manifest_repo: ManifestRepo) -> "ButlerConfig":
        manifests = [m for m in self.manifests if m.repo_url != manifest_repo.repo_url]
        manifests.append(manifest_repo)
        return self.model_copy(update={"active_repo": str(manifest_repo.repo_url), "manifests": manifests})
