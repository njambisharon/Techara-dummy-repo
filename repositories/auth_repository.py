from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.organisation import Organisation
from models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


def get_user_by_phone(db: Session, phone_number: str) -> User | None:
    return db.scalar(select(User).where(User.phone_number == phone_number))


def get_organisation_by_name(
    db: Session, organisation_name: str
) -> Organisation | None:
    return db.scalar(
        select(Organisation).where(
            func.lower(Organisation.organisation_name) == organisation_name.lower()
        )
    )


def create_organisation_and_operator(
    db: Session,
    organisation: Organisation,
    user: User,
) -> None:
    try:
        db.add(organisation)
        db.flush()

        user.organisation_id = organisation.organisation_id
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()
        raise


def update_user_password(
    db: Session,
    user: User,
    password_hash: str,
) -> None:
    try:
        user.password_hash = password_hash
        user.must_change_password = False
        db.commit()
    except Exception:
        db.rollback()
        raise
