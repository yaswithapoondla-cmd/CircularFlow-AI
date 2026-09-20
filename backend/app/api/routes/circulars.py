import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ...schemas.circular import Circular, CircularListResponse, CircularCreate
from ...schemas.circular_gen import CircularGenerateRequest, GeneratedCircularContent, CircularPDFRequest
from ...services.circular_service import CircularService
from ...services.circular_gen_service import generate_circular as svc_generate_circular
from ...services.circular_pdf import build_circular_pdf
from ...db.database import get_db
from ...auth.deps import get_current_user
from ...models.users import User

router = APIRouter(prefix="/circulars", tags=["Circulars & Governance Directives"])


@router.post(
    "",
    response_model=Circular,
    status_code=status.HTTP_201_CREATED,
    summary="Create / Save Circular Draft",
    description="Persists a new circular draft in the PostgreSQL database. Authenticated with JWT. Does not publish it.",
)
async def create_circular(
    data: CircularCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Circular:
    """Authenticated: creates and persists a new circular in Draft status."""
    try:
        return CircularService.create_circular(
            db=db,
            data=data,
            current_user=current_user,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create circular: {str(exc)}",
        )

# ─────────────────────────────────────────────────────────────────────────────
# Phase 18: AI Circular Generation Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GeneratedCircularContent,
    summary="AI Circular Generation",
    description=(
        "Uses the configured LLM to generate a structured institutional circular from a topic description. "
        "Returns a DRAFT — never auto-published. Falls back to a template draft if LLM is unavailable."
    ),
)
async def generate_circular_ai(
    request: CircularGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> GeneratedCircularContent:
    """Authenticated: generates structured circular content using the LLM."""
    if not request.topic.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Circular topic cannot be empty.",
        )
    try:
        return svc_generate_circular(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Circular generation error: {str(exc)}",
        )


@router.post(
    "/generate-pdf",
    summary="Generate Official Circular PDF",
    description=(
        "Accepts final circular content and returns a downloadable branded PDF. "
        "Authentication required. PDF is generated server-side with ReportLab."
    ),
    response_class=Response,
)
async def generate_circular_pdf(
    request: CircularPDFRequest,
    current_user: User = Depends(get_current_user),
):
    """Authenticated: builds and streams a professional PDF of the circular."""
    try:
        pdf_bytes = build_circular_pdf(request)
        # Sanitize title for Content-Disposition filename
        safe_title = re.sub(r"[^\w\-]", "_", request.content.title[:50])
        filename = f"{safe_title}_{request.content.reference}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation error: {str(exc)}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Existing Circular Read Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=CircularListResponse,
    summary="List Institutional Circulars",
    description="Retrieve circulars from the PostgreSQL database with optional filtering by department, status, category, or search query."
)
async def get_circulars(
    department: Optional[str] = Query(None, description="Filter by issuing department"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Active, Superseded, Under Review, Draft)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keyword in title, ref number, or summary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> CircularListResponse:
    try:
        return CircularService.list_circulars(
            db=db,
            department=department,
            status=status_filter,
            category=category,
            search=search,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database query failed: {str(exc)}"
        )

@router.get(
    "/{circular_id}",
    response_model=Circular,
    summary="Get Circular By ID or Reference",
    description="Fetch a specific circular from the database by internal ID (e.g., 'circ-001') or ref number (e.g., 'CIR-2026-052')."
)
async def get_circular_by_id(
    circular_id: str,
    db: Session = Depends(get_db),
) -> Circular:
    try:
        circular = CircularService.get_circular_by_id(db=db, circular_id=circular_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database query failed: {str(exc)}"
        )
    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circular '{circular_id}' not found in the institutional repository."
        )
    return circular
