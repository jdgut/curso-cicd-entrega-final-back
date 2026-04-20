from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.users import UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    service = UserService(db)
    return UserResponse.model_validate(service.register(payload))


@router.post("/login", response_model=UserResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)) -> UserResponse:
    service = UserService(db)
    return UserResponse.model_validate(service.login(str(payload.email), payload.password))
