from pydantic import BaseModel
from typing import Dict
from datetime import datetime

class AppState(BaseModel):
    # 'repo' is now the key in the dictionary, but keeping it here 
    # for full object consistency
    repo: str
    sha: str
    route: str
    entry: str
    deployed_at: datetime

class ServerState(BaseModel):
    # Key: repo URL (str), Value: AppState object
    apps: Dict[str, AppState]
    last_updated: datetime
    uptime: float

class RegisterRequest(AppState):
    zip_bytes: bytes  # Including the file content directly

class Server():
    def __init__(self):
        pass

    def get_state(self) -> ServerState:
        # Example dictionary population
        apps = {
            "https://github.com/mahadhameed095/pathfinder-visualizer": AppState(
                repo="https://github.com/mahadhameed095/pathfinder-visualizer",
                sha="1234",
                route="algorithms/pathfinder-visualizer",
                entry="index.html",
                deployed_at=datetime.utcnow()
            ),
            "https://github.com/mahadhameed095/sortify": AppState(
                repo="https://github.com/mahadhameed095/sortify",
                sha="5678",
                route="sortify",
                entry="index.html",
                deployed_at=datetime.utcnow()
            )
        }
        
        return ServerState(
            apps=apps,
            last_updated=datetime.utcnow(),
            uptime=3600.0
        )
    
    def register(self, request: RegisterRequest):
            # We split the metadata from the file content for the request
            # This keeps the 'data' part strictly JSON-serializable
            metadata = {
                "name": request.name,
                "repo": request.repo,
                "sha": request.sha,
                "route": request.route,
                "entry": request.entry
            }

            return True
    
    def delete(self, repo):
         
        return True