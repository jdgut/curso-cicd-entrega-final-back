from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.domain import TransportMode, TripDirection, TripState
from app.schemas.users import UserRegisterRequest
from app.services.trips import TripService
from app.services.users import UserService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_change_state_backward_requires_new_date(db_session):
    user_service = UserService(db_session)
    user_service.register(
        UserRegisterRequest(email="unitario@eafit.edu.co", password="password123", role="usuario")
    )
    trip_service = TripService(db_session)
    trip = trip_service.create_trip(
        actor_email="unitario@eafit.edu.co",
        title="Prueba",
        meeting_point="Puerta 1",
        start_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
        transport_mode=TransportMode.WALKING,
        direction=TripDirection.METRO_TO_UNIVERSITY,
    )

    trip_service.change_state(trip.id, "unitario@eafit.edu.co", TripState.TO_UNIVERSITY, None)

    with pytest.raises(HTTPException):
        trip_service.change_state(trip.id, "unitario@eafit.edu.co", TripState.IN_METRO, None)
