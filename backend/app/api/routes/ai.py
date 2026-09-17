from fastapi import APIRouter, HTTPException, status
from ...schemas.ai import AIChatRequest, AIChatResponse
from ...services.rag_service import RAGService
from ...llm.service import LLMService

router = APIRouter(prefix="/ai", tags=["Cira Institutional Intelligence"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Cira AI Assistant Chat with RAG Grounding",
    description="Ask questions about institutional policies, circulars, and governance directives. "
                "Answers are strictly grounded in ChromaDB vector records."
)
async def chat_with_cira(request: AIChatRequest) -> AIChatResponse:
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    try:
        # Step 1: Semantic retrieval of relevant knowledge chunks
        chunks = RAGService.retrieve(query=request.message, top_k=5)

        # Step 2: Grounded answer generation via LLM or graceful fallback
        response = LLMService.generate_answer(query=request.message, chunks=chunks)
        return response

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cira AI intelligence service error: {str(exc)}"
        )
