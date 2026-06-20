import os
import urllib.parse
import requests
from models import App


class GithubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })

    @staticmethod
    def _parse_repo(repo: str) -> tuple[str, str]:
        repo = repo.rstrip("/").removeprefix("https://github.com/")
        owner, name = repo.split("/")
        return owner, name

    def get_latest_sha(self, repo: str, branch: str) -> str:
        owner, name = self._parse_repo(repo)
        r = self.session.get(f"{self.BASE}/repos/{owner}/{name}/branches/{branch}")
        r.raise_for_status()
        return r.json()["commit"]["sha"]

    def get_zip(self, repo: str, branch: str) -> bytes:
        owner, name = self._parse_repo(repo)
        r = self.session.get(
            f"{self.BASE}/repos/{owner}/{name}/zipball/{branch}",
            allow_redirects=True
        )
        r.raise_for_status()
        return r.content

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.getenv("SERVER_URL", "http://localhost:8000")).rstrip("/")

    def get_state(self) -> dict:
        resp = requests.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return resp.json()

    def register(self, app: App, sha: str, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            data = {**app.model_dump(), "SHA": sha}
            files = {"File": f}
            resp = requests.post(f"{self.base_url}/register", data=data, files=files)
            resp.raise_for_status()
            return resp.json()

    def delete(self, repo_url: str) -> dict:
        encoded = urllib.parse.quote(repo_url, safe="")
        resp = requests.delete(f"{self.base_url}/apps/{encoded}")
        resp.raise_for_status()
        return resp.json()
