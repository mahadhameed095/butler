# --- MOCK HELPERS (Replace these later with real logic) ---
def get_latest_sha_from_github(repo_url, branch):
    # MOCK: In reality, use GitHub API with a PAT
    # This just generates a dummy hash based on the repo name for testing
    if repo_url == "https://github.com/mahadhameed095/sortify":
        return "5678"
    return f"sha-{hash(repo_url + branch) % 10000}"
