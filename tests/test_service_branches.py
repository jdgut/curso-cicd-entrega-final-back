from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.domain import TransportMode, TripDirection, TripState, UserRole
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


def _register(user_service: UserService, email: str, role: UserRole = UserRole.USER) -> None:
    user_service.register(UserRegisterRequest(email=email, password="password123", role=role))


def _create_trip(trip_service: TripService, actor_email: str, start_delta: timedelta) -> int:
    trip = trip_service.create_trip(
        actor_email=actor_email,
        title="Prueba",
        meeting_point="Puerta 1",
        start_at=datetime.now(UTC).replace(tzinfo=None) + start_delta,
        transport_mode=TransportMode.WALKING,
        direction=TripDirection.METRO_TO_UNIVERSITY,
    )
    return trip.id


def test_user_login_nonexistent_user_raises_401(db_session):
    user_service = UserService(db_session)

    with pytest.raises(HTTPException) as exc:
        user_service.login("nadie@eafit.edu.co", "password123")

    assert exc.value.status_code == 401


def test_user_verify_password_invalid_hash_returns_false(db_session):
    user_service = UserService(db_session)
    assert user_service._verify_password("password123", "invalidhash") is False


def test_update_trip_after_start_raises_400(db_session):
    user_service = UserService(db_session)
    _register(user_service, "editora@eafit.edu.co")

    trip_service = TripService(db_session)
    trip_id = _create_trip(trip_service, "editora@eafit.edu.co", timedelta(minutes=-1))

    with pytest.raises(HTTPException) as exc:
        trip_service.update_trip(
            trip_id=trip_id,
            actor_email="editora@eafit.edu.co",
            title="Nuevo titulo",
            meeting_point=None,
            start_at=None,
        )

    assert exc.value.status_code == 400


def test_leave_trip_creator_is_forbidden(db_session):
    user_service = UserService(db_session)
    _register(user_service, "creador@eafit.edu.co")

    trip_service = TripService(db_session)
    trip_id = _create_trip(trip_service, "creador@eafit.edu.co", timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc:
        trip_service.leave_trip(trip_id, "creador@eafit.edu.co")

    assert exc.value.status_code == 400


def test_leave_trip_non_participant_raises_404(db_session):
    user_service = UserService(db_session)
    _register(user_service, "creador2@eafit.edu.co")
    _register(user_service, "ajeno@eafit.edu.co")

    trip_service = TripService(db_session)
    trip_id = _create_trip(trip_service, "creador2@eafit.edu.co", timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc:
        trip_service.leave_trip(trip_id, "ajeno@eafit.edu.co")

    assert exc.value.status_code == 404


def test_join_trip_after_one_hour_raises_400(db_session):
    user_service = UserService(db_session)
    _register(user_service, "creador3@eafit.edu.co")
    _register(user_service, "tarde@eafit.edu.co")

    trip_service = TripService(db_session)
    trip_id = _create_trip(trip_service, "creador3@eafit.edu.co", timedelta(hours=-2))

    with pytest.raises(HTTPException) as exc:
        trip_service.join_trip(trip_id, "tarde@eafit.edu.co")

    assert exc.value.status_code == 400


def test_change_state_invalid_forward_transition_raises_400(db_session):
    user_service = UserService(db_session)
    _register(user_service, "estado@eafit.edu.co")

    trip_service = TripService(db_session)
    trip_id = _create_trip(trip_service, "estado@eafit.edu.co", timedelta(minutes=15))

    with pytest.raises(HTTPException) as exc:
        trip_service.change_state(
            trip_id=trip_id,
            actor_email="estado@eafit.edu.co",
            new_state=TripState.IN_UNIVERSITY,
            new_start_at=None,
        )

    assert exc.value.status_code == 400


def test_list_active_auto_archives_old_trip(db_session):
    user_service = UserService(db_session)
    _register(user_service, "archivo@eafit.edu.co")

    trip_service = TripService(db_session)
    old_trip_id = _create_trip(trip_service, "archivo@eafit.edu.co", timedelta(hours=-3))

    active = trip_service.list_active()
    reloaded = trip_service.trip_repo.get(old_trip_id)

    assert active == []
    assert reloaded is not None
    assert reloaded.is_archived is True
