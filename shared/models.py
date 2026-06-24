import re
from typing import Any, Dict, Annotated
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, GetCoreSchemaHandler, AfterValidator, Field as PydanticField
from pydantic_core import core_schema
from sqlalchemy import event
from sqlmodel import SQLModel, Field
from fastapi import Form, File, UploadFile
from dataclasses import dataclass
from giturlparse import parse, GitUrlParsed


class GithubRepoURL(str):
    _parsed: GitUrlParsed

    def __new__(cls, value: str) -> "GithubRepoURL":
        parsed = parse(value)
        if not parsed.valid or not parsed.github:
            raise ValueError(f"Invalid GitHub URL: {value}")
        instance = super().__new__(cls, value)
        instance._parsed = parsed
        return instance

    @property
    def owner(self) -> str:
        return self._parsed.owner

    @property
    def repo(self) -> str:
        return self._parsed.repo

    @property
    def url2ssh(self) -> str:
        return self._parsed.url2ssh

    @property
    def url2https(self) -> str:
        return self._parsed.url2https

    @property
    def urls(self) -> dict:
        return self._parsed.urls

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: Any) -> "GithubRepoURL":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value)
        raise ValueError(f"Expected str, got {type(value)}")


def _no_traversal(v: Path) -> Path:
    if ".." in v.parts:
        raise ValueError(f"Path traversal not allowed: {v}")
    return v

SafePath = Annotated[Path, AfterValidator(_no_traversal)]

def _validate_route(v: str) -> str:
    v = v.strip("/")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)*", v):
        raise ValueError(f"Invalid route: '{v}'")
    return v

RouteType = Annotated[str, AfterValidator(_validate_route)]


class App(BaseModel):
    Repo_URL: GithubRepoURL
    Deploy_Dir: SafePath = PydanticField(json_schema_extra={
        "prompt": "Deploy dir",
        "default": lambda repo_url: f"~/.local/{GithubRepoURL(repo_url).repo}",
    })
    Route: RouteType = PydanticField(json_schema_extra={
        "prompt": "Route",
        "default": None,
    })
    Branch: str = PydanticField(json_schema_extra={
        "prompt": "Branch",
        "default": "dist",
    })
    Entry_File: SafePath = PydanticField(json_schema_extra={
        "prompt": "Entry file",
        "default": "index.html",
    })


class DeployedApp(App, SQLModel, table=True):
    __tablename__ = "deployments"

    Repo_URL: GithubRepoURL = Field(primary_key=True)
    SHA: str
    Created_Time: datetime
    Last_Updated_Time: datetime


@event.listens_for(DeployedApp, "load")
def on_load(instance, context):
    try:
        validated = App.model_validate(instance.__dict__)
        for field in App.model_fields:
            setattr(instance, field, getattr(validated, field))
    except Exception as e:
        raise RuntimeError(f"Failed to hydrate DeployedApp from DB: {e}") from e

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
