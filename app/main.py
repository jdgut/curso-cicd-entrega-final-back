import hashlib
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.trips import router as trip_router
from app.api.users import router as user_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.domain import User, UserRole

allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]


def _hash_password(raw_password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}{raw_password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def seed_demo_users() -> None:
    db = SessionLocal()
    try:
        for idx in range(1, 16):
            email = f"test{idx}@eafit.edu.co"
            exists = db.scalar(select(User.id).where(User.email == email))
            if exists:
                continue

            db.add(
                User(
                    email=email,
                    password_hash=_hash_password("testtest"),
                    role=UserRole.USER,
                )
            )

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_demo_users()
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(user_router, prefix="/api")
app.include_router(trip_router, prefix="/api")
