from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.core import deps
from app.core.security import verify_password, get_password_hash
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User, UserLogin

router = APIRouter()


@router.post("/register", response_model=User,
             responses={
                 400: {
                     "description": "Username or email already exists",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Username or email already exists"
                             }
                         }
                     }
                 },
             }
             )
async def register(
        *,
        db: Session = Depends(deps.get_db),
        user_in: UserCreate
):
    """
    Register a new user: Check if username/email exists, hash the password, and create a user.
    """
    # Check if the username or email already exists
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user_in.username) | (UserModel.email == user_in.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )

    # Hash the password
    hashed_password = get_password_hash(user_in.password)

    # Create a new user instance
    new_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True  # You can adjust default user status if needed
    )

    # Add the user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", responses={
    200: {"description": "Login successful",
          "content": {"application/json": {"example": {"message": "Login successful", "user_id": 1}}}},
    401: {"description": "Invalid password",
          "content": {"application/json": {"example": {"detail": "Invalid password"}}}},
    404: {"description": "User not found", "content": {"application/json": {"example": {"detail": "User not found"}}}},
})
async def login(
        request: Request,
        response: Response,
        user_in: UserLogin,
        db: Session = Depends(deps.get_db)
):
    """
    Login a user using their username and password, set user_id in session.
    """
    user = db.query(UserModel).filter(UserModel.username == user_in.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    # Store the user ID in the session to track the logged-in user
    request.session["user_id"] = user.id
    response.status_code = status.HTTP_200_OK
    return {"message": "Login successful", "user_id": user.id}


@router.post("/logout", responses={
    200: {"description": "Successfully logged out",
          "content": {"application/json": {"example": {"message": "Successfully logged out"}}}},
    400: {"description": "No active session to log out from",
          "content": {"application/json": {"example": {"detail": "No active session to log out from"}}}},
})
async def logout(request: Request):
    """
    Log out the user by clearing the session.
    """
    # Clear the session to log out the user
    if "user_id" in request.session:
        request.session.clear()
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active session to log out from"
        )
