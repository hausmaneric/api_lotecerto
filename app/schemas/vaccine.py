from pydantic import BaseModel

from app.schemas.common import ApiSchema


class VaccineBase(BaseModel):
    name: str
    description: str | None = None
    interval_days: int = 0
    is_mandatory: bool = False
    is_active: bool = True


class VaccineCreate(VaccineBase):
    id: str


class VaccineUpdate(VaccineBase):
    pass


class VaccineResponse(ApiSchema):
    id: str
    name: str
    description: str | None = None
    interval_days: int
    is_mandatory: bool
    is_active: bool
    created_at: str
    updated_at: str | None = None
