import os
import tempfile
from shared.models import App
from client.api import APIClient, GithubClient


def add(repo_url, server_path, route, branch, entry, sha):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var not set")

    api = APIClient()
    with GithubClient(token) as gh:
        sha = sha or gh.get_latest_sha(repo_url, branch)
        zip_bytes = gh.get_zip(repo_url, branch)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(zip_bytes)
    tmp.close()

    app = App(Repo_Url=repo_url, Server_Path=server_path,
              Route=route, Branch=branch, Entry=entry)
    result = api.register(app=app, sha=sha, file_path=tmp.name)
    os.unlink(tmp.name)
    return result
