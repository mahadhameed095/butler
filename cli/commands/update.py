import os
import tempfile
from shared.models import App
from client.api import APIClient, GithubClient


def update(repo_url, server_path, route, branch, entry, sha):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var not set")

    api = APIClient()
    state = api.get_state()
    existing = state["Apps"].get(repo_url)
    if not existing:
        raise RuntimeError(f"{repo_url} is not deployed. Use add instead.")

    with GithubClient(token) as gh:
        sha = sha or gh.get_latest_sha(repo_url, branch)
        if sha == existing["SHA"]:
            return "Already up to date."
        zip_bytes = gh.get_zip(repo_url, branch)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(zip_bytes)
    tmp.close()

    app = App(Repo_Url=repo_url, Server_Path=server_path,
              Route=route, Branch=branch, Entry=entry)
    result = api.register(app=app, sha=sha, file_path=tmp.name)
    os.unlink(tmp.name)
    return result
