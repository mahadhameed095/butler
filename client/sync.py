import os
import tempfile
import requests
import pandas as pd
from models import App
from github_service import get_latest_sha_from_github
from client.api import APIClient


def _download_zip(repo_url: str, branch: str) -> str:
    repo_path = repo_url.removeprefix("https://github.com/")
    url = f"https://github.com/{repo_path}/archive/refs/heads/{branch}.zip"
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    for chunk in resp.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    return tmp.name


def sync():
    manifest = pd.read_csv("manifest.csv")

    api = APIClient()
    state = api.get_state()
    deployed = state["Apps"]

    for _, row in manifest.iterrows():
        latest_sha = get_latest_sha_from_github(row["Repo_Url"], row["Branch"])
        existing = deployed.get(row["Repo_Url"])
        if existing is None or existing["SHA"] != latest_sha:
            zip_path = _download_zip(row["Repo_Url"], row["Branch"])
            api.register(
                app=App(**row.to_dict()),
                sha=latest_sha,
                file_path=zip_path,
            )
            os.unlink(zip_path)
            print(f"Deployed {row['Repo_Url']} (SHA: {latest_sha})")
        else:
            print(f"{row['Repo_Url']} is up to date.")

    for repo_url in deployed:
        if repo_url not in manifest["Repo_Url"].values:
            api.delete(repo_url)
            print(f"Removed {repo_url}")


if __name__ == "__main__":
    sync()
