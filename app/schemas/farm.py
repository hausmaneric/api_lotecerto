from pydantic import BaseModel

from app.schemas.common import ApiSchema


class FarmCreate(BaseModel):
    id: str
    name: str
    owner_name: str | None = None


class FarmUpdate(BaseModel):
    name: str
    owner_name: str | None = None


class FarmResponse(ApiSchema):
    id: str
    name: str
    owner_name: str | None = None
    created_at: str
    updated_at: str | None = None
