from utils import Server, RegisterRequest
from github_service import get_latest_sha_from_github
import pandas as pd

# --- CORE LOGIC ---
def sync():
    # 1. Load Desired State from CSV
    with open('manifest.csv', 'r') as f:
        manifest = pd.read_csv('manifest.csv')
    
    # 2. Fetch Actual State
    server = Server()
    deployed_apps = server.get_state()

    # 3. Reconciliation
    # CREATE / UPDATE
    for i, row in manifest.iterrows():
        latest_sha = get_latest_sha_from_github(row['repo'], row['branch'])
        if ((row['repo'] not in deployed_apps.apps)
            or (latest_sha != deployed_apps.apps[row['repo']].sha)):
            server.register(
                RegisterRequest(
                    # pass the params                    
                )
            )
            print(f"Action: Updating/Deploying {row['repo']} (SHA: {latest_sha})")
        else:
            print(f"Action: {row['repo']} is already up to date.")

    # DELETE
    for app in deployed_apps.apps.keys():
        if app not in manifest['repo'].values:
            server.delete(app)
            print(f"Action: Removing {app}")

if __name__ == "__main__":
    sync()