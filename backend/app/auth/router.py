from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.users import User
from .schemas import LoginRequest, TokenResponse, UserResponse
from .service import AuthService
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User and Generate JWT Token",
    description="Authenticates institutional users (Registrar, Faculty, Student) with email/username and password. "
                "Returns signed JWT access token, user profile metadata, and role attributes."
)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    user = AuthService.authenticate_user(
        db=db,
        identifier=credentials.email,
        password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthService.build_token_response(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Authenticated User Profile",
    description="Returns the currently authenticated user profile based on the validated JWT Bearer token. "
                "Never exposes password hash or sensitive credentials."
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)
