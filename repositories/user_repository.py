from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id) -> User | None:
        return db.scalar(select(User).where(User.user_id == user_id))

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def get_by_phone(self, db: Session, phone_number: str) -> User | None:
        return db.scalar(select(User).where(User.phone_number == phone_number))

    def get_by_id_and_organisation(
        self, db: Session, user_id, organisation_id
    ) -> User | None:
        return db.scalar(
            select(User).where(
                User.user_id == user_id,
                User.organisation_id == organisation_id,
            )
        )

    def list_for_organisation(self, db: Session, organisation_id) -> list[User]:
        return db.scalars(
            select(User)
            .where(User.organisation_id == organisation_id)
            .order_by(User.created_at.desc())
        ).all()

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def save(self, db: Session, user: User) -> User:
        db.commit()
        db.refresh(user)
        return user


user_repository = UserRepository()
