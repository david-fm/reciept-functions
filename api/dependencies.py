from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timezone
from services.auth_service import get_user
from core.security import oauth2_schema
from database import get_db
from core.config import settings
from models import TokenData, Usuario
from services.subscription_service import verify_subscription


async def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)],
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Session = Depends(get_db)  # Inject db here
):
    # This ensures the subscription status is verified/updated *before*
    # the active check or any further processing.
    # If verify_subscription determines the user is inactive, it will
    # set user.active to False in the database.
    is_active = await verify_subscription(current_user, db)

    if not is_active:
        # Raise 402 if no active subscription, as per your endpoint's requirement
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    return current_user


def log_operation(user_id: UUID, operation: str, resource: str, resource_id: Optional[str] = None):
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"{timestamp} - User {user_id} - {operation} - {resource}"
    if resource_id:
        log_entry += f" - ID: {resource_id}"

    # In a real app, you'd log to a proper logging system
    print(log_entry)
