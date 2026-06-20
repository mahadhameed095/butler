from client.api import APIClient


def remove(repo_url):
    api = APIClient()
    return api.delete(repo_url)
