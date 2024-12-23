from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.db.session import SessionLocal
from app.schedulers.priority_preemption_scheduler import AdvancedScheduler


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user from the session. If the user is not authenticated, raise an HTTPException.

    Args:
    - request: The FastAPI request object, which contains the session information.
    - db: Database session dependency, used to query the user model.

    Returns:
    - Optional[User]: The current user if authenticated, otherwise raises an HTTPException.
    """
    # Retrieve the user ID from the session (assuming session stores user_id)
    user_id = request.session.get("user_id")

    # If there is no user_id in session, raise unauthorized error
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Query the user from the database
    user = db.query(User).filter(User.id == user_id).first()

    # If the user does not exist, raise unauthorized error
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def get_scheduler():
    # Create the scheduler instance
    scheduler_instance = AdvancedScheduler()
    return scheduler_instance
