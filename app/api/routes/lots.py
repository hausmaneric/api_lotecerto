from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, Farm, Lot, VaccinationRecord
from app.schemas.lot import LotCreate, LotResponse, LotUpdate
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/lots", tags=["lots"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[LotResponse])
def list_lots(
    farm_id: str | None = Query(default=None),
    only_active: bool = False,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> list[Lot]:
    effective_farm_id = farm.id if farm_id is None else farm_id
    if effective_farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado para outra fazenda")

    query = select(Lot).where(Lot.farm_id == farm.id)
    if only_active:
        query = query.where(Lot.is_active.is_(True))
    query = query.order_by(Lot.name)
    return list(db.scalars(query).all())


@router.post("", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(
    payload: LotCreate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> Lot:
    if db.get(Lot, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lote ja existe")
    if payload.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nao e permitido criar lote em outra fazenda")

    lot = Lot(**payload.model_dump(), created_at=DateTimeService.now_iso(), updated_at=None)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.put("/{lot_id}", response_model=LotResponse)
def update_lot(
    lot_id: str,
    payload: LotUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> Lot:
    lot = db.get(Lot, lot_id)
    if lot is None or lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote nao encontrado")
    if payload.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nao e permitido mover lote para outra fazenda")

    for field, value in payload.model_dump().items():
        setattr(lot, field, value)
    lot.updated_at = DateTimeService.now_iso()
    db.commit()
    db.refresh(lot)
    return lot


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lot(
    lot_id: str,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> None:
    lot = db.get(Lot, lot_id)
    if lot is None or lot.farm_id != farm.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote nao encontrado")

    has_records = db.scalar(select(VaccinationRecord.id).where(VaccinationRecord.lot_id == lot_id).limit(1))
    if has_records is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lote possui historico vinculado")

    db.delete(lot)
    db.commit()
