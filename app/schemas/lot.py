from pydantic import BaseModel

from app.schemas.common import ApiSchema


class LotBase(BaseModel):
    farm_id: str
    name: str
    animal_count: int = 0
    category: str | None = None
    notes: str | None = None
    is_active: bool = True


class LotCreate(LotBase):
    id: str


class LotUpdate(LotBase):
    pass


class LotResponse(ApiSchema):
    id: str
    farm_id: str
    name: str
    animal_count: int
    category: str | None = None
    notes: str | None = None
    is_active: bool
    created_at: str
    updated_at: str | None = None
