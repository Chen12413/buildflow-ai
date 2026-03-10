from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Platform(StrEnum):
    WEB = "web"
    MOBILE = "mobile"
    BOTH = "both"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    idea: str = Field(min_length=1, max_length=500)
    target_user: str = Field(min_length=1, max_length=300)
    platform: Platform
    constraints: str | None = Field(default=None, max_length=1000)


class ProjectRead(BaseModel):
    id: str
    name: str
    idea: str
    target_user: str
    platform: Platform
    constraints: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
