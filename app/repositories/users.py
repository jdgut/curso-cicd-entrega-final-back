from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        return self.db.scalar(query)

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
