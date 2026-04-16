from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import ApiUser, Farm
from app.schemas.farm import FarmResponse, FarmUpdate
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/farms", tags=["farms"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[FarmResponse])
def list_farms(farm: Farm = Depends(get_current_farm)) -> list[Farm]:
    return [farm]


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: str,
    payload: FarmUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> Farm:
    if farm.id != farm_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado para outra fazenda")

    for field, value in payload.model_dump().items():
        setattr(farm, field, value)
    farm.updated_at = DateTimeService.now_iso()
    db.commit()
    db.refresh(farm)
    return farm
