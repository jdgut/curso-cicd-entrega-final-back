from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.domain import Trip, TripAudit, TripParticipant


class TripRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, trip_id: int) -> Trip | None:
        query = (
            select(Trip)
            .where(Trip.id == trip_id)
            .options(joinedload(Trip.participants).joinedload(TripParticipant.user), joinedload(Trip.creator))
        )
        return self.db.scalar(query)

    def list_active(self) -> list[Trip]:
        query = (
            select(Trip)
            .where(Trip.is_archived.is_(False))
            .options(joinedload(Trip.participants).joinedload(TripParticipant.user), joinedload(Trip.creator))
            .order_by(Trip.start_at)
        )
        return list(self.db.scalars(query).unique())

    def add(self, trip: Trip) -> Trip:
        self.db.add(trip)
        self.db.flush()
        return trip

    def add_participant(self, participant: TripParticipant) -> TripParticipant:
        self.db.add(participant)
        self.db.flush()
        return participant

    def remove_participant(self, participant: TripParticipant) -> None:
        self.db.delete(participant)
        self.db.flush()

    def add_audit(self, audit: TripAudit) -> None:
        self.db.add(audit)
        self.db.flush()

    def list_audit(self, trip_id: int) -> list[TripAudit]:
        query = select(TripAudit).where(TripAudit.trip_id == trip_id).order_by(TripAudit.created_at)
        return list(self.db.scalars(query))

    def archive_old(self, limit_date: datetime) -> list[Trip]:
        query = select(Trip).where(Trip.is_archived.is_(False), Trip.start_at <= limit_date)
        trips = list(self.db.scalars(query))
        for trip in trips:
            trip.is_archived = True
        self.db.flush()
        return trips
