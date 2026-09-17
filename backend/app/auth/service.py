from typing import Optional
from sqlalchemy.orm import Session
from ..models.users import User
from .security import verify_password, create_access_token
from .schemas import TokenResponse, UserResponse

# Friendly aliases mapping for institutional usernames
USERNAME_ALIASES = {
    "registrar": "registrar@vignan.ac.in",
    "admin": "registrar@vignan.ac.in",
    "faculty": "hod.cse@vignan.ac.in",
    "hod": "hod.cse@vignan.ac.in",
    "student": "vikram.22cse088@vignan.ac.in",
    "vikram": "vikram.22cse088@vignan.ac.in",
}


class AuthService:
    @staticmethod
    def get_user_by_identifier(db: Session, identifier: str) -> Optional[User]:
        clean_id = identifier.strip().lower()
        # Resolve username alias if provided
        target_email = USERNAME_ALIASES.get(clean_id, clean_id)

        user = db.query(User).filter(User.email.ilike(target_email)).first()
        if not user and clean_id != target_email:
            user = db.query(User).filter(User.email.ilike(clean_id)).first()
        if not user:
            # Also try matching user id
            user = db.query(User).filter(User.id == identifier.strip()).first()
        return user

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
        user = AuthService.get_user_by_identifier(db, identifier)
        if not user:
            return None
        if not user.password_hash:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def build_token_response(user: User) -> TokenResponse:
        claims = {
            "role": user.role,
            "email": user.email,
            "name": user.name,
            "department": user.department_name,
        }
        token = create_access_token(subject=user.id, claims=claims)
        user_resp = UserResponse.model_validate(user)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            department=user.department_name,
            user=user_resp,
        )
