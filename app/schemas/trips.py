from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.domain import AuditEventType, TransportMode, TripDirection, TripState


class TripCreateRequest(BaseModel):
    actor_email: str
    title: str = Field(min_length=3, max_length=120)
    meeting_point: str = Field(min_length=3, max_length=255)
    start_at: datetime
    transport_mode: TransportMode
    direction: TripDirection


class TripUpdateRequest(BaseModel):
    actor_email: str
    title: str | None = Field(default=None, min_length=3, max_length=120)
    meeting_point: str | None = Field(default=None, min_length=3, max_length=255)
    start_at: datetime | None = None


class TripActionRequest(BaseModel):
    actor_email: str


class TripStateChangeRequest(BaseModel):
    actor_email: str
    new_state: TripState
    new_start_at: datetime | None = None


class TripParticipantResponse(BaseModel):
    email: str


class TripResponse(BaseModel):
    id: int
    title: str
    meeting_point: str
    start_at: datetime
    transport_mode: TransportMode
    direction: TripDirection
    state: TripState
    is_archived: bool
    creator_email: str
    participants: list[TripParticipantResponse]


class TripAuditResponse(BaseModel):
    event_type: AuditEventType
    user_email: str
    payload: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HeatmapCell(BaseModel):
    state: TripState
    count: int


class HeatmapResponse(BaseModel):
    transport_mode: TransportMode
    cells: list[HeatmapCell]


class VisitorHeatmapResponse(BaseModel):
    simulated: bool = True
    heatmaps: list[HeatmapResponse]

    @field_validator("heatmaps")
    @classmethod
    def ensure_not_empty(cls, value: list[HeatmapResponse]) -> list[HeatmapResponse]:
        if not value:
            raise ValueError("Se requiere al menos un mapa de calor")
        return value
