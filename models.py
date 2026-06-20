from typing import Dict
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from fastapi import Form, File, UploadFile
from dataclasses import dataclass

class App(BaseModel):
    Repo_Url: str
    Server_Path: str
    Route: str
    Branch: str
    Entry: str

class DeployedApp(SQLModel, table=True):
    __tablename__ = "deployments"

    Repo_Url: str = Field(primary_key=True)
    Server_Path: str
    Route: str
    Branch: str
    Entry: str
    SHA: str
    Created_time: datetime
    Last_Updated_Time: datetime

@dataclass
class RegisterRequest:
    Repo_Url: str = Form(...)
    Server_Path: str = Form(...)
    Route: str = Form(...)
    Branch: str = Form(...)
    Entry: str = Form(...)
    SHA: str = Form(...)
    File: UploadFile = File(...)

class ServerState(BaseModel):
    Apps: Dict[str, dict]
    Last_updated: datetime
    Uptime: float
