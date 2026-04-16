import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.entities import ApiUser, AppSettings, Farm
from app.schemas.auth import (
    CreateFarmUserRequest,
    CurrentUserResponse,
    LoginRequest,
    RegisterFarmRequest,
    TokenResponse,
)
from app.services.datetime_service import DateTimeService
from app.services.security import SecurityService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(ApiUser).where(ApiUser.username == payload.username, ApiUser.is_active.is_(True)))
    if user is None or not SecurityService.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario ou senha invalidos")

    farm = db.get(Farm, user.farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fazenda do usuario nao encontrada")

    token = SecurityService.create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        display_name=user.display_name,
        farm_id=farm.id,
        farm_name=farm.name,
        role=user.role,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: ApiUser = Depends(get_current_user), farm: Farm = Depends(get_current_farm)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        farm_id=farm.id,
        farm_name=farm.name,
        username=current_user.username,
        display_name=current_user.display_name,
        role=current_user.role,
    )


@router.post("/register-farm", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_farm(payload: RegisterFarmRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.get(Farm, payload.farm_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fazenda ja existe")
    if db.scalar(select(ApiUser).where(ApiUser.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ja existe")

    now = DateTimeService.now_iso()
    farm = Farm(
        id=payload.farm_id,
        name=payload.farm_name,
        owner_name=payload.owner_name,
        created_at=now,
        updated_at=None,
    )
    user = ApiUser(
        id=str(uuid.uuid4()),
        farm_id=farm.id,
        username=payload.username,
        password_hash=SecurityService.hash_password(payload.password),
        display_name=payload.display_name,
        role="owner",
        is_active=True,
        created_at=now,
        updated_at=None,
    )
    app_settings = AppSettings(
        id=f"settings-{farm.id}",
        farm_id=farm.id,
        farm_name=farm.name,
        alert_days_before=7,
        has_completed_onboarding=False,
        created_at=now,
        updated_at=None,
    )
    db.add(farm)
    db.add(user)
    db.add(app_settings)
    db.commit()

    token = SecurityService.create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        display_name=user.display_name,
        farm_id=farm.id,
        farm_name=farm.name,
        role=user.role,
    )


@router.post("/users", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
def create_farm_user(
    payload: CreateFarmUserRequest,
    current_user: ApiUser = Depends(get_current_user),
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para criar novos acessos")
    if db.scalar(select(ApiUser).where(ApiUser.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ja existe")

    now = DateTimeService.now_iso()
    user = ApiUser(
        id=payload.user_id,
        farm_id=farm.id,
        username=payload.username,
        password_hash=SecurityService.hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
        is_active=True,
        created_at=now,
        updated_at=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return CurrentUserResponse(
        id=user.id,
        farm_id=farm.id,
        farm_name=farm.name,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
    )
