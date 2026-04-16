from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, Farm, Lot, VaccinationRecord, Vaccine
from app.schemas.vaccination import (
    VaccinationRecordCreate,
    VaccinationRecordDetails,
    VaccinationRecordResponse,
    VaccinationRecordUpdate,
)
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/vaccinations", tags=["vaccinations"], dependencies=[Depends(get_current_user)])


def _build_query(farm_id: str, lot_id: str | None, vaccine_id: str | None) -> Select[tuple[VaccinationRecord]]:
    query = (
        select(VaccinationRecord)
        .join(VaccinationRecord.lot)
        .join(VaccinationRecord.vaccine)
        .options(joinedload(VaccinationRecord.lot), joinedload(VaccinationRecord.vaccine))
        .where(Lot.farm_id == farm_id, Vaccine.farm_id == farm_id)
        .order_by(VaccinationRecord.application_date.desc())
    )
    if lot_id:
        query = query.where(VaccinationRecord.lot_id == lot_id)
    if vaccine_id:
        query = query.where(VaccinationRecord.vaccine_id == vaccine_id)
    return query


@router.get("", response_model=list[VaccinationRecordDetails])
def list_vaccinations(
    lot_id: str | None = Query(default=None),
    vaccine_id: str | None = Query(default=None),
    only_alerts: bool = Query(default=False),
    alert_days_before: int = Query(default=7),
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> list[VaccinationRecordDetails]:
    items = list(db.scalars(_build_query(farm.id, lot_id, vaccine_id)).all())
    rows: list[VaccinationRecordDetails] = []
    for item in items:
        status_value = DateTimeService.compute_status(item.next_due_date, alert_days_before)
        if only_alerts and status_value not in {"overdue", "upcoming"}:
            continue
        rows.append(
            VaccinationRecordDetails(
                id=item.id,
                lot_id=item.lot_id,
                vaccine_id=item.vaccine_id,
                lot_name=item.lot.name,
                vaccine_name=item.vaccine.name,
                application_date=item.application_date,
                next_due_date=item.next_due_date,
                quantity_applied=item.quantity_applied,
                responsible_name=item.responsible_name,
                notes=item.notes,
                created_at=item.created_at,
                updated_at=item.updated_at,
                sync_status=item.sync_status,
                status=status_value,
            )
        )
    return rows


@router.post("", response_model=VaccinationRecordResponse, status_code=status.HTTP_201_CREATED)
def create_vaccination(
    payload: VaccinationRecordCreate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> VaccinationRecord:
    if db.get(VaccinationRecord, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registro ja existe")
    lot = db.get(Lot, payload.lot_id)
    vaccine = db.get(Vaccine, payload.vaccine_id)
    if lot is None or lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote nao encontrado")
    if vaccine is None or vaccine.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacina nao encontrada")

    record = VaccinationRecord(**payload.model_dump(), created_at=DateTimeService.now_iso(), updated_at=None)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{record_id}", response_model=VaccinationRecordResponse)
def update_vaccination(
    record_id: str,
    payload: VaccinationRecordUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> VaccinationRecord:
    record = db.get(VaccinationRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro nao encontrado")
    lot = db.get(Lot, payload.lot_id)
    vaccine = db.get(Vaccine, payload.vaccine_id)
    if lot is None or lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote nao encontrado")
    if vaccine is None or vaccine.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacina nao encontrada")
    current_lot = db.get(Lot, record.lot_id)
    if current_lot is None or current_lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro nao encontrado")

    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    record.updated_at = DateTimeService.now_iso()
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vaccination(
    record_id: str,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> None:
    record = db.get(VaccinationRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro nao encontrado")
    lot = db.get(Lot, record.lot_id)
    if lot is None or lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro nao encontrado")
    db.delete(record)
    db.commit()
