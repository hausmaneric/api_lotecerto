from pydantic import BaseModel

from app.schemas.common import ApiSchema


class AppSettingsUpsert(BaseModel):
    id: str
    farm_name: str | None = None
    alert_days_before: int = 7
    has_completed_onboarding: bool = False


class AppSettingsResponse(ApiSchema):
    id: str
    farm_name: str | None = None
    alert_days_before: int
    has_completed_onboarding: bool
    created_at: str
    updated_at: str | None = None
