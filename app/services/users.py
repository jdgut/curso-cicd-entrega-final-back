import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.domain import User
from app.repositories.users import UserRepository
from app.schemas.users import UserRegisterRequest


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, payload: UserRegisterRequest) -> User:
        existing = self.user_repo.get_by_email(str(payload.email))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

        user = User(
            email=str(payload.email),
            password_hash=self._hash_password(payload.password),
            role=payload.role,
        )
        self.user_repo.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _hash_password(self, raw_password: str) -> str:
        # Contexto académico sin autenticación real: hash estable con salt para no guardar texto plano.
        salt = secrets.token_hex(16)
        digest = hashlib.sha256(f"{salt}{raw_password}".encode("utf-8")).hexdigest()
        return f"{salt}${digest}"

    def _verify_password(self, raw_password: str, stored_hash: str) -> bool:
        parts = stored_hash.split("$", 1)
        if len(parts) != 2:
            return False
        salt, expected_digest = parts
        calculated = hashlib.sha256(f"{salt}{raw_password}".encode("utf-8")).hexdigest()
        return secrets.compare_digest(calculated, expected_digest)

    def login(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user or not self._verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        return user

    def get_user_or_404(self, email: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user
