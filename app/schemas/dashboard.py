from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    active_lots_count: int
    inactive_lots_count: int
    active_vaccines_count: int
    overdue_count: int
    upcoming_count: int
    total_records_count: int


class SyncResponse(BaseModel):
    farms: list[dict]
    lots: list[dict]
    vaccines: list[dict]
    vaccination_records: list[dict]
    settings: list[dict]
    deleted_entities: list[dict]
    server_time: str


class PushRequest(BaseModel):
    farms: list[dict] = []
    lots: list[dict] = []
    vaccines: list[dict] = []
    vaccination_records: list[dict] = []
    settings: list[dict] = []
    deleted_entities: list[dict] = []


class PushResponse(BaseModel):
    farms_received: int
    lots_received: int
    vaccines_received: int
    vaccination_records_received: int
    settings_received: int
    deleted_entities_received: int
    server_time: str
