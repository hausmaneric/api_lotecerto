from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, AppSettings, Farm
from app.schemas.settings import AppSettingsResponse, AppSettingsUpsert
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=AppSettingsResponse | None)
def get_settings(
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> AppSettings | None:
    return db.scalar(select(AppSettings).where(AppSettings.farm_id == farm.id).limit(1))


@router.put("", response_model=AppSettingsResponse)
def upsert_settings(
    payload: AppSettingsUpsert,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> AppSettings:
    settings_row = db.scalar(select(AppSettings).where(AppSettings.farm_id == farm.id).limit(1))
    if settings_row is None:
        settings_row = AppSettings(
            id=payload.id,
            farm_id=farm.id,
            farm_name=payload.farm_name,
            alert_days_before=payload.alert_days_before,
            has_completed_onboarding=payload.has_completed_onboarding,
            created_at=DateTimeService.now_iso(),
            updated_at=None,
        )
        db.add(settings_row)
    else:
        settings_row.farm_name = payload.farm_name
        settings_row.alert_days_before = payload.alert_days_before
        settings_row.has_completed_onboarding = payload.has_completed_onboarding
        settings_row.updated_at = DateTimeService.now_iso()

    db.commit()
    db.refresh(settings_row)
    return settings_row
