from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Login request payload.
    Supports email or institutional username.
    """
    email: str = Field(..., min_length=1, description="Institutional email or username")
    password: str = Field(..., min_length=1, description="Account password")


class UserResponse(BaseModel):
    """
    Safe public user profile model.
    Never exposes password_hash or credentials.
    """
    id: str
    name: str
    email: str
    role: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None
    can_upload_documents: bool = True
    can_edit_documents: bool = True
    can_approve_directives: bool = True
    can_broadcast_nudge: bool = True

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """
    Authentication success token response containing JWT and user profile metadata.
    """
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    role: str
    department: Optional[str] = None
    user: UserResponse


class TokenData(BaseModel):
    """
    Decoded JWT token payload data.
    """
    user_id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
