from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.api.deps import get_current_farm, get_current_user
from app.db.database import get_db
from app.models.entities import AppSettings, ApiUser, DeletedEntity, Farm, Lot, VaccinationRecord, Vaccine
from app.schemas.dashboard import PushRequest, PushResponse, SyncResponse
from app.services.datetime_service import DateTimeService

router = APIRouter(prefix="/sync", tags=["sync"], dependencies=[Depends(get_current_user)])


def _raise_sync_database_error(exc: Exception) -> None:
    if isinstance(exc, OperationalError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponivel durante a sincronizacao.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Conflito de dados durante a sincronizacao.",
    ) from exc


def _serialize_public(model) -> dict:
    data = {key: value for key, value in model.__dict__.items() if not key.startswith("_")}
    data.pop("farm_id", None)
    data.pop("role", None)
    return data


def _updated_query(model, updated_since: str | None, farm_id: str):
    query = select(model).where(model.farm_id == farm_id)
    if updated_since:
        query = query.where(or_(model.updated_at >= updated_since, model.created_at >= updated_since))
    return query


def _upsert_rows(db: Session, model, rows: list[dict], farm_id: str) -> int:
    total = 0
    for row in rows:
        item_id = row.get("id")
        if not item_id:
            continue

        row_data = dict(row)
        if hasattr(model, "farm_id"):
            row_data["farm_id"] = farm_id

        instance = db.get(model, item_id)
        if instance is None:
            db.add(model(**row_data))
            total += 1
            continue

        if hasattr(instance, "farm_id") and instance.farm_id != farm_id:
            continue

        for field, value in row_data.items():
            if field == "id":
                continue
            setattr(instance, field, value)
        total += 1
    return total


def _apply_deleted_entities(db: Session, rows: list[dict], farm_id: str) -> int:
    total = 0
    model_map = {
        "farm": Farm,
        "lot": Lot,
        "vaccine": Vaccine,
        "vaccination_record": VaccinationRecord,
    }
    for row in rows:
        entity_type = row.get("entity_type")
        entity_id = row.get("entity_id")
        delete_id = row.get("id")
        if not entity_type or not entity_id or not delete_id:
            continue

        payload = dict(row)
        payload["farm_id"] = farm_id
        existing = db.get(DeletedEntity, delete_id)
        if existing is None:
            db.add(DeletedEntity(**payload))
        model = model_map.get(entity_type)
        if model is not None:
            instance = db.get(model, entity_id)
            if instance is not None:
                if hasattr(instance, "farm_id") and instance.farm_id != farm_id:
                    continue
                if entity_type == "vaccination_record":
                    lot = db.get(Lot, instance.lot_id)
                    if lot is None or lot.farm_id != farm_id:
                        continue
                db.delete(instance)
        total += 1
    return total


@router.get("/pull", response_model=SyncResponse)
def pull_sync(
    updated_since: str | None = Query(default=None),
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> SyncResponse:
    try:
        records_query = (
            select(VaccinationRecord)
            .join(VaccinationRecord.lot)
            .join(VaccinationRecord.vaccine)
            .where(Lot.farm_id == farm.id, Vaccine.farm_id == farm.id)
        )
        if updated_since:
            records_query = records_query.where(
                or_(VaccinationRecord.updated_at >= updated_since, VaccinationRecord.created_at >= updated_since)
            )

        return SyncResponse(
            farms=[_serialize_public(farm)],
            lots=[_serialize_public(item) for item in db.scalars(_updated_query(Lot, updated_since, farm.id)).all()],
            vaccines=[_serialize_public(item) for item in db.scalars(_updated_query(Vaccine, updated_since, farm.id)).all()],
            vaccination_records=[_serialize_public(item) for item in db.scalars(records_query).all()],
            settings=[_serialize_public(item) for item in db.scalars(_updated_query(AppSettings, updated_since, farm.id)).all()],
            deleted_entities=[_serialize_public(item) for item in db.scalars(_updated_query(DeletedEntity, updated_since, farm.id)).all()],
            server_time=DateTimeService.now_iso(),
        )
    except (OperationalError, IntegrityError) as exc:
        _raise_sync_database_error(exc)


@router.post("/push", response_model=PushResponse)
def push_sync(
    payload: PushRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
) -> PushResponse:
    try:
        farms_received = _upsert_rows(db, Farm, payload.farms, farm.id)
        lots_received = _upsert_rows(db, Lot, payload.lots, farm.id)
        vaccines_received = _upsert_rows(db, Vaccine, payload.vaccines, farm.id)
        vaccination_records_received = _upsert_rows(db, VaccinationRecord, payload.vaccination_records, farm.id)
        settings_received = _upsert_rows(db, AppSettings, payload.settings, farm.id)
        deleted_entities_received = _apply_deleted_entities(db, payload.deleted_entities, farm.id)
        db.commit()

        return PushResponse(
            farms_received=farms_received,
            lots_received=lots_received,
            vaccines_received=vaccines_received,
            vaccination_records_received=vaccination_records_received,
            settings_received=settings_received,
            deleted_entities_received=deleted_entities_received,
            server_time=DateTimeService.now_iso(),
        )
    except (OperationalError, IntegrityError) as exc:
        db.rollback()
        _raise_sync_database_error(exc)
