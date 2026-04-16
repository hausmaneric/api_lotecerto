from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import ApiUser, Farm
from app.services.security import SecurityService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> ApiUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token nao informado")

    username, _ = SecurityService.decode_token(credentials.credentials)
    user = db.scalar(select(ApiUser).where(ApiUser.username == username, ApiUser.is_active.is_(True)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado")
    return user


def get_current_farm(
    current_user: ApiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Farm:
    farm = db.get(Farm, current_user.farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fazenda do usuario nao encontrada")
    return farm
