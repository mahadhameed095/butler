import os
import csv
from client.api import GithubClient


def sync():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var not set")

    manifest_path = os.getenv("MANIFEST_REPO_PATH")
    if not manifest_path:
        raise RuntimeError("MANIFEST_REPO_PATH env var not set")

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with GithubClient(token) as gh:
        for row in rows:
            sha = gh.get_latest_sha(row["Repo_Url"], row["Branch"])
            print(f"{row['Repo_Url']}  {sha[:12]}")


if __name__ == "__main__":
    sync()
