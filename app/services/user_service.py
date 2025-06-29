from sqlmodel import Session, select
from datetime import datetime
from app.models.user import User, AuthProvider
from typing import Optional

def get_or_create_user(
    session: Session,
    firebase_uid: str,
    email: str,
    display_name: Optional[str] = None,
    photo_url: Optional[str] = None,
    auth_provider: AuthProvider = AuthProvider.EMAIL,
    is_email_verified: bool = False,
    password: Optional[str] = None
) -> User:
    """Get existing user or create new one"""
    statement = select(User).where(User.firebase_uid == firebase_uid)
    user = session.exec(statement).first()

    if user:
        user.email = email
        user.display_name = display_name
        user.photo_url = photo_url
        user.is_email_verified = is_email_verified
        if password:
            user.password = password
        user.updated_at = datetime.now()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    user = User(
        firebase_uid = firebase_uid,
        email = email,
        password = password,
        display_name = display_name,
        photo_url = photo_url,
        auth_provider = auth_provider,
        is_email_verified = is_email_verified
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user 