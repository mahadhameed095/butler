import zipfile
import io
import os
import shutil
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session, select
from shared.models import ServerState, DeployedApp, RegisterRequest
from dotenv import load_dotenv; load_dotenv()

app = FastAPI()

db_path = os.getenv("DEPLOYMENTS_DB_PATH")
if not db_path:
    raise RuntimeError("DEPLOYMENTS_DB_PATH env var not set")
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/get-state")
def get_state():
    with Session(engine) as session:
        apps = session.exec(select(DeployedApp)).all()
        apps_dict = {a.Repo_Url: a.model_dump() for a in apps}
        now = datetime.now(timezone.utc)
        uptime = (now - min(a.Created_time for a in apps)).total_seconds() if apps else 0
        return ServerState(Apps=apps_dict, Last_updated=now, Uptime=uptime)

@app.post("/register")
def register(params: RegisterRequest = Depends()):
    with Session(engine) as session:
        existing = session.get(DeployedApp, params.Repo_Url)

        if existing is None or existing.SHA != params.SHA:
            extract_path = params.Server_Path
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            os.makedirs(extract_path, exist_ok=True)
            contents = params.File.file.read()
            with zipfile.ZipFile(io.BytesIO(contents)) as z:
                z.extractall(extract_path)

            now = datetime.now(timezone.utc)
            if existing is None:
                new_app = DeployedApp(
                    Repo_Url=params.Repo_Url,
                    Server_Path=params.Server_Path,
                    Route=params.Route,
                    Branch=params.Branch,
                    Entry=params.Entry,
                    SHA=params.SHA,
                    Created_time=now,
                    Last_Updated_Time=now,
                )
                session.add(new_app)
            else:
                existing.Server_Path = params.Server_Path
                existing.Route = params.Route
                existing.Branch = params.Branch
                existing.Entry = params.Entry
                existing.SHA = params.SHA
                existing.Last_Updated_Time = now

            session.commit()
            return {"status": "success"}

        return {"status": "skipped", "reason": "SHA unchanged"}

@app.delete("/apps/{repo:path}")
def delete_app(repo: str):
    with Session(engine) as session:
        app = session.get(DeployedApp, repo)
        if app is None:
            raise HTTPException(status_code=404, detail="App not found")
        session.delete(app)
        session.commit()
        return {"status": "deleted"}
