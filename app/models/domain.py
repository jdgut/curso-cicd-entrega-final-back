from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    USER = "usuario"
    ADMIN = "administrador"


class TransportMode(str, Enum):
    WALKING = "caminando"
    BUS = "bus_universidad"


class TripDirection(str, Enum):
    METRO_TO_UNIVERSITY = "metro_universidad"
    UNIVERSITY_TO_METRO = "universidad_metro"


class TripState(str, Enum):
    IN_METRO = "en_metro"
    TO_UNIVERSITY = "en_desplazamiento_universidad"
    IN_UNIVERSITY = "en_universidad"
    TO_METRO = "en_desplazamiento_metro"


class AuditEventType(str, Enum):
    CREATED = "creado"
    UPDATED = "actualizado"
    JOINED = "usuario_unido"
    LEFT = "usuario_retirado"
    STATE_CHANGED = "estado_cambiado"
    FINALIZED = "finalizado"
    ARCHIVED = "archivado"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    created_trips: Mapped[list[Trip]] = relationship(back_populates="creator")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    meeting_point: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    transport_mode: Mapped[TransportMode] = mapped_column(SQLEnum(TransportMode), nullable=False)
    direction: Mapped[TripDirection] = mapped_column(SQLEnum(TripDirection), nullable=False)
    state: Mapped[TripState] = mapped_column(SQLEnum(TripState), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    creator: Mapped[User] = relationship(back_populates="created_trips")

    participants: Mapped[list[TripParticipant]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[TripAudit]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )


class TripParticipant(Base):
    __tablename__ = "trip_participants"
    __table_args__ = (UniqueConstraint("trip_id", "user_id", name="uq_trip_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    trip: Mapped[Trip] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()


class TripAudit(Base):
    __tablename__ = "trip_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[AuditEventType] = mapped_column(SQLEnum(AuditEventType), nullable=False)
    payload: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    trip: Mapped[Trip] = relationship(back_populates="audit_logs")
