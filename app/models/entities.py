from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TimestampMixin:
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)


class Farm(Base, TimestampMixin):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    lots: Mapped[list["Lot"]] = relationship(back_populates="farm")
    vaccines: Mapped[list["Vaccine"]] = relationship(back_populates="farm")
    users: Mapped[list["ApiUser"]] = relationship(back_populates="farm")


class Lot(Base, TimestampMixin):
    __tablename__ = "lots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    animal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farm: Mapped[Farm] = relationship(back_populates="lots")
    vaccination_records: Mapped[list["VaccinationRecord"]] = relationship(back_populates="lot")


class Vaccine(Base, TimestampMixin):
    __tablename__ = "vaccines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farm: Mapped[Farm] = relationship(back_populates="vaccines")
    vaccination_records: Mapped[list["VaccinationRecord"]] = relationship(back_populates="vaccine")


class VaccinationRecord(Base, TimestampMixin):
    __tablename__ = "vaccination_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("lots.id"), nullable=False, index=True)
    vaccine_id: Mapped[str] = mapped_column(ForeignKey("vaccines.id"), nullable=False, index=True)
    application_date: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    next_due_date: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    quantity_applied: Mapped[float | None] = mapped_column(Float, nullable=True)
    responsible_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), default="synced", nullable=False)

    lot: Mapped[Lot] = relationship(back_populates="vaccination_records")
    vaccine: Mapped[Vaccine] = relationship(back_populates="vaccination_records")


class AppSettings(Base, TimestampMixin):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    farm_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    alert_days_before: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    has_completed_onboarding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class DeletedEntity(Base):
    __tablename__ = "deleted_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    deleted_at: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)


class ApiUser(Base, TimestampMixin):
    __tablename__ = "api_users"
    __table_args__ = (UniqueConstraint("farm_id", "username", name="uq_api_users_farm_username"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farm: Mapped[Farm] = relationship(back_populates="users")
