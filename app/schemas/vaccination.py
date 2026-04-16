from pydantic import BaseModel

from app.schemas.common import ApiSchema


class VaccinationRecordBase(BaseModel):
    lot_id: str
    vaccine_id: str
    application_date: str
    next_due_date: str | None = None
    quantity_applied: float | None = None
    responsible_name: str | None = None
    notes: str | None = None
    sync_status: str = "synced"


class VaccinationRecordCreate(VaccinationRecordBase):
    id: str


class VaccinationRecordUpdate(VaccinationRecordBase):
    pass


class VaccinationRecordResponse(ApiSchema):
    id: str
    lot_id: str
    vaccine_id: str
    application_date: str
    next_due_date: str | None = None
    quantity_applied: float | None = None
    responsible_name: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str | None = None
    sync_status: str


class VaccinationRecordDetails(ApiSchema):
    id: str
    lot_id: str
    vaccine_id: str
    lot_name: str
    vaccine_name: str
    application_date: str
    next_due_date: str | None = None
    quantity_applied: float | None = None
    responsible_name: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str | None = None
    sync_status: str
    status: str
