"""
Temporary diagnostic route for testing Resend connectivity.
POST /api/v1/email/test-resend
"""
from fastapi import APIRouter, Depends
from ...auth.deps import get_current_user
from ...models.users import User
from ...services.email_service import test_resend_connectivity

router = APIRouter(
    prefix="/email",
    tags=["Email Diagnostic"],
)


@router.post("/test-resend", summary="Test Resend Connectivity")
def test_resend_endpoint(current_user: User = Depends(get_current_user)):
    """
    Sends exactly one isolated test email using the existing Resend integration:
      From: onboarding@resend.dev
      To: delivered@resend.dev
      Subject: CircularFlow AI Resend Connectivity Test
      Body: This is a temporary connectivity test for CircularFlow AI.

    Requires valid JWT auth token.
    Creates NO database records.
    Never returns secrets or API keys.
    """
    return test_resend_connectivity()
