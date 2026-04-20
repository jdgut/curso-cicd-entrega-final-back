from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import TransportMode, TripState
from app.schemas.trips import (
    HeatmapCell,
    HeatmapResponse,
    TripActionRequest,
    TripAuditResponse,
    TripCreateRequest,
    TripParticipantResponse,
    TripResponse,
    TripStateChangeRequest,
    TripUpdateRequest,
    VisitorHeatmapResponse,
)
from app.services.trips import STATE_ORDER, TripService

router = APIRouter(prefix="/trips", tags=["trips"])


def _to_response(trip) -> TripResponse:
    return TripResponse(
        id=trip.id,
        title=trip.title,
        meeting_point=trip.meeting_point,
        start_at=trip.start_at,
        transport_mode=trip.transport_mode,
        direction=trip.direction,
        state=trip.state,
        is_archived=trip.is_archived,
        creator_email=trip.creator.email,
        participants=[TripParticipantResponse(email=participant.user.email) for participant in trip.participants],
    )


@router.post("", response_model=TripResponse)
def create_trip(payload: TripCreateRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    trip = service.create_trip(
        actor_email=payload.actor_email,
        title=payload.title,
        meeting_point=payload.meeting_point,
        start_at=payload.start_at,
        transport_mode=payload.transport_mode,
        direction=payload.direction,
    )
    return _to_response(trip)


@router.get("", response_model=list[TripResponse])
def list_active_trips(db: Session = Depends(get_db)) -> list[TripResponse]:
    service = TripService(db)
    return [_to_response(trip) for trip in service.list_active()]


@router.patch("/{trip_id}", response_model=TripResponse)
def edit_trip(trip_id: int, payload: TripUpdateRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    trip = service.update_trip(
        trip_id=trip_id,
        actor_email=payload.actor_email,
        title=payload.title,
        meeting_point=payload.meeting_point,
        start_at=payload.start_at,
    )
    return _to_response(trip)


@router.post("/{trip_id}/join", response_model=TripResponse)
def join_trip(trip_id: int, payload: TripActionRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    return _to_response(service.join_trip(trip_id, payload.actor_email))


@router.post("/{trip_id}/leave", response_model=TripResponse)
def leave_trip(trip_id: int, payload: TripActionRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    return _to_response(service.leave_trip(trip_id, payload.actor_email))


@router.post("/{trip_id}/state", response_model=TripResponse)
def update_trip_state(trip_id: int, payload: TripStateChangeRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    return _to_response(service.change_state(trip_id, payload.actor_email, payload.new_state, payload.new_start_at))


@router.post("/{trip_id}/finalize", response_model=TripResponse)
def finalize_trip(trip_id: int, payload: TripActionRequest, db: Session = Depends(get_db)) -> TripResponse:
    service = TripService(db)
    return _to_response(service.finalize_trip(trip_id, payload.actor_email))


@router.get("/{trip_id}/audit", response_model=list[TripAuditResponse])
def trip_audit(trip_id: int, db: Session = Depends(get_db)) -> list[TripAuditResponse]:
    service = TripService(db)
    return [TripAuditResponse.model_validate(item) for item in service.get_audit(trip_id)]


@router.get("/metrics/heatmap", response_model=list[HeatmapResponse])
def heatmap(db: Session = Depends(get_db)) -> list[HeatmapResponse]:
    service = TripService(db)
    buckets = service.heatmap()
    return [
        HeatmapResponse(
            transport_mode=transport,
            cells=[HeatmapCell(state=state, count=buckets[transport][state]) for state in STATE_ORDER],
        )
        for transport in [TransportMode.WALKING, TransportMode.BUS]
    ]


@router.get("/metrics/heatmap/simulated", response_model=VisitorHeatmapResponse)
def simulated_heatmap() -> VisitorHeatmapResponse:
    return VisitorHeatmapResponse(
        heatmaps=[
            HeatmapResponse(
                transport_mode=TransportMode.WALKING,
                cells=[
                    HeatmapCell(state=TripState.IN_METRO, count=4),
                    HeatmapCell(state=TripState.TO_UNIVERSITY, count=6),
                    HeatmapCell(state=TripState.IN_UNIVERSITY, count=3),
                    HeatmapCell(state=TripState.TO_METRO, count=2),
                ],
            ),
            HeatmapResponse(
                transport_mode=TransportMode.BUS,
                cells=[
                    HeatmapCell(state=TripState.IN_METRO, count=1),
                    HeatmapCell(state=TripState.TO_UNIVERSITY, count=5),
                    HeatmapCell(state=TripState.IN_UNIVERSITY, count=2),
                    HeatmapCell(state=TripState.TO_METRO, count=4),
                ],
            ),
        ]
    )
