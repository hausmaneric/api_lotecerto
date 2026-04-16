from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, Farm, VaccinationRecord, Vaccine
from app.schemas.vaccine import VaccineCreate, VaccineResponse, VaccineUpdate
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/vaccines", tags=["vaccines"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[VaccineResponse])
def list_vaccines(
    only_active: bool = Query(default=False),
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> list[Vaccine]:
    query = select(Vaccine).where(Vaccine.farm_id == farm.id)
    if only_active:
        query = query.where(Vaccine.is_active.is_(True))
    query = query.order_by(Vaccine.name)
    return list(db.scalars(query).all())


@router.post("", response_model=VaccineResponse, status_code=status.HTTP_201_CREATED)
def create_vaccine(
    payload: VaccineCreate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> Vaccine:
    if db.get(Vaccine, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vacina ja existe")

    vaccine = Vaccine(
        id=payload.id,
        farm_id=farm.id,
        name=payload.name,
        description=payload.description,
        interval_days=payload.interval_days,
        is_mandatory=payload.is_mandatory,
        is_active=payload.is_active,
        created_at=DateTimeService.now_iso(),
        updated_at=None,
    )
    db.add(vaccine)
    db.commit()
    db.refresh(vaccine)
    return vaccine


@router.put("/{vaccine_id}", response_model=VaccineResponse)
def update_vaccine(
    vaccine_id: str,
    payload: VaccineUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> Vaccine:
    vaccine = db.get(Vaccine, vaccine_id)
    if vaccine is None or vaccine.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacina nao encontrada")

    for field, value in payload.model_dump().items():
        setattr(vaccine, field, value)
    vaccine.updated_at = DateTimeService.now_iso()
    db.commit()
    db.refresh(vaccine)
    return vaccine


@router.delete("/{vaccine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vaccine(
    vaccine_id: str,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> None:
    vaccine = db.get(Vaccine, vaccine_id)
    if vaccine is None or vaccine.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacina nao encontrada")

    has_records = db.scalar(select(VaccinationRecord.id).where(VaccinationRecord.vaccine_id == vaccine_id).limit(1))
    if has_records is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vacina possui historico vinculado")

    db.delete(vaccine)
    db.commit()
