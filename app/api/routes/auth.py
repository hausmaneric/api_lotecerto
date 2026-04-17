import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
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


def _raise_database_unavailable(exc: OperationalError) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Banco de dados indisponivel no momento.",
    ) from exc


def _raise_integrity_conflict(exc: IntegrityError) -> None:
    message = str(exc.orig).lower() if getattr(exc, "orig", None) is not None else str(exc).lower()
    detail = f"Conflito de dados ao salvar: {message}"

    if "api_users" in message and "username" in message:
        detail = "Usuario ja existe nesta fazenda."
    elif "farms" in message and "id" in message:
        detail = "Fazenda ja existe."
    elif "app_settings" in message and "id" in message:
        detail = "Configuracoes da fazenda ja existem."
    elif "unique constraint failed: api_users.username" in message:
        detail = "Usuario ja existe no banco atual da API."
    elif "unique constraint failed: api_users.farm_id, api_users.username" in message:
        detail = "Usuario ja existe nesta fazenda."
    elif "unique constraint failed: app_settings.id" in message:
        detail = "Configuracoes da fazenda ja existem."

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    ) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user_query = (
            select(ApiUser)
            .join(Farm, Farm.id == ApiUser.farm_id)
            .where(ApiUser.username == payload.username, ApiUser.is_active.is_(True))
        )
        if payload.farm_name:
            user_query = user_query.where(Farm.name == payload.farm_name)

        users = db.scalars(user_query).all()
    except OperationalError as exc:
        _raise_database_unavailable(exc)

    if len(users) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Informe a fazenda para entrar com este usuario.",
        )
    user = users[0] if users else None
    if user is None or not SecurityService.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario ou senha invalidos")

    try:
        farm = db.get(Farm, user.farm_id)
    except OperationalError as exc:
        _raise_database_unavailable(exc)

    if farm is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fazenda do usuario nao encontrada")

    token = SecurityService.create_access_token(user.id)
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
    try:
        if db.get(Farm, payload.farm_id) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fazenda ja existe")
        if db.scalar(
            select(ApiUser).where(
                ApiUser.farm_id == payload.farm_id,
                ApiUser.username == payload.username,
            )
        ) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ja existe")
    except OperationalError as exc:
        _raise_database_unavailable(exc)

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
    try:
        db.add(farm)
        db.add(user)
        db.add(app_settings)
        db.commit()
    except OperationalError as exc:
        db.rollback()
        _raise_database_unavailable(exc)
    except IntegrityError as exc:
        db.rollback()
        _raise_integrity_conflict(exc)

    token = SecurityService.create_access_token(user.id)
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
    try:
        if db.scalar(
            select(ApiUser).where(
                ApiUser.farm_id == farm.id,
                ApiUser.username == payload.username,
            )
        ) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ja existe")
    except OperationalError as exc:
        _raise_database_unavailable(exc)

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
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except OperationalError as exc:
        db.rollback()
        _raise_database_unavailable(exc)
    except IntegrityError as exc:
        db.rollback()
        _raise_integrity_conflict(exc)

    return CurrentUserResponse(
        id=user.id,
        farm_id=farm.id,
        farm_name=farm.name,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
    )
