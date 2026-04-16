from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, AppSettings, Lot, VaccinationRecord, Vaccine
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    alert_days_before: int | None = Query(default=None),
    farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    settings_row = db.scalar(select(AppSettings).where(AppSettings.farm_id == farm.id).limit(1))
    effective_alert_days = alert_days_before or settings_row.alert_days_before if settings_row else 7

    records = list(
        db.scalars(
            select(VaccinationRecord)
            .join(VaccinationRecord.lot)
            .join(VaccinationRecord.vaccine)
            .where(Lot.farm_id == farm.id, Vaccine.farm_id == farm.id)
        ).all()
    )
    overdue_count = 0
    upcoming_count = 0
    for record in records:
        status_value = DateTimeService.compute_status(record.next_due_date, effective_alert_days)
        if status_value == "overdue":
            overdue_count += 1
        elif status_value == "upcoming":
            upcoming_count += 1

    return DashboardSummaryResponse(
        active_lots_count=db.scalar(select(func.count()).select_from(Lot).where(Lot.farm_id == farm.id, Lot.is_active.is_(True))) or 0,
        inactive_lots_count=db.scalar(select(func.count()).select_from(Lot).where(Lot.farm_id == farm.id, Lot.is_active.is_(False))) or 0,
        active_vaccines_count=db.scalar(select(func.count()).select_from(Vaccine).where(Vaccine.farm_id == farm.id, Vaccine.is_active.is_(True))) or 0,
        overdue_count=overdue_count,
        upcoming_count=upcoming_count,
        total_records_count=len(records),
    )
