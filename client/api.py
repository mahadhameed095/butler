import os
import urllib.parse
import requests
from models import App


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
