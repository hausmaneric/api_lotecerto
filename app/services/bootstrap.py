import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import ApiUser, AppSettings, Farm
from app.services.datetime_service import DateTimeService
from app.services.security import SecurityService


class BootstrapService:
    @staticmethod
    def ensure_defaults(db: Session) -> None:
        now = DateTimeService.now_iso()

        farm = db.get(Farm, "default-farm")
        if farm is None:
            farm = Farm(
                id="default-farm",
                name="Minha Fazenda",
                owner_name="Administrador",
                created_at=now,
                updated_at=None,
            )
            db.add(farm)

        app_settings = db.get(AppSettings, "default-settings")
        if app_settings is None:
            db.add(
                AppSettings(
                    id="default-settings",
                    farm_id="default-farm",
                    farm_name="Minha Fazenda",
                    alert_days_before=7,
                    has_completed_onboarding=False,
                    created_at=now,
                    updated_at=None,
                )
            )

        user = db.scalar(select(ApiUser).where(ApiUser.username == settings.default_admin_username))
        if user is None:
            db.add(
                ApiUser(
                    id=str(uuid.uuid4()),
                    farm_id="default-farm",
                    username=settings.default_admin_username,
                    password_hash=SecurityService.hash_password(settings.default_admin_password),
                    display_name="Administrador",
                    role="owner",
                    is_active=True,
                    created_at=now,
                    updated_at=None,
                )
            )

        db.commit()
