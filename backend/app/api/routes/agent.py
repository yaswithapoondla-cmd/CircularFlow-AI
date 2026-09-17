from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...agent.schemas import AgentChatRequest, AgentChatResponse
from ...agent.service import AgentService
from ...models.users import User
from ...auth.deps import get_optional_current_user

router = APIRouter(prefix="/agent", tags=["Cira Institutional AI Agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Cira Institutional AI Agent Workflow",
    description="Execute multi-capability reasoning over PostgreSQL governance records and ChromaDB RAG knowledge. "
                "Classifies intent, dispatches internal tools, and generates grounded institutional answers with tool traces."
)
async def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> AgentChatResponse:
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query message cannot be empty."
        )

    # Derive effective role context from authenticated token or request
    effective_role = None
    if current_user:
        effective_role = current_user.role
    elif request.user_role:
        effective_role = request.user_role

    try:
        response = AgentService.process_query(db=db, message=request.message)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution error: {str(exc)}"
        )
