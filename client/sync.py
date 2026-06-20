import os
import tempfile
import pandas as pd
from shared.models import App
from client.api import APIClient, GithubClient


def sync():
    manifest = pd.read_csv("manifest.csv")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var not set")

    api = APIClient()
    state = api.get_state()
    deployed = state["Apps"]

    with GithubClient(token) as gh:
        for _, row in manifest.iterrows():
            repo_url = row["Repo_Url"]
            latest_sha = gh.get_latest_sha(repo_url, row["Branch"])
            existing = deployed.get(repo_url)
            if existing is None or existing["SHA"] != latest_sha:
                zip_bytes = gh.get_zip(repo_url, row["Branch"])
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                tmp.write(zip_bytes)
                tmp.close()
                api.register(
                    app=App(**row.to_dict()),
                    sha=latest_sha,
                    file_path=tmp.name,
                )
                os.unlink(tmp.name)
                print(f"Deployed {row['Repo_Url']} (SHA: {latest_sha})")
            else:
                print(f"{row['Repo_Url']} is up to date.")

    for repo_url in deployed:
        if repo_url not in manifest["Repo_Url"].values:
            api.delete(repo_url)
            print(f"Removed {repo_url}")


if __name__ == "__main__":
    sync()
