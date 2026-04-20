from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.domain import (
    AuditEventType,
    TransportMode,
    Trip,
    TripAudit,
    TripDirection,
    TripParticipant,
    TripState,
    User,
    UserRole,
)
from app.repositories.trips import TripRepository
from app.services.users import UserService

STATE_ORDER = [TripState.IN_METRO, TripState.TO_UNIVERSITY, TripState.IN_UNIVERSITY, TripState.TO_METRO]


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TripService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.trip_repo = TripRepository(db)
        self.user_service = UserService(db)

    def _assert_can_edit(self, trip: Trip, actor: User) -> None:
        if actor.id != trip.creator_id and actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos de edición")

    def _add_audit(self, trip_id: int, user_email: str, event: AuditEventType, payload: str = "") -> None:
        self.trip_repo.add_audit(
            TripAudit(
                trip_id=trip_id,
                user_email=user_email,
                event_type=event,
                payload=payload,
            )
        )

    def _apply_automatic_rules(self, trip: Trip) -> None:
        now = _utcnow()
        if trip.is_archived:
            return

        if now >= trip.start_at + timedelta(hours=2):
            trip.is_archived = True
            self._add_audit(trip.id, "system", AuditEventType.ARCHIVED, "Archivado automáticamente a las 2 horas")
            return

        if now >= trip.start_at + timedelta(minutes=5):
            if trip.direction == TripDirection.METRO_TO_UNIVERSITY and trip.state == TripState.IN_METRO:
                trip.state = TripState.TO_UNIVERSITY
                self._add_audit(trip.id, "system", AuditEventType.STATE_CHANGED, "Cambio automático a desplazamiento")
            if trip.direction == TripDirection.UNIVERSITY_TO_METRO and trip.state == TripState.IN_UNIVERSITY:
                trip.state = TripState.TO_METRO
                self._add_audit(trip.id, "system", AuditEventType.STATE_CHANGED, "Cambio automático a desplazamiento")

    def _hydrate_and_validate(self, trip_id: int) -> Trip:
        trip = self.trip_repo.get(trip_id)
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desplazamiento no encontrado")
        self._apply_automatic_rules(trip)
        return trip

    def create_trip(
        self,
        actor_email: str,
        title: str,
        meeting_point: str,
        start_at: datetime,
        transport_mode: TransportMode,
        direction: TripDirection,
    ) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        initial_state = TripState.IN_METRO if direction == TripDirection.METRO_TO_UNIVERSITY else TripState.IN_UNIVERSITY
        trip = Trip(
            title=title,
            meeting_point=meeting_point,
            start_at=start_at,
            transport_mode=transport_mode,
            direction=direction,
            state=initial_state,
            creator_id=actor.id,
        )
        self.trip_repo.add(trip)
        self.trip_repo.add_participant(TripParticipant(trip_id=trip.id, user_id=actor.id))
        self._add_audit(trip.id, actor.email, AuditEventType.CREATED, "Desplazamiento creado")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def list_active(self) -> list[Trip]:
        trips = self.trip_repo.list_active()
        for trip in trips:
            self._apply_automatic_rules(trip)
        self.db.commit()
        return [trip for trip in trips if not trip.is_archived]

    def update_trip(
        self,
        trip_id: int,
        actor_email: str,
        title: str | None,
        meeting_point: str | None,
        start_at: datetime | None,
    ) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        trip = self._hydrate_and_validate(trip_id)
        self._assert_can_edit(trip, actor)

        if _utcnow() >= trip.start_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede editar un desplazamiento iniciado")

        if title is not None:
            trip.title = title
        if meeting_point is not None:
            trip.meeting_point = meeting_point
        if start_at is not None:
            trip.start_at = start_at

        self._add_audit(trip.id, actor.email, AuditEventType.UPDATED, "Edición de datos básicos")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def join_trip(self, trip_id: int, actor_email: str) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        trip = self._hydrate_and_validate(trip_id)
        if _utcnow() > trip.start_at + timedelta(hours=1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede unir después de 1 hora de inicio")

        if any(participant.user_id == actor.id for participant in trip.participants):
            return trip

        self.trip_repo.add_participant(TripParticipant(trip_id=trip.id, user_id=actor.id))
        self._add_audit(trip.id, actor.email, AuditEventType.JOINED, "Usuario se unió")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def leave_trip(self, trip_id: int, actor_email: str) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        trip = self._hydrate_and_validate(trip_id)

        if _utcnow() > trip.start_at + timedelta(hours=1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede retirar después de 1 hora de inicio")

        participant = next((item for item in trip.participants if item.user_id == actor.id), None)
        if not participant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no participa en el desplazamiento")
        if trip.creator_id == actor.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El creador no puede retirarse")

        self.trip_repo.remove_participant(participant)
        self._add_audit(trip.id, actor.email, AuditEventType.LEFT, "Usuario se retiró")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def change_state(self, trip_id: int, actor_email: str, new_state: TripState, new_start_at: datetime | None) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        trip = self._hydrate_and_validate(trip_id)
        self._assert_can_edit(trip, actor)

        current_index = STATE_ORDER.index(trip.state)
        next_state = STATE_ORDER[(current_index + 1) % len(STATE_ORDER)]
        target_index = STATE_ORDER.index(new_state)

        if new_state != next_state:
            if target_index < current_index:
                if new_start_at is None or new_start_at <= _utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Para retroceder estado se requiere nueva fecha y hora futura",
                    )
                trip.start_at = new_start_at
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transición de estado inválida")

        trip.state = new_state
        self._add_audit(trip.id, actor.email, AuditEventType.STATE_CHANGED, f"Nuevo estado: {new_state.value}")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def finalize_trip(self, trip_id: int, actor_email: str) -> Trip:
        actor = self.user_service.get_user_or_404(actor_email)
        trip = self._hydrate_and_validate(trip_id)
        self._assert_can_edit(trip, actor)

        trip.finalized_at = _utcnow()
        trip.is_archived = True
        self._add_audit(trip.id, actor.email, AuditEventType.FINALIZED, "Finalización manual")
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def get_audit(self, trip_id: int) -> list[TripAudit]:
        trip = self._hydrate_and_validate(trip_id)
        _ = trip
        self.db.commit()
        return self.trip_repo.list_audit(trip_id)

    def heatmap(self) -> dict[TransportMode, dict[TripState, int]]:
        buckets: dict[TransportMode, dict[TripState, int]] = {
            TransportMode.WALKING: {state: 0 for state in STATE_ORDER},
            TransportMode.BUS: {state: 0 for state in STATE_ORDER},
        }
        trips = self.list_active()
        for trip in trips:
            buckets[trip.transport_mode][trip.state] += 1
        return buckets
